from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, exists, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import HackathonRegistrationStatus, HackathonRegistrationType, HackathonStatus, HackathonSubmissionStatus, ProjectStatus, TeamMembershipStatus, TeamStatus, UserRole
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.hackathon import Hackathon, HackathonRegistration, HackathonRegistrationMember
from app.models.hackathon_submission import HackathonSubmission
from app.models.project import Project
from app.models.team import Team, TeamMembership
from app.models.user import User
from app.schemas.hackathon_submission import HackathonSubmissionCreate, HackathonSubmissionUpdate
from app.services.audit_service import record_privileged_action
from app.utils.pagination import Pagination


class HackathonSubmissionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, actor: User, hackathon_id: UUID, data: HackathonSubmissionCreate) -> HackathonSubmission:
        hackathon = self._locked_hackathon(hackathon_id)
        self._assert_submission_window(hackathon)
        project = self._locked_project(data.project_id)
        team_id = self._validate_project_access(actor, project)
        self._approved_registration(actor, hackathon.id, team_id)
        submission = HackathonSubmission(
            hackathon_id=hackathon.id,
            project_id=project.id,
            submitter_id=actor.id,
            team_id=team_id,
            repository_url=self._url(data.repository_url),
            demo_url=self._url(data.demo_url),
            additional_details=data.additional_details,
        )
        self.db.add(submission)
        try:
            self.db.commit()
            self.db.refresh(submission)
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("This project already has a submission for the hackathon.") from None
        record_privileged_action(action="hackathon_submission_created", actor_id=actor.id, target_id=submission.id)
        return submission

    def get(self, actor: User, submission_id: UUID) -> HackathonSubmission:
        submission = self.db.get(HackathonSubmission, submission_id)
        if submission is None:
            raise NotFoundError("Submission not found.")
        hackathon = self.db.get(Hackathon, submission.hackathon_id)
        if hackathon is None or not self._can_manage(actor, hackathon):
            self._authorize_participant(actor, submission)
        return submission

    def list_for_hackathon(self, actor: User, hackathon_id: UUID, page: Pagination) -> list[HackathonSubmission]:
        hackathon = self.db.get(Hackathon, hackathon_id)
        if hackathon is None:
            raise NotFoundError("Hackathon not found.")
        if not self._can_manage(actor, hackathon):
            raise ForbiddenError("Only the organizer or an administrator can list hackathon submissions.")
        query = select(HackathonSubmission).where(HackathonSubmission.hackathon_id == hackathon_id).order_by(HackathonSubmission.created_at.desc()).offset(page.offset).limit(page.limit)
        return list(self.db.scalars(query))

    def list_mine(self, actor: User, page: Pagination) -> list[HackathonSubmission]:
        individual_registration = exists(select(HackathonRegistration.id).where(HackathonRegistration.hackathon_id == HackathonSubmission.hackathon_id, HackathonRegistration.registration_type == HackathonRegistrationType.INDIVIDUAL, HackathonRegistration.participant_id == actor.id, HackathonRegistration.status == HackathonRegistrationStatus.APPROVED))
        team_registration = exists(select(HackathonRegistration.id).join(HackathonRegistrationMember).where(HackathonRegistration.hackathon_id == HackathonSubmission.hackathon_id, HackathonRegistration.team_id == HackathonSubmission.team_id, HackathonRegistration.status == HackathonRegistrationStatus.APPROVED, HackathonRegistrationMember.user_id == actor.id))
        active_team_member = exists(select(TeamMembership.id).where(TeamMembership.team_id == HackathonSubmission.team_id, TeamMembership.user_id == actor.id, TeamMembership.status == TeamMembershipStatus.ACTIVE))
        query = select(HackathonSubmission).where(or_(and_(HackathonSubmission.submitter_id == actor.id, individual_registration), and_(active_team_member, team_registration))).order_by(HackathonSubmission.created_at.desc()).offset(page.offset).limit(page.limit)
        return list(self.db.scalars(query))

    def list_for_project(self, actor: User, project_id: UUID, page: Pagination) -> list[HackathonSubmission]:
        project = self.db.get(Project, project_id)
        if project is None or project.status == ProjectStatus.ARCHIVED:
            raise NotFoundError("Project not found.")
        if actor.role != UserRole.ADMIN and project.owner_id != actor.id:
            if project.team_id is None or self.db.scalar(select(TeamMembership.id).where(TeamMembership.team_id == project.team_id, TeamMembership.user_id == actor.id, TeamMembership.status == TeamMembershipStatus.ACTIVE)) is None:
                raise NotFoundError("Project not found.")
        query = select(HackathonSubmission).where(HackathonSubmission.project_id == project_id).order_by(HackathonSubmission.created_at.desc()).offset(page.offset).limit(page.limit)
        submissions = list(self.db.scalars(query))
        if actor.role == UserRole.ADMIN:
            return submissions
        visible = []
        for submission in submissions:
            try:
                self._authorize_participant(actor, submission)
            except NotFoundError:
                continue
            visible.append(submission)
        return visible

    def update(self, actor: User, submission_id: UUID, data: HackathonSubmissionUpdate) -> HackathonSubmission:
        submission = self._locked_submission(submission_id)
        self._authorize_participant(actor, submission)
        if submission.status != HackathonSubmissionStatus.DRAFT:
            raise ConflictError("Only draft submissions can be edited.")
        hackathon = self._locked_hackathon(submission.hackathon_id)
        self._assert_submission_window(hackathon)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(submission, key, self._url(value) if key in {"repository_url", "demo_url"} else value)
        self.db.commit()
        self.db.refresh(submission)
        record_privileged_action(action="hackathon_submission_updated", actor_id=actor.id, target_id=submission.id)
        return submission

    def finalize(self, actor: User, submission_id: UUID) -> HackathonSubmission:
        submission = self._locked_submission(submission_id)
        self._authorize_participant(actor, submission)
        if submission.status != HackathonSubmissionStatus.DRAFT:
            raise ConflictError("Only draft submissions can be finalized.")
        hackathon = self._locked_hackathon(submission.hackathon_id)
        self._assert_submission_window(hackathon)
        project = self._locked_project(submission.project_id)
        self._validate_project_access(actor, project)
        self._approved_registration(actor, hackathon.id, submission.team_id)
        self._assert_transition(submission.status, HackathonSubmissionStatus.SUBMITTED)
        submission.status = HackathonSubmissionStatus.SUBMITTED
        submission.submitted_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(submission)
        record_privileged_action(action="hackathon_submission_finalized", actor_id=actor.id, target_id=submission.id)
        return submission

    def withdraw(self, actor: User, submission_id: UUID) -> HackathonSubmission:
        submission = self._locked_submission(submission_id)
        self._authorize_participant(actor, submission)
        if submission.status not in {HackathonSubmissionStatus.DRAFT, HackathonSubmissionStatus.SUBMITTED}:
            raise ConflictError("Withdrawn submissions cannot be changed.")
        hackathon = self._locked_hackathon(submission.hackathon_id)
        self._assert_submission_window(hackathon)
        self._assert_transition(submission.status, HackathonSubmissionStatus.WITHDRAWN)
        submission.status = HackathonSubmissionStatus.WITHDRAWN
        submission.withdrawn_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(submission)
        record_privileged_action(action="hackathon_submission_withdrawn", actor_id=actor.id, target_id=submission.id)
        return submission

    @staticmethod
    def _assert_transition(current: HackathonSubmissionStatus, target: HackathonSubmissionStatus) -> None:
        allowed = {
            HackathonSubmissionStatus.DRAFT: {HackathonSubmissionStatus.SUBMITTED, HackathonSubmissionStatus.WITHDRAWN},
            HackathonSubmissionStatus.SUBMITTED: {HackathonSubmissionStatus.WITHDRAWN},
            HackathonSubmissionStatus.WITHDRAWN: set(),
        }
        if target not in allowed[current]:
            raise ConflictError("Invalid hackathon submission lifecycle transition.")

    @staticmethod
    def _assert_submission_window(hackathon: Hackathon, now: datetime | None = None) -> None:
        now = now or datetime.now(UTC)
        if hackathon.status != HackathonStatus.OPEN:
            raise ConflictError("Hackathon submissions are not currently open.")
        if now < hackathon.registration_start_at:
            raise ConflictError("Hackathon submissions have not opened yet.")
        if now >= hackathon.start_at:
            raise ConflictError("The hackathon submission deadline has passed.")

    def _validate_project_access(self, actor: User, project: Project) -> UUID | None:
        if project is None or project.status != ProjectStatus.ACTIVE:
            raise ConflictError("Only active projects may be submitted.")
        if project.team_id is None:
            if project.owner_id != actor.id:
                raise ForbiddenError("Only the project owner can submit an individual project.")
            return None
        team = self.db.scalar(select(Team).where(Team.id == project.team_id).with_for_update())
        if team is None or team.status != TeamStatus.ACTIVE:
            raise ConflictError("The project team is not active.")
        if self.db.scalar(select(TeamMembership.id).where(TeamMembership.team_id == project.team_id, TeamMembership.user_id == actor.id, TeamMembership.status == TeamMembershipStatus.ACTIVE)) is None:
            raise ForbiddenError("An active member of the project team is required.")
        return project.team_id

    def _approved_registration(self, actor: User, hackathon_id: UUID, team_id: UUID | None) -> HackathonRegistration:
        if team_id is None:
            registration = self.db.scalar(select(HackathonRegistration).where(HackathonRegistration.hackathon_id == hackathon_id, HackathonRegistration.registration_type == HackathonRegistrationType.INDIVIDUAL, HackathonRegistration.participant_id == actor.id, HackathonRegistration.status == HackathonRegistrationStatus.APPROVED))
            if registration is None:
                raise ForbiddenError("An approved individual hackathon registration is required.")
            return registration
        registration = self.db.scalar(select(HackathonRegistration).where(HackathonRegistration.hackathon_id == hackathon_id, HackathonRegistration.registration_type == HackathonRegistrationType.TEAM, HackathonRegistration.team_id == team_id, HackathonRegistration.status == HackathonRegistrationStatus.APPROVED))
        if registration is None:
            raise ForbiddenError("An approved team hackathon registration is required.")
        if self.db.scalar(select(HackathonRegistrationMember.id).where(HackathonRegistrationMember.registration_id == registration.id, HackathonRegistrationMember.user_id == actor.id)) is None:
            raise ForbiddenError("The submitter must be a member of the approved team registration.")
        return registration

    def _authorize_participant(self, actor: User, submission: HackathonSubmission) -> None:
        project = self.db.get(Project, submission.project_id)
        if project is None:
            raise NotFoundError("Submission not found.")
        if project.team_id is None and actor.id == project.owner_id and actor.id == submission.submitter_id:
            self._approved_registration(actor, submission.hackathon_id, None)
            return
        if project.team_id is not None and submission.team_id == project.team_id and self.db.scalar(select(TeamMembership.id).where(TeamMembership.team_id == project.team_id, TeamMembership.user_id == actor.id, TeamMembership.status == TeamMembershipStatus.ACTIVE)) is not None:
            self._approved_registration(actor, submission.hackathon_id, project.team_id)
            return
        raise NotFoundError("Submission not found.")

    def _can_manage(self, actor: User, hackathon: Hackathon) -> bool:
        return actor.role == UserRole.ADMIN or actor.id == hackathon.organizer_id

    def _locked_hackathon(self, hackathon_id: UUID) -> Hackathon:
        hackathon = self.db.scalar(select(Hackathon).where(Hackathon.id == hackathon_id).with_for_update())
        if hackathon is None or hackathon.status == HackathonStatus.ARCHIVED:
            raise NotFoundError("Hackathon not found.")
        return hackathon

    def _locked_project(self, project_id: UUID) -> Project:
        project = self.db.scalar(select(Project).where(Project.id == project_id).with_for_update())
        if project is None or project.status == ProjectStatus.ARCHIVED:
            raise NotFoundError("Project not found.")
        return project

    def _locked_submission(self, submission_id: UUID) -> HackathonSubmission:
        submission = self.db.scalar(select(HackathonSubmission).where(HackathonSubmission.id == submission_id).with_for_update())
        if submission is None:
            raise NotFoundError("Submission not found.")
        return submission

    @staticmethod
    def _url(value: object | None) -> str | None:
        return None if value is None else str(value)
