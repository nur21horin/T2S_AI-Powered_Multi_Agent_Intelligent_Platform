from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import EvaluationStatus, TaskStatus, UserRole
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.evaluation import Evaluation
from app.models.room import RoomMembership, TechnicalRoom
from app.models.submission import Submission
from app.models.task import Task
from app.models.user import User
from app.schemas.progress import ProgressRead


class ProgressService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def personal(self, actor: User, room_id: UUID | None = None) -> ProgressRead:
        return self._calculate(actor, actor.id, room_id)

    def for_user(self, actor: User, room_id: UUID, user_id: UUID) -> ProgressRead:
        room = self.db.get(TechnicalRoom, room_id)
        if room is None or room.is_archived:
            raise NotFoundError("Room not found.")
        if user_id != actor.id and not self._is_manager(actor, room):
            raise ForbiddenError()
        if self.db.get(User, user_id) is None:
            raise NotFoundError("User not found.")
        if self.db.scalar(select(RoomMembership.id).where(RoomMembership.room_id == room_id, RoomMembership.user_id == user_id, RoomMembership.is_active.is_(True))) is None:
            raise NotFoundError("Room membership not found.")
        return self._calculate(actor, user_id, room_id)

    def _calculate(self, actor: User, user_id: UUID, room_id: UUID | None) -> ProgressRead:
        if room_id is not None:
            room = self.db.get(TechnicalRoom, room_id)
            if room is None or room.is_archived:
                raise NotFoundError("Room not found.")
            if self.db.scalar(select(RoomMembership.id).where(RoomMembership.room_id == room_id, RoomMembership.user_id == user_id, RoomMembership.is_active.is_(True))) is None:
                raise ForbiddenError("Room membership is required for progress.")
            rooms = [room]
        else:
            rooms = list(self.db.scalars(select(TechnicalRoom).join(RoomMembership).where(RoomMembership.user_id == user_id, RoomMembership.is_active.is_(True), TechnicalRoom.is_archived.is_(False)).distinct()))
        room_ids = [room.id for room in rooms]
        now = datetime.now(UTC)
        tasks = list(self.db.scalars(select(Task).where(Task.room_id.in_(room_ids), Task.status.in_((TaskStatus.PUBLISHED, TaskStatus.CLOSED)), Task.status != TaskStatus.ARCHIVED, (Task.starts_at.is_(None) | (Task.starts_at <= now))))) if room_ids else []
        task_ids = [task.id for task in tasks]
        submissions = list(self.db.scalars(select(Submission).where(Submission.user_id == user_id, Submission.task_id.in_(task_ids)).order_by(Submission.attempt_number.desc()))) if task_ids else []
        latest: dict[UUID, Submission] = {}
        for submission in submissions:
            latest.setdefault(submission.task_id, submission)
        evaluations = {evaluation.submission_id: evaluation for evaluation in self.db.scalars(select(Evaluation).where(Evaluation.submission_id.in_([s.id for s in latest.values()]))) } if latest else {}
        completed = awaiting = evaluated = finalized = earned = possible = 0
        for task in tasks:
            possible += task.max_score
            submission = latest.get(task.id)
            evaluation = evaluations.get(submission.id) if submission else None
            if evaluation is None:
                if submission:
                    awaiting += 1
                continue
            evaluated += 1
            if evaluation.status == EvaluationStatus.FINALIZED:
                completed += 1
                finalized += 1
                earned += evaluation.score
            else:
                awaiting += 1
        average = (earned / finalized) if finalized else None
        percentage = (completed / len(tasks) * 100) if tasks else 0.0
        return ProgressRead(user_id=user_id, room_id=room_id, total_tasks=len(tasks), completed_tasks=completed, pending_tasks=len(tasks) - completed - awaiting, awaiting_review=awaiting, evaluated_tasks=evaluated, average_score=average, total_earned_score=earned, total_possible_score=possible, completion_percentage=round(percentage, 2))

    def _is_manager(self, actor: User, room: TechnicalRoom) -> bool:
        if room.owner_id == actor.id:
            return True
        return actor.role == UserRole.TEACHER and self.db.scalar(select(RoomMembership.id).where(RoomMembership.room_id == room.id, RoomMembership.user_id == actor.id, RoomMembership.is_active.is_(True))) is not None
