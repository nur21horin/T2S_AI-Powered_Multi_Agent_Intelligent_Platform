from math import ceil

import pytest
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import ResponseError

from app.core.exceptions import ServiceUnavailableError
from app.security.rate_limit import (
    RATE_LIMIT_KEY_PREFIX,
    RateLimitResult,
    consume_rate_limit,
    enforce_rate_limit,
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
