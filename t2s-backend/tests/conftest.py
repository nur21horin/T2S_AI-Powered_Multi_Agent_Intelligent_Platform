import os
import time
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from pydantic import SecretStr
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from app.core.config import Settings
from app.models.auth_token import AuthToken
from app.models.user import User
from app.main import create_app
from tests.factories import FakeEmailSender

BACKEND_ROOT = Path(__file__).resolve().parents[1]


class FakeRedis:
    """Small deterministic Redis substitute for tests; never used by application code."""

    def __init__(self) -> None:
        self.values: dict[str, tuple[str, float]] = {}
        self.available = True
        self.operations: list[str] = []

    def _require_available(self) -> None:
        if not self.available:
            raise RedisConnectionError("test Redis unavailable")

    def exists(self, name: str) -> int:
        self._require_available()
        item = self.values.get(name)
        if item is None:
            return 0
        if item[1] <= time.time():
            del self.values[name]
            return 0
        return 1

    def set(self, name: str, value: str, *, pxat: int) -> bool:
        self._require_available()
        self.operations.append("redis:set")
        self.values[name] = (value, pxat / 1000)
        return True

    def ttl(self, name: str) -> int:
        self._require_available()
        if not self.exists(name):
            return -2
        return max(0, int(self.values[name][1] - time.time()))

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def fake_redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        app_env="testing",
        cors_allowed_origins=["http://localhost:3000"],
        trusted_hosts=["testserver"],
        jwt_secret_key=SecretStr("unit-test-only-secret-key-with-more-than-32-bytes"),
    )


@pytest.fixture
def app(settings):
    return create_app(settings)


@pytest.fixture
def client(app):
    # raise_server_exceptions=False lets us assert the real 500 response body.
    app.state.redis_client = FakeRedis()
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


@pytest.fixture(scope="session")
def migrated_test_database(test_database_url: str) -> None:
    """Upgrade the dedicated *_test database before authenticated API tests."""
    engine = create_engine(test_database_url, poolclass=NullPool)
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    try:
        with engine.connect() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
    finally:
        engine.dispose()


@pytest.fixture
def db_client(test_database_url, migrated_test_database):
    from pydantic import SecretStr

    s = Settings(
        _env_file=None, app_env="testing", trusted_hosts=["testserver"],
        jwt_secret_key=SecretStr("unit-test-only-secret-key-with-more-than-32-bytes"),
        database_url=SecretStr(test_database_url), db_pool_size=2, db_max_overflow=0,
    )
    app = create_app(s)
    fake_sender = FakeEmailSender()
    app.state.email_sender = fake_sender
    app.state.redis_client = FakeRedis()
    try:
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c
    finally:
        emails = set(fake_sender.verification_tokens) | set(fake_sender.password_reset_tokens)
        if emails:
            cleanup_engine = create_engine(test_database_url, poolclass=NullPool)
            try:
                with Session(cleanup_engine) as db, db.begin():
                    user_ids = select(User.id).where(User.email.in_(emails))
                    db.execute(delete(AuthToken).where(AuthToken.user_id.in_(user_ids)))
                    db.execute(delete(User).where(User.email.in_(emails)))
            finally:
                cleanup_engine.dispose()
