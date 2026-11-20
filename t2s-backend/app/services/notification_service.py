from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.enums import NotificationType
from app.core.exceptions import NotFoundError
from app.models.notification import Notification
from app.schemas.notification import NotificationUnreadCount
from app.utils.pagination import Pagination


class NotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        recipient_id: UUID,
        notification_type: NotificationType,
        title: str,
        body: str,
        actor_id: UUID | None = None,
        related_opportunity_id: UUID | None = None,
    ) -> Notification:
        notification = Notification(
            recipient_id=recipient_id,
            actor_id=actor_id,
            related_opportunity_id=related_opportunity_id,
            notification_type=notification_type,
            title=title,
            body=body,
        )
        self.db.add(notification)
        self.db.flush()
        return notification

    def list_for_user(self, recipient_id: UUID, page: Pagination, unread_only: bool = False) -> list[Notification]:
        query = select(Notification).where(Notification.recipient_id == recipient_id)
        if unread_only:
            query = query.where(Notification.read_at.is_(None))
        query = query.order_by(Notification.created_at.desc()).offset(page.offset).limit(page.limit)
        return list(self.db.scalars(query))

    def unread_count(self, recipient_id: UUID) -> NotificationUnreadCount:
        count = self.db.scalar(select(func.count(Notification.id)).where(Notification.recipient_id == recipient_id, Notification.read_at.is_(None))) or 0
        return NotificationUnreadCount(unread_count=count)

    def mark_read(self, recipient_id: UUID, notification_id: UUID) -> None:
        notification = self.db.scalar(select(Notification).where(Notification.id == notification_id, Notification.recipient_id == recipient_id).with_for_update())
        if notification is None:
            raise NotFoundError("Notification not found.")
        if notification.read_at is None:
            notification.read_at = datetime.now(UTC)
            self.db.commit()

    def mark_all_read(self, recipient_id: UUID) -> None:
        self.db.execute(update(Notification).where(Notification.recipient_id == recipient_id, Notification.read_at.is_(None)).values(read_at=datetime.now(UTC)))
        self.db.commit()
