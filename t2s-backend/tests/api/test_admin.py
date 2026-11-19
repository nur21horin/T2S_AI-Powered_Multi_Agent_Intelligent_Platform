from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.security.passwords import hash_password
from app.security.tokens import create_access_token


def _create_user(db_client, *, role: UserRole, email: str | None = None) -> User:
    email = email or f"admin-test-{uuid4().hex}@example.com"
    db: Session = db_client.app.state.session_factory()
    try:
        user = User(
            email=email,
            full_name="Authorization Test",
            password_hash=hash_password("a-valid-test-password-123"),
            role=role,
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        # The fixture removes only users whose emails are registered here.
        db_client.app.state.email_sender.verification_tokens[email] = "test-cleanup"
        return user
    finally:
        db.close()


def _auth_headers(client, user: User) -> dict[str, str]:
    token = create_access_token(user.id, client.app.state.settings, user.auth_version)
    return {"Authorization": f"Bearer {token}"}


def test_unauthenticated_caller_cannot_assign_roles(db_client):
    target = _create_user(db_client, role=UserRole.STUDENT)

    response = db_client.patch(
        f"/api/v1/admin/users/{target.id}/role", json={"role": "ADMIN"}
    )

    assert response.status_code == 401


def test_administrator_bootstrap_is_not_exposed_as_a_public_api(db_client):
    response = db_client.post("/api/v1/admin/bootstrap")

    assert response.status_code == 404


def test_non_admin_roles_cannot_assign_roles(db_client):
    target = _create_user(db_client, role=UserRole.STUDENT)
    for role in (UserRole.STUDENT, UserRole.TEACHER, UserRole.ALUMNI):
        actor = _create_user(db_client, role=role)
        response = db_client.patch(
            f"/api/v1/admin/users/{target.id}/role",
            json={"role": "ADMIN"},
            headers=_auth_headers(db_client, actor),
        )
        assert response.status_code == 403


def test_admin_can_assign_privileged_role_and_invalidates_old_access_token(db_client):
    actor = _create_user(db_client, role=UserRole.ADMIN)
    target = _create_user(db_client, role=UserRole.STUDENT)
    old_target_token = create_access_token(
        target.id, db_client.app.state.settings, target.auth_version
    )

    response = db_client.patch(
        f"/api/v1/admin/users/{target.id}/role",
        json={"role": "ADMIN"},
        headers=_auth_headers(db_client, actor),
    )

    assert response.status_code == 200, response.text
    assert response.json()["role"] == "ADMIN"
    db: Session = db_client.app.state.session_factory()
    try:
        updated = db.scalar(select(User).where(User.id == target.id))
        assert updated.role == UserRole.ADMIN
        assert updated.auth_version == target.auth_version + 1
    finally:
        db.close()
    assert db_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {old_target_token}"}
    ).status_code == 401


def test_admin_cannot_change_own_role(db_client):
    admin = _create_user(db_client, role=UserRole.ADMIN)

    response = db_client.patch(
        f"/api/v1/admin/users/{admin.id}/role",
        json={"role": "STUDENT"},
        headers=_auth_headers(db_client, admin),
    )

    assert response.status_code == 403


def test_admin_can_demote_another_admin_without_removing_final_admin(db_client):
    actor = _create_user(db_client, role=UserRole.ADMIN)
    target = _create_user(db_client, role=UserRole.ADMIN)

    response = db_client.patch(
        f"/api/v1/admin/users/{target.id}/role",
        json={"role": "STUDENT"},
        headers=_auth_headers(db_client, actor),
    )

    assert response.status_code == 200
    db: Session = db_client.app.state.session_factory()
    try:
        remaining_admin = db.scalar(select(User).where(User.id == actor.id))
        demoted = db.scalar(select(User).where(User.id == target.id))
        assert remaining_admin.role == UserRole.ADMIN and remaining_admin.is_active
        assert demoted.role == UserRole.STUDENT
    finally:
        db.close()


def test_role_change_emits_structured_audit_metadata_without_credentials(
    db_client, monkeypatch
):
    actor = _create_user(db_client, role=UserRole.ADMIN)
    target = _create_user(db_client, role=UserRole.ALUMNI)
    captured = []
    monkeypatch.setattr(
        "app.services.user_service.record_privileged_action",
        lambda **fields: captured.append(fields),
    )

    response = db_client.patch(
        f"/api/v1/admin/users/{target.id}/role",
        json={"role": "TEACHER"},
        headers=_auth_headers(db_client, actor),
    )

    assert response.status_code == 200
    assert captured == [
        {
            "action": "admin.user_role.changed",
            "actor_id": actor.id,
            "target_id": target.id,
            "old_role": "ALUMNI",
            "new_role": "TEACHER",
        }
    ]
    assert "password" not in repr(captured).lower()


def test_role_and_auth_version_change_roll_back_together(db_client, monkeypatch):
    actor = _create_user(db_client, role=UserRole.ADMIN)
    target = _create_user(db_client, role=UserRole.STUDENT)

    def fail_version_update(*_args):
        raise RuntimeError("injected database failure")

    monkeypatch.setattr(UserRepository, "increment_auth_version", fail_version_update)
    response = db_client.patch(
        f"/api/v1/admin/users/{target.id}/role",
        json={"role": "TEACHER"},
        headers=_auth_headers(db_client, actor),
    )

    assert response.status_code == 500
    assert "injected database failure" not in response.text
    db: Session = db_client.app.state.session_factory()
    try:
        unchanged = db.scalar(select(User).where(User.id == target.id))
        assert unchanged.role == UserRole.STUDENT
        assert unchanged.auth_version == target.auth_version
    finally:
        db.close()
