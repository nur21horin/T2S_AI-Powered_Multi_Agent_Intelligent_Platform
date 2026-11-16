from math import ceil
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import ResponseError
from starlette.requests import Request

from app.api.v1.endpoints.auth import _client_ip
from app.core.exceptions import ServiceUnavailableError
from app.security.rate_limit import (
    RATE_LIMIT_KEY_PREFIX,
    _MULTI_FIXED_WINDOW_SCRIPT,
    RateLimitResult,
    RateLimitRule,
    consume_rate_limit,
    consume_rate_limits,
    enforce_rate_limit,
    identifier_digest,
    rate_limit_key,
)


_DIGEST = "a" * 64


def _key(scope: str = "login") -> str:
    return rate_limit_key(scope, _DIGEST)


def test_allows_requests_below_and_at_limit(fake_redis):
    key = _key()

    first = consume_rate_limit(fake_redis, key=key, limit=2, window_seconds=60)
    second = consume_rate_limit(fake_redis, key=key, limit=2, window_seconds=60)

    assert first == RateLimitResult(allowed=True, remaining=1, retry_after_seconds=0)
    assert second == RateLimitResult(allowed=True, remaining=0, retry_after_seconds=0)


def test_rejects_above_limit_with_remaining_and_retry_after(fake_redis, monkeypatch):
    monkeypatch.setattr(
        fake_redis, "eval", lambda *_args: [4, 1501]
    )

    result = consume_rate_limit(fake_redis, key=_key(), limit=3, window_seconds=60)

    assert result == RateLimitResult(allowed=False, remaining=0, retry_after_seconds=2)
    assert result.retry_after_seconds == ceil(1501 / 1000)


def test_rejected_retry_after_is_at_least_one_second(fake_redis, monkeypatch):
    monkeypatch.setattr(fake_redis, "eval", lambda *_args: [2, 0])

    result = consume_rate_limit(fake_redis, key=_key(), limit=1, window_seconds=60)

    assert result.retry_after_seconds == 1


def test_counter_expires_and_starts_a_new_window(fake_redis):
    key = _key()
    fake_redis.rate_limit_counters[key] = (5, fake_redis.rate_limit_now - 1)

    result = consume_rate_limit(fake_redis, key=key, limit=5, window_seconds=30)

    count, expires_at = fake_redis.rate_limit_counters[key]
    assert result.allowed
    assert count == 1
    assert expires_at == fake_redis.rate_limit_now + 30


def test_missing_ttl_is_repaired(fake_redis):
    key = _key()
    fake_redis.rate_limit_counters[key] = (2, None)

    result = consume_rate_limit(fake_redis, key=key, limit=3, window_seconds=30)

    count, expires_at = fake_redis.rate_limit_counters[key]
    assert result.allowed
    assert count == 3
    assert expires_at == fake_redis.rate_limit_now + 30


@pytest.mark.parametrize(
    ("limit", "window_seconds"),
    [(0, 1), (-1, 1), (1, 0), (1, -5), (True, 1), (1, False)],
)
def test_rejects_non_positive_or_boolean_limits_and_windows(
    fake_redis, limit, window_seconds
):
    with pytest.raises(ValueError):
        consume_rate_limit(
            fake_redis, key=_key(), limit=limit, window_seconds=window_seconds
        )


def test_rate_limit_key_requires_opaque_digest_and_safe_scope():
    key = rate_limit_key("login", _DIGEST)

    assert key == f"{RATE_LIMIT_KEY_PREFIX}login:{_DIGEST}"
    with pytest.raises(ValueError):
        rate_limit_key("login", "person@example.com")
    with pytest.raises(ValueError):
        rate_limit_key("login:person@example.com", _DIGEST)
    with pytest.raises(ValueError):
        consume_rate_limit(
            None,
            key=f"{RATE_LIMIT_KEY_PREFIX}person@example.com",
            limit=1,
            window_seconds=60,
        )


def test_identifier_hmac_is_stable_and_domain_separated():
    secret = SecretStr("unit-test-rate-limit-secret-with-32-bytes")
    email_digest = identifier_digest(secret, "email", " Student@Example.com ")

    assert email_digest == identifier_digest(secret, "email", "student@example.com")
    assert identifier_digest(secret, "email", "192.0.2.1") != identifier_digest(
        secret, "ip", "192.0.2.1"
    )
    assert email_digest != identifier_digest(secret, "email", "other@example.com")
    assert len(email_digest) == 64
    assert email_digest == email_digest.lower()


