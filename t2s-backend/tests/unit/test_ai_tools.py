from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from AI.tools.platform import PLATFORM_TOOL_NAMES, PlatformToolExecutor
from app.core.enums import OpportunityType, TaskDifficulty, TaskStatus, UserRole
from app.core.exceptions import ForbiddenError, NotFoundError
from app.schemas.ai_tools import CandidateSearchInput, ProfileInput, ProjectInput
from app.services.ai_tools_service import AIToolsService


def _user(role=UserRole.STUDENT):
    return SimpleNamespace(id=uuid4(), role=role)


def test_candidate_search_requires_a_filter_and_is_opt_in_student_only():
    with pytest.raises(ValidationError):
        CandidateSearchInput()
    with pytest.raises(ForbiddenError):
        AIToolsService(MagicMock(), _user(UserRole.TEACHER)).search_student_profiles({"skills": ["Python"]})


def test_candidate_query_is_opt_in_paginated_and_uses_batched_skills():
    actor, candidate_id = _user(), uuid4()
    db = MagicMock()
    page_rows, skill_rows = MagicMock(), MagicMock()
    page_rows.all.return_value = [(candidate_id, "Computing")]
    skill_rows.all.return_value = [(candidate_id, "Python"), (candidate_id, "FastAPI")]
    db.execute.side_effect = [page_rows, skill_rows]

    result = AIToolsService(db, actor).search_student_profiles({"skills": ["Python"], "page": 2, "limit": 1})

    assert result["data"] == [{
        "user_id": str(candidate_id), "department": "Computing",
        "skills": ["Python"], "matching_skills": ["Python"],
    }]
    statement = db.execute.call_args_list[0].args[0]
    assert "skills_discoverable" in str(statement)
    assert "LIMIT" in str(statement) and "OFFSET" in str(statement)
    assert actor.id in statement.compile().params.values()
    assert len(db.execute.call_args_list) == 2


def test_profile_tool_is_bound_to_authenticated_actor_and_rejects_identity_args():
    actor, other_id = _user(), uuid4()
    with pytest.raises(ValidationError):
        ProfileInput.model_validate({"user_id": str(other_id)})
    with pytest.raises(ValidationError):
        AIToolsService(MagicMock(), actor).get_student_profile({"user_id": str(other_id)})
    db = MagicMock()
    profile = SimpleNamespace(__table__=SimpleNamespace(columns=[]))
    with patch("app.services.ai_tools_service.ProfileService") as profile_service:
        profile_service.return_value.get.return_value = (profile, "student")
        result = AIToolsService(db, actor).get_student_profile()
    assert result["data"]["user_id"] == str(actor.id)
    profile_service.return_value.get.assert_called_once_with(actor)


def test_progress_tool_rejects_cross_user_identity_argument():
    with pytest.raises(ValidationError):
        AIToolsService(MagicMock(), _user()).get_student_progress({"user_id": str(uuid4())})


def test_skills_and_progress_are_scoped_to_actor():
    actor = _user()
    db = MagicMock()
    db.scalars.side_effect = [iter(["Python"]), iter(["Robotics"])]
    skills = AIToolsService(db, actor).get_student_skills()
    assert skills["data"] == {"skills": ["Python"], "interests": ["Robotics"]}
    query = db.scalars.call_args_list[0].args[0]
    assert actor.id in query.compile().params.values()

    progress = SimpleNamespace(model_dump=lambda: {
        "user_id": actor.id, "room_id": None, "total_tasks": 1, "completed_tasks": 0,
        "pending_tasks": 1, "awaiting_review": 0, "evaluated_tasks": 0,
        "average_score": None, "total_earned_score": 0, "total_possible_score": 100,
        "completion_percentage": 0,
    })
    with patch("app.services.ai_tools_service.ProgressService") as progress_service:
        progress_service.return_value.personal.return_value = progress
        result = AIToolsService(MagicMock(), actor).get_student_progress()
    assert result["data"]["user_id"] == str(actor.id)
    progress_service.return_value.personal.assert_called_once_with(actor)


def test_task_tool_uses_service_and_returns_published_tasks_only():
    actor, room_id = _user(), uuid4()
    published = SimpleNamespace(id=uuid4(), room_id=room_id, title="Python project", description="Build it",
        difficulty=TaskDifficulty.BEGINNER, status=TaskStatus.PUBLISHED, starts_at=None, due_at=None)
    closed = SimpleNamespace(**{**published.__dict__, "id": uuid4(), "status": TaskStatus.CLOSED})
    tool = AIToolsService(MagicMock(), actor)
    with patch.object(tool, "_visible_room_ids", return_value=[room_id]), \
         patch("app.services.ai_tools_service.TaskService") as task_service:
        task_service.return_value.list_for_room.return_value = [published, closed]
        result = tool.get_available_tasks()
    assert [item["id"] for item in result["data"]] == [str(published.id)]
    task_service.return_value.list_for_room.assert_called_once_with(actor, room_id, limit=100)


