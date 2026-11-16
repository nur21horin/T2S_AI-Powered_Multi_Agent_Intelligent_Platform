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
