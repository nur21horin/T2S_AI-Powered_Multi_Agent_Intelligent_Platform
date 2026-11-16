"""Centralized exception types and handlers. Error responses never leak internals."""
import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import request_id_ctx

logger = logging.getLogger(__name__)


class AppException(Exception):
    status_code = 500
    code = "internal_error"
    message = "An unexpected error occurred."

    def __init__(self, message: str | None = None, details: Any = None) -> None:
        self.message = message or self.message
        self.details = details
        super().__init__(self.message)


class BadRequestError(AppException):
    status_code, code, message = 400, "bad_request", "Bad request."


class UnauthorizedError(AppException):
    status_code, code, message = 401, "unauthorized", "Authentication required."


class ForbiddenError(AppException):
    status_code, code, message = 403, "forbidden", "You do not have permission."


class NotFoundError(AppException):
    status_code, code, message = 404, "not_found", "Resource not found."


class ConflictError(AppException):
    status_code, code, message = 409, "conflict", "Conflict with current state."


class TooManyRequestsError(AppException):
    status_code, code, message = 429, "rate_limited", "Too many requests."


def _error_response(status: int, code: str, message: str, details: Any = None,
                    headers: dict[str, str] | None = None) -> JSONResponse:
    body = {"error": {"code": code, "message": message, "details": details,
                      "request_id": request_id_ctx.get()}}
    return JSONResponse(status_code=status, content=body, headers=headers)


async def _app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
    return _error_response(exc.status_code, exc.code, exc.message, exc.details)


async def _http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = {404: "not_found", 405: "method_not_allowed"}.get(exc.status_code, "http_error")
    return _error_response(exc.status_code, code, str(exc.detail), headers=exc.headers)


async def _validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    # Deliberately drop "input"/"ctx": they can echo submitted secrets such as passwords.
    details = [{"field": ".".join(str(p) for p in err["loc"]), "message": err["msg"],
                "type": err["type"]} for err in exc.errors()]
    return _error_response(422, "validation_error", "Request validation failed.", details)


async def _unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception", exc_info=exc)
    return _error_response(500, "internal_error", "An unexpected error occurred.")


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppException, _app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)
