from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, Integer, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import EvaluationStatus
from app.db.base import Base
from app.db.mixins import TimestampMixin


class Evaluation(TimestampMixin, Base):
    __tablename__ = "evaluations"
    __table_args__ = (CheckConstraint("score >= 0", name="score_nonnegative"),)

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    submission_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, unique=True)
    evaluator_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    feedback: Mapped[str | None] = mapped_column(Text)
    status: Mapped[EvaluationStatus] = mapped_column(
        SAEnum(EvaluationStatus, name="evaluation_status", native_enum=False, create_constraint=True, validate_strings=True),
        nullable=False,
        default=EvaluationStatus.FINALIZED,
        server_default=EvaluationStatus.FINALIZED.value,
    )
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    submission: Mapped["Submission"] = relationship("Submission", back_populates="evaluation")
    evaluator: Mapped["User"] = relationship("User", back_populates="evaluations")
