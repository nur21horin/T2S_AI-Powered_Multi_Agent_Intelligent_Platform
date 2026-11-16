import os
import time
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from pydantic import SecretStr
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import ResponseError
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
        self.rate_limit_counters: dict[str, tuple[int, float | None]] = {}
        self.rate_limit_ttl_overrides: dict[str, int] = {}
        self.rate_limit_key_types: dict[str, str] = {}
        self.rate_limit_events: list[tuple[str, str]] = []
        self.rate_limit_now = 1_000_000.0
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

    def eval(self, script: str, numkeys: int, *keys_and_args: object) -> list[int]:
        """Emulate the limiter Lua script deterministically for unit tests."""
        self._require_available()
        if numkeys < 1 or len(keys_and_args) < numkeys:
            raise ValueError("unexpected rate-limit script arguments")
        keys = list(keys_and_args[:numkeys])
        args = list(keys_and_args[numkeys:])
        if any(not isinstance(key, str) for key in keys):
            raise ValueError("invalid rate-limit keys")
        now = self.rate_limit_now
        if numkeys == 1 and len(args) == 1:
            window_ms = args[0]
            if not isinstance(window_ms, int):
                raise ValueError("invalid rate-limit window")
            key = keys[0]
            count, expires_at = self.rate_limit_counters.get(key, (0, None))
            if expires_at is not None and expires_at <= now:
                count, expires_at = 0, None
            count += 1
            if count == 1 or expires_at is None:
                expires_at = now + window_ms / 1000
            ttl_ms = max(0, int((expires_at - now) * 1000))
            self.rate_limit_counters[key] = (count, expires_at)
            self.operations.append("redis:eval")
            return [count, ttl_ms]

        if len(args) != numkeys * 2:
            raise ValueError("unexpected multi-key rate-limit arguments")
        limits, windows_ms = args[:numkeys], args[numkeys:]
        if any(not isinstance(value, int) for value in (*limits, *windows_ms)):
            raise ValueError("invalid multi-key rate-limit values")

        preflight: list[tuple[str, int, int, float | None]] = []
        for key, limit, window_ms in zip(keys, limits, windows_ms):
            key_type = self.rate_limit_key_types.get(
                key, "string" if key in self.rate_limit_counters else "none"
            )
            if key_type not in {"none", "string"}:
                raise ResponseError("invalid rate-limit counter type")

            count, expires_at = self.rate_limit_counters.get(key, (0, None))
            if key in self.rate_limit_ttl_overrides:
                ttl_ms = self.rate_limit_ttl_overrides[key]
            elif key_type == "none" or (expires_at is not None and expires_at <= now):
                ttl_ms = -2
            elif expires_at is None:
                ttl_ms = -1
            else:
                ttl_ms = max(0, int((expires_at - now) * 1000))

            self.rate_limit_events.append(("preflight", key))
            if ttl_ms == -2:
                count, expires_at = 0, None
            elif ttl_ms == -1 or ttl_ms > 0:
                if key_type != "string" or key not in self.rate_limit_counters:
                    raise ResponseError("invalid rate-limit counter state")
            else:
                raise ResponseError("invalid rate-limit counter TTL")
            preflight.append((key, count, ttl_ms, expires_at))

        updated: list[tuple[int, int]] = []
        allowed = 1
        remaining: int | None = None
        retry_after = 0
        for (key, count, ttl_ms_before, expires_at), limit, window_ms in zip(
            preflight, limits, windows_ms
        ):
            if ttl_ms_before == -2:
                count = 1
                expires_at = now + window_ms / 1000
                ttl_ms = window_ms
            elif ttl_ms_before == -1:
                count += 1
                expires_at = now + window_ms / 1000
                ttl_ms = window_ms
            else:
                count += 1
                ttl_ms = max(0, int((expires_at - now) * 1000))
            self.rate_limit_counters[key] = (count, expires_at)
            self.rate_limit_events.append(("write", key))
            left = max(limit - count, 0)
            remaining = left if remaining is None else min(remaining, left)
            if count > limit:
                allowed = 0
                retry_after = max(retry_after, max(1, (ttl_ms + 999) // 1000))
            updated.append((count, ttl_ms))

        self.operations.append("redis:eval-multi")
        result = [allowed, remaining or 0, retry_after]
        for count, ttl_ms in updated:
            result.extend((count, ttl_ms))
        return result

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
        rate_limit_key_secret=SecretStr("unit-test-rate-limit-secret-with-32-bytes"),
    )


@pytest.fixture
def app(settings):
    return create_app(settings)


@pytest.fixture
def client(app):
    # raise_server_exceptions=False lets us assert the real 500 response body.
    app.state.redis_client = FakeRedis()
    with TestClient(
        app, raise_server_exceptions=False, client=("127.0.0.1", 50000)
    ) as c:
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
        rate_limit_key_secret=SecretStr("unit-test-rate-limit-secret-with-32-bytes"),
        database_url=SecretStr(test_database_url), db_pool_size=2, db_max_overflow=0,
    )
    app = create_app(s)
    fake_sender = FakeEmailSender()
    app.state.email_sender = fake_sender
    app.state.redis_client = FakeRedis()
    try:
        with TestClient(
            app, raise_server_exceptions=False, client=("127.0.0.1", 50000)
        ) as c:
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
