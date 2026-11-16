import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.exceptions import ServiceUnavailableError
from app.schemas.common import ErrorResponse, HealthResponse, ReadinessResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Liveness check")
def health() -> HealthResponse:
    """Process is up. Does not touch the database (used for liveness)."""
    return HealthResponse(status="ok")


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    responses={503: {"model": ErrorResponse}},
    summary="Readiness check (database reachable)",
)
def ready(db: Annotated[Session, Depends(get_db)]) -> ReadinessResponse:
    """Used by the load balancer to decide whether this instance can serve traffic."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        # Log only the exception type: never connection details.
        logger.warning("Readiness check failed: %s", type(exc).__name__)
        raise ServiceUnavailableError("Database unavailable.") from None
    return ReadinessResponse(status="ready", database="ok")
