"""Startup / shutdown hooks. The DB engine is created here and disposed on shutdown."""
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis import Redis

from app.db.session import create_db_engine, create_session_factory

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Application starting")
    settings = app.state.settings
    engine = None
    managed_redis = None
    app.state.engine = None
    app.state.session_factory = None
    if settings.database_url is not None:
        engine = create_db_engine(settings)  # lazy: does not connect yet
        app.state.engine = engine
        app.state.session_factory = create_session_factory(engine)
    else:
        logger.warning("DATABASE_URL not configured; database features are unavailable")
    if app.state.redis_client is None and settings.redis_url is not None:
        managed_redis = Redis.from_url(
            settings.redis_url.get_secret_value(),
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        app.state.redis_client = managed_redis
    try:
        yield
    finally:
        if engine is not None:
            engine.dispose()
        if managed_redis is not None:
            managed_redis.close()
            app.state.redis_client = None
        logger.info("Application shutting down")