def test_ip_and_uuid_identifier_canonicalization():
    secret = SecretStr("unit-test-rate-limit-secret-with-32-bytes")

    assert identifier_digest(secret, "ip", "192.0.2.1") == identifier_digest(
        secret, "ip", "::ffff:192.0.2.1"
    )
    assert identifier_digest(secret, "ip", "2001:0db8:0:0::1") == identifier_digest(
        secret, "ip", "2001:db8::1"
    )
    user_id = UUID("12345678-1234-5678-1234-567812345678")
    assert identifier_digest(secret, "user", user_id) == identifier_digest(
        secret, "user", str(user_id).upper()
    )


def test_identifier_digests_keep_raw_values_out_of_redis_keys():
    secret = SecretStr("unit-test-rate-limit-secret-with-32-bytes")
    email = "sensitive.person@example.com"
    digest = identifier_digest(secret, "email", email)
    key = rate_limit_key("email-wide", digest)

    assert email not in key
    assert "sensitive" not in key


def test_missing_or_weak_hmac_secret_fails_closed():
    with pytest.raises(ServiceUnavailableError):
        identifier_digest(None, "email", "person@example.com")
    with pytest.raises(ServiceUnavailableError):
        identifier_digest(SecretStr("too-short"), "email", "person@example.com")


def test_multi_key_limits_consume_both_dimensions(fake_redis):
    email_key = _key("forgot-email")
    ip_key = rate_limit_key("forgot-ip", "b" * 64)
    rules = (
        RateLimitRule(email_key, 2, 3600),
        RateLimitRule(ip_key, 3, 3600),
    )

    first = consume_rate_limits(fake_redis, rules=rules)
    second = consume_rate_limits(fake_redis, rules=rules)
    rejected = consume_rate_limits(fake_redis, rules=rules)

    assert first == RateLimitResult(True, 1, 0)
    assert second == RateLimitResult(True, 0, 0)
    assert rejected.allowed is False
    assert rejected.remaining == 0
    assert rejected.retry_after_seconds == 3600
    assert fake_redis.rate_limit_counters[email_key][0] == 3
    assert fake_redis.rate_limit_counters[ip_key][0] == 3


def test_multi_key_preflights_all_keys_before_any_write(fake_redis):
    keys = (_key("preflight-one"), _key("preflight-two"))
    rules = tuple(RateLimitRule(key, 3, 60) for key in keys)

    consume_rate_limits(fake_redis, rules=rules)

    assert fake_redis.rate_limit_events == [
        ("preflight", keys[0]),
        ("preflight", keys[1]),
        ("write", keys[0]),
        ("write", keys[1]),
    ]
    # FakeRedis models expected ordering. This source check ensures the actual
    # Lua's PTTL preflight loop precedes its first mutating Redis command.
    preflight_end = _MULTI_FIXED_WINDOW_SCRIPT.index("\nlocal allowed")
    assert "redis.call('PTTL', KEYS[i])" in _MULTI_FIXED_WINDOW_SCRIPT[:preflight_end]
    assert "redis.call('SET'" not in _MULTI_FIXED_WINDOW_SCRIPT[:preflight_end]
    assert "redis.call('SET'" in _MULTI_FIXED_WINDOW_SCRIPT[preflight_end:]


def test_multi_key_missing_keys_start_at_one_with_configured_window(fake_redis):
    keys = (_key("missing-one"), _key("missing-two"))

    consume_rate_limits(
        fake_redis,
        rules=(RateLimitRule(keys[0], 2, 30), RateLimitRule(keys[1], 2, 90)),
    )

    assert fake_redis.rate_limit_counters[keys[0]] == (
        1,
        fake_redis.rate_limit_now + 30,
    )
    assert fake_redis.rate_limit_counters[keys[1]] == (
        1,
        fake_redis.rate_limit_now + 90,
    )


def test_multi_key_positive_ttl_preserves_existing_expiration(fake_redis):
    key = _key("preserve-ttl")
    deadline = fake_redis.rate_limit_now + 17.25
    fake_redis.rate_limit_counters[key] = (4, deadline)

    result = consume_rate_limits(
        fake_redis, rules=(RateLimitRule(key, 10, 60),)
    )

    assert result.allowed
    assert fake_redis.rate_limit_counters[key] == (5, deadline)


