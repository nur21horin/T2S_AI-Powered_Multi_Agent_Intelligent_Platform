"""Atomic, Redis-backed fixed-window rate-limit primitives."""
from dataclasses import dataclass
import hashlib
import hmac
import ipaddress
import math
import re
from typing import Literal, Protocol
from uuid import UUID

from pydantic import SecretStr
from redis.exceptions import RedisError

from app.core.exceptions import ServiceUnavailableError, TooManyRequestsError

RATE_LIMIT_KEY_PREFIX = "t2s:ratelimit:v1:"

# INCR, expiry handling, and TTL retrieval happen in one Redis operation. If a
# pre-existing counter has lost its expiry, repair it rather than leave it
# permanently allocated.
_FIXED_WINDOW_SCRIPT = """
local count = redis.call('INCR', KEYS[1])
local ttl = redis.call('PTTL', KEYS[1])
if count == 1 or ttl < 0 then
    redis.call('PEXPIRE', KEYS[1], ARGV[1])
    ttl = tonumber(ARGV[1])
end
return {count, ttl}
"""

# Preflight every key, counter, and TTL before updating any dimension. Redis
# scripts do not roll back earlier writes if a later runtime/OOM error occurs.
_MULTI_FIXED_WINDOW_SCRIPT = """
local n = #KEYS
if n < 1 or #ARGV ~= n * 2 then
    return redis.error_reply('invalid rate-limit script arguments')
end
local counts = {}
local ttls = {}
local function increment_decimal(value)
    local carry = 1
    for i = #value, 1, -1 do
        local digit = string.byte(value, i) - 48 + carry
        if digit == 10 then
            digit = 0
            carry = 1
        else
            carry = 0
        end
        value = string.sub(value, 1, i - 1)
            .. string.char(48 + digit) .. string.sub(value, i + 1)
        if carry == 0 then
            return value
        end
    end
    return '1' .. value
end
local function decimal_greater(left, right)
    left = string.gsub(left, '^0+', '')
    right = string.gsub(right, '^0+', '')
    if left == '' then left = '0' end
    if right == '' then right = '0' end
    if #left ~= #right then
        return #left > #right
    end
    return left > right
end
for i = 1, n do
    local limit = tonumber(ARGV[i])
    local window = tonumber(ARGV[n + i])
    if not limit or limit < 1 or limit ~= math.floor(limit)
       or not window or window < 1 or window ~= math.floor(window) then
        return redis.error_reply('invalid rate-limit policy')
    end
    local key_type = redis.call('TYPE', KEYS[i]).ok
    if key_type ~= 'none' and key_type ~= 'string' then
        return redis.error_reply('invalid rate-limit counter type')
    end
    local value = redis.call('GET', KEYS[i])
    local ttl = redis.call('PTTL', KEYS[i])
    if ttl == -2 then
        -- The key may have expired during preflight; it is a new window.
        counts[i] = 0
    elseif ttl == -1 or ttl > 0 then
        if key_type ~= 'string' or not value then
            return redis.error_reply('invalid rate-limit counter state')
        end
        local digits = string.gsub(value, '^0+', '')
        if digits == '' then digits = '0' end
        if not string.match(digits, '^%d+$')
           or #digits > 19
           or (#digits == 19 and digits >= '9223372036854775807') then
            return redis.error_reply('invalid rate-limit counter value')
        end
        counts[i] = digits
    else
        return redis.error_reply('invalid rate-limit counter TTL')
    end
    ttls[i] = ttl
end

local allowed = 1
local remaining = nil
local retry_after = 0
local result = {}
for i = 1, n do
    local window = ARGV[n + i]
    local window_ms = tonumber(window)
    local count
    local ttl
    if ttls[i] == -2 then
        -- Missing or expired during preflight: begin a fresh fixed window.
        count = 1
        redis.call('SET', KEYS[i], '1', 'PX', window)
        ttl = window_ms
    elseif ttls[i] == -1 then
        -- Preserve the count while repairing a persistent key's expiry.
        count = increment_decimal(counts[i])
        redis.call('SET', KEYS[i], count, 'PX', window)
        ttl = window_ms
    else
        -- SET KEEPTTL preserves the existing fixed-window deadline exactly.
        count = increment_decimal(counts[i])
        redis.call('SET', KEYS[i], count, 'KEEPTTL')
        ttl = redis.call('PTTL', KEYS[i])
        if ttl == -1 or ttl == -2 then
            -- It expired between preflight and SET; start a fresh window.
            count = 1
            redis.call('SET', KEYS[i], '1', 'PX', window)
            ttl = window_ms
        elseif ttl < 0 then
            return redis.error_reply('invalid rate-limit counter TTL after update')
        end
    end
    local over_limit = decimal_greater(count, ARGV[i])
    local left = 0
    if not over_limit then
        left = tonumber(ARGV[i]) - tonumber(count)
    end
    if remaining == nil or left < remaining then
        remaining = left
    end
    if over_limit then
        allowed = 0
        retry_after = math.max(retry_after, math.max(1, math.ceil(ttl / 1000)))
    end
    table.insert(result, count)
    table.insert(result, ttl)
end
return {allowed, remaining or 0, retry_after, unpack(result)}
"""

