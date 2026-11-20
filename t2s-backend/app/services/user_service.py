"""User administration operations with transactional authorization safeguards."""
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest
from app.security.passwords import hash_password
from app.services.audit_service import record_privileged_action


class UserService:
    def __init__(self, db: Session, users: UserRepository | None = None) -> None:
        self.db = db
        self.users = users or UserRepository()

    def assign_role(self, actor_id: UUID, target_id: UUID, role: UserRole) -> User:
        if not isinstance(role, UserRole):
            raise ValueError("role must be a UserRole")
        try:
            self.users.lock_admin_state(self.db)
            actor = self.users.get_by_id_for_update(self.db, actor_id)
            if (
                actor is None
                or actor.role != UserRole.ADMIN
                or not actor.is_active
                or not actor.is_verified
            ):
                raise ForbiddenError()
            if actor_id == target_id:
                raise ForbiddenError("Administrators cannot change their own role.")

            target = self.users.get_by_id_for_update(self.db, target_id)
            if target is None:
                raise NotFoundError("User not found.")
            old_role = target.role
            if (
                target.role == UserRole.ADMIN
                and target.is_active
                and role != UserRole.ADMIN
                and self.users.count_active_administrators(self.db) <= 1
            ):
                raise ConflictError("The final active administrator cannot be demoted.")

            if target.role == role:
                self.db.commit()
                return target

            target.role = role
            self.db.flush()
            self.users.increment_auth_version(self.db, target)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        record_privileged_action(
            action="admin.user_role.changed",
            actor_id=actor_id,
            target_id=target_id,
            old_role=old_role.value,
            new_role=role.value,
        )
        return target

    def bootstrap_initial_admin(self, data: RegisterRequest) -> User:
        """Create the first administrator once, serialized across all workers."""
        try:
            self.users.lock_admin_state(self.db)
            if self.users.count_administrators(self.db) > 0:
                raise ConflictError("Administrator bootstrap has already been completed.")
            if self.users.get_by_email(self.db, str(data.email)) is not None:
                raise ConflictError("An account with this email already exists.")

            user = User(
                email=str(data.email).lower(),
                full_name=data.full_name,
                password_hash=hash_password(data.password),
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
            )
            self.users.add(self.db, user)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("An account with this email already exists.") from None
        except Exception:
            self.db.rollback()
            raise

        record_privileged_action(
            action="admin.bootstrap.created",
            actor_id=None,
            target_id=user.id,
        )
        return user
