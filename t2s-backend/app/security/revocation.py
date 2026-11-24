"""Redis-backed revocation checks for access JWTs."""
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from fastapi import Request
from redis.exceptions import RedisError

from app.core.exceptions import ServiceUnavailableError
from app.security.tokens import AccessTokenClaims

REVOCATION_KEY_PREFIX = "t2s:auth:revoked:jti:"


class RedisRevocationStore(Protocol):
    def exists(self, name: str) -> int: ...

    def set(self, name: str, value: str, *, pxat: int) -> object: ...


def get_redis_client(request: Request) -> RedisRevocationStore:
    client = getattr(request.app.state, "redis_client", None)
    if client is None:
        raise ServiceUnavailableError("Token revocation service is unavailable.")
    return client


def revocation_key(jti: UUID) -> str:
    return f"{REVOCATION_KEY_PREFIX}{jti}"


def is_access_token_revoked(store: RedisRevocationStore, jti: UUID) -> bool:
    try:
        return bool(store.exists(revocation_key(jti)))
    except RedisError as exc:
        raise ServiceUnavailableError("Token revocation service is unavailable.") from exc


def revoke_access_token(
    store: RedisRevocationStore,
    claims: AccessTokenClaims,
    now: datetime | None = None,
) -> None:
    current_time = now or datetime.now(UTC)
    # Redis PXAT uses an absolute millisecond expiry, avoiding TTL rounding past JWT exp.
    expires_at_ms = int(claims.expires_at.timestamp() * 1000)
    if expires_at_ms <= int(current_time.timestamp() * 1000):
        return
    try:
        stored = store.set(revocation_key(claims.jti), "1", pxat=expires_at_ms)
    except RedisError as exc:
        raise ServiceUnavailableError("Token revocation service is unavailable.") from exc
    if not stored:
        raise ServiceUnavailableError("Token revocation service is unavailable.")
