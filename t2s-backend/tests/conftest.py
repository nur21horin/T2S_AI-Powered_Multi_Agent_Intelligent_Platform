import os

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        app_env="testing",
        cors_allowed_origins=["http://localhost:3000"],
        trusted_hosts=["testserver"],
    )


@pytest.fixture
def app(settings):
    return create_app(settings)


@pytest.fixture
def client(app):
    # raise_server_exceptions=False lets us assert the real 500 response body.
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """Real PostgreSQL URL for DB tests. Skips if unset; refuses non-*_test databases."""
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        configured = Settings(_env_file=".env").test_database_url
        url = configured.get_secret_value() if configured else None
    if not url:
        pytest.skip("TEST_DATABASE_URL not set")
    if not url.rsplit("/", 1)[-1].split("?")[0].endswith("_test"):
        pytest.fail("TEST_DATABASE_URL must point to a database whose name ends with '_test'")
    return url


@pytest.fixture
def db_client(test_database_url):
    from pydantic import SecretStr

    s = Settings(
        _env_file=None, app_env="testing", trusted_hosts=["testserver"],
        database_url=SecretStr(test_database_url), db_pool_size=2, db_max_overflow=0,
    )
    app = create_app(s)
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
