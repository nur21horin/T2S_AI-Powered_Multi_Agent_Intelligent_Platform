from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.progress import ProgressRead
from app.services.progress_service import ProgressService


router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/me", response_model=ProgressRead)
def my_progress(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)], room_id: UUID | None = Query(default=None)):
    return ProgressService(db).personal(user, room_id)


@router.get("/rooms/{room_id}/users/{user_id}", response_model=ProgressRead)
def user_progress(room_id: UUID, user_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return ProgressService(db).for_user(user, room_id, user_id)
