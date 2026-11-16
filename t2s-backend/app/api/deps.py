"""Shared FastAPI dependencies."""
from collections.abc import Iterator

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.exceptions import ServiceUnavailableError


def get_db(request: Request) -> Iterator[Session]:
    """One session per request. Services commit explicitly; errors roll back; always closed."""
    factory = getattr(request.app.state, "session_factory", None)
    if factory is None:
        raise ServiceUnavailableError("Database is not configured.")
    session: Session = factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
