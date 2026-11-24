from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import EvaluationStatus, SubmissionStatus
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.evaluation import Evaluation
from app.models.submission import Submission
from app.models.task import Task
from app.models.user import User
from app.services.submission_service import SubmissionService
from app.schemas.evaluation import EvaluationCreate


class EvaluationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def save(self, actor: User, submission_id: UUID, data: EvaluationCreate) -> Evaluation:
        submission = self.db.scalar(select(Submission).where(Submission.id == submission_id).with_for_update())
        if submission is None:
            raise NotFoundError("Submission not found.")
        if submission.user_id == actor.id:
            raise ForbiddenError("You cannot evaluate your own submission.")
        task = SubmissionService(self.db)._manager_for_task(actor, submission.task_id)
        if data.score > task.max_score:
            raise ConflictError("Score cannot exceed the task maximum score.")
        evaluation = self.db.scalar(select(Evaluation).where(Evaluation.submission_id == submission.id).with_for_update())
        if evaluation is None:
            evaluation = Evaluation(submission_id=submission.id, evaluator_id=actor.id, score=data.score, feedback=data.feedback, status=data.status, evaluated_at=datetime.now(UTC))
            self.db.add(evaluation)
        else:
            evaluation.evaluator_id = actor.id
            evaluation.score = data.score
            evaluation.feedback = data.feedback
            evaluation.status = data.status
            evaluation.evaluated_at = datetime.now(UTC)
        submission.status = SubmissionStatus.EVALUATED if data.status == EvaluationStatus.FINALIZED else SubmissionStatus.RETURNED
        self.db.commit()
        self.db.refresh(evaluation)
        return evaluation

    def get(self, actor: User, submission_id: UUID) -> Evaluation:
        evaluation = self.db.scalar(select(Evaluation).where(Evaluation.submission_id == submission_id))
        if evaluation is None:
            raise NotFoundError("Evaluation not found.")
        submission = self.db.get(Submission, submission_id)
        if submission is None:
            raise NotFoundError("Submission not found.")
        if submission.user_id != actor.id:
            SubmissionService(self.db)._manager_for_task(actor, submission.task_id)
        return evaluation
