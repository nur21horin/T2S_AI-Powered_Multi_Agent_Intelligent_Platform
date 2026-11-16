import base64
import hashlib
import hmac
import secrets

from fastapi import Request

from app.core.config import Settings
from app.core.exceptions import ForbiddenError, ServiceUnavailableError
from app.security.tokens import _secret


def create_csrf_token(secret: str) -> str:
    nonce = secrets.token_urlsafe(32)
    signature = hmac.new(secret.encode("utf-8"), nonce.encode("ascii"), hashlib.sha256).digest()
    encoded_signature = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
    return f"{nonce}.{encoded_signature}"


def is_valid_csrf_token(token: str | None, secret: str) -> bool:
    if not token or len(token) > 256 or "." not in token:
        return False
    nonce, supplied_signature = token.rsplit(".", 1)
    try:
        expected = create_signature(nonce, secret)
        return hmac.compare_digest(supplied_signature, expected)
    except (UnicodeError, ValueError):
        return False


def verify_csrf_pair(cookie_token: str | None, header_token: str | None, secret: str) -> bool:
    if cookie_token is None or header_token is None:
        return False
    try:
        return hmac.compare_digest(cookie_token, header_token) and is_valid_csrf_token(
            cookie_token, secret
        )
    except (TypeError, UnicodeError):
        return False


def require_cookie_csrf(request: Request, settings: Settings) -> None:
    origin = request.headers.get("origin")
    if origin not in settings.cors_allowed_origins:
        raise ForbiddenError("Request origin is not allowed.")
    try:
        secret = _secret(settings)
    except RuntimeError:
        raise ServiceUnavailableError("Authentication is not configured.") from None
    if not verify_csrf_pair(
        request.cookies.get(settings.csrf_cookie_name),
        request.headers.get("x-csrf-token"),
        secret,
    ):
        raise ForbiddenError("CSRF validation failed.")


def create_signature(nonce: str, secret: str) -> str:
    signature = hmac.new(secret.encode("utf-8"), nonce.encode("ascii"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
