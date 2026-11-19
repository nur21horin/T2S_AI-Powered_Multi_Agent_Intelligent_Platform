from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.task_service import TaskService


router = APIRouter(tags=["tasks"])


@router.post("/rooms/{room_id}/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(room_id: UUID, data: TaskCreate, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return TaskService(db).create(user, room_id, data)


@router.get("/rooms/{room_id}/tasks", response_model=list[TaskRead])
def list_tasks(room_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)], limit: int = Query(default=100, ge=1, le=100)):
    return TaskService(db).list_for_room(user, room_id, limit)


@router.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(task_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return TaskService(db).get(user, task_id)


@router.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: UUID, data: TaskUpdate, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return TaskService(db).update(user, task_id, data)


@router.post("/tasks/{task_id}/publish", response_model=TaskRead)
def publish_task(task_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return TaskService(db).publish(user, task_id)


@router.post("/tasks/{task_id}/close", response_model=TaskRead)
def close_task(task_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return TaskService(db).close(user, task_id)


@router.post("/tasks/{task_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
def archive_task(task_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    TaskService(db).archive(user, task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
