from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.schemas.admin import UserRoleUpdate
from app.schemas.user import UserRead
from app.security.permissions import Permission, require_permission
from app.services.user_service import UserService

router = APIRouter(prefix="/admin", tags=["administrator"])


@router.patch("/users/{user_id}/role", response_model=UserRead)
def assign_user_role(
    user_id: UUID,
    data: UserRoleUpdate,
    actor: Annotated[User, Depends(require_permission(Permission.MANAGE_USER_ROLES))],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    return UserService(db).assign_role(actor.id, user_id, data.role)
