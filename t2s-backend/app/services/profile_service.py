from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.models.profile import AlumniProfile, StudentProfile, TeacherProfile
from app.models.user import User
from app.schemas.profile import ProfileUpdate


_PROFILE_TYPES = {
    UserRole.STUDENT: (StudentProfile, "student"),
    UserRole.TEACHER: (TeacherProfile, "teacher"),
    UserRole.ALUMNI: (AlumniProfile, "alumni"),
}


class ProfileService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user: User, target_id: UUID | None = None):
        target = user if target_id is None else self.db.get(User, target_id)
        if target is None or not target.is_active:
            raise NotFoundError("Profile not found.")
        model_type = _PROFILE_TYPES.get(target.role)
        if model_type is None:
            raise NotFoundError("Profile not found.")
        profile = self.db.scalar(select(model_type[0]).where(model_type[0].user_id == target.id))
        if profile is None:
            raise NotFoundError("Profile has not been created.")
        if target_id is not None and target.id != user.id and target.role == UserRole.ADMIN:
            raise NotFoundError("Profile not found.")
        return profile, model_type[1]

    def save(self, user: User, data: ProfileUpdate):
        model_type = _PROFILE_TYPES.get(user.role)
        if model_type is None:
            raise ForbiddenError("This role cannot create a profile.")
        profile = self.db.scalar(select(model_type[0]).where(model_type[0].user_id == user.id))
        values = data.model_dump(exclude_unset=True)
        allowed = set(model_type[0].__table__.columns.keys())
        disallowed = set(values) - allowed
        if disallowed:
            raise BadRequestError("Fields are not valid for this role.")
        values = {key: value for key, value in values.items() if key in allowed}
        try:
            if profile is None:
                profile = model_type[0](user_id=user.id, **values)
                self.db.add(profile)
            else:
                for key, value in values.items():
                    setattr(profile, key, value)
            self.db.commit()
            self.db.refresh(profile)
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("A profile already exists for this account.") from None
        return profile, model_type[1]
