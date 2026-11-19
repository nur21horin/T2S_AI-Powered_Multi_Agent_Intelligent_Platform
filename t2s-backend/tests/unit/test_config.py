import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import Settings


def test_csv_env_values_are_split(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://a.com, http://b.com")
    monkeypatch.setenv("TRUSTED_HOSTS", "a.com,b.com")
    s = Settings(_env_file=None)
    assert s.cors_allowed_origins == ["http://a.com", "http://b.com"]
    assert s.trusted_hosts == ["a.com", "b.com"]


def test_wildcard_cors_origin_is_rejected():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, cors_allowed_origins=["*"])


def test_is_production_flag():
    assert Settings(
        _env_file=None,
        app_env="production",
        jwt_secret_key=SecretStr("production-test-secret-key-over-32-bytes-long"),
        rate_limit_key_secret=SecretStr("unit-test-rate-limit-secret-with-32-bytes"),
    ).is_production
    assert not Settings(_env_file=None, app_env="development").is_production


def test_production_requires_a_long_jwt_signing_key():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, app_env="production", jwt_secret_key="too-short")


def test_production_requires_rate_limit_key_secret():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            app_env="production",
            jwt_secret_key=SecretStr("production-jwt-secret-key-with-at-least-32-bytes"),
        )


@pytest.mark.parametrize("secret", ["", "short-secret", " " * 32])
def test_rate_limit_key_secret_rejects_empty_or_short_values(secret):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, rate_limit_key_secret=SecretStr(secret))


def test_valid_rate_limit_key_secret_is_masked():
    secret = "test-only-rate-limit-secret-with-32-bytes"
    settings = Settings(
        _env_file=None,
        app_env="production",
        jwt_secret_key=SecretStr("production-jwt-secret-key-with-at-least-32-bytes"),
        rate_limit_key_secret=SecretStr(secret),
    )

    assert settings.rate_limit_key_secret.get_secret_value() == secret
    assert secret not in repr(settings)
    assert secret not in str(settings.model_dump())


def test_database_url_is_secret_in_repr():
    s = Settings(_env_file=None, database_url="postgresql+psycopg://u:TopSecret@h/db")
    assert "TopSecret" not in repr(s) and "TopSecret" not in str(s.model_dump())
    assert "TopSecret" in s.database_url.get_secret_value()


def test_admin_bootstrap_is_disabled_by_default_and_can_be_explicitly_enabled(monkeypatch):
    monkeypatch.delenv("ADMIN_BOOTSTRAP_ENABLED", raising=False)
    assert Settings(_env_file=None).admin_bootstrap_enabled is False

    monkeypatch.setenv("ADMIN_BOOTSTRAP_ENABLED", "true")
    assert Settings(_env_file=None).admin_bootstrap_enabled is True
