from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, String, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import InvitationStatus, JoinRequestStatus, TeamMembershipRole, TeamMembershipStatus, TeamStatus, TeamVisibility
from app.db.base import Base
from app.db.mixins import TimestampMixin


class Team(TimestampMixin, Base):
    __tablename__ = "teams"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    visibility: Mapped[TeamVisibility] = mapped_column(SAEnum(TeamVisibility, name="team_visibility", native_enum=False, create_constraint=True, validate_strings=True), nullable=False, default=TeamVisibility.PRIVATE, server_default=TeamVisibility.PRIVATE.value)
    status: Mapped[TeamStatus] = mapped_column(SAEnum(TeamStatus, name="team_status", native_enum=False, create_constraint=True, validate_strings=True), nullable=False, default=TeamStatus.ACTIVE, server_default=TeamStatus.ACTIVE.value)
    owner: Mapped["User"] = relationship("User", back_populates="owned_teams")
    memberships: Mapped[list["TeamMembership"]] = relationship(back_populates="team", cascade="all, delete-orphan")
    invitations: Mapped[list["TeamInvitation"]] = relationship(back_populates="team", cascade="all, delete-orphan")
    join_requests: Mapped[list["TeamJoinRequest"]] = relationship(back_populates="team", cascade="all, delete-orphan")
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="team")


class TeamMembership(TimestampMixin, Base):
    __tablename__ = "team_memberships"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    team_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[TeamMembershipRole] = mapped_column(SAEnum(TeamMembershipRole, name="team_membership_role", native_enum=False, create_constraint=True, validate_strings=True), nullable=False, default=TeamMembershipRole.MEMBER, server_default=TeamMembershipRole.MEMBER.value)
    status: Mapped[TeamMembershipStatus] = mapped_column(SAEnum(TeamMembershipStatus, name="team_membership_status", native_enum=False, create_constraint=True, validate_strings=True), nullable=False, default=TeamMembershipStatus.ACTIVE, server_default=TeamMembershipStatus.ACTIVE.value)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    team: Mapped[Team] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship("User")
    __table_args__ = (Index("ix_team_memberships_active_unique", "team_id", "user_id", unique=True, postgresql_where=text("status = 'ACTIVE'")), Index("ix_team_memberships_team_status", "team_id", "status"), Index("ix_team_memberships_leader_unique", "team_id", unique=True, postgresql_where=text("status = 'ACTIVE' AND role = 'LEADER'")))


class TeamInvitation(TimestampMixin, Base):
    __tablename__ = "team_invitations"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    team_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    invitee_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    inviter_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status: Mapped[InvitationStatus] = mapped_column(SAEnum(InvitationStatus, name="team_invitation_status", native_enum=False, create_constraint=True, validate_strings=True), nullable=False, default=InvitationStatus.PENDING, server_default=InvitationStatus.PENDING.value)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    team: Mapped[Team] = relationship(back_populates="invitations")
    __table_args__ = (Index("ix_team_invitations_pending_unique", "team_id", "invitee_id", unique=True, postgresql_where=text("status = 'PENDING'")),)


class TeamJoinRequest(TimestampMixin, Base):
    __tablename__ = "team_join_requests"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    team_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    requester_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[JoinRequestStatus] = mapped_column(SAEnum(JoinRequestStatus, name="team_join_request_status", native_enum=False, create_constraint=True), nullable=False, default=JoinRequestStatus.PENDING, server_default=JoinRequestStatus.PENDING.value)
    reviewed_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    team: Mapped[Team] = relationship(back_populates="join_requests")
    __table_args__ = (Index("ix_team_join_requests_pending_unique", "team_id", "requester_id", unique=True, postgresql_where=text("status = 'PENDING'")), Index("ix_team_join_requests_team_status", "team_id", "status"))
