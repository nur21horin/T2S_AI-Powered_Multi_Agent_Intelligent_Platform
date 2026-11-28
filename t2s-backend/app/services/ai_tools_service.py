from __future__ import annotations

import logging
from typing import Any, TypeVar
from uuid import UUID

from pydantic import BaseModel, ValidationError
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.enums import OpportunityType, RoomVisibility, TaskStatus, UserRole
from app.core.exceptions import AppException, ForbiddenError, NotFoundError
from app.models.opportunity import Opportunity
from app.models.profile import StudentProfile
from app.models.room import RoomMembership, TechnicalRoom
from app.models.skill import Interest, Skill, UserInterest, UserSkill
from app.models.task import Task
from app.models.user import User
from app.schemas.ai_tools import (
    CandidateData,
    CandidateSearchInput,
    AssignedTaskInput,
    OpportunityData,
    OpportunityListInput,
    OpportunityQueryInput,
    PageInput,
    ProfileInput,
    ProjectInput,
    ProjectRequirementsData,
    ProgressData,
    ResearchQueryInput,
    ResourceQueryInput,
    StudentProfileData,
    StudentSkillsData,
    TaskData,
    TaskQueryInput,
    TaskSearchInput,
    ToolResult,
)
from app.services.opportunity_service import OpportunityService
from app.services.profile_service import ProfileService
from app.services.progress_service import ProgressService
from app.services.project_service import ProjectService
from app.services.task_service import TaskService
from app.utils.pagination import Pagination

InputModel = TypeVar("InputModel", bound=BaseModel)
logger = logging.getLogger(__name__)


def _input(model: type[InputModel], value: InputModel | dict[str, Any] | None) -> InputModel:
    if value is None:
        return model()
    if isinstance(value, model):
        return value
    return model.model_validate(value)


def _page(value: PageInput) -> Pagination:
    return Pagination(page=value.page, limit=value.limit)


def _result(data: Any, explanation: str | None = None) -> dict[str, Any]:
    return ToolResult(data=data, explanation=explanation).model_dump(mode="json")


