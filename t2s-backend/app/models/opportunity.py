from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Enum as SAEnum, ForeignKey, Index, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import OpportunityApplicationStatus, OpportunityStatus, OpportunityType
from app.db.base import Base
from app.db.mixins import TimestampMixin


class Opportunity(TimestampMixin, Base):
    __tablename__ = "opportunities"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    opportunity_type: Mapped[OpportunityType] = mapped_column(SAEnum(OpportunityType, name="opportunity_type", native_enum=False, create_constraint=True, validate_strings=True), nullable=False)
    organization: Mapped[str] = mapped_column(String(160), nullable=False)
    location: Mapped[str | None] = mapped_column(String(160))
    application_url: Mapped[str | None] = mapped_column(String(2048))
    deadline: Mapped[datetime | None] = mapped_column()
    status: Mapped[OpportunityStatus] = mapped_column(SAEnum(OpportunityStatus, name="opportunity_status", native_enum=False, create_constraint=True, validate_strings=True), nullable=False, default=OpportunityStatus.DRAFT, server_default=OpportunityStatus.DRAFT.value)

    __table_args__ = (
        CheckConstraint("length(trim(title)) > 0", name="opportunity_title_nonempty"),
        CheckConstraint("length(trim(description)) > 0", name="opportunity_description_nonempty"),
        CheckConstraint("length(trim(organization)) > 0", name="opportunity_organization_nonempty"),
        Index("ix_opportunities_status_type_deadline", "status", "opportunity_type", "deadline"),
    )


class OpportunityApplication(TimestampMixin, Base):
    __tablename__ = "opportunity_applications"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    opportunity_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False)
    applicant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[OpportunityApplicationStatus] = mapped_column(SAEnum(OpportunityApplicationStatus, name="opportunity_application_status", native_enum=False, create_constraint=True, validate_strings=True), nullable=False, default=OpportunityApplicationStatus.PENDING, server_default=OpportunityApplicationStatus.PENDING.value)
    cover_note: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column()

    __table_args__ = (
        UniqueConstraint("opportunity_id", "applicant_id", name="uq_opportunity_applications_opportunity_applicant"),
        Index("ix_opportunity_applications_applicant_status", "applicant_id", "status"),
        Index("ix_opportunity_applications_opportunity_status", "opportunity_id", "status"),
    )
