from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import TaskDifficulty, TaskStatus
from app.db.base import Base
from app.db.mixins import TimestampMixin


class Task(TimestampMixin, Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("length(trim(title)) > 0", name="title_nonempty"),
        CheckConstraint("max_score > 0", name="max_score_positive"),
        CheckConstraint("max_attempts IS NULL OR max_attempts > 0", name="max_attempts_positive"),
        CheckConstraint("due_at IS NULL OR starts_at IS NULL OR due_at >= starts_at", name="valid_schedule"),
        Index("ix_tasks_room_status", "room_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    room_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("technical_rooms.id", ondelete="CASCADE"), nullable=False)
    creator_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    instructions: Mapped[str | None] = mapped_column(Text)
    difficulty: Mapped[TaskDifficulty] = mapped_column(
        SAEnum(TaskDifficulty, name="task_difficulty", native_enum=False, create_constraint=True, validate_strings=True),
        nullable=False,
        default=TaskDifficulty.BEGINNER,
        server_default=TaskDifficulty.BEGINNER.value,
    )
    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus, name="task_status", native_enum=False, create_constraint=True, validate_strings=True),
        nullable=False,
        default=TaskStatus.DRAFT,
        server_default=TaskStatus.DRAFT.value,
    )
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    max_score: Mapped[int] = mapped_column(Integer, nullable=False, default=100, server_default="100")
    allow_resubmission: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    max_attempts: Mapped[int | None] = mapped_column(Integer)

    room: Mapped["TechnicalRoom"] = relationship("TechnicalRoom", back_populates="tasks")
    creator: Mapped["User"] = relationship("User", back_populates="created_tasks")
    submissions: Mapped[list["Submission"]] = relationship("Submission", back_populates="task", cascade="all, delete-orphan")
