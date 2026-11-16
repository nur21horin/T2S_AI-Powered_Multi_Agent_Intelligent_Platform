from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from jwt.exceptions import PyJWTError

from app.core.config import Settings


class InvalidAccessToken(ValueError):
    pass


def _secret(settings: Settings) -> str:
    if settings.jwt_secret_key is None:
        raise RuntimeError("JWT_SECRET_KEY is not configured.")
    secret = settings.jwt_secret_key.get_secret_value()
    if len(secret.encode("utf-8")) < 32:
        raise RuntimeError("JWT_SECRET_KEY must contain at least 32 bytes.")
    return secret


def create_access_token(
    user_id: UUID, settings: Settings, now: datetime | None = None
) -> str:
    issued_at = now or datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": issued_at,
        "exp": issued_at + timedelta(minutes=settings.access_token_expire_minutes),
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, _secret(settings), algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> UUID:
    try:
        payload = jwt.decode(
            token,
            _secret(settings),
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["sub", "type", "iat", "exp", "jti"]},
        )
        if payload.get("type") != "access":
            raise InvalidAccessToken
        return UUID(payload["sub"])
    except (PyJWTError, KeyError, TypeError, ValueError) as exc:
        raise InvalidAccessToken from exc


def generate_opaque_token() -> str:
    return secrets.token_urlsafe(48)


def hash_opaque_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
