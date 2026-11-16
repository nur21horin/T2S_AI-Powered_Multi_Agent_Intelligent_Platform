from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from jwt.exceptions import PyJWTError

from app.core.config import Settings


class InvalidAccessToken(ValueError):
    pass


@dataclass(frozen=True)
class AccessTokenClaims:
    user_id: UUID
    jti: UUID
    auth_version: int
    expires_at: datetime


def _secret(settings: Settings) -> str:
    if settings.jwt_secret_key is None:
        raise RuntimeError("JWT_SECRET_KEY is not configured.")
    secret = settings.jwt_secret_key.get_secret_value()
    if len(secret.encode("utf-8")) < 32:
        raise RuntimeError("JWT_SECRET_KEY must contain at least 32 bytes.")
    return secret


def create_access_token(
    user_id: UUID,
    settings: Settings,
    auth_version: int,
    now: datetime | None = None,
) -> str:
    if type(auth_version) is not int or auth_version < 0:
        raise ValueError("auth_version must be a non-negative integer")
    issued_at = now or datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": issued_at,
        "exp": issued_at + timedelta(minutes=settings.access_token_expire_minutes),
        "jti": str(uuid4()),
        "auth_version": auth_version,
    }
    return jwt.encode(payload, _secret(settings), algorithm=settings.jwt_algorithm)


def _decode_access_token(
    token: str, settings: Settings, *, verify_expiration: bool
) -> AccessTokenClaims:
    try:
        payload = jwt.decode(
            token,
            _secret(settings),
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={
                "require": ["sub", "type", "iat", "exp", "jti", "auth_version"],
                "verify_exp": verify_expiration,
            },
        )
        if payload.get("type") != "access":
            raise InvalidAccessToken
        auth_version = payload["auth_version"]
        if type(auth_version) is not int or auth_version < 0:
            raise InvalidAccessToken
        expires_at = payload["exp"]
        if isinstance(expires_at, bool) or not isinstance(expires_at, (int, float)):
            raise InvalidAccessToken
        return AccessTokenClaims(
            user_id=UUID(payload["sub"]),
            jti=UUID(payload["jti"]),
            auth_version=auth_version,
            expires_at=datetime.fromtimestamp(expires_at, UTC),
        )
    except (PyJWTError, KeyError, TypeError, ValueError, OverflowError) as exc:
        raise InvalidAccessToken from exc


def decode_access_token(token: str, settings: Settings) -> AccessTokenClaims:
    return _decode_access_token(token, settings, verify_expiration=True)


def decode_access_token_for_logout(token: str, settings: Settings) -> AccessTokenClaims:
    """Verify a presented token while allowing an expired token for refresh logout."""
    return _decode_access_token(token, settings, verify_expiration=False)


def generate_opaque_token() -> str:
    return secrets.token_urlsafe(48)


def hash_opaque_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