class AIToolsService:
    """Read-only, identity-scoped operations for application-controlled AI tools."""

    MAX_DISCOVERY_ROOMS = 20
    TOOL_INPUT_MODELS: dict[str, type[BaseModel]] = {
        "get_student_profile": ProfileInput,
        "get_student_skills": ProfileInput,
        "get_student_progress": ProfileInput,
        "get_available_tasks": TaskQueryInput,
        "get_assigned_tasks": AssignedTaskInput,
        "search_matching_tasks": TaskSearchInput,
        "search_student_profiles": CandidateSearchInput,
        "get_project_requirements": ProjectInput,
        "find_complementary_skills": CandidateSearchInput,
        "get_available_opportunities": OpportunityListInput,
        "search_matching_opportunities": OpportunityQueryInput,
        "search_research_opportunities": ResearchQueryInput,
        "get_research_projects": PageInput,
        "retrieve_knowledge_resources": ResourceQueryInput,
        "semantic_search_resources": ResourceQueryInput,
    }

    def __init__(self, db: Session, actor: User) -> None:
        self.db = db
        self.actor = actor

    def input_model_for(self, tool_name: str) -> type[BaseModel]:
        try:
            return self.TOOL_INPUT_MODELS[tool_name]
        except KeyError:
            raise ValueError("Unknown platform tool.") from None

    def execute_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        """Validate and execute a registered tool with an agent-safe error contract."""
        model = self.input_model_for(tool_name)
        try:
            validated = model.model_validate({} if arguments is None else arguments)
        except ValidationError:
            return ToolResult(success=False, error={
                "code": "invalid_arguments", "message": "Tool arguments are invalid."
            }).model_dump(mode="json")
        try:
            return getattr(self, tool_name)(validated)
        except ForbiddenError:
            return ToolResult(success=False, error={
                "code": "forbidden", "message": "You do not have permission to access this data."
            }).model_dump(mode="json")
        except NotFoundError:
            return ToolResult(success=False, error={
                "code": "not_found", "message": "The requested resource was not found."
            }).model_dump(mode="json")
        except AppException:
            return ToolResult(success=False, error={
                "code": "tool_error", "message": "The tool request could not be completed."
            }).model_dump(mode="json")
        except Exception:
            logger.exception("AI platform tool failed", extra={"tool_name": tool_name})
            return ToolResult(success=False, error={
                "code": "internal_error", "message": "The tool request could not be completed."
            }).model_dump(mode="json")

    def get_student_profile(self, arguments: ProfileInput | dict[str, Any] | None = None) -> dict[str, Any]:
        _input(ProfileInput, arguments)
        profile, kind = ProfileService(self.db).get(self.actor)
        # This is the caller's own profile. Do not include account/authentication fields.
        data = {column.name: getattr(profile, column.name) for column in profile.__table__.columns}
        data.pop("user_id", None)
        return _result(StudentProfileData(user_id=self.actor.id, role=self.actor.role.value,
                                          profile_type=kind, profile=data))

    def get_student_skills(self, arguments: ProfileInput | dict[str, Any] | None = None) -> dict[str, Any]:
        _input(ProfileInput, arguments)
        # Reuse service-level access semantics; querying relationship rows only reads caller data.
        skills = list(self.db.scalars(select(Skill.name).join(UserSkill).where(UserSkill.user_id == self.actor.id)))
        interests = list(self.db.scalars(select(Interest.name).join(UserInterest).where(UserInterest.user_id == self.actor.id)))
        return _result(StudentSkillsData(skills=skills, interests=interests))

    def get_student_progress(self, arguments: ProfileInput | dict[str, Any] | None = None) -> dict[str, Any]:
        _input(ProfileInput, arguments)
        progress = ProgressService(self.db).personal(self.actor)
        return _result(ProgressData.model_validate(progress.model_dump()))

    def get_available_tasks(self, arguments: TaskQueryInput | dict[str, Any] | None = None) -> dict[str, Any]:
        params = _input(TaskQueryInput, arguments)
        rooms = self._visible_room_ids(params.room_id)
        records: list[Task] = []
        service = TaskService(self.db)
        for room_id in rooms:
            records.extend(service.list_for_room(self.actor, room_id, limit=100))
        records = [task for task in records if task.status == TaskStatus.PUBLISHED]
        return _result([self._task_data(task) for task in self._slice(records, params)])

    def get_assigned_tasks(self, arguments: AssignedTaskInput | dict[str, Any] | None = None) -> dict[str, Any]:
        params = _input(AssignedTaskInput, arguments)
        # The data model has room membership, not individual task assignment. Return tasks
        # available in the caller's active rooms, which is the platform's assignment scope.
        # Explicit room IDs are subject to the same active-membership check.
        room_ids = self._visible_room_ids(params.room_id, memberships_only=True)
        service = TaskService(self.db)
        records = [task for room_id in room_ids for task in service.list_for_room(self.actor, room_id, 100)
                   if task.status == TaskStatus.PUBLISHED]
        return _result([self._task_data(task) for task in self._slice(records, params)],
                       "Tasks are associated with rooms; the platform has no individual task-assignment record.")

    def search_matching_tasks(self, arguments: TaskSearchInput | dict[str, Any]) -> dict[str, Any]:
        params = _input(TaskSearchInput, arguments)
        result = self.get_available_tasks(params)
        records = [TaskData.model_validate(item) for item in result["data"]]
        terms = self._terms(params.query)
        matches = [task for task in records if self._matches(terms, task.title, task.description)]
        return _result(matches)

    def search_student_profiles(self, arguments: CandidateSearchInput | dict[str, Any]) -> dict[str, Any]:
        params = _input(CandidateSearchInput, arguments)
        if self.actor.role != UserRole.STUDENT:
            raise ForbiddenError("Only students may search for student collaborators.")

        query = select(User.id, StudentProfile.department).join(
            StudentProfile, StudentProfile.user_id == User.id
        ).where(
            User.role == UserRole.STUDENT, User.is_active.is_(True), User.is_verified.is_(True),
            User.id != self.actor.id, StudentProfile.skills_discoverable.is_(True),
        )
        requested = {" ".join(skill.casefold().split()) for skill in params.skills}
        text_terms = self._terms(params.query or "")
        if requested:
            matching_ids = select(UserSkill.user_id).join(Skill).where(
                Skill.normalized_name.in_(requested)
            )
            query = query.where(User.id.in_(matching_ids))
        for term in text_terms:
            pattern = f"%{self._escape_like(term)}%"
            skill_match = select(UserSkill.user_id).join(Skill).where(
                UserSkill.user_id == User.id, Skill.name.ilike(pattern, escape="\\")
            ).exists()
            query = query.where(or_(StudentProfile.department.ilike(pattern, escape="\\"), skill_match))

        page_rows = self.db.execute(
            query.order_by(User.created_at, User.id)
            .offset((params.page - 1) * params.limit)
            .limit(params.limit)
        ).all()
        if not page_rows:
            return _result([])

        candidate_ids = [user_id for user_id, _ in page_rows]
        skill_rows = self.db.execute(
            select(UserSkill.user_id, Skill.name)
            .join(Skill, Skill.id == UserSkill.skill_id)
            .where(UserSkill.user_id.in_(candidate_ids))
        ).all()
        skills_by_user: dict[UUID, list[str]] = {user_id: [] for user_id in candidate_ids}
        for user_id, skill_name in skill_rows:
            normalized = skill_name.strip().casefold()
            if requested and normalized not in requested:
                continue
            if text_terms and not requested and not any(term in normalized for term in text_terms):
                continue
            skills_by_user[user_id].append(skill_name)

        results = [
            CandidateData(user_id=user_id, department=department,
                          skills=skills_by_user[user_id], matching_skills=skills_by_user[user_id])
            for user_id, department in page_rows
        ]
        return _result(results)

    def get_project_requirements(self, arguments: ProjectInput | dict[str, Any]) -> dict[str, Any]:
        params = _input(ProjectInput, arguments)
        project = ProjectService(self.db).get(self.actor, params.project_id)
        return _result(ProjectRequirementsData(
            project_id=project["id"], title=project["title"], description=project.get("description"),
            objectives=project.get("objectives"), project_type=project.get("project_type"),
            requirements=self._requirements(project.get("objectives")),
        ))

    def find_complementary_skills(self, arguments: CandidateSearchInput | dict[str, Any]) -> dict[str, Any]:
        params = _input(CandidateSearchInput, arguments)
        return self.search_student_profiles(params)

    def get_available_opportunities(self, arguments: OpportunityListInput | dict[str, Any] | None = None) -> dict[str, Any]:
        params = _input(OpportunityListInput, arguments)
        records = OpportunityService(self.db).list_public(self.actor, _page(params), params.opportunity_type)
        return _result([self._opportunity_data(item) for item in records])

    def search_matching_opportunities(self, arguments: OpportunityQueryInput | dict[str, Any]) -> dict[str, Any]:
        params = _input(OpportunityQueryInput, arguments)
        page = PageInput(page=1, limit=100)
        records = OpportunityService(self.db).list_public(self.actor, _page(page), params.opportunity_type)
        terms = self._terms(params.query or "")
        requested = [skill.strip() for skill in params.skills if skill.strip()]
        output = []
        for item in records:
            text = (item.title, item.description, item.organization)
            matched = [skill for skill in requested if self._matches(self._terms(skill), *text)]
            if requested and not matched:
                continue
            if terms and not self._matches(terms, *text):
                continue
            output.append(self._opportunity_data(item))
        explanation = (
            "Results were text-filtered, but records do not contain structured skill requirements; verified skill matches are unavailable."
            if requested else None
        )
        return _result(output[(params.page - 1) * params.limit:params.page * params.limit], explanation)

    def search_research_opportunities(self, arguments: ResearchQueryInput | dict[str, Any] | None = None) -> dict[str, Any]:
        params = _input(ResearchQueryInput, arguments)
        records = OpportunityService(self.db).list_public(self.actor, _page(params), OpportunityType.RESEARCH)
        terms = self._terms(params.query or "")
        results = [self._opportunity_data(item) for item in records
                   if not terms or self._matches(terms, item.title, item.description, item.organization)]
        return _result(results, None if results else "No published research opportunities are currently available.")

    def get_research_projects(self, arguments: PageInput | dict[str, Any] | None = None) -> dict[str, Any]:
        params = _input(PageInput, arguments)
        records = OpportunityService(self.db).list_public(self.actor, _page(params), OpportunityType.RESEARCH)
        results = [self._opportunity_data(item) for item in records]
        return _result(results, None if results else "No published research projects are currently available.")

    def retrieve_knowledge_resources(self, arguments: ResourceQueryInput | dict[str, Any]) -> dict[str, Any]:
        _input(ResourceQueryInput, arguments)
        return _result([], "Knowledge resource persistence is not implemented; no resources can be retrieved.")

    def semantic_search_resources(self, arguments: ResourceQueryInput | dict[str, Any]) -> dict[str, Any]:
        _input(ResourceQueryInput, arguments)
        return _result([], "Semantic search is unavailable: resource storage, embeddings, and vector index are not implemented.")

    def _visible_room_ids(self, room_id: UUID | None, memberships_only: bool = False) -> list[UUID]:
        if room_id is not None:
            if memberships_only:
                membership = self.db.scalar(select(RoomMembership.id).where(
                    RoomMembership.room_id == room_id,
                    RoomMembership.user_id == self.actor.id,
                    RoomMembership.is_active.is_(True),
                ))
                if membership is None:
                    # Match the existing not-found behavior for inaccessible private rooms.
                    raise NotFoundError("Room not found.")
            return [room_id]
        query = select(TechnicalRoom.id).where(TechnicalRoom.is_archived.is_(False))
        if memberships_only:
            query = query.join(RoomMembership, RoomMembership.room_id == TechnicalRoom.id).where(
                RoomMembership.user_id == self.actor.id, RoomMembership.is_active.is_(True))
        else:
            membership = select(RoomMembership.id).where(RoomMembership.room_id == TechnicalRoom.id,
                RoomMembership.user_id == self.actor.id, RoomMembership.is_active.is_(True)).exists()
            query = query.where(or_(TechnicalRoom.visibility == RoomVisibility.PUBLIC, membership))
        return list(self.db.scalars(query.distinct().order_by(TechnicalRoom.id).limit(self.MAX_DISCOVERY_ROOMS)))

    @staticmethod
    def _task_data(task: Task) -> TaskData:
        return TaskData(id=task.id, room_id=task.room_id, title=task.title, description=task.description,
                        difficulty=task.difficulty, status=task.status, starts_at=task.starts_at, due_at=task.due_at)

    @staticmethod
    def _opportunity_data(item: Opportunity, skills: list[str] | None = None) -> OpportunityData:
        return OpportunityData(id=item.id, title=item.title, description=item.description,
            opportunity_type=item.opportunity_type, organization=item.organization, location=item.location,
            application_url=item.application_url, deadline=item.deadline, matching_skills=skills or [])

    @staticmethod
    def _slice(records: list[Any], params: PageInput) -> list[Any]:
        return records[(params.page - 1) * params.limit:params.page * params.limit]

    @staticmethod
    def _terms(value: str) -> list[str]:
        return [term.casefold() for term in value.split() if term.strip()]

    @staticmethod
    def _escape_like(value: str) -> str:
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    @classmethod
    def _matches(cls, terms: list[str], *values: str | None) -> bool:
        haystack = " ".join(value or "" for value in values).casefold()
        return all(term in haystack for term in terms)

    @staticmethod
    def _requirements(objectives: str | None) -> list[str]:
        if not objectives:
            return []
        return [line.strip(" -\t") for line in objectives.splitlines() if line.strip(" -\t")]


# Name retained for concise imports from endpoint wiring.
AIToolService = AIToolsService