def test_assigned_tasks_requires_membership_for_explicit_public_room():
    actor, room_id = _user(), uuid4()
    db = MagicMock()
    db.scalar.return_value = None
    with pytest.raises(NotFoundError):
        AIToolsService(db, actor).get_assigned_tasks({"room_id": room_id})
    statement = db.scalar.call_args.args[0]
    assert actor.id in statement.compile().params.values()


def test_task_discovery_bounds_room_fanout_at_query_level():
    actor = _user()
    db = MagicMock()
    db.scalars.return_value = [uuid4() for _ in range(20)]
    tool = AIToolsService(db, actor)
    with patch("app.services.ai_tools_service.TaskService") as task_service:
        task_service.return_value.list_for_room.return_value = []
        assert tool.get_available_tasks()["data"] == []
    query = db.scalars.call_args.args[0]
    assert query._limit_clause.value == tool.MAX_DISCOVERY_ROOMS
    assert task_service.return_value.list_for_room.call_count == tool.MAX_DISCOVERY_ROOMS


def test_private_project_authorization_is_delegated_to_project_service():
    actor, project_id = _user(), uuid4()
    with patch("app.services.ai_tools_service.ProjectService") as project_service:
        project_service.return_value.get.side_effect = NotFoundError("Project not found.")
        result = AIToolsService(MagicMock(), actor).execute_tool(
            "get_project_requirements", {"project_id": str(project_id)}
        )
    assert result["success"] is False
    assert result["error"]["code"] == "not_found"
    project_service.return_value.get.assert_called_once_with(actor, project_id)


def test_invalid_inputs_and_unknown_tools_have_safe_errors():
    service = AIToolsService(MagicMock(), _user())
    executor = PlatformToolExecutor(service)
    with pytest.raises(ValidationError):
        ProjectInput.model_validate({"project_id": "bad"})
    with pytest.raises(ValidationError):
        ProfileInput.model_validate({"user_id": str(uuid4())})
    assert executor.execute("delete_everything", {})["error"]["code"] == "unknown_tool"
    invalid = executor.execute("get_project_requirements", {"project_id": "bad"})
    assert invalid["error"]["code"] == "invalid_arguments"


def test_executor_rejects_invalid_wiring_and_derives_schema_from_backend_models():
    with pytest.raises(TypeError):
        PlatformToolExecutor(object())
    service = AIToolsService(MagicMock(), _user())
    executor = PlatformToolExecutor(service)
    definitions = {tool.name: tool for tool in executor.definitions}
    assert set(definitions) == set(service.TOOL_INPUT_MODELS) == set(PLATFORM_TOOL_NAMES)
    assert definitions["get_project_requirements"].arguments_schema == ProjectInput.model_json_schema()


def test_executor_errors_do_not_return_internal_exception_details():
    service = AIToolsService(MagicMock(), _user())
    with patch.object(service, "get_student_progress", side_effect=RuntimeError("SQL password=secret")):
        result = PlatformToolExecutor(service).execute("get_student_progress", {})
    assert result["success"] is False
    assert result["error"] == {"code": "internal_error", "message": "The tool request could not be completed."}
    assert "password" not in str(result) and "secret" not in str(result)


def test_empty_research_results_are_explained():
    with patch("app.services.ai_tools_service.OpportunityService") as opportunity_service:
        opportunity_service.return_value.list_public.return_value = []
        result = AIToolsService(MagicMock(), _user()).get_research_projects()
    assert result["data"] == []
    assert "No published research projects" in result["explanation"]


def test_opportunity_matching_does_not_claim_unverified_skills():
    actor = _user()
    opportunity = SimpleNamespace(id=uuid4(), title="AI internship", description="Python-oriented general role",
        opportunity_type=OpportunityType.INTERNSHIP, organization="Example Org", location=None,
        application_url=None, deadline=None)
    with patch("app.services.ai_tools_service.OpportunityService") as opportunity_service:
        opportunity_service.return_value.list_public.return_value = [opportunity]
        result = AIToolsService(MagicMock(), actor).search_matching_opportunities({"skills": ["Python"]})
    assert result["data"][0]["matching_skills"] == []
    assert "structured skill requirements" in result["explanation"]
