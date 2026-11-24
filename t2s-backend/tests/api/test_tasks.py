from uuid import uuid4

from app.core.enums import UserRole
from tests.api.test_profiles_rooms_step4 import _headers, _user


def _room(client, owner):
    response = client.post(
        "/api/v1/rooms",
        json={"name": f"Step5 Room {uuid4().hex}"},
        headers=_headers(client, owner),
    )
    assert response.status_code == 201, response.text
    return response.json()


def _member(client, owner, member, room):
    request = client.post(
        f"/api/v1/rooms/{room['id']}/join-requests", headers=_headers(client, member)
    )
    assert request.status_code == 201, request.text
    approved = client.post(
        f"/api/v1/rooms/{room['id']}/join-requests/{request.json()['id']}/approve",
        headers=_headers(client, owner),
    )
    assert approved.status_code == 200, approved.text


def test_task_lifecycle_and_room_authorization(db_client):
    owner = _user(db_client, UserRole.TEACHER)
    student = _user(db_client, UserRole.STUDENT)
    room = _room(db_client, owner)
    owner_headers, student_headers = _headers(db_client, owner), _headers(db_client, student)

    created = db_client.post(
        f"/api/v1/rooms/{room['id']}/tasks",
        json={"title": "Secure API task", "max_score": 20},
        headers=owner_headers,
    )
    assert created.status_code == 201, created.text
    task = created.json()
    assert task["status"] == "DRAFT"
    assert db_client.get(f"/api/v1/rooms/{room['id']}/tasks", headers=student_headers).json() == []
    assert db_client.post(
        f"/api/v1/rooms/{room['id']}/tasks",
        json={"title": "Unauthorized"},
        headers=student_headers,
    ).status_code == 403

    assert db_client.post(f"/api/v1/tasks/{task['id']}/publish", headers=owner_headers).status_code == 200
    visible = db_client.get(f"/api/v1/rooms/{room['id']}/tasks", headers=student_headers)
    assert visible.status_code == 200 and visible.json()[0]["id"] == task["id"]
    assert db_client.patch(f"/api/v1/tasks/{task['id']}", json={"max_score": 30}, headers=student_headers).status_code == 403
    assert db_client.post(f"/api/v1/tasks/{task['id']}/close", headers=owner_headers).status_code == 200
    assert db_client.post(f"/api/v1/tasks/{task['id']}/publish", headers=owner_headers).status_code == 409


def test_teacher_member_can_manage_tasks_but_student_cannot(db_client):
    owner = _user(db_client, UserRole.STUDENT)
    teacher = _user(db_client, UserRole.TEACHER)
    student = _user(db_client, UserRole.STUDENT)
    room = _room(db_client, owner)
    _member(db_client, owner, teacher, room)
    _member(db_client, owner, student, room)
    response = db_client.post(
        f"/api/v1/rooms/{room['id']}/tasks",
        json={"title": "Teacher managed"},
        headers=_headers(db_client, teacher),
    )
    assert response.status_code == 201, response.text
    assert db_client.post(
        f"/api/v1/tasks/{response.json()['id']}/publish", headers=_headers(db_client, student)
    ).status_code == 403


def test_task_update_rejects_null_non_nullable_fields_and_naive_dates(db_client):
    owner = _user(db_client, UserRole.TEACHER)
    room = _room(db_client, owner)
    created = db_client.post(
        f"/api/v1/rooms/{room['id']}/tasks",
        json={"title": "Validation task"},
        headers=_headers(db_client, owner),
    )
    task_id = created.json()["id"]
    headers = _headers(db_client, owner)
    assert db_client.patch(f"/api/v1/tasks/{task_id}", json={"max_score": None}, headers=headers).status_code == 409
    assert db_client.patch(f"/api/v1/tasks/{task_id}", json={"difficulty": None}, headers=headers).status_code == 409
    assert db_client.patch(f"/api/v1/tasks/{task_id}", json={"due_at": "2030-01-01T00:00:00"}, headers=headers).status_code == 422
