from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from app.models.auth_token import AuthToken
from app.repositories.token_repository import TokenRepository
from app.security.revocation import revocation_key
from app.security.tokens import (
    create_access_token,
    decode_access_token,
    hash_opaque_token,
)
from tests.api.test_auth import WEB_ORIGIN, _login, _register_and_verify


def _logout(client, csrf: str, access: str | None = None):
    headers = {"Origin": WEB_ORIGIN, "X-CSRF-Token": csrf}
    if access is not None:
        headers["Authorization"] = f"Bearer {access}"
    return client.post("/api/v1/auth/logout", headers=headers)


def _token_row(test_database_url: str, refresh: str) -> AuthToken:
    engine = create_engine(test_database_url, poolclass=NullPool)
    try:
        with Session(engine) as db:
            token = db.scalar(
                select(AuthToken).where(AuthToken.token_hash == hash_opaque_token(refresh))
            )
            assert token is not None
            db.expunge(token)
            return token
    finally:
        engine.dispose()


def test_logout_revokes_redis_before_database_and_repeated_calls_are_idempotent(
    db_client, test_database_url, monkeypatch
):
    email = _register_and_verify(db_client)
    login = _login(db_client, email)
    access = login.json()["access_token"]
    refresh = db_client.cookies.get("t2s_refresh")
    csrf = login.json()["csrf_token"]
    store = db_client.app.state.redis_client
    store.operations.clear()

    original_get = TokenRepository.get_by_hash
    original_revoke = TokenRepository.revoke_family
    original_commit = Session.commit

    def tracked_get(repository, db, token_hash):
        store.operations.append("postgres:lookup")
        return original_get(repository, db, token_hash)

    def tracked_revoke(repository, db, family_id, now):
        store.operations.append("postgres:revoke")
        return original_revoke(repository, db, family_id, now)

    def tracked_commit(db):
        store.operations.append("postgres:commit")
        return original_commit(db)

    monkeypatch.setattr(TokenRepository, "get_by_hash", tracked_get)
    monkeypatch.setattr(TokenRepository, "revoke_family", tracked_revoke)
    monkeypatch.setattr(Session, "commit", tracked_commit)

    first = _logout(db_client, csrf, access)
    assert first.status_code == 200
    assert store.operations == [
        "redis:set",
        "postgres:lookup",
        "postgres:revoke",
        "postgres:commit",
    ]
    claims = decode_access_token(access, db_client.app.state.settings)
    assert revocation_key(claims.jti) in store.values
    assert _token_row(test_database_url, refresh).revoked_at is not None

    db_client.cookies.set("t2s_refresh", refresh, path="/api/v1/auth")
    db_client.cookies.set("t2s_csrf", csrf, path="/api/v1/auth")
    repeated = _logout(db_client, csrf, access)
    assert repeated.status_code == 200
    assert store.operations[4:] == [
        "redis:set",
        "postgres:lookup",
        "postgres:revoke",
        "postgres:commit",
    ]
    assert db_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"}
    ).status_code == 401


def test_redis_failure_prevents_database_revocation_and_retry_completes(
    db_client, test_database_url
):
    email = _register_and_verify(db_client)
    login = _login(db_client, email)
    access = login.json()["access_token"]
    refresh = db_client.cookies.get("t2s_refresh")
    csrf = login.json()["csrf_token"]
    store = db_client.app.state.redis_client
    store.available = False

    failed = _logout(db_client, csrf, access)
    assert failed.status_code == 503
    assert store.operations == []
    assert _token_row(test_database_url, refresh).revoked_at is None

    store.available = True
    retried = _logout(db_client, csrf, access)
    assert retried.status_code == 200
    assert _token_row(test_database_url, refresh).revoked_at is not None
    assert db_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"}
    ).status_code == 401


