from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.enums import NotificationType


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    actor_id: UUID | None
    related_opportunity_id: UUID | None
    notification_type: NotificationType
    title: str
    body: str
    read_at: datetime | None
    created_at: datetime
    updated_at: datetime


class NotificationUnreadCount(BaseModel):
    unread_count: int
