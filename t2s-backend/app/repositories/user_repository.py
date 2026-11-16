from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def get_by_id(self, db: Session, user_id: UUID) -> User | None:
        return db.get(User, user_id)

    def get_by_email(self, db: Session, email: str) -> User | None:
        return db.scalar(select(User).where(User.email == email))

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
