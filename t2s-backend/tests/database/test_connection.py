from fastapi import Depends
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import text

from app.api.deps import get_db
from app.core.config import Settings
from app.main import create_app

BOGUS_URL = "postgresql+psycopg://t2s:SuperSecretPw@127.0.0.1:1/nodb"  # nothing listens on :1


def _client(**overrides):
    s = Settings(_env_file=None, app_env="testing", trusted_hosts=["testserver"], **overrides)
    return TestClient(create_app(s), raise_server_exceptions=False)


def test_ready_ok_with_database(db_client):
    r = db_client.get("/api/v1/health/ready")
    assert r.status_code == 200
    assert r.json() == {"status": "ready", "database": "ok"}


def test_ready_503_when_database_not_configured():
    with _client() as c:
        r = c.get("/api/v1/health/ready")
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "service_unavailable"


def test_ready_503_when_database_unreachable_and_no_secret_leak():
    with _client(database_url=SecretStr(BOGUS_URL)) as c:
        r = c.get("/api/v1/health/ready")
        assert r.status_code == 503
        assert "SuperSecretPw" not in r.text and "127.0.0.1" not in r.text
        # the app stays alive: liveness is unaffected by DB outage
        assert c.get("/api/v1/health").status_code == 200


def test_app_starts_even_if_database_is_down():
    with _client(database_url=SecretStr(BOGUS_URL)) as c:
        assert c.get("/api/v1/health").status_code == 200


def test_statement_timeout_applied(db_client):
    app = db_client.app

    @app.get("/_test/timeout")
    def show(db=Depends(get_db)) -> dict:
        return {"v": db.execute(text("SHOW statement_timeout")).scalar()}

    assert db_client.get("/_test/timeout").json() == {"v": "30s"}


def test_no_connection_leak_after_success_and_error(db_client):
    app = db_client.app

    @app.get("/_test/ok")
    def ok(db=Depends(get_db)) -> dict:
        db.execute(text("SELECT 1"))
        return {}

    @app.get("/_test/fail")
    def fail(db=Depends(get_db)) -> dict:
        db.execute(text("SELECT 1"))
        raise RuntimeError("boom")

    for _ in range(5):  # pool_size=2, max_overflow=0: a leak would exhaust the pool
        assert db_client.get("/_test/ok").status_code == 200
        assert db_client.get("/_test/fail").status_code == 500
    assert app.state.engine.pool.checkedout() == 0