_SCOPE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_DIGEST_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_KEY_PATTERN = re.compile(
    rf"^{re.escape(RATE_LIMIT_KEY_PREFIX)}[a-z0-9][a-z0-9_-]{{0,63}}:[a-f0-9]{{64}}$"
)


class RateLimitStore(Protocol):
    """Subset of the existing application-managed Redis client used here."""

    def eval(self, script: str, numkeys: int, *keys_and_args: object) -> object: ...


@dataclass(frozen=True, slots=True)
class RateLimitRule:
    key: str
    limit: int
    window_seconds: int


@dataclass(frozen=True, slots=True)
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after_seconds: int


def canonicalize_identifier(
    identifier_type: Literal["email", "ip", "user"], identifier: str | UUID
) -> str:
    """Normalize an email, IP address, or user UUID before generating its digest."""
    if identifier_type == "email":
        if not isinstance(identifier, str):
            raise ValueError("email identifier must be text")
        value = identifier.strip().lower()
        if not value:
            raise ValueError("email identifier cannot be empty")
        return value
    if identifier_type == "ip":
        if not isinstance(identifier, str):
            raise ValueError("IP identifier must be text")
        address = ipaddress.ip_address(identifier)
        # Treat IPv4-mapped IPv6 as the equivalent IPv4 address.
        if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
            address = address.ipv4_mapped
        return address.compressed
    if identifier_type == "user":
        try:
            return UUID(str(identifier)).hex
        except (ValueError, AttributeError, TypeError):
            raise ValueError("user identifier must be a UUID") from None
    raise ValueError("unsupported rate-limit identifier type")


def identifier_digest(
    secret: SecretStr | None,
    identifier_type: Literal["email", "ip", "user"],
    identifier: str | UUID,
) -> str:
    """Return a versioned, domain-separated HMAC-SHA256 identifier digest."""
    if secret is None:
        raise ServiceUnavailableError("Rate limiting service is unavailable.")
    secret_bytes = secret.get_secret_value().encode("utf-8")
    if len(secret_bytes) < 32:
        raise ServiceUnavailableError("Rate limiting service is unavailable.")
    canonical = canonicalize_identifier(identifier_type, identifier)
    message = b"t2s-rate-limit:v1\0" + identifier_type.encode("ascii") + b"\0"
    return hmac.new(secret_bytes, message + canonical.encode("utf-8"), hashlib.sha256).hexdigest()


def rate_limit_key(scope: str, identifier_digest: str) -> str:
    """Build a key from a policy scope and opaque SHA-256/HMAC-SHA-256 digest.

    Callers must pass a keyed digest for sensitive identifiers. Raw identifiers
    are deliberately not accepted as a key component.
    """
    if not isinstance(scope, str) or not _SCOPE_PATTERN.fullmatch(scope):
        raise ValueError("scope must be a lowercase key-safe identifier")
    if not isinstance(identifier_digest, str) or not _DIGEST_PATTERN.fullmatch(identifier_digest):
        raise ValueError("identifier_digest must be a 64-character lowercase hex digest")
    return f"{RATE_LIMIT_KEY_PREFIX}{scope}:{identifier_digest}"


