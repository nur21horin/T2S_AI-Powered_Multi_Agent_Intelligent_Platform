from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import TaskStatus, UserRole
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.room import RoomMembership, TechnicalRoom
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, actor: User, room_id: UUID, data: TaskCreate) -> Task:
        room = self._manager_room(actor, room_id)
        max_attempts = data.max_attempts if data.allow_resubmission else 1
        task = Task(
            room_id=room.id,
            creator_id=actor.id,
            title=data.title.strip(),
            description=data.description,
            instructions=data.instructions,
            difficulty=data.difficulty,
            starts_at=data.starts_at,
            due_at=data.due_at,
            max_score=data.max_score,
            allow_resubmission=data.allow_resubmission,
            max_attempts=max_attempts,
        )
        self.db.add(task)
        try:
            self.db.commit()
            self.db.refresh(task)
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("Task could not be created.") from None
        return task

    def list_for_room(self, actor: User, room_id: UUID, limit: int = 100) -> list[Task]:
        room = self._viewable_room(actor, room_id)
        query = select(Task).where(Task.room_id == room.id, Task.status != TaskStatus.ARCHIVED)
        if not self._is_manager(actor, room):
            query = query.where(Task.status.in_((TaskStatus.PUBLISHED, TaskStatus.CLOSED)))
        return list(self.db.scalars(query.order_by(Task.created_at.desc()).limit(limit)))

    def get(self, actor: User, task_id: UUID) -> Task:
        task = self.db.get(Task, task_id)
        if task is None or task.status == TaskStatus.ARCHIVED:
            raise NotFoundError("Task not found.")
        room = self._viewable_room(actor, task.room_id)
        if task.status == TaskStatus.DRAFT and not self._is_manager(actor, room):
            raise NotFoundError("Task not found.")
        return task

    def update(self, actor: User, task_id: UUID, data: TaskUpdate) -> Task:
        task = self._managed_task(actor, task_id)
        if task.status != TaskStatus.DRAFT:
            raise ConflictError("Only draft tasks can be edited.")
        values = data.model_dump(exclude_unset=True)
        for key in ("title", "difficulty", "max_score", "allow_resubmission"):
            if key in values and values[key] is None:
                raise ConflictError(f"{key} cannot be null.")
        if "title" in values and values["title"] is not None:
            values["title"] = values["title"].strip()
        if "starts_at" in values and "due_at" not in values:
            due_at = task.due_at
        else:
            due_at = values.get("due_at", task.due_at)
        starts_at = values.get("starts_at", task.starts_at)
        if starts_at and due_at and due_at < starts_at:
            raise ConflictError("due_at must not be earlier than starts_at.")
        if values.get("allow_resubmission") is False and values.get("max_attempts", task.max_attempts) not in (None, 1):
            raise ConflictError("max_attempts must be 1 when resubmission is disabled.")
        for key, value in values.items():
            setattr(task, key, value)
        if task.allow_resubmission and task.max_attempts is not None and task.max_attempts < 2:
            raise ConflictError("resubmission requires at least two attempts.")
        self.db.commit()
        self.db.refresh(task)
        return task

    def publish(self, actor: User, task_id: UUID) -> Task:
        task = self._managed_task(actor, task_id)
        if task.status != TaskStatus.DRAFT:
            raise ConflictError("Only draft tasks can be published.")
        task.status = TaskStatus.PUBLISHED
        self.db.commit()
        self.db.refresh(task)
        return task

    def close(self, actor: User, task_id: UUID) -> Task:
        task = self._managed_task(actor, task_id)
        if task.status != TaskStatus.PUBLISHED:
            raise ConflictError("Only published tasks can be closed.")
        task.status = TaskStatus.CLOSED
        self.db.commit()
        self.db.refresh(task)
        return task

    def archive(self, actor: User, task_id: UUID) -> None:
        task = self._managed_task(actor, task_id)
        if task.status == TaskStatus.ARCHIVED:
            raise ConflictError("Task is already archived.")
        task.status = TaskStatus.ARCHIVED
        self.db.commit()

    def _managed_task(self, actor: User, task_id: UUID) -> Task:
        task = self.db.get(Task, task_id)
        if task is None or task.status == TaskStatus.ARCHIVED:
            raise NotFoundError("Task not found.")
        self._manager_room(actor, task.room_id)
        return task

    def _viewable_room(self, actor: User, room_id: UUID) -> TechnicalRoom:
        room = self.db.get(TechnicalRoom, room_id)
        if room is None or room.is_archived:
            raise NotFoundError("Room not found.")
        member = self.db.scalar(select(RoomMembership).where(
            RoomMembership.room_id == room.id,
            RoomMembership.user_id == actor.id,
            RoomMembership.is_active.is_(True),
        ))
        if room.visibility.value == "PRIVATE" and member is None:
            raise NotFoundError("Room not found.")
        return room

    def _manager_room(self, actor: User, room_id: UUID) -> TechnicalRoom:
        room = self._viewable_room(actor, room_id)
        if not self._is_manager(actor, room):
            raise ForbiddenError("You cannot manage tasks in this room.")
        return room

    def _is_manager(self, actor: User, room: TechnicalRoom) -> bool:
        if room.owner_id == actor.id:
            return True
        if actor.role != UserRole.TEACHER:
            return False
        return self.db.scalar(select(RoomMembership.id).where(
            RoomMembership.room_id == room.id,
            RoomMembership.user_id == actor.id,
            RoomMembership.is_active.is_(True),
        )) is not None
