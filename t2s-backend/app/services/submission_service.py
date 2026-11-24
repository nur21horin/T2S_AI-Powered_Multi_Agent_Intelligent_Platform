from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import TaskStatus, UserRole
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.room import RoomMembership, TechnicalRoom
from app.models.submission import Submission
from app.models.task import Task
from app.models.user import User
from app.schemas.submission import SubmissionCreate


class SubmissionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, actor: User, task_id: UUID, data: SubmissionCreate) -> Submission:
        task = self._eligible_task(actor, task_id)
        task = self.db.scalar(select(Task).where(Task.id == task.id).with_for_update())
        latest = self.db.scalar(select(func.max(Submission.attempt_number)).where(Submission.task_id == task.id, Submission.user_id == actor.id)) or 0
        max_attempts = task.max_attempts or 1
        if latest >= max_attempts or not task.allow_resubmission and latest > 0:
            raise ConflictError("This task does not accept another submission.")
        submission = Submission(
            task_id=task.id,
            user_id=actor.id,
            content=data.content.strip(),
            repository_url=str(data.repository_url) if data.repository_url else None,
            project_url=str(data.project_url) if data.project_url else None,
            attempt_number=latest + 1,
            submitted_at=datetime.now(UTC),
        )
        self.db.add(submission)
        try:
            self.db.commit()
            self.db.refresh(submission)
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("Submission attempt was created concurrently.") from None
        return submission

    def own_for_task(self, actor: User, task_id: UUID, limit: int = 100) -> list[Submission]:
        self._eligible_task(actor, task_id, check_deadline=False)
        return list(self.db.scalars(select(Submission).where(Submission.task_id == task_id, Submission.user_id == actor.id).order_by(Submission.attempt_number.desc()).limit(limit)))

    def get(self, actor: User, submission_id: UUID) -> Submission:
        submission = self.db.get(Submission, submission_id)
        if submission is None:
            raise NotFoundError("Submission not found.")
        if submission.user_id == actor.id:
            self._eligible_task(actor, submission.task_id, check_deadline=False)
            return submission
        self._manager_for_task(actor, submission.task_id)
        return submission

    def for_review(self, actor: User, task_id: UUID, limit: int = 100) -> list[Submission]:
        self._manager_for_task(actor, task_id)
        return list(self.db.scalars(select(Submission).where(Submission.task_id == task_id).order_by(Submission.user_id, Submission.attempt_number.desc()).limit(limit)))

    def _eligible_task(self, actor: User, task_id: UUID, *, check_deadline: bool = True) -> Task:
        task = self.db.get(Task, task_id)
        if task is None or task.status in (TaskStatus.DRAFT, TaskStatus.ARCHIVED):
            raise NotFoundError("Task not found.")
        room = self.db.get(TechnicalRoom, task.room_id)
        if room is None or room.is_archived:
            raise NotFoundError("Task not found.")
        member = self.db.scalar(select(RoomMembership.id).where(
            RoomMembership.room_id == room.id,
            RoomMembership.user_id == actor.id,
            RoomMembership.is_active.is_(True),
        ))
        if member is None:
            raise ForbiddenError("Room membership is required for submissions.")
        now = datetime.now(UTC)
        if task.status != TaskStatus.PUBLISHED and check_deadline:
            raise ConflictError("This task is closed to submissions.")
        if check_deadline and task.starts_at and now < task.starts_at:
            raise ConflictError("This task is not open yet.")
        if check_deadline and task.due_at and now > task.due_at:
            raise ConflictError("The submission deadline has passed.")
        return task

    def _manager_for_task(self, actor: User, task_id: UUID) -> Task:
        task = self.db.get(Task, task_id)
        if task is None or task.status == TaskStatus.ARCHIVED:
            raise NotFoundError("Task not found.")
        room = self.db.get(TechnicalRoom, task.room_id)
        if room is None or room.is_archived:
            raise NotFoundError("Task not found.")
        if room.owner_id == actor.id:
            return task
        if actor.role != UserRole.TEACHER or self.db.scalar(select(RoomMembership.id).where(
            RoomMembership.room_id == room.id,
            RoomMembership.user_id == actor.id,
            RoomMembership.is_active.is_(True),
        )) is None:
            raise ForbiddenError()
        return task
