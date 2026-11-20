from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.enums import HackathonParticipationMode, HackathonRegistrationStatus, HackathonRegistrationType, HackathonStatus, HackathonVisibility, TeamMembershipRole, TeamMembershipStatus, TeamStatus, UserRole
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.models.hackathon import Hackathon, HackathonEligibleRole, HackathonRegistration, HackathonRegistrationMember
from app.models.hackathon_submission import HackathonSubmission
from app.models.team import Team, TeamMembership
from app.models.user import User
from app.schemas.hackathon import HackathonCreate, HackathonUpdate
from app.services.audit_service import record_privileged_action
from app.utils.pagination import Pagination


def _slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.strip().casefold()).strip("-")
    if not result:
        raise BadRequestError("Hackathon title must contain letters or numbers.")
    return result[:170]


class HackathonService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, actor: User, data: HackathonCreate) -> Hackathon:
        self._require_organizer(actor)
        hackathon = Hackathon(organizer_id=actor.id, title=data.title.strip(), slug=_slug(data.title), description=data.description, visibility=data.visibility, participation_mode=data.participation_mode, start_at=data.start_at, end_at=data.end_at, registration_start_at=data.registration_start_at, registration_end_at=data.registration_end_at, participant_limit=data.participant_limit, team_size_min=data.team_size_min, team_size_max=data.team_size_max)
        hackathon.eligible_roles = [HackathonEligibleRole(role=role) for role in dict.fromkeys(data.eligible_roles)]
        self.db.add(hackathon)
        try:
            self.db.commit()
            self.db.refresh(hackathon)
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("A hackathon with this title already exists.") from None
        record_privileged_action(action="hackathon_created", actor_id=actor.id, target_id=hackathon.id)
        return hackathon

    def get(self, actor: User, hackathon_id: UUID) -> Hackathon:
        hackathon = self.db.get(Hackathon, hackathon_id)
        if hackathon is None or hackathon.status == HackathonStatus.ARCHIVED:
            raise NotFoundError("Hackathon not found.")
        if hackathon.visibility == HackathonVisibility.PRIVATE and not self._can_view_private(actor, hackathon):
            raise NotFoundError("Hackathon not found.")
        return hackathon

    def list(self, actor: User, page: Pagination, status: HackathonStatus | None = None, participation_mode: HackathonParticipationMode | None = None) -> list[Hackathon]:
        query = select(Hackathon).where(Hackathon.status != HackathonStatus.ARCHIVED)
        if actor.role != UserRole.ADMIN:
            query = query.where((Hackathon.visibility == HackathonVisibility.PUBLIC) | (Hackathon.organizer_id == actor.id))
        if status is not None:
            query = query.where(Hackathon.status == status)
        if participation_mode is not None:
            query = query.where(Hackathon.participation_mode == participation_mode)
        return list(self.db.scalars(query.order_by(Hackathon.start_at.asc()).offset(page.offset).limit(page.limit)))

    def update(self, actor: User, hackathon_id: UUID, data: HackathonUpdate) -> Hackathon:
        hackathon = self._managed(actor, hackathon_id)
        if hackathon.status not in {HackathonStatus.DRAFT, HackathonStatus.PUBLISHED}:
            raise ConflictError("Only draft or published hackathons can be edited.")
        values = data.model_dump(exclude_unset=True)
        for field in ("title", "visibility", "participation_mode", "team_size_min", "team_size_max", "eligible_roles"):
            if field in values and values[field] is None:
                raise BadRequestError(f"{field} cannot be null.")
        roles = values.pop("eligible_roles", None)
        if "title" in values:
            values["title"] = values["title"].strip()
            values["slug"] = _slug(values["title"])
        self._validate_persisted_dates(hackathon, values)
        for key, value in values.items():
            setattr(hackathon, key, value)
        if roles is not None:
            hackathon.eligible_roles = [HackathonEligibleRole(role=role) for role in dict.fromkeys(roles)]
        try:
            self.db.commit()
            self.db.refresh(hackathon)
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("Hackathon update conflicts with current state.") from None
        record_privileged_action(action="hackathon_updated", actor_id=actor.id, target_id=hackathon.id)
        return hackathon

    def transition(self, actor: User, hackathon_id: UUID, target: HackathonStatus) -> Hackathon:
        hackathon = self._managed(actor, hackathon_id, lock=True)
        now = datetime.now(UTC)
        allowed = {
            HackathonStatus.PUBLISHED: {HackathonStatus.DRAFT},
            HackathonStatus.OPEN: {HackathonStatus.PUBLISHED},
            HackathonStatus.CLOSED: {HackathonStatus.OPEN},
            HackathonStatus.COMPLETED: {HackathonStatus.CLOSED},
            HackathonStatus.ARCHIVED: {HackathonStatus.COMPLETED},
        }
        if target not in allowed or hackathon.status not in allowed[target]:
            raise ConflictError("Invalid hackathon lifecycle transition.")
        if target == HackathonStatus.OPEN and not (hackathon.registration_start_at <= now < hackathon.registration_end_at and now < hackathon.start_at):
            raise ConflictError("Registration is not within its configured opening window.")
        if target == HackathonStatus.COMPLETED and now < hackathon.end_at:
            raise ConflictError("The hackathon has not ended yet.")
        hackathon.status = target
        if target == HackathonStatus.PUBLISHED: hackathon.published_at = now
        elif target == HackathonStatus.CLOSED: hackathon.closed_at = now
        elif target == HackathonStatus.COMPLETED: hackathon.completed_at = now
        elif target == HackathonStatus.ARCHIVED: hackathon.archived_at = now
        self.db.commit()
        self.db.refresh(hackathon)
        record_privileged_action(action=f"hackathon_{target.value.lower()}", actor_id=actor.id, target_id=hackathon.id)
        return hackathon

    def register_individual(self, actor: User, hackathon_id: UUID) -> HackathonRegistration:
        hackathon = self._registration_target(hackathon_id, HackathonParticipationMode.INDIVIDUAL)
        self._lock_capacity(hackathon)
        self._check_eligible(hackathon, actor)
        if self.db.scalar(select(HackathonRegistration.id).where(HackathonRegistration.hackathon_id == hackathon.id, HackathonRegistration.registration_type == HackathonRegistrationType.INDIVIDUAL, HackathonRegistration.participant_id == actor.id, HackathonRegistration.status.in_((HackathonRegistrationStatus.PENDING, HackathonRegistrationStatus.APPROVED)))) is not None:
            raise ConflictError("You already have an active registration for this hackathon.")
        self._ensure_capacity(hackathon, {actor.id})
        registration = HackathonRegistration(hackathon_id=hackathon.id, registration_type=HackathonRegistrationType.INDIVIDUAL, participant_id=actor.id)
        registration.members = [HackathonRegistrationMember(user_id=actor.id, display_name_snapshot=actor.full_name, role_snapshot=actor.role.value)]
        return self._save_registration(registration, actor.id)

    def register_team(self, actor: User, hackathon_id: UUID, team_id: UUID) -> HackathonRegistration:
        hackathon = self._registration_target(hackathon_id, HackathonParticipationMode.TEAM)
        self._lock_capacity(hackathon)
        team = self.db.get(Team, team_id)
        if team is None or team.status != TeamStatus.ACTIVE:
            raise NotFoundError("Team not found.")
        if not self._team_manager(actor.id, team_id):
            raise ForbiddenError("Only the team owner or delegated leader may register the team.")
        members = list(self.db.scalars(select(TeamMembership).join(User).where(TeamMembership.team_id == team_id, TeamMembership.status == TeamMembershipStatus.ACTIVE).order_by(TeamMembership.joined_at.asc())))
        if not hackathon.team_size_min <= len(members) <= hackathon.team_size_max:
            raise ConflictError("The team size does not satisfy the hackathon requirements.")
        for membership in members:
            user = self.db.get(User, membership.user_id)
            if user is None or not user.is_active or not user.is_verified:
                raise ConflictError("Every active team member must be active and verified.")
            self._check_eligible(hackathon, user)
        if self.db.scalar(select(HackathonRegistration.id).where(HackathonRegistration.hackathon_id == hackathon.id, HackathonRegistration.registration_type == HackathonRegistrationType.TEAM, HackathonRegistration.team_id == team_id, HackathonRegistration.status.in_((HackathonRegistrationStatus.PENDING, HackathonRegistrationStatus.APPROVED)))) is not None:
            raise ConflictError("The team already has an active registration for this hackathon.")
        self._ensure_capacity(hackathon, {member.user_id for member in members})
        registration = HackathonRegistration(hackathon_id=hackathon.id, registration_type=HackathonRegistrationType.TEAM, team_id=team.id, team_name_snapshot=team.name)
        registration.members = [HackathonRegistrationMember(user_id=member.user_id, display_name_snapshot=self.db.get(User, member.user_id).full_name, role_snapshot=member.role.value) for member in members]
        return self._save_registration(registration, actor.id)

    def registrations(self, actor: User, hackathon_id: UUID, page: Pagination, status: HackathonRegistrationStatus | None = None) -> list[HackathonRegistration]:
        hackathon = self._managed(actor, hackathon_id)
        query = select(HackathonRegistration).where(HackathonRegistration.hackathon_id == hackathon.id)
        if status is not None: query = query.where(HackathonRegistration.status == status)
        return list(self.db.scalars(query.order_by(HackathonRegistration.registered_at.desc()).offset(page.offset).limit(page.limit)))

    def mine(self, actor: User, hackathon_id: UUID, page: Pagination) -> list[HackathonRegistration]:
        self.get(actor, hackathon_id)
        query = select(HackathonRegistration).join(HackathonRegistration.members).where(HackathonRegistration.hackathon_id == hackathon_id, HackathonRegistrationMember.user_id == actor.id, HackathonRegistration.status.in_((HackathonRegistrationStatus.PENDING, HackathonRegistrationStatus.APPROVED))).order_by(HackathonRegistration.registered_at.desc()).offset(page.offset).limit(page.limit)
        return list(self.db.scalars(query))

    def get_registration(self, actor: User, registration_id: UUID) -> HackathonRegistration:
        registration = self.db.scalar(select(HackathonRegistration).options(selectinload(HackathonRegistration.members)).where(HackathonRegistration.id == registration_id))
        if registration is None: raise NotFoundError("Registration not found.")
        if not self._can_view_registration(actor, registration): raise NotFoundError("Registration not found.")
        return registration

    def cancel(self, actor: User, registration_id: UUID) -> HackathonRegistration:
        registration = self.db.scalar(select(HackathonRegistration).where(HackathonRegistration.id == registration_id).with_for_update())
        if registration is None: raise NotFoundError("Registration not found.")
        hackathon = self.db.scalar(select(Hackathon).where(Hackathon.id == registration.hackathon_id).with_for_update())
        if hackathon is None: raise NotFoundError("Hackathon not found.")
        if not self._can_cancel(actor, registration, hackathon): raise ForbiddenError()
        if registration.status not in {HackathonRegistrationStatus.PENDING, HackathonRegistrationStatus.APPROVED}: raise ConflictError("Registration is no longer active.")
        if actor.role != UserRole.ADMIN and actor.id != hackathon.organizer_id and datetime.now(UTC) >= hackathon.start_at: raise ConflictError("Registration can no longer be cancelled.")
        if registration.status == HackathonRegistrationStatus.APPROVED and self._has_submission(registration):
            raise ConflictError("Registration cannot be cancelled while it has a hackathon submission.")
        registration.status = HackathonRegistrationStatus.CANCELLED
        registration.cancelled_at = datetime.now(UTC)
        self.db.commit(); self.db.refresh(registration)
        record_privileged_action(action="hackathon_registration_cancelled", actor_id=actor.id, target_id=registration.id)
        return registration

    def _has_submission(self, registration: HackathonRegistration) -> bool:
        query = select(HackathonSubmission.id).where(HackathonSubmission.hackathon_id == registration.hackathon_id)
        if registration.registration_type == HackathonRegistrationType.INDIVIDUAL:
            query = query.where(HackathonSubmission.submitter_id == registration.participant_id)
        else:
            query = query.where(HackathonSubmission.team_id == registration.team_id)
        return self.db.scalar(query.limit(1)) is not None

    def review(self, actor: User, registration_id: UUID, approve: bool) -> HackathonRegistration:
        registration = self.db.scalar(select(HackathonRegistration).where(HackathonRegistration.id == registration_id).with_for_update())
        if registration is None: raise NotFoundError("Registration not found.")
        hackathon = self.db.scalar(select(Hackathon).where(Hackathon.id == registration.hackathon_id).with_for_update())
        if hackathon is None: raise NotFoundError("Hackathon not found.")
        if not self._is_manager(actor, hackathon): raise ForbiddenError()
        if hackathon.status != HackathonStatus.OPEN:
            raise ConflictError("Registrations can only be reviewed while the hackathon is open.")
        if registration.status != HackathonRegistrationStatus.PENDING: raise ConflictError("Registration is no longer pending.")
        registration.status = HackathonRegistrationStatus.APPROVED if approve else HackathonRegistrationStatus.REJECTED
        registration.reviewed_by = actor.id; registration.reviewed_at = datetime.now(UTC)
        self.db.commit(); self.db.refresh(registration)
        record_privileged_action(action="hackathon_registration_approved" if approve else "hackathon_registration_rejected", actor_id=actor.id, target_id=registration.id)
        return registration

    def _registration_target(self, hackathon_id: UUID, requested: HackathonParticipationMode) -> Hackathon:
        hackathon = self.db.scalar(select(Hackathon).where(Hackathon.id == hackathon_id).with_for_update())
        if hackathon is None or hackathon.status == HackathonStatus.ARCHIVED: raise NotFoundError("Hackathon not found.")
        now = datetime.now(UTC)
        if hackathon.status != HackathonStatus.OPEN or not (hackathon.registration_start_at <= now < hackathon.registration_end_at and now < hackathon.start_at): raise ConflictError("Registration is not currently open.")
        if hackathon.participation_mode not in {requested, HackathonParticipationMode.BOTH}: raise ConflictError("This participation mode is not accepted.")
        return hackathon

    def _lock_capacity(self, hackathon: Hackathon) -> None:
        self.db.execute(select(Hackathon.id).where(Hackathon.id == hackathon.id).with_for_update())

    def _ensure_capacity(self, hackathon: Hackathon, incoming_participant_ids: set[UUID]) -> None:
        if hackathon.participant_limit is None: return
        active_member_ids = set(self.db.scalars(select(HackathonRegistrationMember.user_id).join(HackathonRegistration).where(HackathonRegistration.hackathon_id == hackathon.id, HackathonRegistration.status.in_((HackathonRegistrationStatus.PENDING, HackathonRegistrationStatus.APPROVED)), HackathonRegistrationMember.user_id.is_not(None)).distinct()))
        new_participant_count = len(incoming_participant_ids - active_member_ids)
        if len(active_member_ids) + new_participant_count > hackathon.participant_limit: raise ConflictError("The hackathon participant capacity has been reached.")

    def _save_registration(self, registration: HackathonRegistration, actor_id: UUID) -> HackathonRegistration:
        self.db.add(registration)
        try:
            self.db.commit(); self.db.refresh(registration)
        except IntegrityError:
            self.db.rollback(); raise ConflictError("An active registration already exists.") from None
        record_privileged_action(action="hackathon_registration_created", actor_id=actor_id, target_id=registration.id)
        return registration

    def _check_eligible(self, hackathon: Hackathon, user: User) -> None:
        if not user.is_active or not user.is_verified: raise ForbiddenError("An active verified account is required.")
        roles = {eligible.role for eligible in hackathon.eligible_roles}
        if roles and user.role not in roles: raise ForbiddenError("Your account role is not eligible for this hackathon.")

    def _team_manager(self, user_id: UUID, team_id: UUID) -> bool:
        return self.db.scalar(select(TeamMembership.id).where(TeamMembership.team_id == team_id, TeamMembership.user_id == user_id, TeamMembership.status == TeamMembershipStatus.ACTIVE, TeamMembership.role.in_((TeamMembershipRole.OWNER, TeamMembershipRole.LEADER)))) is not None

    def _can_view_private(self, actor: User, hackathon: Hackathon) -> bool:
        return actor.role == UserRole.ADMIN or (hackathon.organizer_id is not None and actor.id == hackathon.organizer_id) or self.db.scalar(select(HackathonRegistrationMember.id).join(HackathonRegistration).where(HackathonRegistration.hackathon_id == hackathon.id, HackathonRegistrationMember.user_id == actor.id, HackathonRegistration.status.in_((HackathonRegistrationStatus.PENDING, HackathonRegistrationStatus.APPROVED)))) is not None

    def _can_view_registration(self, actor: User, registration: HackathonRegistration) -> bool:
        return actor.role == UserRole.ADMIN or (self.db.scalar(select(Hackathon.organizer_id).join(HackathonRegistration, HackathonRegistration.hackathon_id == Hackathon.id).where(HackathonRegistration.id == registration.id, Hackathon.organizer_id == actor.id)) is not None) or (registration.status in {HackathonRegistrationStatus.PENDING, HackathonRegistrationStatus.APPROVED} and self.db.scalar(select(HackathonRegistrationMember.id).where(HackathonRegistrationMember.registration_id == registration.id, HackathonRegistrationMember.user_id == actor.id)) is not None)

    def _can_cancel(self, actor: User, registration: HackathonRegistration, hackathon: Hackathon) -> bool:
        if actor.role == UserRole.ADMIN:
            return True
        if registration.registration_type == HackathonRegistrationType.TEAM:
            return registration.team_id is not None and self._team_manager(actor.id, registration.team_id)
        return (hackathon.organizer_id is not None and actor.id == hackathon.organizer_id) or self.db.scalar(select(HackathonRegistrationMember.id).where(HackathonRegistrationMember.registration_id == registration.id, HackathonRegistrationMember.user_id == actor.id)) is not None

    def _is_manager(self, actor: User, hackathon: Hackathon) -> bool:
        return actor.role == UserRole.ADMIN or (hackathon.organizer_id is not None and actor.id == hackathon.organizer_id)

    def _managed(self, actor: User, hackathon_id: UUID, lock: bool = False) -> Hackathon:
        query = select(Hackathon).where(Hackathon.id == hackathon_id)
        if lock: query = query.with_for_update()
        hackathon = self.db.scalar(query)
        if hackathon is None or hackathon.status == HackathonStatus.ARCHIVED: raise NotFoundError("Hackathon not found.")
        if not self._is_manager(actor, hackathon): raise ForbiddenError()
        return hackathon

    def _require_organizer(self, actor: User) -> None:
        if actor.role not in {UserRole.TEACHER, UserRole.ALUMNI, UserRole.ADMIN}: raise ForbiddenError("Only organizers can manage hackathons.")

    def _validate_persisted_dates(self, hackathon: Hackathon, overrides: dict | None = None) -> None:
        values = overrides or {}
        start_at = values.get("start_at", hackathon.start_at)
        end_at = values.get("end_at", hackathon.end_at)
        registration_start_at = values.get("registration_start_at", hackathon.registration_start_at)
        registration_end_at = values.get("registration_end_at", hackathon.registration_end_at)
        team_size_min = values.get("team_size_min", hackathon.team_size_min)
        team_size_max = values.get("team_size_max", hackathon.team_size_max)
        date_values = (start_at, end_at, registration_start_at, registration_end_at)
        if any(value is None for value in date_values):
            raise BadRequestError("Hackathon date fields cannot be null.")
        if team_size_min is None or team_size_max is None:
            raise BadRequestError("Hackathon team-size bounds cannot be null.")
        if any(value.tzinfo is None for value in date_values):
            raise BadRequestError("Hackathon date fields must include a timezone.")
        if end_at <= start_at or registration_end_at <= registration_start_at or registration_end_at > start_at or team_size_max < team_size_min:
            raise BadRequestError("Hackathon dates or team-size bounds are invalid.")
