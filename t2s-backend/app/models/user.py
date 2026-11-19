from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, Enum as SAEnum, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import UserRole
from app.db.base import Base
from app.db.mixins import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("email = lower(email)", name="email_lowercase"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(
            UserRole,
            name="user_role",
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
        default=UserRole.STUDENT,
        server_default=UserRole.STUDENT.value,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    auth_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    auth_tokens: Mapped[list["AuthToken"]] = relationship(
        "AuthToken",
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    student_profile: Mapped["StudentProfile | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    teacher_profile: Mapped["TeacherProfile | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    alumni_profile: Mapped["AlumniProfile | None"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    skills: Mapped[list["UserSkill"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    interests: Mapped[list["UserInterest"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    owned_rooms: Mapped[list["TechnicalRoom"]] = relationship(back_populates="owner")
    room_memberships: Mapped[list["RoomMembership"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    created_tasks: Mapped[list["Task"]] = relationship("Task", back_populates="creator")
    submissions: Mapped[list["Submission"]] = relationship("Submission", back_populates="user", cascade="all, delete-orphan")
    evaluations: Mapped[list["Evaluation"]] = relationship("Evaluation", back_populates="evaluator")
