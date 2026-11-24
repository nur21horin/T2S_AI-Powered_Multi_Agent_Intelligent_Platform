from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, Index, Integer, Text, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import SubmissionStatus
from app.db.base import Base
from app.db.mixins import TimestampMixin


class Submission(TimestampMixin, Base):
    __tablename__ = "submissions"
    __table_args__ = (
        UniqueConstraint("task_id", "user_id", "attempt_number"),
        CheckConstraint("attempt_number > 0", name="attempt_positive"),
        CheckConstraint("length(trim(content)) > 0", name="content_nonempty"),
        Index("ix_submissions_task_user", "task_id", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    repository_url: Mapped[str | None] = mapped_column(Text)
    project_url: Mapped[str | None] = mapped_column(Text)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[SubmissionStatus] = mapped_column(
        SAEnum(SubmissionStatus, name="submission_status", native_enum=False, create_constraint=True, validate_strings=True),
        nullable=False,
        default=SubmissionStatus.SUBMITTED,
        server_default=SubmissionStatus.SUBMITTED.value,
    )
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    task: Mapped["Task"] = relationship("Task", back_populates="submissions")
    user: Mapped["User"] = relationship("User", back_populates="submissions")
    evaluation: Mapped["Evaluation | None"] = relationship("Evaluation", back_populates="submission", uselist=False, cascade="all, delete-orphan")
