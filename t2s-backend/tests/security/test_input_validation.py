from fastapi import HTTPException
from pydantic import BaseModel


class _Login(BaseModel):
    password: str


def test_validation_error_does_not_echo_submitted_input(app, client):
    @app.post("/_test/login")
    def login(body: _Login) -> dict:
        return {}

    r = client.post("/_test/login", json={"password": 12345, "extra": "SECRET-VALUE"})
    assert r.status_code == 422
    assert "12345" not in r.text and "SECRET-VALUE" not in r.text
    body = r.json()["error"]
    assert body["code"] == "validation_error"
    assert body["details"][0]["field"] == "body.password"


def test_unhandled_exception_returns_safe_500(app, client):
    @app.get("/_test/boom")
    def boom() -> None:
        raise RuntimeError("db password=hunter2")

    r = client.get("/_test/boom")
    assert r.status_code == 500
    assert "hunter2" not in r.text and "Traceback" not in r.text
    assert r.json()["error"]["code"] == "internal_error"


def test_unknown_route_uses_error_envelope(client):
    r = client.get("/api/v1/nope")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


def test_docs_disabled_in_production():
    from app.core.config import Settings
    from app.main import create_app
    from fastapi.testclient import TestClient
    from pydantic import SecretStr

    s = Settings(
        _env_file=None,
        app_env="production",
        trusted_hosts=["testserver"],
        jwt_secret_key=SecretStr("production-test-secret-key-over-32-bytes-long"),
    )
    c = TestClient(create_app(s), raise_server_exceptions=False)
    assert c.get("/docs").status_code == 404
