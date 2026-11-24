from fastapi import Response

from app.core.config import Settings
from app.security.csrf import create_csrf_token
from app.security.tokens import _secret


def _cookie_options(settings: Settings) -> dict[str, object]:
    return {
        "secure": (
            settings.cookie_secure
            or settings.is_production
            or settings.cookie_samesite == "none"
        ),
        "samesite": settings.cookie_samesite,
        "path": settings.cookie_path,
        "domain": settings.cookie_domain,
    }


def set_auth_cookies(response: Response, refresh_token: str, settings: Settings) -> str:
    secure = settings.cookie_secure or settings.is_production or settings.cookie_samesite == "none"
    csrf_token = create_csrf_token(_secret(settings))
    response.set_cookie(
        settings.refresh_cookie_name,
        refresh_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=secure,
        samesite=settings.cookie_samesite,
        path=settings.cookie_path,
        domain=settings.cookie_domain,
    )
    response.set_cookie(
        settings.csrf_cookie_name,
        csrf_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        httponly=False,
        secure=secure,
        samesite=settings.cookie_samesite,
        path=settings.cookie_path,
        domain=settings.cookie_domain,
    )
    return csrf_token


def clear_auth_cookies(response: Response, settings: Settings) -> None:
    for name in (settings.refresh_cookie_name, settings.csrf_cookie_name):
        response.delete_cookie(name, **_cookie_options(settings))
