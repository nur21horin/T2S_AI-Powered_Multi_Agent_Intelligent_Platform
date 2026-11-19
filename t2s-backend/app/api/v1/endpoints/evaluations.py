from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.evaluation import EvaluationCreate, EvaluationRead
from app.services.evaluation_service import EvaluationService


router = APIRouter(tags=["evaluations"])


@router.put("/submissions/{submission_id}/evaluation", response_model=EvaluationRead)
def evaluate_submission(submission_id: UUID, data: EvaluationCreate, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return EvaluationService(db).save(user, submission_id, data)


@router.get("/submissions/{submission_id}/evaluation", response_model=EvaluationRead)
def get_evaluation(submission_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return EvaluationService(db).get(user, submission_id)