def test_redis_failure_when_family_is_already_revoked_is_retryable(
    db_client, test_database_url
):
    email = _register_and_verify(db_client)
    login = _login(db_client, email)
    access = login.json()["access_token"]
    refresh = db_client.cookies.get("t2s_refresh")
    csrf = login.json()["csrf_token"]
    row = _token_row(test_database_url, refresh)

    engine = create_engine(test_database_url, poolclass=NullPool)
    try:
        with Session(engine) as db, db.begin():
            db.execute(
                update(AuthToken)
                .where(AuthToken.family_id == row.family_id)
                .values(revoked_at=datetime.now(UTC))
            )
    finally:
        engine.dispose()

    store = db_client.app.state.redis_client
    store.available = False
    failed_retry = _logout(db_client, csrf, access)
    assert failed_retry.status_code == 503
    assert _token_row(test_database_url, refresh).revoked_at is not None

    store.available = True
    completed_retry = _logout(db_client, csrf, access)
    assert completed_retry.status_code == 200
    assert revocation_key(decode_access_token(access, db_client.app.state.settings).jti) in (
        store.values
    )


def test_database_failure_after_redis_write_rolls_back_and_can_be_retried(
    db_client, test_database_url, monkeypatch
):
    email = _register_and_verify(db_client)
    login = _login(db_client, email)
    access = login.json()["access_token"]
    refresh = db_client.cookies.get("t2s_refresh")
    csrf = login.json()["csrf_token"]
    claims = decode_access_token(access, db_client.app.state.settings)
    rollback_calls = []
    original_rollback = Session.rollback

    def tracked_rollback(db):
        rollback_calls.append(True)
        return original_rollback(db)

    with monkeypatch.context() as patch:
        patch.setattr(
            TokenRepository,
            "revoke_family",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                SQLAlchemyError("simulated database failure")
            ),
        )
        patch.setattr(Session, "rollback", tracked_rollback)
        failed = _logout(db_client, csrf, access)

    assert failed.status_code == 503
    assert rollback_calls
    assert revocation_key(claims.jti) in db_client.app.state.redis_client.values
    assert _token_row(test_database_url, refresh).revoked_at is None

    retried = _logout(db_client, csrf, access)
    assert retried.status_code == 200
    assert _token_row(test_database_url, refresh).revoked_at is not None


def test_expired_or_invalid_access_token_does_not_block_refresh_logout(db_client):
    email = _register_and_verify(db_client)
    login = _login(db_client, email)
    access = login.json()["access_token"]
    csrf = login.json()["csrf_token"]
    claims = decode_access_token(access, db_client.app.state.settings)
    expired = create_access_token(
        claims.user_id,
        db_client.app.state.settings,
        claims.auth_version,
        now=datetime.now(UTC) - timedelta(minutes=30),
    )
    store = db_client.app.state.redis_client

    expired_response = _logout(db_client, csrf, expired)
    assert expired_response.status_code == 200
    assert store.operations == []

    # Repeated logout with a malformed token still revokes no usable credential.
    db_client.cookies.set(
        "t2s_refresh", login.cookies.get("t2s_refresh"), path="/api/v1/auth"
    )
    db_client.cookies.set("t2s_csrf", csrf, path="/api/v1/auth")
    invalid_response = _logout(db_client, csrf, "not-a-jwt")
    assert invalid_response.status_code == 200
    assert store.operations == []


def test_logout_handles_missing_access_and_refresh_tokens(db_client):
    email = _register_and_verify(db_client)
    login = _login(db_client, email)
    access = login.json()["access_token"]
    refresh = login.cookies.get("t2s_refresh")
    csrf = login.json()["csrf_token"]
    store = db_client.app.state.redis_client

    # Without the access token, logout revokes the presented refresh family only.
    no_access = _logout(db_client, csrf)
    assert no_access.status_code == 200
    assert store.operations == []

    # A valid access token can still be revoked when no refresh cookie is present.
    db_client.cookies.set("t2s_refresh", refresh, path="/api/v1/auth")
    db_client.cookies.set("t2s_csrf", csrf, path="/api/v1/auth")
    db_client.cookies.delete("t2s_refresh")
    no_refresh = _logout(db_client, csrf, access)
    assert no_refresh.status_code == 200
    assert store.operations == ["redis:set"]
