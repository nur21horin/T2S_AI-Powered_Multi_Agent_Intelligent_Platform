"""Atomic, Redis-backed fixed-window rate-limit primitives."""
from dataclasses import dataclass
import math
import re
from typing import Protocol

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

_SCOPE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_DIGEST_PATTERN = re.compile(r"^[a-f0-9]{64}$")
_KEY_PATTERN = re.compile(
    rf"^{re.escape(RATE_LIMIT_KEY_PREFIX)}[a-z0-9][a-z0-9_-]{{0,63}}:[a-f0-9]{{64}}$"
)


class RateLimitStore(Protocol):
    """Subset of the existing application-managed Redis client used here."""

    def eval(self, script: str, numkeys: int, *keys_and_args: object) -> object: ...


@dataclass(frozen=True, slots=True)
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after_seconds: int


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


def consume_rate_limit(
    store: RateLimitStore | None,
    *,
    key: str,
    limit: int,
    window_seconds: int,
) -> RateLimitResult:
    """Atomically consume one fixed-window request using the shared Redis store."""
    limit = _positive_int("limit", limit)
    window_seconds = _positive_int("window_seconds", window_seconds)
    if not isinstance(key, str) or not _KEY_PATTERN.fullmatch(key):
        raise ValueError("key must use the rate-limit namespace and contain an opaque digest")
    if store is None:
        raise ServiceUnavailableError("Rate limiting service is unavailable.")

    try:
        response = store.eval(_FIXED_WINDOW_SCRIPT, 1, key, window_seconds * 1000)
    except RedisError as exc:
        raise ServiceUnavailableError("Rate limiting service is unavailable.") from exc

    try:
        count, ttl_ms = response  # type: ignore[misc]
        count, ttl_ms = int(count), int(ttl_ms)
        if count < 1 or ttl_ms < 0:
            raise ValueError
    except (TypeError, ValueError):
        # A malformed script response is also an unavailable required operation.
        raise ServiceUnavailableError("Rate limiting service is unavailable.") from None

    allowed = count <= limit
    remaining = max(limit - count, 0)
    retry_after = max(1, math.ceil(ttl_ms / 1000)) if not allowed else 0
    return RateLimitResult(allowed, remaining, retry_after)


def enforce_rate_limit(result: RateLimitResult) -> None:
    """Raise the standard 429 response when a consumed request exceeded its limit."""
    if not result.allowed:
        raise TooManyRequestsError(headers={"Retry-After": str(result.retry_after_seconds)})
