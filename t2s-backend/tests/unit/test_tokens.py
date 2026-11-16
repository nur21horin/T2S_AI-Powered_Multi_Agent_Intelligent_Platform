from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from fastapi import Response

from app.core.config import Settings
from app.security.tokens import (
    InvalidAccessToken,
    create_access_token,
    decode_access_token,
    generate_opaque_token,
    hash_opaque_token,
)
from app.security.cookies import set_auth_cookies


def test_access_token_round_trip_and_claim_validation(settings):
    user_id = uuid4()
    token = create_access_token(user_id, settings)

    assert decode_access_token(token, settings) == user_id
    with pytest.raises(InvalidAccessToken):
        decode_access_token(token, settings.model_copy(update={"jwt_audience": "wrong"}))


def test_access_token_rejects_expired_and_wrong_type_tokens(settings):
    now = datetime.now(UTC)
    expired = jwt.encode(
        {
            "sub": str(uuid4()), "type": "access", "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience, "iat": now - timedelta(minutes=10),
            "exp": now - timedelta(minutes=1), "jti": str(uuid4()),
        },
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )
    wrong_type = jwt.encode(
        {
            "sub": str(uuid4()), "type": "refresh", "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience, "iat": now,
            "exp": now + timedelta(minutes=5), "jti": str(uuid4()),
        },
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(InvalidAccessToken):
        decode_access_token(expired, settings)
    with pytest.raises(InvalidAccessToken):
        decode_access_token(wrong_type, settings)
    with pytest.raises(InvalidAccessToken):
        decode_access_token("not-a-jwt", settings)


def test_opaque_tokens_are_high_entropy_and_only_compared_by_hash():
    first = generate_opaque_token()
    second = generate_opaque_token()

    assert len(first) >= 64
    assert first != second
    assert hash_opaque_token(first) != first
    assert hash_opaque_token(first) != hash_opaque_token(second)


def test_missing_signing_secret_fails_closed():
    settings = Settings(_env_file=None, app_env="testing", jwt_secret_key=None)
    with pytest.raises(RuntimeError):
        create_access_token(uuid4(), settings)


def test_refresh_cookie_is_http_only_and_secure_in_production(settings):
    response = Response()
    production_settings = settings.model_copy(update={"app_env": "production"})

    csrf_token = set_auth_cookies(response, "opaque-refresh-token", production_settings)
    cookies = response.headers.getlist("set-cookie")
    refresh_cookie = next(value for value in cookies if "t2s_refresh=" in value)
    csrf_cookie = next(value for value in cookies if "t2s_csrf=" in value)

    assert "httponly" in refresh_cookie.lower()
    assert "secure" in refresh_cookie.lower()
    assert "secure" in csrf_cookie.lower()
    assert "httponly" not in csrf_cookie.lower()
    assert csrf_token in csrf_cookie
