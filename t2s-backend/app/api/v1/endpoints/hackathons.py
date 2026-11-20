from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.enums import HackathonParticipationMode, HackathonRegistrationStatus, HackathonStatus
from app.models.hackathon import HackathonRegistration, HackathonRegistrationMember
from app.models.user import User
from app.schemas.hackathon import HackathonCreate, HackathonRead, HackathonUpdate, RegistrationDetail, RegistrationRead, TeamRegistrationCreate
from app.services.hackathon_service import HackathonService
from app.utils.pagination import Pagination, pagination_params

router = APIRouter(prefix="/hackathons", tags=["hackathons"])


@router.post("", response_model=HackathonRead, status_code=status.HTTP_201_CREATED)
def create_hackathon(data: HackathonCreate, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return HackathonService(db).create(user, data)


@router.get("", response_model=list[HackathonRead])
def list_hackathons(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)], page: Annotated[Pagination, Depends(pagination_params)], hackathon_status: HackathonStatus | None = Query(default=None, alias="status"), participation_mode: HackathonParticipationMode | None = None):
    return HackathonService(db).list(user, page, hackathon_status, participation_mode)


@router.get("/{hackathon_id}", response_model=HackathonRead)
def get_hackathon(hackathon_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return HackathonService(db).get(user, hackathon_id)


@router.patch("/{hackathon_id}", response_model=HackathonRead)
def update_hackathon(hackathon_id: UUID, data: HackathonUpdate, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return HackathonService(db).update(user, hackathon_id, data)


def _transition(target: HackathonStatus):
    def endpoint(hackathon_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
        return HackathonService(db).transition(user, hackathon_id, target)
    return endpoint


router.add_api_route("/{hackathon_id}/publish", _transition(HackathonStatus.PUBLISHED), methods=["POST"], response_model=HackathonRead)
router.add_api_route("/{hackathon_id}/open", _transition(HackathonStatus.OPEN), methods=["POST"], response_model=HackathonRead)
router.add_api_route("/{hackathon_id}/close", _transition(HackathonStatus.CLOSED), methods=["POST"], response_model=HackathonRead)
router.add_api_route("/{hackathon_id}/complete", _transition(HackathonStatus.COMPLETED), methods=["POST"], response_model=HackathonRead)
router.add_api_route("/{hackathon_id}/archive", _transition(HackathonStatus.ARCHIVED), methods=["POST"], response_model=HackathonRead)


@router.post("/{hackathon_id}/registrations/individual", response_model=RegistrationRead, status_code=status.HTTP_201_CREATED)
def register_individual(hackathon_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return HackathonService(db).register_individual(user, hackathon_id)


@router.post("/{hackathon_id}/registrations/team", response_model=RegistrationRead, status_code=status.HTTP_201_CREATED)
def register_team(hackathon_id: UUID, data: TeamRegistrationCreate, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return HackathonService(db).register_team(user, hackathon_id, data.team_id)


@router.get("/{hackathon_id}/registrations/me", response_model=list[RegistrationRead])
def my_hackathon_registrations(hackathon_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)], page: Annotated[Pagination, Depends(pagination_params)]):
    return HackathonService(db).mine(user, hackathon_id, page)


@router.get("/{hackathon_id}/registrations", response_model=list[RegistrationRead])
def list_registrations(hackathon_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)], page: Annotated[Pagination, Depends(pagination_params)], registration_status: HackathonRegistrationStatus | None = Query(default=None, alias="status")):
    return HackathonService(db).registrations(user, hackathon_id, page, registration_status)


registrations_router = APIRouter(prefix="/hackathon-registrations", tags=["hackathon registrations"])


@registrations_router.get("/me", response_model=list[RegistrationRead])
def my_registrations(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)], page: Annotated[Pagination, Depends(pagination_params)]):
    query = select(HackathonRegistration).join(HackathonRegistrationMember).where(HackathonRegistrationMember.user_id == user.id, HackathonRegistration.status.in_((HackathonRegistrationStatus.PENDING, HackathonRegistrationStatus.APPROVED))).order_by(HackathonRegistration.registered_at.desc()).offset(page.offset).limit(page.limit)
    return list(db.scalars(query))


@registrations_router.get("/{registration_id}", response_model=RegistrationDetail)
def get_registration(registration_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return HackathonService(db).get_registration(user, registration_id)


@registrations_router.post("/{registration_id}/cancel", response_model=RegistrationRead)
def cancel_registration(registration_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return HackathonService(db).cancel(user, registration_id)


@registrations_router.post("/{registration_id}/approve", response_model=RegistrationRead)
def approve_registration(registration_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return HackathonService(db).review(user, registration_id, True)


@registrations_router.post("/{registration_id}/reject", response_model=RegistrationRead)
def reject_registration(registration_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return HackathonService(db).review(user, registration_id, False)
