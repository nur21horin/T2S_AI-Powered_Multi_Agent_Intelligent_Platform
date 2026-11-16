from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_auth_service, get_current_user, get_db
from app.core.config import Settings
from app.core.exceptions import ForbiddenError
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    ChangePasswordRequest,
    CsrfTokenResponse,
    EmailTokenRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
)
from app.schemas.user import UserRead
from app.security.cookies import clear_auth_cookies, set_auth_cookies
from app.security.csrf import require_cookie_csrf
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])


def _require_allowed_origin(request: Request, settings: Settings) -> None:
    if request.headers.get("origin") not in settings.cors_allowed_origins:
        raise ForbiddenError("Request origin is not allowed.")


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(
    data: RegisterRequest,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    return auth.register(data)


@router.post("/login", response_model=AuthResponse)
def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthResponse:
    settings: Settings = request.app.state.settings
    _require_allowed_origin(request, settings)
    user, access_token, refresh_token = auth.login(str(data.email), data.password)
    csrf_token = set_auth_cookies(response, refresh_token, settings)
    return AuthResponse(access_token=access_token, csrf_token=csrf_token, user=user)


@router.post("/refresh", response_model=AuthResponse)
def refresh(
    request: Request,
    response: Response,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> AuthResponse:
    settings: Settings = request.app.state.settings
    require_cookie_csrf(request, settings)
    user, access_token, refresh_token = auth.refresh(
        request.cookies.get(settings.refresh_cookie_name)
    )
    csrf_token = set_auth_cookies(response, refresh_token, settings)
    return AuthResponse(access_token=access_token, csrf_token=csrf_token, user=user)


@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    response: Response,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    settings: Settings = request.app.state.settings
    require_cookie_csrf(request, settings)
    auth.logout(request.cookies.get(settings.refresh_cookie_name))
    clear_auth_cookies(response, settings)
    return MessageResponse(message="Logged out.")


@router.get("/csrf", response_model=CsrfTokenResponse)
def csrf_token(
    request: Request,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> CsrfTokenResponse:
    settings: Settings = request.app.state.settings
    _require_allowed_origin(request, settings)
    token = auth.current_csrf_token(
        request.cookies.get(settings.refresh_cookie_name),
        request.cookies.get(settings.csrf_cookie_name),
    )
    return CsrfTokenResponse(csrf_token=token)


@router.get("/me", response_model=UserRead)
def current_user(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user


@router.post("/email/verify", response_model=MessageResponse)
def verify_email(
    data: EmailTokenRequest,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    auth.verify_email(data.token)
    return MessageResponse(message="Email verified. You can now sign in.")


@router.post("/email/verification/request", response_model=MessageResponse)
def request_email_verification(
    data: ForgotPasswordRequest,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    auth.request_email_verification(str(data.email))
    return MessageResponse(message="If the account can be verified, an email will be sent.")


@router.post("/password/forgot", response_model=MessageResponse)
def forgot_password(
    data: ForgotPasswordRequest,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    auth.request_password_reset(str(data.email))
    return MessageResponse(message="If the account exists, a reset email will be sent.")


@router.post("/password/reset", response_model=MessageResponse)
def reset_password(
    data: ResetPasswordRequest,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    auth.reset_password(data.token, data.new_password)
    return MessageResponse(message="Password reset successfully.")


@router.post("/password/change", response_model=MessageResponse)
def change_password(
    data: ChangePasswordRequest,
    user: Annotated[User, Depends(get_current_user)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> MessageResponse:
    auth.change_password(user, data.current_password, data.new_password)
    return MessageResponse(message="Password changed. Please sign in again.")
