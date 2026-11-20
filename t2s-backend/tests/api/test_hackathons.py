from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.enums import UserRole
from tests.api.test_profiles_rooms_step4 import _headers, _user


def _window(*, registration_start=None, registration_end=None, start=None, end=None):
    now = datetime.now(UTC)
    return {
        "registration_start_at": (registration_start or now - timedelta(days=1)).isoformat(),
        "registration_end_at": (registration_end or now + timedelta(days=1)).isoformat(),
        "start_at": (start or now + timedelta(days=2)).isoformat(),
        "end_at": (end or now + timedelta(days=3)).isoformat(),
    }


def _create_open_hackathon(client, organizer, **overrides):
    payload = {"title": f"Test Hackathon {uuid4().hex[:8]}", **_window(), **overrides}
    created = client.post("/api/v1/hackathons", json=payload, headers=_headers(client, organizer))
    assert created.status_code == 201, created.text
    hackathon = created.json()
    assert client.post(f"/api/v1/hackathons/{hackathon['id']}/publish", headers=_headers(client, organizer)).status_code == 200
    opened = client.post(f"/api/v1/hackathons/{hackathon['id']}/open", headers=_headers(client, organizer))
    assert opened.status_code == 200, opened.text
    return hackathon


def test_hackathon_creation_requires_organizer_and_valid_dates(db_client):
    client = db_client
    student = _user(client, UserRole.STUDENT)
    invalid = {"title": "Invalid", **_window(start=datetime.now(UTC) + timedelta(days=1), end=datetime.now(UTC))}
    assert client.post("/api/v1/hackathons", json=invalid, headers=_headers(client, student)).status_code == 422
    assert client.post("/api/v1/hackathons", json={"title": "Valid", **_window()}, headers=_headers(client, student)).status_code == 403


def test_hackathon_lifecycle_rejects_invalid_transition(db_client):
    client = db_client
    organizer = _user(client, UserRole.TEACHER)
    unauthorized = _user(client, UserRole.STUDENT)
    created_response = client.post("/api/v1/hackathons", json={"title": f"Lifecycle {uuid4().hex[:8]}", **_window()}, headers=_headers(client, organizer))
    assert created_response.status_code == 201, created_response.text
    created = created_response.json()
    hackathon_id = created["id"]
    assert client.post(f"/api/v1/hackathons/{hackathon_id}/publish", headers=_headers(client, unauthorized)).status_code == 403
    assert client.post(f"/api/v1/hackathons/{hackathon_id}/complete", headers=_headers(client, organizer)).status_code == 409
    assert client.post(f"/api/v1/hackathons/{hackathon_id}/archive", headers=_headers(client, organizer)).status_code == 409
    assert client.post(f"/api/v1/hackathons/{hackathon_id}/publish", headers=_headers(client, organizer)).status_code == 200
    assert client.post(f"/api/v1/hackathons/{hackathon_id}/publish", headers=_headers(client, organizer)).status_code == 409
    assert client.post(f"/api/v1/hackathons/{hackathon_id}/close", headers=_headers(client, organizer)).status_code == 409
    assert client.post(f"/api/v1/hackathons/{hackathon_id}/open", headers=_headers(client, organizer)).status_code == 200
    assert client.post(f"/api/v1/hackathons/{hackathon_id}/close", headers=_headers(client, organizer)).status_code == 200
    assert client.post(f"/api/v1/hackathons/{hackathon_id}/archive", headers=_headers(client, organizer)).status_code == 409


def test_individual_registration_duplicate_capacity_and_cancellation(db_client):
    client = db_client
    organizer = _user(client, UserRole.TEACHER)
    participant = _user(client, UserRole.STUDENT)
    hackathon = _create_open_hackathon(client, organizer, participant_limit=1, participation_mode="INDIVIDUAL")
    headers = _headers(client, participant)
    first = client.post(f"/api/v1/hackathons/{hackathon['id']}/registrations/individual", headers=headers)
    assert first.status_code == 201
    assert client.post(f"/api/v1/hackathons/{hackathon['id']}/registrations/individual", headers=headers).status_code == 409
    other = _user(client, UserRole.STUDENT)
    assert client.post(f"/api/v1/hackathons/{hackathon['id']}/registrations/individual", headers=_headers(client, other)).status_code == 409
    cancelled = client.post(f"/api/v1/hackathon-registrations/{first.json()['id']}/cancel", headers=headers)
    assert cancelled.status_code == 200
    replacement = client.post(f"/api/v1/hackathons/{hackathon['id']}/registrations/individual", headers=_headers(client, other))
    assert replacement.status_code == 201


