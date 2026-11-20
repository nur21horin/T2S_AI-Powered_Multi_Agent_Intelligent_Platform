from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.profile import NamedItemRead, NamedItemsUpdate, ProfileRead, ProfileUpdate
from app.security.permissions import Permission, require_permission
from app.services.profile_service import ProfileService
from app.services.skill_service import SkillService

router = APIRouter(prefix="/profiles", tags=["profiles"])


def _profile_response(profile, kind: str, *, public: bool = False) -> dict:
    data = {column.name: getattr(profile, column.name) for column in profile.__table__.columns}
    if public:
        allowed = {"id", "user_id", "created_at", "updated_at", "department", "bio", "introduction", "areas_of_expertise", "research_interests", "current_professional_field"}
        data = {key: value for key, value in data.items() if key in allowed}
    data["profile_type"] = kind
    data["user_id"] = str(data["user_id"])
    return data


@router.get("/me", response_model=ProfileRead)
def get_my_profile(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    profile, kind = ProfileService(db).get(user)
    return _profile_response(profile, kind)


@router.put("/me", response_model=ProfileRead, status_code=status.HTTP_200_OK)
def save_my_profile(
    data: ProfileUpdate,
    user: Annotated[User, Depends(require_permission(Permission.MANAGE_OWN_PROFILE))],
    db: Annotated[Session, Depends(get_db)],
):
    profile, kind = ProfileService(db).save(user, data)
    return _profile_response(profile, kind)


@router.get("/{user_id}", response_model=ProfileRead)
def get_profile(user_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    profile, kind = ProfileService(db).get(user, user_id)
    return _profile_response(profile, kind, public=user_id != user.id)


@router.put("/me/skills", response_model=list[NamedItemRead])
def add_skills(data: NamedItemsUpdate, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return SkillService(db).set_skills(user, data.names)


@router.delete("/me/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_skill(skill_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    SkillService(db).remove_skill(user, skill_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/me/interests", response_model=list[NamedItemRead])
def add_interests(data: NamedItemsUpdate, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    return SkillService(db).set_interests(user, data.names)


@router.delete("/me/interests/{interest_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_interest(interest_id: UUID, user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]):
    SkillService(db).remove_interest(user, interest_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
