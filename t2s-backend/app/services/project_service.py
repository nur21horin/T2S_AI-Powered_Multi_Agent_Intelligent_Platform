from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import ProjectStatus, ProjectVisibility, TeamMembershipRole, TeamMembershipStatus
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.project import Project
from app.models.hackathon_submission import HackathonSubmission
from app.models.team import Team, TeamMembership
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.audit_service import record_privileged_action
from app.utils.pagination import Pagination


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, actor: User, data: ProjectCreate) -> Project:
        project = Project(owner_id=actor.id, title=data.title.strip(), description=data.description, objectives=data.objectives, project_type=data.project_type, visibility=data.visibility)
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        record_privileged_action(action="project_created", actor_id=actor.id, target_id=project.id)
        return project

    def get(self, actor: User, project_id: UUID) -> dict:
        project = self.db.get(Project, project_id)
        if project is None or project.status == ProjectStatus.ARCHIVED:
            raise NotFoundError("Project not found.")
        if project.visibility == ProjectVisibility.PRIVATE and not self._can_view(actor, project):
            raise NotFoundError("Project not found.")
        return self._safe_read(actor, project)

    def list(self, actor: User, page: Pagination, owned: bool = False) -> list[dict]:
        query = select(Project).where(Project.status != ProjectStatus.ARCHIVED)
        if owned:
            query = query.where(Project.owner_id == actor.id)
        else:
            query = query.where((Project.visibility == ProjectVisibility.PUBLIC) | (Project.owner_id == actor.id))
        return [self._safe_read(actor, project) for project in self.db.scalars(query.order_by(Project.created_at.desc()).offset(page.offset).limit(page.limit))]

    def update(self, actor: User, project_id: UUID, data: ProjectUpdate) -> Project:
        project = self._locked_project(project_id)
        if project is None or project.status == ProjectStatus.ARCHIVED:
            raise NotFoundError("Project not found.")
        if project.owner_id != actor.id:
            raise ForbiddenError()
        if data.status == ProjectStatus.ARCHIVED and self._has_hackathon_submissions(project.id):
            raise ConflictError("Projects with hackathon submissions cannot be archived.")
        for key, value in data.model_dump(exclude_unset=True).items():
            if key == "title" and value is not None:
                value = value.strip()
            setattr(project, key, value)
        self.db.commit()
        self.db.refresh(project)
        record_privileged_action(action="project_updated", actor_id=actor.id, target_id=project.id)
        return project

    def archive(self, actor: User, project_id: UUID) -> None:
        project = self._locked_project(project_id)
        if project is None:
            raise NotFoundError("Project not found.")
        if project.owner_id != actor.id:
            raise ForbiddenError()
        if self._has_hackathon_submissions(project.id):
            raise ConflictError("Projects with hackathon submissions cannot be archived.")
        project.status = ProjectStatus.ARCHIVED
        self.db.commit()
        record_privileged_action(action="project_archived", actor_id=actor.id, target_id=project.id)

    def attach_team(self, actor: User, project_id: UUID, team_id: UUID | None) -> Project:
        project = self._locked_project(project_id)
        if project is None or project.status == ProjectStatus.ARCHIVED:
            raise NotFoundError("Project not found.")
        if project.owner_id != actor.id:
            raise ForbiddenError()
        if team_id != project.team_id and self._has_hackathon_submissions(project.id):
            raise ConflictError("Projects with hackathon submissions cannot change team association.")
        if team_id is not None:
            team = self.db.scalar(select(Team).where(Team.id == team_id).with_for_update())
            if team is None or team.status.value == "ARCHIVED":
                raise NotFoundError("Team not found.")
            member = self.db.scalar(select(TeamMembership).where(TeamMembership.team_id == team_id, TeamMembership.user_id == actor.id, TeamMembership.status == TeamMembershipStatus.ACTIVE))
            if member is None:
                raise ForbiddenError("Active membership in the target team is required.")
        project.team_id = team_id
        try:
            self.db.commit()
            self.db.refresh(project)
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("Project team association conflicts with current state.") from None
        record_privileged_action(action="project_team_attached" if team_id else "project_team_detached", actor_id=actor.id, target_id=project.id)
        return project

    def _can_view(self, actor: User, project: Project) -> bool:
        if project.owner_id == actor.id:
            return True
        if project.team_id is None:
            return False
        return self.db.scalar(select(TeamMembership.id).where(TeamMembership.team_id == project.team_id, TeamMembership.user_id == actor.id, TeamMembership.status == TeamMembershipStatus.ACTIVE)) is not None

    def _safe_read(self, actor: User, project: Project) -> dict:
        result = ProjectRead.model_validate(project).model_dump()
        if project.team_id is not None:
            team = self.db.get(Team, project.team_id)
            if team is not None and team.visibility.value == "PRIVATE" and not self._can_view(actor, project):
                result["team_id"] = None
        return result

    def _has_hackathon_submissions(self, project_id: UUID) -> bool:
        return self.db.scalar(select(HackathonSubmission.id).where(HackathonSubmission.project_id == project_id).limit(1)) is not None

    def _locked_project(self, project_id: UUID) -> Project:
        project = self.db.scalar(select(Project).where(Project.id == project_id).with_for_update())
        if project is None or project.status == ProjectStatus.ARCHIVED:
            raise NotFoundError("Project not found.")
        return project
