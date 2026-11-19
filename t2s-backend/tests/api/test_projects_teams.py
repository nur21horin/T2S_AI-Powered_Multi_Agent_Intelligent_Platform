from tests.api.test_profiles_rooms_step4 import _headers, _user
from app.core.enums import UserRole


def test_team_owner_membership_and_private_visibility(db_client):
    client = db_client
    owner = _user(client, UserRole.STUDENT)
    outsider = _user(client, UserRole.STUDENT)
    response = client.post("/api/v1/teams", json={"name": "Private Team", "visibility": "PRIVATE"}, headers=_headers(client, owner))
    assert response.status_code == 201
    team_id = response.json()["id"]
    assert client.get(f"/api/v1/teams/{team_id}", headers=_headers(client, outsider)).status_code == 404
    members = client.get(f"/api/v1/teams/{team_id}/members", headers=_headers(client, owner))
    assert members.status_code == 200
    assert members.json()[0]["role"] == "OWNER"


def test_join_request_approval_is_atomic_and_duplicate_pending_is_rejected(db_client):
    client = db_client
    owner = _user(client, UserRole.STUDENT)
    applicant = _user(client, UserRole.STUDENT)
    team = client.post("/api/v1/teams", json={"name": "Join Team", "visibility": "PUBLIC"}, headers=_headers(client, owner)).json()
    headers = _headers(client, applicant)
    first = client.post(f"/api/v1/teams/{team['id']}/join-requests", headers=headers)
    assert first.status_code == 201
    assert client.post(f"/api/v1/teams/{team['id']}/join-requests", headers=headers).status_code == 409
    request_id = first.json()["id"]
    approved = client.post(f"/api/v1/teams/{team['id']}/join-requests/{request_id}/approve", headers=_headers(client, owner))
    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"
    members = client.get(f"/api/v1/teams/{team['id']}/members", headers=headers)
    assert members.status_code == 200
    assert any(row["user_id"] == str(applicant.id) for row in members.json())


def test_project_cannot_attach_private_team_without_membership(db_client):
    client = db_client
    owner = _user(client, UserRole.STUDENT)
    other = _user(client, UserRole.STUDENT)
    team = client.post("/api/v1/teams", json={"name": "Attach Team", "visibility": "PRIVATE"}, headers=_headers(client, other)).json()
    project = client.post("/api/v1/projects", json={"title": "Project", "visibility": "PRIVATE"}, headers=_headers(client, owner)).json()
    assert client.put(f"/api/v1/projects/{project['id']}/team/{team['id']}", headers=_headers(client, owner)).status_code == 403
