from app.core.enums import UserRole
from tests.api.test_profiles_rooms_step4 import _headers, _user
from tests.api.test_submissions_evaluations import _published_task
from tests.api.test_tasks import _member, _room


def test_progress_is_calculated_from_submissions_and_evaluations(db_client):
    owner = _user(db_client, UserRole.TEACHER)
    student = _user(db_client, UserRole.STUDENT)
    room = _room(db_client, owner)
    _member(db_client, owner, student, room)
    headers = _headers(db_client, student)
    assert db_client.get("/api/v1/progress/me", headers=headers).json()["total_tasks"] == 0
    task = _published_task(db_client, owner, room, max_score=20)
    pending = db_client.get(f"/api/v1/progress/me?room_id={room['id']}", headers=headers).json()
    assert pending["total_tasks"] == 1 and pending["pending_tasks"] == 1 and pending["completion_percentage"] == 0
    submission = db_client.post(f"/api/v1/tasks/{task['id']}/submissions", json={"content": "work"}, headers=headers).json()
    awaiting = db_client.get(f"/api/v1/progress/me?room_id={room['id']}", headers=headers).json()
    assert awaiting["awaiting_review"] == 1 and awaiting["completed_tasks"] == 0
    evaluated = db_client.put(f"/api/v1/submissions/{submission['id']}/evaluation", json={"score": 15}, headers=_headers(db_client, owner))
    assert evaluated.status_code == 200
    complete = db_client.get(f"/api/v1/progress/me?room_id={room['id']}", headers=headers).json()
    assert complete["completed_tasks"] == 1
    assert complete["total_earned_score"] == 15
    assert complete["completion_percentage"] == 100


def test_progress_for_another_student_requires_room_manager(db_client):
    owner = _user(db_client, UserRole.TEACHER)
    student = _user(db_client, UserRole.STUDENT)
    other = _user(db_client, UserRole.STUDENT)
    room = _room(db_client, owner)
    _member(db_client, owner, student, room)
    _member(db_client, owner, other, room)
    path = f"/api/v1/progress/rooms/{room['id']}/users/{other.id}"
    assert db_client.get(path, headers=_headers(db_client, student)).status_code == 403
    assert db_client.get(path, headers=_headers(db_client, owner)).status_code == 200