def test_multi_key_persistent_key_repairs_ttl_without_resetting_counter(fake_redis):
    key = _key("persistent")
    fake_redis.rate_limit_counters[key] = (7, None)

    result = consume_rate_limits(
        fake_redis, rules=(RateLimitRule(key, 10, 45),)
    )

    assert result.allowed
    assert fake_redis.rate_limit_counters[key] == (
        8,
        fake_redis.rate_limit_now + 45,
    )


@pytest.mark.parametrize("unexpected_ttl", [0, -3])
def test_multi_key_unexpected_ttl_fails_before_any_counter_mutation(
    fake_redis, unexpected_ttl
):
    keys = (_key("valid-ttl"), _key("invalid-ttl"))
    fake_redis.rate_limit_counters[keys[0]] = (2, fake_redis.rate_limit_now + 30)
    fake_redis.rate_limit_counters[keys[1]] = (5, fake_redis.rate_limit_now + 30)
    fake_redis.rate_limit_ttl_overrides[keys[1]] = unexpected_ttl
    before = dict(fake_redis.rate_limit_counters)

    with pytest.raises(ServiceUnavailableError):
        consume_rate_limits(
            fake_redis,
            rules=(RateLimitRule(keys[0], 10, 60), RateLimitRule(keys[1], 10, 60)),
        )

    assert fake_redis.rate_limit_counters == before
    assert not any(event == "write" for event, _key_name in fake_redis.rate_limit_events)


def test_multi_key_redis_failure_returns_http_503(app, fake_redis):
    fake_redis.available = False
    app.state.redis_client = fake_redis

    @app.get("/test-multi-rate-limit-unavailable")
    def unavailable():
        consume_rate_limits(fake_redis, rules=(RateLimitRule(_key(), 1, 60),))

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/test-multi-rate-limit-unavailable")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "service_unavailable"


def test_multi_key_redis_failure_fails_closed(fake_redis):
    fake_redis.available = False
    rules = (
        RateLimitRule(_key("multi-one"), 1, 60),
        RateLimitRule(_key("multi-two"), 1, 60),
    )

    with pytest.raises(ServiceUnavailableError) as exc_info:
        consume_rate_limits(fake_redis, rules=rules)

    assert "test Redis unavailable" not in str(exc_info.value)


@pytest.mark.parametrize("client", [None, ("not-an-ip", 1234)])
def test_missing_or_invalid_direct_client_ip_fails_closed(client):
    request = Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": [],
            "client": client,
            "server": ("testserver", 80),
        }
    )

    with pytest.raises(ServiceUnavailableError):
        _client_ip(request)


def test_missing_redis_fails_closed_without_local_fallback():
    with pytest.raises(ServiceUnavailableError):
        consume_rate_limit(None, key=_key(), limit=1, window_seconds=60)


@pytest.mark.parametrize(
    "redis_error",
    [RedisConnectionError("private host"), ResponseError("script internals")],
)
def test_redis_connection_and_script_errors_map_to_safe_503(
    fake_redis, monkeypatch, redis_error
):
    def fail(*_args):
        raise redis_error

    monkeypatch.setattr(fake_redis, "eval", fail)

    with pytest.raises(ServiceUnavailableError) as exc_info:
        consume_rate_limit(fake_redis, key=_key(), limit=1, window_seconds=60)

    assert "private host" not in str(exc_info.value)
    assert "script internals" not in str(exc_info.value)


def test_rejection_uses_actual_exception_handler_and_preserves_envelope(app):
    @app.get("/test-rate-limit-rejected")
    def reject_request():
        enforce_rate_limit(RateLimitResult(False, 0, 7))

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get(
            "/test-rate-limit-rejected", headers={"X-Request-ID": "rate-limit-test-1"}
        )

    assert response.status_code == 429
    assert response.headers["retry-after"] == "7"
    assert response.json() == {
        "error": {
            "code": "rate_limited",
            "message": "Too many requests.",
            "details": None,
            "request_id": "rate-limit-test-1",
        }
    }


def test_unavailable_response_is_safe_and_preserves_standard_envelope(app):
    @app.get("/test-rate-limit-unavailable")
    def unavailable():
        consume_rate_limit(None, key=_key(), limit=1, window_seconds=60)

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get(
            "/test-rate-limit-unavailable", headers={"X-Request-ID": "rate-limit-test-2"}
        )

    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "service_unavailable",
            "message": "Rate limiting service is unavailable.",
            "details": None,
            "request_id": "rate-limit-test-2",
        }
    }
