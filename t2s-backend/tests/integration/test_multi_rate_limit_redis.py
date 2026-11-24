import pytest

from app.core.exceptions import ServiceUnavailableError
from app.security.rate_limit import RateLimitRule, consume_rate_limits
from time import monotonic


def _rules(test_redis, *, email_limit=5, ip_limit=5, email_window=30, ip_window=30):
    return (
        RateLimitRule(test_redis.owned_rate_limit_key(), email_limit, email_window),
        RateLimitRule(test_redis.owned_rate_limit_key(), ip_limit, ip_window),
    )


def test_multi_key_initializes_both_counters_and_ttls(test_redis):
    rules = _rules(test_redis, email_window=30, ip_window=45)

    result = consume_rate_limits(test_redis.client, rules=rules)

    assert result.allowed
    assert result.remaining == 4
    for rule, window in zip(rules, (30, 45)):
        assert test_redis.client.get(rule.key) == "1"
        ttl_ms = test_redis.client.pttl(rule.key)
        assert window * 1000 - 1000 <= ttl_ms <= window * 1000


@pytest.mark.parametrize(
    ("email_limit", "ip_limit"),
    [(2, 5), (5, 2)],
)
def test_multi_key_enforces_each_dimension_and_counts_both(
    test_redis, email_limit, ip_limit
):
    rules = _rules(test_redis, email_limit=email_limit, ip_limit=ip_limit)
    expected_limit = min(email_limit, ip_limit)
    results = [
        consume_rate_limits(test_redis.client, rules=rules)
        for _ in range(expected_limit + 1)
    ]

    assert all(result.allowed for result in results[:expected_limit])
    assert results[0].remaining == expected_limit - 1
    assert results[expected_limit - 1].remaining == 0
    assert not results[-1].allowed
    assert results[-1].remaining == 0
    assert results[-1].retry_after_seconds >= 1
    for rule in rules:
        assert test_redis.client.get(rule.key) == str(expected_limit + 1)


def test_multi_key_increments_preserve_each_existing_expiry(test_redis):
    rules = _rules(test_redis, email_limit=10, ip_limit=10, email_window=60, ip_window=90)
    email_key, ip_key = (rule.key for rule in rules)
    assert test_redis.client.set(email_key, "3", px=8_000)
    assert test_redis.client.set(ip_key, "4", px=10_000)
    started = monotonic()
    before = {key: test_redis.client.pttl(key) for key in (email_key, ip_key)}

    result = consume_rate_limits(test_redis.client, rules=rules)

    after = {key: test_redis.client.pttl(key) for key in (email_key, ip_key)}
    elapsed_ms = (monotonic() - started) * 1000
    assert result.allowed
    assert result.remaining == 5
    assert test_redis.client.get(email_key) == "4"
    assert test_redis.client.get(ip_key) == "5"
    assert all(0 < after[key] for key in after)
    assert all(abs((before[key] - after[key]) - elapsed_ms) <= 250 for key in before)


def test_multi_key_repairs_persistent_ttl_and_initializes_missing_dimension(test_redis):
    rules = _rules(test_redis, email_limit=10, ip_limit=10, email_window=45, ip_window=90)
    email_key, ip_key = (rule.key for rule in rules)
    assert test_redis.client.set(email_key, "7")
    assert test_redis.client.pttl(email_key) == -1

    result = consume_rate_limits(test_redis.client, rules=rules)

    assert result.allowed
    assert result.remaining == 2
    assert test_redis.client.get(email_key) == "8"
    assert test_redis.client.get(ip_key) == "1"
    for key, window in ((email_key, 45), (ip_key, 90)):
        ttl_ms = test_redis.client.pttl(key)
        assert window * 1000 - 1000 <= ttl_ms <= window * 1000


def test_multi_key_preflight_wrong_type_does_not_consume_other_dimension(test_redis):
    rules = _rules(test_redis, email_limit=10, ip_limit=10)
    valid_key, wrong_type_key = (rule.key for rule in rules)
    assert test_redis.client.set(valid_key, "6", px=20_000)
    assert test_redis.client.rpush(wrong_type_key, "not-a-counter") == 1
    before_ttl = test_redis.client.pttl(valid_key)

    with pytest.raises(ServiceUnavailableError) as exc_info:
        consume_rate_limits(test_redis.client, rules=rules)

    assert str(exc_info.value) == "Rate limiting service is unavailable."
    assert test_redis.client.get(valid_key) == "6"
    assert 0 < test_redis.client.pttl(valid_key) <= before_ttl
    assert test_redis.client.type(wrong_type_key) == "list"
