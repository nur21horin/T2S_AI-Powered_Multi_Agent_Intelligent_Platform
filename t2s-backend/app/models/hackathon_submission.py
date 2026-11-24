from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, Index, String, Text, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import HackathonSubmissionStatus
from app.db.base import Base
from app.db.mixins import TimestampMixin


class HackathonSubmission(TimestampMixin, Base):
    __tablename__ = "hackathon_submissions"
    __table_args__ = (
        UniqueConstraint("hackathon_id", "project_id", name="uq_hackathon_submissions_hackathon_project"),
        CheckConstraint("status <> 'SUBMITTED' OR submitted_at IS NOT NULL", name="submitted_timestamp_required"),
        CheckConstraint("status <> 'WITHDRAWN' OR withdrawn_at IS NOT NULL", name="withdrawn_timestamp_required"),
        Index("ix_hackathon_submissions_hackathon_status", "hackathon_id", "status"),
        Index("ix_hackathon_submissions_submitter", "submitter_id"),
        Index("ix_hackathon_submissions_team", "team_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    hackathon_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("hackathons.id", ondelete="RESTRICT"), nullable=False)
    project_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    submitter_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    team_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"))
    status: Mapped[HackathonSubmissionStatus] = mapped_column(
        SAEnum(HackathonSubmissionStatus, name="hackathon_submission_status", native_enum=False, create_constraint=True, validate_strings=True),
        nullable=False,
        default=HackathonSubmissionStatus.DRAFT,
        server_default=HackathonSubmissionStatus.DRAFT.value,
    )
    repository_url: Mapped[str | None] = mapped_column(String(2048))
    demo_url: Mapped[str | None] = mapped_column(String(2048))
    additional_details: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    hackathon: Mapped["Hackathon"] = relationship("Hackathon")
    project: Mapped["Project"] = relationship("Project")
    submitter: Mapped["User"] = relationship("User")
    team: Mapped["Team | None"] = relationship("Team")
