from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.notification import NotificationRead, NotificationUnreadCount
from app.services.notification_service import NotificationService
from app.utils.pagination import Pagination, pagination_params


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
def list_notifications(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: Annotated[Pagination, Depends(pagination_params)],
    unread_only: bool = False,
):
    return NotificationService(db).list_for_user(user.id, page, unread_only)


@router.get("/unread-count", response_model=NotificationUnreadCount)
def unread_count(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return NotificationService(db).unread_count(user.id)


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_read(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    NotificationService(db).mark_all_read(user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_notification_read(notification_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    NotificationService(db).mark_read(user.id, notification_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
