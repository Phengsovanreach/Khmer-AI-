"""
Khmer Translator AI — Production Database Engine.
Provides resilient SQLAlchemy session management, connection pooling, health checks,
and dual-engine support (PostgreSQL in production, SQLite fallback in local development).
"""
from __future__ import annotations

import logging
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

logger = logging.getLogger(__name__)

Base = declarative_base()

# Resolve Database URL
_RAW_DB_URL = os.getenv("DATABASE_URL", "").strip()

if not _RAW_DB_URL:
    # Fallback to local SQLite under backend/auth.db
    _DEFAULT_SQLITE_PATH = Path(__file__).resolve().parents[2] / "auth.db"
    _DEFAULT_SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite:///{_DEFAULT_SQLITE_PATH.as_posix()}"
else:
    DATABASE_URL = _RAW_DB_URL
    # Normalize legacy Heroku/Render postgres:// prefix to postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

IS_POSTGRES = DATABASE_URL.startswith("postgresql")
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# Configure engine with production-ready connection pooling
engine_kwargs: dict[str, Any] = {
    "pool_pre_ping": True,
}

if IS_POSTGRES:
    engine_kwargs.update({
        "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "300")),
        "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
    })
elif IS_SQLITE:
    engine_kwargs.update({
        "connect_args": {"check_same_thread": False},
    })

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database tables safely if they do not exist."""
    try:
        from . import models  # noqa: F401 - ensure models are registered
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema verified and initialized on %s", "PostgreSQL" if IS_POSTGRES else "SQLite")
    except Exception as exc:
        logger.error("Failed to initialize database tables: %s", exc)
        raise


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for obtaining a thread-safe database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_db_health() -> dict[str, Any]:
    """
    Executes a lightweight query (SELECT 1) to verify database connectivity and measure latency.
    Returns status, latency in milliseconds, engine type, and error message if any.
    """
    start_time = time.perf_counter()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return {
            "status": "CONNECTED",
            "is_healthy": True,
            "engine": "PostgreSQL" if IS_POSTGRES else "SQLite",
            "latency_ms": round(latency_ms, 2),
            "error": None,
        }
    except Exception as exc:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        logger.error("Database health check failed: %s", exc)
        return {
            "status": "DISCONNECTED",
            "is_healthy": False,
            "engine": "PostgreSQL" if IS_POSTGRES else "SQLite",
            "latency_ms": round(latency_ms, 2),
            "error": str(exc),
        }
