from threading import Event
from time import monotonic

import pytest

from app.core.exceptions import ServiceUnavailableError
from app.security.rate_limit import consume_rate_limit
from tests.conftest import RedisTestScope


def _owned_key(test_redis: RedisTestScope) -> str:
    return test_redis.owned_rate_limit_key()


def test_single_key_initializes_missing_counter_with_finite_ttl(test_redis):
    key = _owned_key(test_redis)
    window_seconds = 30

    assert test_redis.client.exists(key) == 0
    result = consume_rate_limit(
        test_redis.client,
        key=key,
        limit=3,
        window_seconds=window_seconds,
    )

    ttl_ms = test_redis.client.pttl(key)
    assert result.allowed
    assert result.remaining == 2
    assert test_redis.client.get(key) == "1"
    assert window_seconds * 1000 - 1000 <= ttl_ms <= window_seconds * 1000


def test_single_key_increments_and_reports_limit_remaining(test_redis):
    key = _owned_key(test_redis)
    limit = 2
    window_seconds = 30

    first = consume_rate_limit(
        test_redis.client, key=key, limit=limit, window_seconds=window_seconds
    )
    second = consume_rate_limit(
        test_redis.client, key=key, limit=limit, window_seconds=window_seconds
    )
    rejected = consume_rate_limit(
        test_redis.client, key=key, limit=limit, window_seconds=window_seconds
    )

    assert first.allowed and first.remaining == 1
    assert second.allowed and second.remaining == 0
    assert not rejected.allowed
    assert rejected.remaining == 0
    assert 1 <= rejected.retry_after_seconds <= window_seconds
    assert test_redis.client.get(key) == "3"


def test_single_key_increment_preserves_existing_window_expiry(test_redis):
    key = _owned_key(test_redis)
    assert test_redis.client.set(key, "4", px=5_000)
    started = monotonic()
    ttl_before_ms = test_redis.client.pttl(key)

    result = consume_rate_limit(
        test_redis.client, key=key, limit=10, window_seconds=60
    )

    ttl_after_ms = test_redis.client.pttl(key)
    elapsed_ms = (monotonic() - started) * 1000
    assert result.allowed
    assert result.remaining == 5
    assert test_redis.client.get(key) == "5"
    assert 0 < ttl_after_ms <= 5_000
    assert abs((ttl_before_ms - ttl_after_ms) - elapsed_ms) <= 250


def test_single_key_expired_counter_starts_new_window(test_redis):
    key = _owned_key(test_redis)
    assert test_redis.client.set(key, "8", px=1)
    deadline = monotonic() + 2
    while test_redis.client.pttl(key) != -2:
        if monotonic() >= deadline:
            pytest.fail("Test counter did not expire before the bounded deadline.")
        Event().wait(0.01)

    window_seconds = 30
    result = consume_rate_limit(
        test_redis.client,
        key=key,
        limit=3,
        window_seconds=window_seconds,
    )

    ttl_ms = test_redis.client.pttl(key)
    assert result.allowed
    assert result.remaining == 2
    assert test_redis.client.get(key) == "1"
    assert window_seconds * 1000 - 1000 <= ttl_ms <= window_seconds * 1000


def test_single_key_persistent_counter_ttl_is_repaired(test_redis):
    key = _owned_key(test_redis)
    assert test_redis.client.set(key, "4")
    assert test_redis.client.pttl(key) == -1
    window_seconds = 30

    result = consume_rate_limit(
        test_redis.client,
        key=key,
        limit=10,
        window_seconds=window_seconds,
    )

    ttl_ms = test_redis.client.pttl(key)
    assert result.allowed
    assert result.remaining == 5
    assert test_redis.client.get(key) == "5"
    assert window_seconds * 1000 - 1000 <= ttl_ms <= window_seconds * 1000


def test_single_key_wrong_type_maps_to_safe_service_unavailable(test_redis):
    key = _owned_key(test_redis)
    assert test_redis.client.rpush(key, "not-a-counter") == 1

    with pytest.raises(ServiceUnavailableError) as exc_info:
        consume_rate_limit(test_redis.client, key=key, limit=3, window_seconds=30)

    assert str(exc_info.value) == "Rate limiting service is unavailable."
    assert test_redis.client.type(key) == "list"
