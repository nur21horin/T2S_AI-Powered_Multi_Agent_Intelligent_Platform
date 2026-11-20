from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.enums import AuthTokenPurpose, UserRole
from app.core.exceptions import ConflictError, UnauthorizedError, ServiceUnavailableError
from app.models.auth_token import AuthToken
from app.models.user import User
from app.repositories.token_repository import TokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterRequest
from app.security.passwords import hash_password, password_hash_needs_rehash, verify_password
from app.security.revocation import RedisRevocationStore, revoke_access_token
from app.security.tokens import (
    InvalidAccessToken,
    create_access_token,
    decode_access_token_for_logout,
    generate_opaque_token,
    hash_opaque_token,
)
from app.security.csrf import is_valid_csrf_token
from app.services.email_service import EmailSender


class AuthService:
    def __init__(
        self,
        db: Session,
        settings: Settings,
        email_sender: EmailSender,
        users: UserRepository | None = None,
        tokens: TokenRepository | None = None,
    ) -> None:
        self.db = db
        self.settings = settings
        self.email_sender = email_sender
        self.users = users or UserRepository()
        self.tokens = tokens or TokenRepository()

    def register(self, data: RegisterRequest) -> User:
        self._require_email_delivery()
        user = User(
            email=str(data.email).lower(),
            full_name=data.full_name,
            password_hash=hash_password(data.password),
            role=UserRole.STUDENT,
            is_active=True,
            is_verified=False,
        )
        try:
            self.users.add(self.db, user)
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("An account with this email already exists.") from None

        raw_token = self._create_one_time_token(
            user, AuthTokenPurpose.EMAIL_VERIFICATION, self.settings.email_token_expire_minutes
        )
        try:
            self.email_sender.send_verification(user.email, raw_token)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return user

    def login(self, email: str, password: str) -> tuple[User, str, str]:
        self._signing_secret()
        user = self.users.get_by_email(self.db, email.lower())
        if user is None:
            # Spend comparable Argon2 work for unknown accounts to reduce timing-based discovery.
            hash_password(password)
            raise UnauthorizedError("Invalid email or password.")
        if not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password.")
        if not user.is_active or not user.is_verified:
            raise UnauthorizedError("Invalid email or password.")
        if password_hash_needs_rehash(user.password_hash):
            user.password_hash = hash_password(password)
        access_token = create_access_token(user.id, self.settings, user.auth_version)
        raw_refresh, _ = self._new_refresh_token(user.id)
        self.db.commit()
        return user, access_token, raw_refresh

    def refresh(self, raw_refresh: str | None) -> tuple[User, str, str]:
        self._signing_secret()
        if not raw_refresh:
            raise UnauthorizedError("Authentication required.")
        token = self.tokens.get_by_hash(self.db, hash_opaque_token(raw_refresh))
        if token is None or token.purpose != AuthTokenPurpose.REFRESH or token.family_id is None:
            raise UnauthorizedError("Authentication required.")

        now = datetime.now(UTC)
        user = self.users.get_by_id(self.db, token.user_id)
        if user is None or not user.is_active or not user.is_verified:
            self.tokens.revoke_family(self.db, token.family_id, now)
            self.db.commit()
            raise UnauthorizedError("Authentication required.")

        if not self.tokens.consume_refresh(self.db, token.id, now):
            # Reuse, revocation, and expiry all invalidate the entire rotation family.
            self.tokens.revoke_family(self.db, token.family_id, now)
            self.db.commit()
            raise UnauthorizedError("Authentication required.")

        access_token = create_access_token(user.id, self.settings, user.auth_version)
        raw_next, _ = self._new_refresh_token(user.id, family_id=token.family_id)
        self.db.commit()
        return user, access_token, raw_next

    def logout(
        self,
        raw_refresh: str | None,
        access_token: str | None = None,
        revocation_store: RedisRevocationStore | None = None,
    ) -> None:
        claims = None
        if access_token:
            try:
                claims = decode_access_token_for_logout(access_token, self.settings)
            except InvalidAccessToken:
                # Invalid and expired access tokens cannot authenticate later requests.
                claims = None

        if claims is not None and claims.expires_at > datetime.now(UTC):
            if revocation_store is None:
                raise ServiceUnavailableError("Token revocation service is unavailable.")
            # Revoke the presented access token first. Redis and PostgreSQL do not
            # share a transaction, so this makes Redis outages leave refresh state
            # untouched; retries repeat this write idempotently.
            revoke_access_token(revocation_store, claims)

        if raw_refresh:
            try:
                # get_by_hash deliberately includes consumed/revoked rows. Their
                # family_id remains available for safe retries of this operation.
                token = self.tokens.get_by_hash(self.db, hash_opaque_token(raw_refresh))
                if token and token.purpose == AuthTokenPurpose.REFRESH and token.family_id:
                    self.tokens.revoke_family(self.db, token.family_id, datetime.now(UTC))
                self.db.commit()
            except SQLAlchemyError as exc:
                self.db.rollback()
                raise ServiceUnavailableError(
                    "Logout could not be completed. Retry the request."
                ) from exc

    def current_csrf_token(self, raw_refresh: str | None, csrf_token: str | None) -> str:
        if not raw_refresh or not csrf_token or not is_valid_csrf_token(
            csrf_token, self._signing_secret()
        ):
            raise UnauthorizedError("Authentication required.")
        token = self.tokens.get_by_hash(self.db, hash_opaque_token(raw_refresh))
        now = datetime.now(UTC)
        if (
            token is None
            or token.purpose != AuthTokenPurpose.REFRESH
            or token.consumed_at is not None
            or token.revoked_at is not None
            or token.expires_at <= now
        ):
            raise UnauthorizedError("Authentication required.")
        user = self.users.get_by_id(self.db, token.user_id)
        if user is None or not user.is_active or not user.is_verified:
            raise UnauthorizedError("Authentication required.")
        return csrf_token

    def request_email_verification(self, email: str) -> None:
        self._require_email_delivery()
        user = self.users.get_by_email(self.db, email.lower())
        if user is None or not user.is_active or user.is_verified:
            return
        raw_token = self._create_one_time_token(
            user, AuthTokenPurpose.EMAIL_VERIFICATION, self.settings.email_token_expire_minutes
        )
        try:
            self.email_sender.send_verification(user.email, raw_token)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def verify_email(self, raw_token: str) -> None:
        token = self._get_valid_one_time_token(raw_token, AuthTokenPurpose.EMAIL_VERIFICATION)
        now = datetime.now(UTC)
        if not self.tokens.consume_one_time(
            self.db, token.id, AuthTokenPurpose.EMAIL_VERIFICATION, now
        ):
            self.db.rollback()
            raise UnauthorizedError("Verification link is invalid or expired.")
        user = self.users.get_by_id(self.db, token.user_id)
        if user is None or not user.is_active:
            self.db.rollback()
            raise UnauthorizedError("Verification link is invalid or expired.")
        user.is_verified = True
        self.db.commit()

    def request_password_reset(self, email: str) -> None:
        self._require_email_delivery()
        user = self.users.get_by_email(self.db, email.lower())
        if user is None or not user.is_active:
            return
        raw_token = self._create_one_time_token(
            user,
            AuthTokenPurpose.PASSWORD_RESET,
            self.settings.password_reset_token_expire_minutes,
        )
        try:
            self.email_sender.send_password_reset(user.email, raw_token)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def reset_password(self, raw_token: str, new_password: str) -> None:
        token = self._get_valid_one_time_token(raw_token, AuthTokenPurpose.PASSWORD_RESET)
        now = datetime.now(UTC)
        if not self.tokens.consume_one_time(
            self.db, token.id, AuthTokenPurpose.PASSWORD_RESET, now
        ):
            self.db.rollback()
            raise UnauthorizedError("Password reset link is invalid or expired.")
        user = self.users.get_by_id(self.db, token.user_id)
        if user is None or not user.is_active:
            self.db.rollback()
            raise UnauthorizedError("Password reset link is invalid or expired.")
        user.password_hash = hash_password(new_password)
        self.users.increment_auth_version(self.db, user)
        self.tokens.revoke_user_refresh_tokens(self.db, user.id, now)
        self.db.commit()

    def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if not verify_password(current_password, user.password_hash):
            raise UnauthorizedError("Current password is incorrect.")
        now = datetime.now(UTC)
        user.password_hash = hash_password(new_password)
        self.users.increment_auth_version(self.db, user)
        self.tokens.revoke_user_refresh_tokens(self.db, user.id, now)
        self.db.commit()

    def _new_refresh_token(
        self, user_id: UUID, family_id: UUID | None = None
    ) -> tuple[str, AuthToken]:
        raw = generate_opaque_token()
        now = datetime.now(UTC)
        row = AuthToken(
            user_id=user_id,
            token_hash=hash_opaque_token(raw),
            purpose=AuthTokenPurpose.REFRESH,
            family_id=family_id or uuid4(),
            expires_at=now + timedelta(days=self.settings.refresh_token_expire_days),
        )
        self.tokens.add(self.db, row)
        return raw, row

    def _create_one_time_token(
        self, user: User, purpose: AuthTokenPurpose, expires_minutes: int
    ) -> str:
        raw = generate_opaque_token()
        self.tokens.add(
            self.db,
            AuthToken(
                user_id=user.id,
                token_hash=hash_opaque_token(raw),
                purpose=purpose,
                expires_at=datetime.now(UTC) + timedelta(minutes=expires_minutes),
            ),
        )
        return raw

    def _get_valid_one_time_token(
        self, raw_token: str, purpose: AuthTokenPurpose
    ) -> AuthToken:
        token = self.tokens.get_by_hash(self.db, hash_opaque_token(raw_token))
        now = datetime.now(UTC)
        if (
            token is None
            or token.purpose != purpose
            or token.consumed_at is not None
            or token.revoked_at is not None
            or token.expires_at <= now
        ):
            raise UnauthorizedError("Token is invalid or expired.")
        return token

    def _require_email_delivery(self) -> None:
        if not self.email_sender.is_configured:
            raise ServiceUnavailableError("Email delivery is not configured.")

    def _signing_secret(self) -> str:
        secret = self.settings.jwt_secret_key
        if secret is None or len(secret.get_secret_value().encode("utf-8")) < 32:
            raise ServiceUnavailableError("Authentication is not configured.")
        return secret.get_secret_value()