def _positive_int(name: str, value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _window_milliseconds(value: int) -> int:
    seconds = _positive_int("window_seconds", value)
    milliseconds = seconds * 1000
    if milliseconds > 9_223_372_036_854_775_807:
        raise ValueError("window_seconds is too large")
    return milliseconds


def consume_rate_limit(
    store: RateLimitStore | None,
    *,
    key: str,
    limit: int,
    window_seconds: int,
) -> RateLimitResult:
    """Atomically consume one fixed-window request using the shared Redis store."""
    limit = _positive_int("limit", limit)
    window_ms = _window_milliseconds(window_seconds)
    if not isinstance(key, str) or not _KEY_PATTERN.fullmatch(key):
        raise ValueError("key must use the rate-limit namespace and contain an opaque digest")
    if store is None:
        raise ServiceUnavailableError("Rate limiting service is unavailable.")

    try:
        response = store.eval(_FIXED_WINDOW_SCRIPT, 1, key, window_ms)
    except RedisError as exc:
        raise ServiceUnavailableError("Rate limiting service is unavailable.") from exc

    try:
        count, ttl_ms = response  # type: ignore[misc]
        count, ttl_ms = int(count), int(ttl_ms)
        if count < 1 or ttl_ms < 0:
            raise ValueError
    except (TypeError, ValueError, OverflowError):
        # A malformed script response is also an unavailable required operation.
        raise ServiceUnavailableError("Rate limiting service is unavailable.") from None

    allowed = count <= limit
    remaining = max(limit - count, 0)
    retry_after = max(1, math.ceil(ttl_ms / 1000)) if not allowed else 0
    return RateLimitResult(allowed, remaining, retry_after)


def consume_rate_limits(
    store: RateLimitStore | None, *, rules: tuple[RateLimitRule, ...]
) -> RateLimitResult:
    """Atomically consume multiple independent fixed-window rate-limit dimensions."""
    if not rules:
        raise ValueError("at least one rate-limit rule is required")
    keys: list[str] = []
    limits: list[int] = []
    windows_ms: list[int] = []
    for rule in rules:
        if not isinstance(rule, RateLimitRule):
            raise ValueError("rules must contain RateLimitRule values")
        _positive_int("limit", rule.limit)
        window_ms = _window_milliseconds(rule.window_seconds)
        if not isinstance(rule.key, str) or not _KEY_PATTERN.fullmatch(rule.key):
            raise ValueError("key must use the rate-limit namespace and contain an opaque digest")
        keys.append(rule.key)
        limits.append(rule.limit)
        windows_ms.append(window_ms)
    if len(set(keys)) != len(keys):
        raise ValueError("rate-limit rules must use distinct keys")
    if store is None:
        raise ServiceUnavailableError("Rate limiting service is unavailable.")

    try:
        response = store.eval(
            _MULTI_FIXED_WINDOW_SCRIPT,
            len(keys),
            *keys,
            *limits,
            *windows_ms,
        )
    except RedisError as exc:
        raise ServiceUnavailableError("Rate limiting service is unavailable.") from exc

    try:
        values = [int(value) for value in response]  # type: ignore[union-attr]
        if len(values) != 3 + 2 * len(rules):
            raise ValueError
        allowed, remaining, retry_after = values[:3]
        if (
            allowed not in {0, 1}
            or remaining < 0
            or retry_after < 0
            or (allowed == 0 and retry_after < 1)
        ):
            raise ValueError
        pairs = values[3:]
        if any(count < 1 or ttl < 0 for count, ttl in zip(pairs[::2], pairs[1::2])):
            raise ValueError
    except (TypeError, ValueError, OverflowError):
        raise ServiceUnavailableError("Rate limiting service is unavailable.") from None
    return RateLimitResult(bool(allowed), remaining, retry_after)


def enforce_rate_limit(result: RateLimitResult) -> None:
    """Raise the standard 429 response when a consumed request exceeded its limit."""
    if not result.allowed:
        raise TooManyRequestsError(headers={"Retry-After": str(result.retry_after_seconds)})
