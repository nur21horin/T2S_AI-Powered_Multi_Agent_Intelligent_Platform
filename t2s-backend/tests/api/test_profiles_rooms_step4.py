from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.models.user import User
from app.security.passwords import hash_password
from app.security.tokens import create_access_token


def _user(client, role: UserRole) -> User:
    email = f"step4-{role.value.lower()}-{uuid4().hex}@example.com"
    db: Session = client.app.state.session_factory()
    try:
        user = User(email=email, full_name="Step Four User", password_hash=hash_password("step4-password-123"), role=role, is_active=True, is_verified=True)
        db.add(user)
        db.commit()
        db.refresh(user)
        client.app.state.email_sender.verification_tokens[email] = "cleanup"
        return user
    finally:
        db.close()


def _headers(client, user: User) -> dict[str, str]:
    token = create_access_token(user.id, client.app.state.settings, user.auth_version)
    return {"Authorization": f"Bearer {token}"}


def test_role_specific_profile_and_protected_fields(db_client):
    student = _user(db_client, UserRole.STUDENT)
    response = db_client.put("/api/v1/profiles/me", json={"department": "Computer Science", "bio": "Learner"}, headers=_headers(db_client, student))
    assert response.status_code == 200, response.text
    assert response.json()["profile_type"] == "student"
    assert response.json()["department"] == "Computer Science"

    forbidden_field = db_client.put("/api/v1/profiles/me", json={"designation": "Professor"}, headers=_headers(db_client, student))
    assert forbidden_field.status_code == 400


def test_profile_is_explicit_and_cross_user_access_does_not_expose_admin(db_client):
    student = _user(db_client, UserRole.STUDENT)
    other = _user(db_client, UserRole.STUDENT)
    assert db_client.get("/api/v1/profiles/me", headers=_headers(db_client, student)).status_code == 404
    assert db_client.put("/api/v1/profiles/me", json={"bio": "Private"}, headers=_headers(db_client, other)).status_code == 200
    assert db_client.get(f"/api/v1/profiles/{other.id}", headers=_headers(db_client, student)).status_code == 200


def test_skill_and_interest_associations_are_normalized_and_owned(db_client):
    student = _user(db_client, UserRole.STUDENT)
    headers = _headers(db_client, student)
    skills = db_client.put("/api/v1/profiles/me/skills", json={"names": [" Python ", "python"]}, headers=headers)
    interests = db_client.put("/api/v1/profiles/me/interests", json={"names": [" Machine Learning "]}, headers=headers)
    assert skills.status_code == 200 and interests.status_code == 200
    assert {item["name"] for item in skills.json()} == {"Python"}
    assert db_client.delete(f"/api/v1/profiles/me/skills/{uuid4()}", headers=headers).status_code == 204


def test_room_creation_assigns_owner_and_public_discovery_is_not_membership(db_client):
    owner = _user(db_client, UserRole.TEACHER)
    member = _user(db_client, UserRole.STUDENT)
    owner_headers, member_headers = _headers(db_client, owner), _headers(db_client, member)
    created = db_client.post("/api/v1/rooms", json={"name": "Python Programming", "visibility": "PUBLIC"}, headers=owner_headers)
    assert created.status_code == 201
    room = created.json()
    listed = db_client.get("/api/v1/rooms", headers=member_headers)
    assert listed.status_code == 200 and listed.json()[0]["id"] == room["id"]
    assert db_client.get(f"/api/v1/rooms/{room['id']}/members", headers=member_headers).status_code == 403


def test_room_membership_request_approval_and_owner_protection(db_client):
    owner = _user(db_client, UserRole.TEACHER)
    member = _user(db_client, UserRole.STUDENT)
    owner_headers, member_headers = _headers(db_client, owner), _headers(db_client, member)
    room = db_client.post("/api/v1/rooms", json={"name": f"Room {uuid4().hex}"}, headers=owner_headers).json()
    request = db_client.post(f"/api/v1/rooms/{room['id']}/join-requests", headers=member_headers)
    assert request.status_code == 201
    duplicate = db_client.post(f"/api/v1/rooms/{room['id']}/join-requests", headers=member_headers)
    assert duplicate.status_code == 409
    approved = db_client.post(f"/api/v1/rooms/{room['id']}/join-requests/{request.json()['id']}/approve", headers=owner_headers)
    assert approved.status_code == 200 and approved.json()["status"] == "APPROVED"
    assert db_client.get(f"/api/v1/rooms/{room['id']}/members", headers=member_headers).status_code == 200
    assert db_client.delete(f"/api/v1/rooms/{room['id']}/membership", headers=owner_headers).status_code == 403


