from uuid import uuid4

from app.services.email_service import SMTPEmailService
from tests.factories import FakeEmailSender

WEB_ORIGIN = "http://localhost:3000"


def _register_and_verify(client, email: str | None = None) -> str:
    email = email or f"student-{uuid4().hex}@example.com"
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email.upper(),
            "full_name": "Test Student",
            "password": "correct-horse-battery-42",
            "role": "ADMIN",
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["role"] == "STUDENT"
    assert "password" not in response.json()
    assert "password_hash" not in response.json()

    sender: FakeEmailSender = client.app.state.email_sender
    verification_token = sender.verification_tokens[email.lower()]
    verified = client.post(
        "/api/v1/auth/email/verify", json={"token": verification_token}
    )
    assert verified.status_code == 200, verified.text
    return email.lower()


def _login(client, email: str, password: str = "correct-horse-battery-42"):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
        headers={"Origin": WEB_ORIGIN},
    )


def test_registration_normalizes_email_and_rejects_duplicate(db_client):
    email = f"student-{uuid4().hex}@example.com"
    response = db_client.post(
        "/api/v1/auth/register",
        json={
            "email": email.upper(),
            "full_name": "Test Student",
            "password": "correct-horse-battery-42",
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["email"] == email

    duplicate = db_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Duplicate Student",
            "password": "another-correct-password-42",
        },
    )
    assert duplicate.status_code == 409


def test_unverified_cannot_login_then_verified_user_can_login_and_read_self(db_client):
    email = f"student-{uuid4().hex}@example.com"
    registration = db_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Test Student",
            "password": "correct-horse-battery-42",
        },
    )
    assert registration.status_code == 201
    assert _login(db_client, email).status_code == 401

    token = db_client.app.state.email_sender.verification_tokens[email]
    assert db_client.post("/api/v1/auth/email/verify", json={"token": token}).status_code == 200
    response = _login(db_client, email)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["csrf_token"]
    assert "password_hash" not in response.text
    assert body["access_token"] not in db_client.cookies.values()
    refresh_cookie = next(
        value for value in response.headers.get_list("set-cookie") if "t2s_refresh=" in value
    )
    assert "httponly" in refresh_cookie.lower()
    assert "samesite=lax" in refresh_cookie.lower()
    assert "correct-horse-battery-42" not in response.text

    me = db_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["email"] == email
    assert "password_hash" not in me.text


def test_refresh_rotates_cookie_and_replay_revokes_entire_family(db_client):
    email = _register_and_verify(db_client)
    login = _login(db_client, email)
    assert login.status_code == 200
    original_refresh = db_client.cookies.get("t2s_refresh")
    csrf = login.json()["csrf_token"]
    assert original_refresh

    rotated = db_client.post(
        "/api/v1/auth/refresh",
        headers={"Origin": WEB_ORIGIN, "X-CSRF-Token": csrf},
    )
    assert rotated.status_code == 200, rotated.text
    rotated_refresh = db_client.cookies.get("t2s_refresh")
    assert rotated_refresh and rotated_refresh != original_refresh

    replay = db_client.post(
        "/api/v1/auth/refresh",
        headers={
            "Origin": WEB_ORIGIN,
            "X-CSRF-Token": rotated.json()["csrf_token"],
            "Cookie": f"t2s_refresh={original_refresh}; t2s_csrf={rotated.json()['csrf_token']}",
        },
    )
    assert replay.status_code == 401

    family_token = db_client.post(
        "/api/v1/auth/refresh",
        headers={
            "Origin": WEB_ORIGIN,
            "X-CSRF-Token": rotated.json()["csrf_token"],
            "Cookie": f"t2s_refresh={rotated_refresh}; t2s_csrf={rotated.json()['csrf_token']}",
        },
    )
    assert family_token.status_code == 401


def test_logout_requires_csrf_and_revokes_refresh_cookie(db_client):
    email = _register_and_verify(db_client)
    login = _login(db_client, email)
    assert login.status_code == 200
    csrf = login.json()["csrf_token"]
    refresh = db_client.cookies.get("t2s_refresh")

    missing_csrf = db_client.post("/api/v1/auth/logout", headers={"Origin": WEB_ORIGIN})
    assert missing_csrf.status_code == 403
    wrong_origin = db_client.post(
        "/api/v1/auth/logout",
        headers={"Origin": "https://attacker.example", "X-CSRF-Token": csrf},
    )
    assert wrong_origin.status_code == 403

    response = db_client.post(
        "/api/v1/auth/logout",
        headers={"Origin": WEB_ORIGIN, "X-CSRF-Token": csrf},
    )
    assert response.status_code == 200
    assert db_client.post(
        "/api/v1/auth/refresh",
        headers={
            "Origin": WEB_ORIGIN,
            "X-CSRF-Token": csrf,
            "Cookie": f"t2s_refresh={refresh}; t2s_csrf={csrf}",
        },
    ).status_code == 401


def test_csrf_endpoint_supports_frontend_reload(db_client):
    email = _register_and_verify(db_client)
    login = _login(db_client, email)
    csrf = login.json()["csrf_token"]

    response = db_client.get("/api/v1/auth/csrf", headers={"Origin": WEB_ORIGIN})
    assert response.status_code == 200
    assert response.json()["csrf_token"] == csrf


def test_password_recovery_is_generic_and_resets_password(db_client):
    email = _register_and_verify(db_client)
    existing = db_client.post("/api/v1/auth/password/forgot", json={"email": email})
    missing = db_client.post(
        "/api/v1/auth/password/forgot", json={"email": f"missing-{uuid4().hex}@example.com"}
    )
    assert existing.status_code == missing.status_code == 200
    assert existing.json() == missing.json()

    token = db_client.app.state.email_sender.password_reset_tokens[email]
    reset = db_client.post(
        "/api/v1/auth/password/reset",
        json={"token": token, "new_password": "new-correct-password-57"},
    )
    assert reset.status_code == 200
    assert db_client.post(
        "/api/v1/auth/password/reset",
        json={"token": token, "new_password": "another-password-58"},
    ).status_code == 401
    assert _login(db_client, email).status_code == 401
    assert _login(db_client, email, "new-correct-password-57").status_code == 200


def test_password_change_requires_current_password_and_invalidates_refresh(db_client):
    email = _register_and_verify(db_client)
    login = _login(db_client, email)
    access = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {access}"}

    rejected = db_client.post(
        "/api/v1/auth/password/change",
        json={"current_password": "wrong-password", "new_password": "new-correct-password-57"},
        headers=headers,
    )
    assert rejected.status_code == 401
    changed = db_client.post(
        "/api/v1/auth/password/change",
        json={
            "current_password": "correct-horse-battery-42",
            "new_password": "new-correct-password-57",
        },
        headers=headers,
    )
    assert changed.status_code == 200
    assert _login(db_client, email).status_code == 401
    assert _login(db_client, email, "new-correct-password-57").status_code == 200


def test_email_endpoints_fail_safely_without_smtp(db_client):
    db_client.app.state.email_sender = SMTPEmailService(db_client.app.state.settings)
    response = db_client.post(
        "/api/v1/auth/password/forgot", json={"email": "person@example.com"}
    )
    assert response.status_code == 503
    assert "sent" not in response.text.lower()
