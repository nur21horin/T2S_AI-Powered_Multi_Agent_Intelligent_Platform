"""Startup / shutdown hooks. The DB engine is created here and disposed on shutdown."""
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.session import create_db_engine, create_session_factory

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Application starting")
    settings = app.state.settings
    engine = None
    app.state.engine = None
    app.state.session_factory = None
    if settings.database_url is not None:
        engine = create_db_engine(settings)  # lazy: does not connect yet
        app.state.engine = engine
        app.state.session_factory = create_session_factory(engine)
    else:
        logger.warning("DATABASE_URL not configured; database features are unavailable")
    yield
    if engine is not None:
        engine.dispose()
    logger.info("Application shutting down")
