from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import NotificationType
from app.db.base import Base
from app.db.mixins import TimestampMixin


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    recipient_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    actor_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    related_opportunity_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("opportunities.id", ondelete="SET NULL"))
    notification_type: Mapped[NotificationType] = mapped_column(SAEnum(NotificationType, name="notification_type", native_enum=False, create_constraint=True, validate_strings=True), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("ix_notifications_recipient_read_created", "recipient_id", "read_at", "created_at"),
        Index("ix_notifications_related_opportunity", "related_opportunity_id"),
    )
