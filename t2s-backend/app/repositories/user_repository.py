from uuid import UUID

from sqlalchemy import func, select, text, update
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.models.user import User

ADMIN_STATE_ADVISORY_LOCK_KEY = 0x54525341444D494E


class UserRepository:
    def get_by_id(self, db: Session, user_id: UUID) -> User | None:
        return db.get(User, user_id)

    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.scalar(select(User).where(User.email == email))

    def get_by_id_for_update(self, db: Session, user_id: UUID) -> User | None:
        return db.scalar(select(User).where(User.id == user_id).with_for_update())

    def lock_admin_state(self, db: Session) -> None:
        """Serialize role/bootstrap changes across application processes."""
        db.execute(
            text("SELECT pg_advisory_xact_lock(:lock_key)"),
            {"lock_key": ADMIN_STATE_ADVISORY_LOCK_KEY},
        )

    def count_active_administrators(self, db: Session) -> int:
        return int(
            db.scalar(
                select(func.count())
                .select_from(User)
                .where(User.role == UserRole.ADMIN, User.is_active.is_(True))
            )
            or 0
        )

    def count_administrators(self, db: Session) -> int:
        """Count all administrator accounts, including inactive accounts."""
        return int(
            db.scalar(
                select(func.count())
                .select_from(User)
                .where(User.role == UserRole.ADMIN)
            )
            or 0
        )

    def add(self, db: Session, user: User) -> User:
        db.add(user)
        db.flush()
        return user

    def increment_auth_version(self, db: Session, user: User) -> int:
        """Atomically increment a user's token version in the current transaction."""
        version = db.execute(
            update(User)
            .where(User.id == user.id)
            .values(auth_version=User.auth_version + 1)
            .returning(User.auth_version)
            .execution_options(synchronize_session=False)
        ).scalar_one()
        # Keep the ORM attribute expired so a later flush cannot overwrite the
        # database-side increment with a value read before a concurrent update.
        db.expire(user, ["auth_version"])
        return version
