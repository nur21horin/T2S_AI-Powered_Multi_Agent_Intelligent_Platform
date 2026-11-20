from pydantic import SecretStr
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from tests.conftest import FakeRedis


def test_lifespan_creates_and_closes_shared_redis_client(monkeypatch):
    fake = FakeRedis()
    settings = Settings(
        _env_file=None,
        app_env="testing",
        trusted_hosts=["testserver"],
        redis_url=SecretStr("redis://localhost:6379/0"),
    )
    monkeypatch.setattr("app.core.lifespan.Redis.from_url", lambda *args, **kwargs: fake)
    app = create_app(settings)

    with TestClient(app) as client:
        assert app.state.redis_client is fake
        assert client.get("/api/v1/health").status_code == 200

    assert fake.closed
