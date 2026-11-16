"""Engine and session factory. The engine is created lazily: no connection is opened at startup."""
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings


def create_db_engine(settings: Settings, url: str | None = None) -> Engine:
    if url is None:
        if settings.database_url is None:
            raise ValueError("DATABASE_URL is not configured")
        url = settings.database_url.get_secret_value()
    return create_engine(
        url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=settings.db_pool_recycle,
        pool_pre_ping=True,  # drop dead connections (DB restarts, idle timeouts)
        connect_args={
            "connect_timeout": settings.db_connect_timeout,
            "options": f"-c statement_timeout={settings.db_statement_timeout_ms}",
        },
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    # autoflush off + expire_on_commit off: explicit, predictable behaviour for services.
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
