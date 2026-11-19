from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.submission import SubmissionCreate, SubmissionRead
from app.services.submission_service import SubmissionService


router = APIRouter(tags=["submissions"])


@router.post("/tasks/{task_id}/submissions", response_model=SubmissionRead, status_code=201)
def submit_task(task_id: UUID, data: SubmissionCreate, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return SubmissionService(db).create(user, task_id, data)


@router.get("/tasks/{task_id}/submissions/mine", response_model=list[SubmissionRead])
def own_task_submissions(task_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)], limit: int = Query(default=100, ge=1, le=100)):
    return SubmissionService(db).own_for_task(user, task_id, limit)


@router.get("/tasks/{task_id}/submissions", response_model=list[SubmissionRead])
def review_task_submissions(task_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)], limit: int = Query(default=100, ge=1, le=100)):
    return SubmissionService(db).for_review(user, task_id, limit)


@router.get("/submissions/{submission_id}", response_model=SubmissionRead)
def get_submission(submission_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return SubmissionService(db).get(user, submission_id)
