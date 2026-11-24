import pytest

from app.security.rate_limit import RATE_LIMIT_KEY_PREFIX, _KEY_PATTERN
from tests.conftest import (
    RedisTestConfigurationError,
    RedisTestScope,
    _new_test_redis_namespace,
    _require_test_redis_url,
    _validate_test_redis_configuration,
)


class RecordingRedis:
    def __init__(self):
        self.deleted = []

    def delete(self, key):
        self.deleted.append(key)


class FailingRedis(RecordingRedis):
    def __init__(self, failures):
        super().__init__()
        self.failures = failures

    def delete(self, key):
        self.deleted.append(key)
        if key in self.failures:
            raise self.failures[key]


def test_missing_test_redis_url_skips_instead_of_using_application_url(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://shared-dev:6379/0")

    with pytest.raises(pytest.skip.Exception, match="TEST_REDIS_URL"):
        _require_test_redis_url(None)


def test_test_redis_requires_explicit_opt_in():
    try:
        _validate_test_redis_configuration(
            "redis://localhost:6389/0",
            opt_in=None,
            known_application_urls=(),
        )
    except RedisTestConfigurationError as exc:
        assert "TEST_REDIS_INTEGRATION=1" in str(exc)
    else:
        raise AssertionError("configured Redis must require explicit test opt-in")


def test_test_redis_rejects_known_application_endpoint():
    try:
        _validate_test_redis_configuration(
            "redis://user:secret@shared-dev:6379/5",
            opt_in="1",
            known_application_urls=("redis://user:secret@shared-dev:6379/0",),
        )
    except RedisTestConfigurationError as exc:
        assert "same Redis endpoint" in str(exc)
        assert "secret" not in str(exc)
    else:
        raise AssertionError("application Redis endpoint must be rejected")


def test_test_redis_rejects_malformed_target():
    try:
        _validate_test_redis_configuration(
            "http://localhost:6389/0", opt_in="1", known_application_urls=()
        )
    except RedisTestConfigurationError as exc:
        assert "redis://" in str(exc)
    else:
        raise AssertionError("non-Redis URL must be rejected")


def test_namespace_generation_is_unique():
    first = _new_test_redis_namespace(RecordingRedis())
    second = _new_test_redis_namespace(RecordingRedis())

    assert first.namespace.startswith("t2s:test:")
    assert second.namespace.startswith("t2s:test:")
    assert first.namespace != second.namespace


def test_cleanup_deletes_only_registered_test_owned_keys():
    client = RecordingRedis()
    redis_scope = RedisTestScope(client=client, namespace="t2s:test:current")
    owned_key = redis_scope.owned_key("counter:one")

    redis_scope.cleanup()

    assert client.deleted == [owned_key]
    assert "t2s:test:other:counter" not in client.deleted
    assert redis_scope._owned_keys == set()


def test_cleanup_attempts_all_owned_keys_after_a_deletion_failure():
    client = FailingRedis({"t2s:test:current:counter:one": OSError("delete failed")})
    redis_scope = RedisTestScope(client=client, namespace="t2s:test:current")
    owned_keys = {
        redis_scope.owned_key("counter:one"),
        redis_scope.owned_key("counter:two"),
        redis_scope.owned_key("counter:three"),
    }

    with pytest.raises(ExceptionGroup):
        redis_scope.cleanup()

    assert set(client.deleted) == owned_keys


def test_cleanup_clears_ownership_after_deletion_attempts():
    client = FailingRedis({"t2s:test:current:counter:one": OSError("delete failed")})
    redis_scope = RedisTestScope(client=client, namespace="t2s:test:current")
    redis_scope.owned_key("counter:one")
    redis_scope.owned_key("counter:two")

    with pytest.raises(ExceptionGroup):
        redis_scope.cleanup()

    assert redis_scope._owned_keys == set()


def test_cleanup_exception_group_preserves_original_errors():
    original_error = OSError("test key deletion failed")
    client = FailingRedis({"t2s:test:current:counter:one": original_error})
    redis_scope = RedisTestScope(client=client, namespace="t2s:test:current")
    redis_scope.owned_key("counter:one")
    redis_scope.owned_key("counter:two")

    with pytest.raises(ExceptionGroup) as exc_info:
        redis_scope.cleanup()

    assert exc_info.value.exceptions == (original_error,)
    assert str(exc_info.value.exceptions[0]) == "test key deletion failed"


def test_owned_rate_limit_key_is_unique_valid_and_registered():
    client = RecordingRedis()
    redis_scope = RedisTestScope(client=client, namespace="t2s:test:current")

    first_key = redis_scope.owned_rate_limit_key()
    second_key = redis_scope.owned_rate_limit_key()

    assert first_key.startswith(RATE_LIMIT_KEY_PREFIX)
    assert second_key.startswith(RATE_LIMIT_KEY_PREFIX)
    assert _KEY_PATTERN.fullmatch(first_key)
    assert _KEY_PATTERN.fullmatch(second_key)
    assert first_key != second_key
    assert redis_scope._owned_keys == {first_key, second_key}

    redis_scope.cleanup()

    assert set(client.deleted) == {first_key, second_key}


def test_real_test_redis_connectivity(test_redis):
    assert test_redis.client.ping()
    assert test_redis.namespace.startswith("t2s:test:")