def test_non_owner_cannot_manage_room_or_requests(db_client):
    owner = _user(db_client, UserRole.STUDENT)
    other = _user(db_client, UserRole.STUDENT)
    owner_headers, other_headers = _headers(db_client, owner), _headers(db_client, other)
    room = db_client.post("/api/v1/rooms", json={"name": f"Owned {uuid4().hex}"}, headers=owner_headers).json()
    assert db_client.patch(f"/api/v1/rooms/{room['id']}", json={"topic": "x"}, headers=other_headers).status_code == 403
    assert db_client.get(f"/api/v1/rooms/{room['id']}/join-requests", headers=other_headers).status_code == 403


def test_request_cancellation_is_bound_to_room_path(db_client):
    owner = _user(db_client, UserRole.TEACHER)
    member = _user(db_client, UserRole.STUDENT)
    owner_headers, member_headers = _headers(db_client, owner), _headers(db_client, member)
    room_a = db_client.post("/api/v1/rooms", json={"name": f"Room A {uuid4().hex}"}, headers=owner_headers).json()
    room_b = db_client.post("/api/v1/rooms", json={"name": f"Room B {uuid4().hex}"}, headers=owner_headers).json()
    request = db_client.post(f"/api/v1/rooms/{room_a['id']}/join-requests", headers=member_headers).json()

    wrong_room = db_client.delete(f"/api/v1/rooms/{room_b['id']}/join-requests/{request['id']}", headers=member_headers)
    assert wrong_room.status_code == 404
    assert db_client.get("/api/v1/rooms/join-requests/mine", headers=member_headers).json()[0]["status"] == "PENDING"


def test_left_member_can_rejoin_after_new_approval(db_client):
    owner = _user(db_client, UserRole.TEACHER)
    member = _user(db_client, UserRole.STUDENT)
    owner_headers, member_headers = _headers(db_client, owner), _headers(db_client, member)
    room = db_client.post("/api/v1/rooms", json={"name": f"Rejoin {uuid4().hex}"}, headers=owner_headers).json()

    first = db_client.post(f"/api/v1/rooms/{room['id']}/join-requests", headers=member_headers).json()
    assert db_client.post(f"/api/v1/rooms/{room['id']}/join-requests/{first['id']}/approve", headers=owner_headers).status_code == 200
    assert db_client.delete(f"/api/v1/rooms/{room['id']}/membership", headers=member_headers).status_code == 204
    second = db_client.post(f"/api/v1/rooms/{room['id']}/join-requests", headers=member_headers)
    assert second.status_code == 201
    approved = db_client.post(f"/api/v1/rooms/{room['id']}/join-requests/{second.json()['id']}/approve", headers=owner_headers)
    assert approved.status_code == 200
    assert any(item["user_id"] == str(member.id) for item in db_client.get(f"/api/v1/rooms/{room['id']}/members", headers=member_headers).json())


def test_invalid_nullable_room_updates_are_client_errors(db_client):
    owner = _user(db_client, UserRole.TEACHER)
    headers = _headers(db_client, owner)
    room = db_client.post("/api/v1/rooms", json={"name": f"Validation {uuid4().hex}"}, headers=headers).json()
    assert db_client.patch(f"/api/v1/rooms/{room['id']}", json={"name": None}, headers=headers).status_code == 400
    assert db_client.patch(f"/api/v1/rooms/{room['id']}", json={"visibility": None}, headers=headers).status_code == 400


def test_archived_room_rejects_membership_decisions(db_client):
    owner = _user(db_client, UserRole.TEACHER)
    member = _user(db_client, UserRole.STUDENT)
    owner_headers, member_headers = _headers(db_client, owner), _headers(db_client, member)
    room = db_client.post("/api/v1/rooms", json={"name": f"Archived {uuid4().hex}"}, headers=owner_headers).json()
    request = db_client.post(f"/api/v1/rooms/{room['id']}/join-requests", headers=member_headers).json()
    assert db_client.post(f"/api/v1/rooms/{room['id']}/archive", headers=owner_headers).status_code == 204
    assert db_client.post(f"/api/v1/rooms/{room['id']}/join-requests/{request['id']}/approve", headers=owner_headers).status_code == 404
