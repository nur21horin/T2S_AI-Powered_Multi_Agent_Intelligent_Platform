from uuid import uuid4

from app.core.enums import UserRole
from tests.api.test_hackathons import _create_open_hackathon
from tests.api.test_profiles_rooms_step4 import _headers, _user


def _active_project(client, owner):
    created = client.post(
        "/api/v1/projects",
        json={"title": f"Submission project {uuid4().hex[:8]}", "visibility": "PRIVATE"},
        headers=_headers(client, owner),
    )
    assert created.status_code == 201, created.text
    project = created.json()
    activated = client.patch(
        f"/api/v1/projects/{project['id']}",
        json={"status": "ACTIVE"},
        headers=_headers(client, owner),
    )
    assert activated.status_code == 200, activated.text
    return project


def _approve_individual_registration(client, hackathon, organizer, participant):
    registration = client.post(
        f"/api/v1/hackathons/{hackathon['id']}/registrations/individual",
        headers=_headers(client, participant),
    )
    assert registration.status_code == 201, registration.text
    approved = client.post(
        f"/api/v1/hackathon-registrations/{registration.json()['id']}/approve",
        headers=_headers(client, organizer),
    )
    assert approved.status_code == 200, approved.text


def test_owner_can_create_finalize_read_and_withdraw_submission(db_client):
    client = db_client
    organizer = _user(client, UserRole.TEACHER)
    participant = _user(client, UserRole.STUDENT)
    hackathon = _create_open_hackathon(client, organizer, participation_mode="INDIVIDUAL")
    project = _active_project(client, participant)
    _approve_individual_registration(client, hackathon, organizer, participant)

    created = client.post(
        f"/api/v1/hackathons/{hackathon['id']}/submissions",
        json={"project_id": project["id"], "repository_url": "https://github.com/example/project"},
        headers=_headers(client, participant),
    )
    assert created.status_code == 201, created.text
    submission_id = created.json()["id"]
    assert created.json()["status"] == "DRAFT"
    finalized = client.post(f"/api/v1/hackathon-submissions/{submission_id}/finalize", headers=_headers(client, participant))
    assert finalized.status_code == 200, finalized.text
    assert finalized.json()["status"] == "SUBMITTED"
    assert client.get(f"/api/v1/hackathon-submissions/{submission_id}", headers=_headers(client, participant)).status_code == 200
    withdrawn = client.post(f"/api/v1/hackathon-submissions/{submission_id}/withdraw", headers=_headers(client, participant))
    assert withdrawn.status_code == 200
    assert withdrawn.json()["status"] == "WITHDRAWN"


def test_submission_requires_approved_registration_and_duplicate_is_rejected(db_client):
    client = db_client
    organizer = _user(client, UserRole.TEACHER)
    participant = _user(client, UserRole.STUDENT)
    hackathon = _create_open_hackathon(client, organizer, participation_mode="INDIVIDUAL")
    project = _active_project(client, participant)
    blocked = client.post(
        f"/api/v1/hackathons/{hackathon['id']}/submissions",
        json={"project_id": project["id"]},
        headers=_headers(client, participant),
    )
    assert blocked.status_code == 403
    _approve_individual_registration(client, hackathon, organizer, participant)
    first = client.post(
        f"/api/v1/hackathons/{hackathon['id']}/submissions",
        json={"project_id": project["id"]},
        headers=_headers(client, participant),
    )
    assert first.status_code == 201, first.text
    duplicate = client.post(
        f"/api/v1/hackathons/{hackathon['id']}/submissions",
        json={"project_id": project["id"]},
        headers=_headers(client, participant),
    )
    assert duplicate.status_code == 409


def test_organizer_can_list_but_unrelated_user_cannot_read_submission(db_client):
    client = db_client
    organizer = _user(client, UserRole.TEACHER)
    participant = _user(client, UserRole.STUDENT)
    unrelated = _user(client, UserRole.STUDENT)
    hackathon = _create_open_hackathon(client, organizer, participation_mode="INDIVIDUAL")
    project = _active_project(client, participant)
    _approve_individual_registration(client, hackathon, organizer, participant)
    created = client.post(
        f"/api/v1/hackathons/{hackathon['id']}/submissions",
        json={"project_id": project["id"]},
        headers=_headers(client, participant),
    )
    assert created.status_code == 201, created.text
    submission_id = created.json()["id"]
    assert client.get(f"/api/v1/hackathons/{hackathon['id']}/submissions", headers=_headers(client, organizer)).status_code == 200
    assert client.get(f"/api/v1/hackathon-submissions/{submission_id}", headers=_headers(client, unrelated)).status_code == 404