def test_team_registration_requires_manager_and_preserves_member_snapshot(db_client):
    client = db_client
    organizer = _user(client, UserRole.TEACHER)
    owner = _user(client, UserRole.STUDENT)
    member = _user(client, UserRole.STUDENT)
    team = client.post("/api/v1/teams", json={"name": "Hack Team", "visibility": "PUBLIC"}, headers=_headers(client, owner)).json()
    request = client.post(f"/api/v1/teams/{team['id']}/join-requests", headers=_headers(client, member)).json()
    assert client.post(f"/api/v1/teams/{team['id']}/join-requests/{request['id']}/approve", headers=_headers(client, owner)).status_code == 200
    hackathon = _create_open_hackathon(client, organizer, participation_mode="TEAM", team_size_min=2, team_size_max=2)
    forbidden = client.post(f"/api/v1/hackathons/{hackathon['id']}/registrations/team", json={"team_id": team["id"]}, headers=_headers(client, member))
    assert forbidden.status_code == 403
    registered = client.post(f"/api/v1/hackathons/{hackathon['id']}/registrations/team", json={"team_id": team["id"]}, headers=_headers(client, owner))
    assert registered.status_code == 201, registered.text
    registration_id = registered.json()["id"]
    assert client.post(f"/api/v1/hackathon-registrations/{registration_id}/cancel", headers=_headers(client, member)).status_code == 403
    assert client.delete(f"/api/v1/teams/{team['id']}/membership", headers=_headers(client, member)).status_code == 204
    detail = client.get(f"/api/v1/hackathon-registrations/{registration_id}", headers=_headers(client, member))
    assert detail.status_code == 200
    snapshot = {row["user_id"]: row["display_name_snapshot"] for row in detail.json()["members"]}
    assert str(member.id) in snapshot


def test_team_members_reserve_individual_capacity(db_client):
    client = db_client
    organizer = _user(client, UserRole.TEACHER)
    owner = _user(client, UserRole.STUDENT)
    member = _user(client, UserRole.STUDENT)
    other = _user(client, UserRole.STUDENT)
    team = client.post("/api/v1/teams", json={"name": "Capacity Team", "visibility": "PUBLIC"}, headers=_headers(client, owner)).json()
    request = client.post(f"/api/v1/teams/{team['id']}/join-requests", headers=_headers(client, member)).json()
    assert client.post(f"/api/v1/teams/{team['id']}/join-requests/{request['id']}/approve", headers=_headers(client, owner)).status_code == 200
    hackathon = _create_open_hackathon(client, organizer, participant_limit=2, participation_mode="BOTH", team_size_min=2, team_size_max=2)
    registered = client.post(f"/api/v1/hackathons/{hackathon['id']}/registrations/team", json={"team_id": team["id"]}, headers=_headers(client, owner))
    assert registered.status_code == 201, registered.text
    assert client.post(f"/api/v1/hackathons/{hackathon['id']}/registrations/individual", headers=_headers(client, other)).status_code == 409


def test_rejected_registration_does_not_grant_private_access(db_client):
    client = db_client
    organizer = _user(client, UserRole.TEACHER)
    participant = _user(client, UserRole.STUDENT)
    hackathon = _create_open_hackathon(client, organizer, visibility="PRIVATE", participation_mode="INDIVIDUAL")
    registration = client.post(f"/api/v1/hackathons/{hackathon['id']}/registrations/individual", headers=_headers(client, participant))
    assert registration.status_code == 201, registration.text
    registration_id = registration.json()["id"]
    assert client.post(f"/api/v1/hackathon-registrations/{registration_id}/reject", headers=_headers(client, organizer)).status_code == 200
    assert client.get(f"/api/v1/hackathons/{hackathon['id']}", headers=_headers(client, participant)).status_code == 404
    assert client.get(f"/api/v1/hackathons/{hackathon['id']}/registrations/me", headers=_headers(client, participant)).status_code == 404
    assert client.get(f"/api/v1/hackathon-registrations/{registration_id}", headers=_headers(client, participant)).status_code == 404


def _create_two_person_team(client, owner, member, name):
    team = client.post("/api/v1/teams", json={"name": name, "visibility": "PUBLIC"}, headers=_headers(client, owner)).json()
    request = client.post(f"/api/v1/teams/{team['id']}/join-requests", headers=_headers(client, member)).json()
    assert client.post(f"/api/v1/teams/{team['id']}/join-requests/{request['id']}/approve", headers=_headers(client, owner)).status_code == 200
    return team


def test_team_larger_than_total_capacity_is_rejected(db_client):
    client = db_client
    organizer = _user(client, UserRole.TEACHER)
    owner = _user(client, UserRole.STUDENT)
    member = _user(client, UserRole.STUDENT)
    team = _create_two_person_team(client, owner, member, "Oversized Capacity Team")
    hackathon = _create_open_hackathon(client, organizer, participant_limit=1, participation_mode="TEAM", team_size_min=2, team_size_max=2)
    response = client.post(f"/api/v1/hackathons/{hackathon['id']}/registrations/team", json={"team_id": team["id"]}, headers=_headers(client, owner))
    assert response.status_code == 409


