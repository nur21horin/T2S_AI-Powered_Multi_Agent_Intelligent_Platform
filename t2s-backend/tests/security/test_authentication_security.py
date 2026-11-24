from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from app.core.enums import AuthTokenPurpose
from app.models.auth_token import AuthToken
from app.models.user import User
from app.security.tokens import hash_opaque_token
from app.services.email_service import SMTPEmailService


def test_password_and_verification_tokens_are_only_stored_as_hashes(db_client, test_database_url):
    email = f"private-{uuid4().hex}@example.com"
    password = "correct-horse-battery-42"
    response = db_client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Private Student", "password": password},
    )
    assert response.status_code == 201
    raw_email_token = db_client.app.state.email_sender.verification_tokens[email]

    engine = create_engine(test_database_url, poolclass=NullPool)
    try:
        with Session(engine) as db:
            user = db.scalar(select(User).where(User.email == email))
            token = db.scalar(
                select(AuthToken).where(
                    AuthToken.user_id == user.id,
                    AuthToken.purpose == AuthTokenPurpose.EMAIL_VERIFICATION,
                )
            )
            assert user.password_hash.startswith("$argon2id$")
            assert password not in user.password_hash
            assert token.token_hash == hash_opaque_token(raw_email_token)
            assert raw_email_token not in token.token_hash
    finally:
        engine.dispose()


def test_inactive_users_cannot_login_or_use_existing_access_token(db_client, test_database_url):
    email = f"inactive-{uuid4().hex}@example.com"
    register = db_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Inactive Student",
            "password": "correct-horse-battery-42",
        },
    )
    assert register.status_code == 201
    token = db_client.app.state.email_sender.verification_tokens[email]
    assert db_client.post("/api/v1/auth/email/verify", json={"token": token}).status_code == 200
    login = db_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "correct-horse-battery-42"},
        headers={"Origin": "http://localhost:3000"},
    )
    assert login.status_code == 200

    engine = create_engine(test_database_url, poolclass=NullPool)
    try:
        with Session(engine) as db:
            user = db.scalar(select(User).where(User.email == email))
            user.is_active = False
            db.commit()
    finally:
        engine.dispose()

    assert db_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "correct-horse-battery-42"},
        headers={"Origin": "http://localhost:3000"},
    ).status_code == 401
    assert db_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    ).status_code == 401


def test_expired_verification_token_cannot_verify_account(db_client, test_database_url):
    email = f"expired-{uuid4().hex}@example.com"
    response = db_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Expired Student",
            "password": "correct-horse-battery-42",
        },
    )
    assert response.status_code == 201
    raw_token = db_client.app.state.email_sender.verification_tokens[email]

    engine = create_engine(test_database_url, poolclass=NullPool)
    try:
        with Session(engine) as db:
            token = db.scalar(
                select(AuthToken).where(AuthToken.token_hash == hash_opaque_token(raw_token))
            )
            token.expires_at = datetime.now(UTC) - timedelta(seconds=1)
            db.commit()
    finally:
        engine.dispose()

    assert db_client.post(
        "/api/v1/auth/email/verify", json={"token": raw_token}
    ).status_code == 401


def test_registration_does_not_create_account_if_email_delivery_unavailable(
    db_client, test_database_url
):
    email = f"no-mail-{uuid4().hex}@example.com"
    db_client.app.state.email_sender = SMTPEmailService(db_client.app.state.settings)
    response = db_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "No Mail Student",
            "password": "correct-horse-battery-42",
        },
    )
    assert response.status_code == 503
    assert "sent" not in response.text.lower()

    engine = create_engine(test_database_url, poolclass=NullPool)
    try:
        with Session(engine) as db:
            assert db.scalar(select(User).where(User.email == email)) is None
    finally:
        engine.dispose()


def test_csrf_token_is_signed_and_cannot_be_forged(settings):
    from app.security.csrf import create_csrf_token, verify_csrf_pair

    secret = settings.jwt_secret_key.get_secret_value()
    valid = create_csrf_token(secret)
    assert verify_csrf_pair(valid, valid, secret)
    assert not verify_csrf_pair(valid, "attacker-token", secret)
    assert not verify_csrf_pair("unsigned.value", "unsigned.value", secret)
