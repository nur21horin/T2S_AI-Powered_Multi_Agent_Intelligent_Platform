from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.enums import AuthTokenPurpose
from app.models.auth_token import AuthToken


class TokenRepository:
    def get_by_hash(self, db: Session, token_hash: str) -> AuthToken | None:
        return db.scalar(select(AuthToken).where(AuthToken.token_hash == token_hash))

    def add(self, db: Session, token: AuthToken) -> AuthToken:
        db.add(token)
        db.flush()
        return token

    def consume_refresh(self, db: Session, token_id: UUID, now: datetime) -> bool:
        result = db.execute(
            update(AuthToken)
            .where(
                AuthToken.id == token_id,
                AuthToken.purpose == AuthTokenPurpose.REFRESH,
                AuthToken.consumed_at.is_(None),
                AuthToken.revoked_at.is_(None),
                AuthToken.expires_at > now,
            )
            .values(consumed_at=now)
            .returning(AuthToken.id)
        )
        return result.scalar_one_or_none() is not None

    def consume_one_time(
        self,
        db: Session,
        token_id: UUID,
        purpose: AuthTokenPurpose,
        now: datetime,
    ) -> bool:
        result = db.execute(
            update(AuthToken)
            .where(
                AuthToken.id == token_id,
                AuthToken.purpose == purpose,
                AuthToken.consumed_at.is_(None),
                AuthToken.revoked_at.is_(None),
                AuthToken.expires_at > now,
            )
            .values(consumed_at=now)
            .returning(AuthToken.id)
        )
        return result.scalar_one_or_none() is not None

    def revoke_family(self, db: Session, family_id: UUID, now: datetime) -> None:
        db.execute(
            update(AuthToken)
            .where(
                AuthToken.family_id == family_id,
                AuthToken.purpose == AuthTokenPurpose.REFRESH,
                AuthToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )

    def revoke_user_refresh_tokens(self, db: Session, user_id: UUID, now: datetime) -> None:
        db.execute(
            update(AuthToken)
            .where(
                AuthToken.user_id == user_id,
                AuthToken.purpose == AuthTokenPurpose.REFRESH,
                AuthToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