def test_team_larger_than_remaining_capacity_is_rejected(db_client):
    client = db_client
    organizer = _user(client, UserRole.TEACHER)
    participant = _user(client, UserRole.STUDENT)
    owner = _user(client, UserRole.STUDENT)
    member = _user(client, UserRole.STUDENT)
    team = _create_two_person_team(client, owner, member, "Remaining Capacity Team")
    hackathon = _create_open_hackathon(client, organizer, participant_limit=2, participation_mode="BOTH", team_size_min=2, team_size_max=2)
    assert client.post(f"/api/v1/hackathons/{hackathon['id']}/registrations/individual", headers=_headers(client, participant)).status_code == 201
    response = client.post(f"/api/v1/hackathons/{hackathon['id']}/registrations/team", json={"team_id": team["id"]}, headers=_headers(client, owner))
    assert response.status_code == 409


def test_already_counted_team_member_is_not_counted_twice(db_client):
    client = db_client
    organizer = _user(client, UserRole.TEACHER)
    owner = _user(client, UserRole.STUDENT)
    member = _user(client, UserRole.STUDENT)
    team = _create_two_person_team(client, owner, member, "Duplicate Participant Team")
    hackathon = _create_open_hackathon(client, organizer, participant_limit=2, participation_mode="BOTH", team_size_min=2, team_size_max=2)
    assert client.post(f"/api/v1/hackathons/{hackathon['id']}/registrations/individual", headers=_headers(client, owner)).status_code == 201
    response = client.post(f"/api/v1/hackathons/{hackathon['id']}/registrations/team", json={"team_id": team["id"]}, headers=_headers(client, owner))
    assert response.status_code == 201, response.text


def test_rejected_registration_releases_capacity(db_client):
    client = db_client
    organizer = _user(client, UserRole.TEACHER)
    participant = _user(client, UserRole.STUDENT)
    other = _user(client, UserRole.STUDENT)
    hackathon = _create_open_hackathon(client, organizer, participant_limit=1, participation_mode="INDIVIDUAL")
    registration = client.post(f"/api/v1/hackathons/{hackathon['id']}/registrations/individual", headers=_headers(client, participant))
    assert registration.status_code == 201
    assert client.post(f"/api/v1/hackathon-registrations/{registration.json()['id']}/reject", headers=_headers(client, organizer)).status_code == 200
    replacement = client.post(f"/api/v1/hackathons/{hackathon['id']}/registrations/individual", headers=_headers(client, other))
    assert replacement.status_code == 201, replacement.text


def test_unlimited_capacity_allows_team_registration(db_client):
    client = db_client
    organizer = _user(client, UserRole.TEACHER)
    owner = _user(client, UserRole.STUDENT)
    member = _user(client, UserRole.STUDENT)
    team = _create_two_person_team(client, owner, member, "Unlimited Capacity Team")
    hackathon = _create_open_hackathon(client, organizer, participation_mode="TEAM", team_size_min=2, team_size_max=2)
    response = client.post(f"/api/v1/hackathons/{hackathon['id']}/registrations/team", json={"team_id": team["id"]}, headers=_headers(client, owner))
    assert response.status_code == 201, response.text


def test_registration_me_endpoints_show_only_active_own_registrations(db_client):
    client = db_client
    organizer = _user(client, UserRole.TEACHER)
    participant = _user(client, UserRole.STUDENT)
    other = _user(client, UserRole.STUDENT)
    headers = _headers(client, participant)
    other_headers = _headers(client, other)
    hackathon = _create_open_hackathon(client, organizer, participation_mode="INDIVIDUAL")
    pending = client.post(f"/api/v1/hackathons/{hackathon['id']}/registrations/individual", headers=headers)
    assert pending.status_code == 201
    pending_id = pending.json()["id"]
    other_registration = client.post(f"/api/v1/hackathons/{hackathon['id']}/registrations/individual", headers=other_headers)
    assert other_registration.status_code == 201
    other_id = other_registration.json()["id"]
    for url in (f"/api/v1/hackathons/{hackathon['id']}/registrations/me", "/api/v1/hackathon-registrations/me"):
        ids = {row["id"] for row in client.get(url, headers=headers).json()}
        assert pending_id in ids
        assert other_id not in ids
    assert client.post(f"/api/v1/hackathon-registrations/{pending_id}/approve", headers=_headers(client, organizer)).status_code == 200
    for url in (f"/api/v1/hackathons/{hackathon['id']}/registrations/me", "/api/v1/hackathon-registrations/me"):
        assert pending_id in {row["id"] for row in client.get(url, headers=headers).json()}
    assert client.post(f"/api/v1/hackathon-registrations/{pending_id}/cancel", headers=headers).status_code == 200
    for url in (f"/api/v1/hackathons/{hackathon['id']}/registrations/me", "/api/v1/hackathon-registrations/me"):
        assert pending_id not in {row["id"] for row in client.get(url, headers=headers).json()}
    rejected_hackathon = _create_open_hackathon(client, organizer, participation_mode="INDIVIDUAL")
    rejected = client.post(f"/api/v1/hackathons/{rejected_hackathon['id']}/registrations/individual", headers=headers)
    assert rejected.status_code == 201
    rejected_id = rejected.json()["id"]
    assert client.post(f"/api/v1/hackathon-registrations/{rejected_id}/reject", headers=_headers(client, organizer)).status_code == 200
    assert rejected_id not in {row["id"] for row in client.get("/api/v1/hackathon-registrations/me", headers=headers).json()}
