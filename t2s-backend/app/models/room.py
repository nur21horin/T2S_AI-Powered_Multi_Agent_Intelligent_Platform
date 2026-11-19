from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Index, String, Text, Uuid, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import MembershipRequestStatus, MembershipRole, RoomVisibility
from app.db.base import Base
from app.db.mixins import TimestampMixin


class TechnicalRoom(TimestampMixin, Base):
    __tablename__ = "technical_rooms"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    topic: Mapped[str | None] = mapped_column(String(120))
    visibility: Mapped[RoomVisibility] = mapped_column(
        SAEnum(RoomVisibility, name="room_visibility", native_enum=False, create_constraint=True, validate_strings=True), nullable=False,
        default=RoomVisibility.PUBLIC, server_default=RoomVisibility.PUBLIC.value
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    owner: Mapped["User"] = relationship("User", back_populates="owned_rooms")
    memberships: Mapped[list["RoomMembership"]] = relationship(back_populates="room", cascade="all, delete-orphan")
    requests: Mapped[list["MembershipRequest"]] = relationship(back_populates="room", cascade="all, delete-orphan")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="room", cascade="all, delete-orphan")


class RoomMembership(TimestampMixin, Base):
    __tablename__ = "room_memberships"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    room_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("technical_rooms.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[MembershipRole] = mapped_column(
        SAEnum(MembershipRole, name="membership_role", native_enum=False, create_constraint=True, validate_strings=True), nullable=False,
        default=MembershipRole.MEMBER, server_default=MembershipRole.MEMBER.value
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    room: Mapped[TechnicalRoom] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship("User", back_populates="room_memberships")
    __table_args__ = (UniqueConstraint("room_id", "user_id"),)


class MembershipRequest(TimestampMixin, Base):
    __tablename__ = "membership_requests"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    room_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("technical_rooms.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[MembershipRequestStatus] = mapped_column(
        SAEnum(MembershipRequestStatus, name="membership_request_status", native_enum=False, create_constraint=True, validate_strings=True), nullable=False,
        default=MembershipRequestStatus.PENDING, server_default=MembershipRequestStatus.PENDING.value
    )
    reviewed_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    room: Mapped[TechnicalRoom] = relationship(back_populates="requests")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    reviewer: Mapped["User | None"] = relationship("User", foreign_keys=[reviewed_by])
    __table_args__ = (
        Index("ix_membership_requests_pending_unique", "room_id", "user_id", unique=True,
              postgresql_where=text("status = 'PENDING'")),
        Index("ix_membership_requests_room_status", "room_id", "status"),
    )
