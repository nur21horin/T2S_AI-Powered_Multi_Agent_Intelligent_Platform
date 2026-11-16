"""Shared FastAPI dependencies."""
from collections.abc import Iterator

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import ServiceUnavailableError, UnauthorizedError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.security.revocation import get_redis_client, is_access_token_revoked
from app.security.tokens import InvalidAccessToken, decode_access_token
from app.services.auth_service import AuthService
from app.services.email_service import EmailSender

_bearer_scheme = HTTPBearer(auto_error=False)


def get_db(request: Request) -> Iterator[Session]:
    """One session per request. Services commit explicitly; errors roll back; always closed."""
    factory = getattr(request.app.state, "session_factory", None)
    if factory is None:
        raise ServiceUnavailableError("Database is not configured.")
    session: Session = factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_email_sender(request: Request) -> EmailSender:
    sender = getattr(request.app.state, "email_sender", None)
    if sender is None:
        raise ServiceUnavailableError("Email delivery is unavailable.")
    return sender


def get_auth_service(
    request: Request,
    db: Session = Depends(get_db),
    email_sender: EmailSender = Depends(get_email_sender),
) -> AuthService:
    return AuthService(db, request.app.state.settings, email_sender)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Authentication required.")
    try:
        claims = decode_access_token(credentials.credentials, request.app.state.settings)
    except InvalidAccessToken:
        raise UnauthorizedError("Authentication required.") from None
    except RuntimeError:
        raise ServiceUnavailableError("Authentication is not configured.") from None

    user = UserRepository().get_by_id(db, claims.user_id)
    if (
        user is None
        or not user.is_active
        or not user.is_verified
        or user.auth_version != claims.auth_version
    ):
        raise UnauthorizedError("Authentication required.")
    redis_client = get_redis_client(request)
    revoked = is_access_token_revoked(redis_client, claims.jti)
    if revoked:
        raise UnauthorizedError("Authentication required.")
    return user
