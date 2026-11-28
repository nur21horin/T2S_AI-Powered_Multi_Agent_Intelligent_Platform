from uuid import uuid4

import pytest

from app.api.deps import get_ai_tools_service, get_current_user
from app.core.enums import UserRole
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.services.ai_tools_service import AIToolsService
from tests.api.test_profiles_rooms_step4 import _headers, _user


def _bound_tool(client, actor):
    db = client.app.state.session_factory()
    authenticated_actor = db.get(User, actor.id)
    return db, get_ai_tools_service(db=db, user=authenticated_actor)


def _room(client, owner, visibility):
    response = client.post(
        "/api/v1/rooms",
        json={"name": f"AI tool {visibility} {uuid4().hex}", "visibility": visibility},
        headers=_headers(client, owner),
    )
    assert response.status_code == 201, response.text
    return response.json()


def _join_room(client, owner, member, room):
    request = client.post(f"/api/v1/rooms/{room['id']}/join-requests", headers=_headers(client, member))
    assert request.status_code == 201, request.text
    approved = client.post(
        f"/api/v1/rooms/{room['id']}/join-requests/{request.json()['id']}/approve",
        headers=_headers(client, owner),
    )
    assert approved.status_code == 200, approved.text


def _published_task(client, owner, room, title):
    created = client.post(f"/api/v1/rooms/{room['id']}/tasks", json={"title": title}, headers=_headers(client, owner))
    assert created.status_code == 201, created.text
    published = client.post(f"/api/v1/tasks/{created.json()['id']}/publish", headers=_headers(client, owner))
    assert published.status_code == 200, published.text
    return created.json()


def test_candidate_discovery_defaults_private_and_requires_explicit_opt_in(db_client):
    client = db_client
    candidate, searcher = _user(client, UserRole.STUDENT), _user(client, UserRole.STUDENT)
    candidate_headers = _headers(client, candidate)
    profile = client.put("/api/v1/profiles/me", json={"department": "Computing"}, headers=candidate_headers)
    assert profile.status_code == 200 and profile.json()["skills_discoverable"] is False
    assert client.put("/api/v1/profiles/me/skills", json={"names": ["PrivateSkill"]}, headers=candidate_headers).status_code == 200

    db, tool = _bound_tool(client, searcher)
    try:
        assert tool.search_student_profiles({"skills": ["PrivateSkill"]})["data"] == []
        assert tool.search_student_profiles({"query": "PrivateSkill"})["data"] == []
    finally:
        db.close()

    opt_in = client.put("/api/v1/profiles/me", json={"skills_discoverable": True}, headers=candidate_headers)
    assert opt_in.status_code == 200 and opt_in.json()["skills_discoverable"] is True
    public_profile = client.get(f"/api/v1/profiles/{candidate.id}", headers=_headers(client, searcher))
    assert public_profile.status_code == 200
    assert public_profile.json().get("skills_discoverable") is not True

    db, tool = _bound_tool(client, searcher)
    try:
        results = tool.search_student_profiles({"skills": ["PrivateSkill"]})["data"]
        assert [item["user_id"] for item in results] == [str(candidate.id)]
        assert results[0]["skills"] == ["PrivateSkill"]
        assert "email" not in results[0] and "bio" not in results[0]
    finally:
        db.close()


def test_assigned_tasks_requires_membership_in_public_and_private_rooms(db_client):
    client = db_client
    owner = _user(client, UserRole.TEACHER)
    member, nonmember = _user(client, UserRole.STUDENT), _user(client, UserRole.STUDENT)
    public_room = _room(client, owner, "PUBLIC")
    private_room = _room(client, owner, "PRIVATE")
    _join_room(client, owner, member, private_room)
    public_task = _published_task(client, owner, public_room, "Public room task")
    private_task = _published_task(client, owner, private_room, "Private room task")

    db, tool = _bound_tool(client, nonmember)
    try:
        # Public discovery remains available through the separate tool.
        found = tool.get_available_tasks({"room_id": public_room["id"]})["data"]
        assert [item["id"] for item in found] == [public_task["id"]]
        with pytest.raises(NotFoundError):
            tool.get_assigned_tasks({"room_id": public_room["id"]})
        with pytest.raises(NotFoundError):
            tool.get_assigned_tasks({"room_id": private_room["id"]})
        with pytest.raises(NotFoundError):
            tool.get_available_tasks({"room_id": private_room["id"]})
    finally:
        db.close()

    db, tool = _bound_tool(client, member)
    try:
        assigned = tool.get_assigned_tasks({"room_id": private_room["id"]})["data"]
        assert [item["id"] for item in assigned] == [private_task["id"]]
    finally:
        db.close()


def test_private_project_requirements_are_hidden_from_nonmembers(db_client):
    client = db_client
    owner, outsider = _user(client, UserRole.STUDENT), _user(client, UserRole.STUDENT)
    project = client.post(
        "/api/v1/projects", json={"title": "Private AI project", "objectives": "Only owner objective"},
        headers=_headers(client, owner),
    )
    assert project.status_code == 201, project.text

    db, tool = _bound_tool(client, outsider)
    try:
        response = tool.execute_tool("get_project_requirements", {"project_id": project.json()["id"]})
        assert response["success"] is False and response["error"]["code"] == "not_found"
        assert "Only owner objective" not in str(response)
    finally:
        db.close()


def test_authenticated_dependency_binds_only_current_request_user(db_client):
    client = db_client
    actor = _user(client, UserRole.STUDENT)
    db, tool = _bound_tool(client, actor)
    try:
        assert isinstance(tool, AIToolsService)
        assert tool.actor.id == actor.id
        assert tool.db is db
    finally:
        db.close()


def test_tool_service_dependency_requires_trusted_current_user():
    from fastapi import params
    from inspect import signature

    default = signature(get_ai_tools_service).parameters["user"].default
    assert isinstance(default, params.Depends)
    assert default.dependency is get_current_user
