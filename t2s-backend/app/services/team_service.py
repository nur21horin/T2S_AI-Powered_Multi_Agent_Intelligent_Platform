from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import InvitationStatus, JoinRequestStatus, TeamMembershipRole, TeamMembershipStatus, TeamStatus, TeamVisibility
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.team import Team, TeamInvitation, TeamJoinRequest, TeamMembership
from app.models.user import User
from app.schemas.team import TeamCreate, TeamUpdate
from app.services.audit_service import record_privileged_action
from app.utils.pagination import Pagination


class TeamService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, actor: User, data: TeamCreate) -> Team:
        team = Team(owner_id=actor.id, name=data.name.strip(), description=data.description, visibility=data.visibility)
        self.db.add(team)
        self.db.flush()
        self.db.add(TeamMembership(team_id=team.id, user_id=actor.id, role=TeamMembershipRole.OWNER))
        self.db.commit()
        self.db.refresh(team)
        record_privileged_action(action="team_created", actor_id=actor.id, target_id=team.id)
        return team

    def get(self, actor: User, team_id: UUID) -> Team:
        team = self.db.get(Team, team_id)
        if team is None or team.status == TeamStatus.ARCHIVED:
            raise NotFoundError("Team not found.")
        if team.visibility == TeamVisibility.PRIVATE and not self._active_member(actor.id, team_id):
            raise NotFoundError("Team not found.")
        return team

    def list(self, actor: User, page: Pagination, owned: bool = False) -> list[Team]:
        query = select(Team).where(Team.status == TeamStatus.ACTIVE)
        query = query.where(Team.owner_id == actor.id if owned else ((Team.visibility == TeamVisibility.PUBLIC) | (Team.owner_id == actor.id)))
        return list(self.db.scalars(query.order_by(Team.created_at.desc()).offset(page.offset).limit(page.limit)))

    def update(self, actor: User, team_id: UUID, data: TeamUpdate) -> Team:
        team = self.db.get(Team, team_id)
        if team is None or team.status == TeamStatus.ARCHIVED:
            raise NotFoundError("Team not found.")
        if not self._manager(actor.id, team):
            raise ForbiddenError()
        if data.status == TeamStatus.ARCHIVED and team.owner_id != actor.id:
            raise ForbiddenError("Only the team owner can archive the team.")
        for key, value in data.model_dump(exclude_unset=True).items():
            if key == "name" and value is not None:
                value = value.strip()
            setattr(team, key, value)
        self.db.commit()
        self.db.refresh(team)
        record_privileged_action(action="team_updated", actor_id=actor.id, target_id=team.id)
        return team

    def archive(self, actor: User, team_id: UUID) -> None:
        team = self.db.get(Team, team_id)
        if team is None:
            raise NotFoundError("Team not found.")
        if team.owner_id != actor.id:
            raise ForbiddenError()
        team.status = TeamStatus.ARCHIVED
        self.db.commit()
        record_privileged_action(action="team_archived", actor_id=actor.id, target_id=team.id)

    def set_leader(self, actor: User, team_id: UUID, user_id: UUID | None) -> TeamMembership | None:
        team = self._managed_team(actor.id, team_id)
        current = self.db.scalar(select(TeamMembership).where(TeamMembership.team_id == team_id, TeamMembership.role == TeamMembershipRole.LEADER, TeamMembership.status == TeamMembershipStatus.ACTIVE).with_for_update())
        if user_id is None:
            if current:
                current.role = TeamMembershipRole.MEMBER
                self.db.commit()
            return None
        if user_id == team.owner_id:
            raise ConflictError("The owner is not a delegated leader.")
        target = self._active_member(user_id, team_id)
        if target is None:
            raise ConflictError("The delegated leader must be an active member.")
        if current and current.user_id != user_id:
            current.role = TeamMembershipRole.MEMBER
        target.role = TeamMembershipRole.LEADER
        try:
            self.db.commit()
            self.db.refresh(target)
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("Leader changed concurrently.") from None
        record_privileged_action(action="team_leader_changed", actor_id=actor.id, target_id=team_id)
        return target

    def members(self, actor: User, team_id: UUID) -> list[TeamMembership]:
        self.get(actor, team_id)
        if not self._active_member(actor.id, team_id):
            raise ForbiddenError()
        return list(self.db.scalars(select(TeamMembership).where(TeamMembership.team_id == team_id, TeamMembership.status == TeamMembershipStatus.ACTIVE)))

    def invite(self, actor: User, team_id: UUID, invitee_id: UUID) -> TeamInvitation:
        team = self._managed_team(actor.id, team_id)
        if self.db.get(User, invitee_id) is None:
            raise NotFoundError("User not found.")
        if invitee_id == team.owner_id or self._active_member(invitee_id, team_id):
            raise ConflictError("The user is already a team member.")
        invitation = TeamInvitation(team_id=team_id, invitee_id=invitee_id, inviter_id=actor.id, expires_at=datetime.now(UTC) + timedelta(days=7))
        self.db.add(invitation)
        try:
            self.db.commit(); self.db.refresh(invitation)
        except IntegrityError:
            self.db.rollback(); raise ConflictError("An invitation is already pending.") from None
        return invitation

    def respond_invitation(self, actor: User, invitation_id: UUID, accept: bool) -> TeamInvitation:
        invitation = self.db.scalar(select(TeamInvitation).where(TeamInvitation.id == invitation_id, TeamInvitation.invitee_id == actor.id).with_for_update())
        if invitation is None:
            raise NotFoundError("Invitation not found.")
        if invitation.status != InvitationStatus.PENDING:
            raise ConflictError("Invitation is no longer pending.")
        now = datetime.now(UTC)
        if invitation.expires_at <= now:
            invitation.status = InvitationStatus.EXPIRED
            self.db.commit()
            raise ConflictError("Invitation has expired.")
        invitation.status = InvitationStatus.ACCEPTED if accept else InvitationStatus.REJECTED
        invitation.responded_at = now
        if accept:
            self._activate_member(invitation.team_id, actor.id, TeamMembershipRole.MEMBER)
        self.db.commit(); self.db.refresh(invitation)
        return invitation

    def request_join(self, actor: User, team_id: UUID) -> TeamJoinRequest:
        team = self.db.get(Team, team_id)
        if team is None or team.status == TeamStatus.ARCHIVED:
            raise NotFoundError("Team not found.")
        if self._active_member(actor.id, team_id):
            raise ConflictError("You are already a team member.")
        request = TeamJoinRequest(team_id=team_id, requester_id=actor.id)
        self.db.add(request)
        try:
            self.db.commit(); self.db.refresh(request)
        except IntegrityError:
            self.db.rollback(); raise ConflictError("A join request is already pending.") from None
        return request

    def decide_request(self, actor: User, team_id: UUID, request_id: UUID, approve: bool) -> TeamJoinRequest:
        self._managed_team(actor.id, team_id)
        request = self.db.scalar(select(TeamJoinRequest).where(TeamJoinRequest.id == request_id, TeamJoinRequest.team_id == team_id).with_for_update())
        if request is None: raise NotFoundError("Join request not found.")
        if request.status != JoinRequestStatus.PENDING: raise ConflictError("Join request is no longer pending.")
        request.status = JoinRequestStatus.APPROVED if approve else JoinRequestStatus.REJECTED
        request.reviewed_by = actor.id; request.reviewed_at = datetime.now(UTC)
        if approve: self._activate_member(team_id, request.requester_id, TeamMembershipRole.MEMBER)
        try:
            self.db.commit(); self.db.refresh(request)
        except IntegrityError:
            self.db.rollback(); raise ConflictError("Join request changed concurrently.") from None
        return request

    def leave(self, actor: User, team_id: UUID) -> None:
        membership = self._active_member(actor.id, team_id)
        if membership is None: raise NotFoundError("Membership not found.")
        if membership.role == TeamMembershipRole.OWNER: raise ForbiddenError("The team owner cannot leave the team.")
        membership.status = TeamMembershipStatus.LEFT; membership.ended_at = datetime.now(UTC)
        self.db.commit()

    def _active_member(self, user_id: UUID, team_id: UUID) -> TeamMembership | None:
        return self.db.scalar(select(TeamMembership).where(TeamMembership.user_id == user_id, TeamMembership.team_id == team_id, TeamMembership.status == TeamMembershipStatus.ACTIVE))

    def _manager(self, user_id: UUID, team: Team) -> bool:
        if team.owner_id == user_id: return True
        return self.db.scalar(select(TeamMembership.id).where(TeamMembership.team_id == team.id, TeamMembership.user_id == user_id, TeamMembership.role == TeamMembershipRole.LEADER, TeamMembership.status == TeamMembershipStatus.ACTIVE)) is not None

    def _managed_team(self, user_id: UUID, team_id: UUID) -> Team:
        team = self.db.get(Team, team_id)
        if team is None or team.status == TeamStatus.ARCHIVED: raise NotFoundError("Team not found.")
        if not self._manager(user_id, team): raise ForbiddenError()
        return team

    def _activate_member(self, team_id: UUID, user_id: UUID, role: TeamMembershipRole) -> TeamMembership:
        membership = TeamMembership(team_id=team_id, user_id=user_id, role=role)
        self.db.add(membership)
        self.db.flush()
        return membership
