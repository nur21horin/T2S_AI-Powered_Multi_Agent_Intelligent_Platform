from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.exceptions import ServiceUnavailableError
from app.security.revocation import (
    REVOCATION_KEY_PREFIX,
    is_access_token_revoked,
    revoke_access_token,
    revocation_key,
)
from app.security.tokens import AccessTokenClaims


def test_revocation_key_is_namespaced_and_expiry_does_not_exceed_jwt(fake_redis):
    now = datetime.now(UTC)
    claims = AccessTokenClaims(
        user_id=uuid4(),
        jti=uuid4(),
        auth_version=0,
        expires_at=now + timedelta(seconds=90),
    )

    revoke_access_token(fake_redis, claims, now=now)

    key = revocation_key(claims.jti)
    assert key.startswith(REVOCATION_KEY_PREFIX)
    assert fake_redis.exists(key) == 1
    assert fake_redis.values[key][1] <= claims.expires_at.timestamp()
    assert fake_redis.ttl(key) <= 90
    assert fake_redis.ttl(key) > 0
    assert is_access_token_revoked(fake_redis, claims.jti)


def test_expired_token_does_not_create_a_denylist_entry(fake_redis):
    now = datetime.now(UTC)
    claims = AccessTokenClaims(
        user_id=uuid4(),
        jti=uuid4(),
        auth_version=0,
        expires_at=now - timedelta(seconds=1),
    )

    revoke_access_token(fake_redis, claims, now=now)

    assert fake_redis.exists(revocation_key(claims.jti)) == 0


def test_redis_errors_fail_closed_for_revocation(fake_redis):
    fake_redis.available = False

    with pytest.raises(ServiceUnavailableError):
        is_access_token_revoked(fake_redis, uuid4())

    claims = AccessTokenClaims(
        user_id=uuid4(),
        jti=uuid4(),
        auth_version=0,
        expires_at=datetime.now(UTC) + timedelta(minutes=1),
    )
    with pytest.raises(ServiceUnavailableError):
        revoke_access_token(fake_redis, claims)
