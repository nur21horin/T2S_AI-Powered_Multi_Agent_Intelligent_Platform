from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.hackathon_submission import HackathonSubmissionCreate, HackathonSubmissionRead, HackathonSubmissionUpdate
from app.services.hackathon_submission_service import HackathonSubmissionService
from app.utils.pagination import Pagination, pagination_params


router = APIRouter(tags=["hackathon submissions"])


@router.post("/hackathons/{hackathon_id}/submissions", response_model=HackathonSubmissionRead, status_code=status.HTTP_201_CREATED)
def create_submission(hackathon_id: UUID, data: HackathonSubmissionCreate, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return HackathonSubmissionService(db).create(user, hackathon_id, data)


@router.get("/hackathons/{hackathon_id}/submissions", response_model=list[HackathonSubmissionRead])
def list_hackathon_submissions(hackathon_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)], page: Annotated[Pagination, Depends(pagination_params)]):
    return HackathonSubmissionService(db).list_for_hackathon(user, hackathon_id, page)


@router.get("/hackathon-submissions/me", response_model=list[HackathonSubmissionRead])
def list_my_submissions(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)], page: Annotated[Pagination, Depends(pagination_params)]):
    return HackathonSubmissionService(db).list_mine(user, page)


@router.get("/projects/{project_id}/hackathon-submissions", response_model=list[HackathonSubmissionRead])
def list_project_submissions(project_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)], page: Annotated[Pagination, Depends(pagination_params)]):
    return HackathonSubmissionService(db).list_for_project(user, project_id, page)


@router.get("/hackathon-submissions/{submission_id}", response_model=HackathonSubmissionRead)
def get_submission(submission_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return HackathonSubmissionService(db).get(user, submission_id)


@router.patch("/hackathon-submissions/{submission_id}", response_model=HackathonSubmissionRead)
def update_submission(submission_id: UUID, data: HackathonSubmissionUpdate, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return HackathonSubmissionService(db).update(user, submission_id, data)


@router.post("/hackathon-submissions/{submission_id}/finalize", response_model=HackathonSubmissionRead)
def finalize_submission(submission_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return HackathonSubmissionService(db).finalize(user, submission_id)


@router.post("/hackathon-submissions/{submission_id}/withdraw", response_model=HackathonSubmissionRead)
def withdraw_submission(submission_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return HackathonSubmissionService(db).withdraw(user, submission_id)
