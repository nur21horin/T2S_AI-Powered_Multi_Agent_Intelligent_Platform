import pytest
from pydantic import ValidationError

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
    assert Settings(_env_file=None, app_env="production").is_production
    assert not Settings(_env_file=None, app_env="development").is_production


def test_database_url_is_secret_in_repr():
    s = Settings(_env_file=None, database_url="postgresql+psycopg://u:TopSecret@h/db")
    assert "TopSecret" not in repr(s) and "TopSecret" not in str(s.model_dump())
    assert "TopSecret" in s.database_url.get_secret_value()
