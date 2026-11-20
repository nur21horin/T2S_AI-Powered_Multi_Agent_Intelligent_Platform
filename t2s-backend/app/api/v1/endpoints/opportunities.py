from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.enums import OpportunityType
from app.models.user import User
from app.schemas.opportunity import OpportunityApplicationCreate, OpportunityApplicationRead, OpportunityApplicationReview, OpportunityCreate, OpportunityRead, OpportunityUpdate
from app.services.opportunity_service import OpportunityService
from app.utils.pagination import Pagination, pagination_params


router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.post("", response_model=OpportunityRead, status_code=status.HTTP_201_CREATED)
def create_opportunity(data: OpportunityCreate, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return OpportunityService(db).create(user, data)


@router.get("", response_model=list[OpportunityRead])
def list_opportunities(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)], page: Annotated[Pagination, Depends(pagination_params)], opportunity_type: OpportunityType | None = None):
    return OpportunityService(db).list_public(user, page, opportunity_type)


@router.get("/owned", response_model=list[OpportunityRead])
def owned_opportunities(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)], page: Annotated[Pagination, Depends(pagination_params)]):
    return OpportunityService(db).list_owned(user, page)


@router.get("/applications/me", response_model=list[OpportunityApplicationRead])
def my_applications(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)], page: Annotated[Pagination, Depends(pagination_params)]):
    return OpportunityService(db).list_my_applications(user, page)


@router.get("/{opportunity_id}", response_model=OpportunityRead)
def get_opportunity(opportunity_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return OpportunityService(db).get(user, opportunity_id)


@router.patch("/{opportunity_id}", response_model=OpportunityRead)
def update_opportunity(opportunity_id: UUID, data: OpportunityUpdate, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return OpportunityService(db).update(user, opportunity_id, data)


@router.post("/{opportunity_id}/publish", response_model=OpportunityRead)
def publish_opportunity(opportunity_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return OpportunityService(db).publish(user, opportunity_id)


@router.post("/{opportunity_id}/close", response_model=OpportunityRead)
def close_opportunity(opportunity_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return OpportunityService(db).close(user, opportunity_id)


@router.post("/{opportunity_id}/archive", status_code=status.HTTP_204_NO_CONTENT)
def archive_opportunity(opportunity_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    OpportunityService(db).archive(user, opportunity_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{opportunity_id}/applications", response_model=OpportunityApplicationRead, status_code=status.HTTP_201_CREATED)
def apply_to_opportunity(opportunity_id: UUID, data: OpportunityApplicationCreate, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return OpportunityService(db).apply(user, opportunity_id, data)


@router.get("/{opportunity_id}/applications", response_model=list[OpportunityApplicationRead])
def list_opportunity_applications(opportunity_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)], page: Annotated[Pagination, Depends(pagination_params)]):
    return OpportunityService(db).list_applications(user, opportunity_id, page)


@router.post("/applications/{application_id}/review", response_model=OpportunityApplicationRead)
def review_opportunity_application(application_id: UUID, data: OpportunityApplicationReview, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return OpportunityService(db).review_application(user, application_id, data)


@router.post("/applications/{application_id}/withdraw", response_model=OpportunityApplicationRead)
def withdraw_opportunity_application(application_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return OpportunityService(db).withdraw_application(user, application_id)
