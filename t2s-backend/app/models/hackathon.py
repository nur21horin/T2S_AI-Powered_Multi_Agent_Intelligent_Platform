from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, Index, Integer, String, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import HackathonParticipationMode, HackathonRegistrationStatus, HackathonRegistrationType, HackathonStatus, HackathonVisibility, UserRole
from app.db.base import Base
from app.db.mixins import TimestampMixin


class Hackathon(TimestampMixin, Base):
    __tablename__ = "hackathons"
    __table_args__ = (
        CheckConstraint("length(trim(title)) > 0", name="title_nonempty"),
        CheckConstraint("participant_limit IS NULL OR participant_limit > 0", name="participant_limit_positive"),
        CheckConstraint("team_size_min >= 1", name="team_size_min_positive"),
        CheckConstraint("team_size_max >= team_size_min", name="team_size_range_valid"),
        CheckConstraint("registration_end_at > registration_start_at", name="registration_window_valid"),
        CheckConstraint("end_at > start_at", name="event_window_valid"),
        CheckConstraint("registration_end_at <= start_at", name="registration_before_event"),
        Index("ix_hackathons_visibility_status", "visibility", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    organizer_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[HackathonStatus] = mapped_column(SAEnum(HackathonStatus, name="hackathon_status", native_enum=False, create_constraint=True, validate_strings=True), nullable=False, default=HackathonStatus.DRAFT, server_default=HackathonStatus.DRAFT.value)
    visibility: Mapped[HackathonVisibility] = mapped_column(SAEnum(HackathonVisibility, name="hackathon_visibility", native_enum=False, create_constraint=True, validate_strings=True), nullable=False, default=HackathonVisibility.PUBLIC, server_default=HackathonVisibility.PUBLIC.value)
    participation_mode: Mapped[HackathonParticipationMode] = mapped_column(SAEnum(HackathonParticipationMode, name="hackathon_participation_mode", native_enum=False, create_constraint=True, validate_strings=True), nullable=False, default=HackathonParticipationMode.BOTH, server_default=HackathonParticipationMode.BOTH.value)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    registration_start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    registration_end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    participant_limit: Mapped[int | None] = mapped_column(Integer)
    team_size_min: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    team_size_max: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    organizer: Mapped["User"] = relationship("User")
    eligible_roles: Mapped[list["HackathonEligibleRole"]] = relationship(back_populates="hackathon", cascade="all, delete-orphan")
    registrations: Mapped[list["HackathonRegistration"]] = relationship(back_populates="hackathon", cascade="all, delete-orphan")


class HackathonEligibleRole(Base):
    __tablename__ = "hackathon_eligible_roles"
    hackathon_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("hackathons.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, name="user_role", native_enum=False, create_constraint=False, validate_strings=True), primary_key=True)
    hackathon: Mapped[Hackathon] = relationship(back_populates="eligible_roles")


class HackathonRegistration(TimestampMixin, Base):
    __tablename__ = "hackathon_registrations"
    __table_args__ = (
        CheckConstraint("(registration_type = 'INDIVIDUAL' AND participant_id IS NOT NULL AND team_id IS NULL) OR (registration_type = 'TEAM' AND participant_id IS NULL AND team_id IS NOT NULL)", name="registration_target_valid"),
        Index("ix_hackathon_registrations_hackathon_status", "hackathon_id", "status"),
        Index("ix_hackathon_registrations_participant", "participant_id"),
        Index("ix_hackathon_registrations_team", "team_id"),
        Index("ix_hackathon_registrations_individual_unique", "hackathon_id", "participant_id", unique=True, postgresql_where=text("registration_type = 'INDIVIDUAL' AND status <> 'CANCELLED' AND status <> 'REJECTED'")),
        Index("ix_hackathon_registrations_team_unique", "hackathon_id", "team_id", unique=True, postgresql_where=text("registration_type = 'TEAM' AND status <> 'CANCELLED' AND status <> 'REJECTED'")),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    hackathon_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("hackathons.id", ondelete="RESTRICT"), nullable=False)
    registration_type: Mapped[HackathonRegistrationType] = mapped_column(SAEnum(HackathonRegistrationType, name="hackathon_registration_type", native_enum=False, create_constraint=True, validate_strings=True), nullable=False)
    participant_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    team_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"))
    team_name_snapshot: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[HackathonRegistrationStatus] = mapped_column(SAEnum(HackathonRegistrationStatus, name="hackathon_registration_status", native_enum=False, create_constraint=True, validate_strings=True), nullable=False, default=HackathonRegistrationStatus.PENDING, server_default=HackathonRegistrationStatus.PENDING.value)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    hackathon: Mapped[Hackathon] = relationship(back_populates="registrations")
    members: Mapped[list["HackathonRegistrationMember"]] = relationship(back_populates="registration", cascade="all, delete-orphan")


class HackathonRegistrationMember(Base):
    __tablename__ = "hackathon_registration_members"
    __table_args__ = (Index("ix_hackathon_registration_members_user", "user_id"),)
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    registration_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("hackathon_registrations.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    display_name_snapshot: Mapped[str] = mapped_column(String(120), nullable=False)
    role_snapshot: Mapped[str | None] = mapped_column(String(40))
    registration: Mapped[HackathonRegistration] = relationship(back_populates="members")
