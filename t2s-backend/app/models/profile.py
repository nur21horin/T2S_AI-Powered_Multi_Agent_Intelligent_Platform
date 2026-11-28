from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import Boolean, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin


class StudentProfile(TimestampMixin, Base):
    __tablename__ = "student_profiles"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    department: Mapped[str | None] = mapped_column(String(120))
    academic_year: Mapped[int | None] = mapped_column()
    semester: Mapped[str | None] = mapped_column(String(60))
    technical_background: Mapped[str | None] = mapped_column(Text)
    bio: Mapped[str | None] = mapped_column(Text)
    learning_goals: Mapped[str | None] = mapped_column(Text)
    skills_discoverable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    user: Mapped["User"] = relationship("User", back_populates="student_profile")


class TeacherProfile(TimestampMixin, Base):
    __tablename__ = "teacher_profiles"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    department: Mapped[str | None] = mapped_column(String(120))
    designation: Mapped[str | None] = mapped_column(String(120))
    introduction: Mapped[str | None] = mapped_column(Text)
    areas_of_expertise: Mapped[str | None] = mapped_column(Text)
    research_interests: Mapped[str | None] = mapped_column(Text)
    mentorship_interests: Mapped[str | None] = mapped_column(Text)
    user: Mapped["User"] = relationship("User", back_populates="teacher_profile")


class AlumniProfile(TimestampMixin, Base):
    __tablename__ = "alumni_profiles"
    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    graduation_year: Mapped[int | None] = mapped_column()
    graduation_program: Mapped[str | None] = mapped_column(String(120))
    professional_background: Mapped[str | None] = mapped_column(Text)
    current_professional_field: Mapped[str | None] = mapped_column(String(120))
    job_title: Mapped[str | None] = mapped_column(String(120))
    company: Mapped[str | None] = mapped_column(String(160))
    bio: Mapped[str | None] = mapped_column(Text)
    mentorship_available: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")
    user: Mapped["User"] = relationship("User", back_populates="alumni_profile")
