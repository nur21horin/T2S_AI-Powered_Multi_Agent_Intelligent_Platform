from uuid import uuid4

from app.core.enums import UserRole
from tests.api.test_profiles_rooms_step4 import _headers, _user
from tests.api.test_tasks import _member, _room


def _published_task(client, owner, room, **overrides):
    data = {"title": f"Submission task {uuid4().hex}", **overrides}
    response = client.post(f"/api/v1/rooms/{room['id']}/tasks", json=data, headers=_headers(client, owner))
    assert response.status_code == 201, response.text
    task = response.json()
    published = client.post(f"/api/v1/tasks/{task['id']}/publish", headers=_headers(client, owner))
    assert published.status_code == 200, published.text
    return task


def test_submission_requires_membership_and_isolated_ownership(db_client):
    owner = _user(db_client, UserRole.TEACHER)
    student = _user(db_client, UserRole.STUDENT)
    other = _user(db_client, UserRole.STUDENT)
    room = _room(db_client, owner)
    task = _published_task(db_client, owner, room)
    student_headers, other_headers = _headers(db_client, student), _headers(db_client, other)

    denied = db_client.post(f"/api/v1/tasks/{task['id']}/submissions", json={"content": "answer"}, headers=student_headers)
    assert denied.status_code == 403
    _member(db_client, owner, student, room)
    submission = db_client.post(f"/api/v1/tasks/{task['id']}/submissions", json={"content": "answer"}, headers=student_headers)
    assert submission.status_code == 201, submission.text
    submission_id = submission.json()["id"]
    assert db_client.post(f"/api/v1/tasks/{task['id']}/submissions", json={"content": "second"}, headers=student_headers).status_code == 409
    assert db_client.get(f"/api/v1/submissions/{submission_id}", headers=other_headers).status_code == 403
    assert db_client.get(f"/api/v1/submissions/{submission_id}", headers=_headers(db_client, owner)).status_code == 200


def test_resubmission_limit_and_deadline_are_enforced(db_client):
    owner = _user(db_client, UserRole.TEACHER)
    student = _user(db_client, UserRole.STUDENT)
    room = _room(db_client, owner)
    _member(db_client, owner, student, room)
    task = _published_task(db_client, owner, room, allow_resubmission=True, max_attempts=2)
    headers = _headers(db_client, student)
    first = db_client.post(f"/api/v1/tasks/{task['id']}/submissions", json={"content": "one"}, headers=headers)
    second = db_client.post(f"/api/v1/tasks/{task['id']}/submissions", json={"content": "two"}, headers=headers)
    assert first.status_code == 201 and second.status_code == 201
    assert second.json()["attempt_number"] == 2
    assert db_client.post(f"/api/v1/tasks/{task['id']}/submissions", json={"content": "three"}, headers=headers).status_code == 409


def test_evaluation_validates_reviewer_identity_and_score(db_client):
    owner = _user(db_client, UserRole.TEACHER)
    student = _user(db_client, UserRole.STUDENT)
    other = _user(db_client, UserRole.STUDENT)
    room = _room(db_client, owner)
    _member(db_client, owner, student, room)
    task = _published_task(db_client, owner, room, max_score=10)
    submission = db_client.post(f"/api/v1/tasks/{task['id']}/submissions", json={"content": "answer"}, headers=_headers(db_client, student)).json()
    path = f"/api/v1/submissions/{submission['id']}/evaluation"
    assert db_client.put(path, json={"score": 11}, headers=_headers(db_client, owner)).status_code == 409
    assert db_client.put(path, json={"score": 10}, headers=_headers(db_client, student)).status_code == 403
    evaluation = db_client.put(path, json={"score": 8, "feedback": "Good"}, headers=_headers(db_client, owner))
    assert evaluation.status_code == 200, evaluation.text
    assert db_client.get(path, headers=_headers(db_client, student)).json()["score"] == 8
    assert db_client.get(path, headers=_headers(db_client, other)).status_code == 403


def test_blank_submission_content_is_rejected(db_client):
    owner = _user(db_client, UserRole.TEACHER)
    student = _user(db_client, UserRole.STUDENT)
    room = _room(db_client, owner)
    _member(db_client, owner, student, room)
    task = _published_task(db_client, owner, room)
    response = db_client.post(
        f"/api/v1/tasks/{task['id']}/submissions",
        json={"content": "   "},
        headers=_headers(db_client, student),
    )
    assert response.status_code == 422
