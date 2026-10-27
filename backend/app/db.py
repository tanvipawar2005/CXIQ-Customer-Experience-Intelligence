"""
db.py

PostgreSQL connection setup via SQLAlchemy.

GRACEFUL DEGRADATION: CXIQ is designed to work with or without a database.
If DATABASE_URL is unreachable at startup (Postgres not installed/running,
wrong credentials, network issue), the app logs a clear warning and falls
back to the original in-memory storage — every feature still works, it just
won't persist across restarts. This mirrors the same fallback philosophy
already used for Gemini (optional) and translation (optional network call).

`db_available()` is checked once at startup (see main.py) and the result is
used by dashboard_service.py to pick between the database-backed repository
and the legacy in-memory dict.
"""
from __future__ import annotations
import logging
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

logger = logging.getLogger("cxiq")

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

_db_available: bool = False


def check_db_connection() -> bool:
    """Attempts a real connection and creates tables if reachable. Called
    once at startup. Never raises — returns False on any failure."""
    global _db_available
    try:
        from app import models_db  # noqa: F401  (registers models on Base)
        with engine.connect() as conn:
            conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        Base.metadata.create_all(bind=engine)
        _db_available = True
        logger.info("Database connected: tables ready.")
    except Exception as exc:
        _db_available = False
        logger.warning(
            "Database unavailable (%s). Falling back to in-memory storage — "
            "data will not persist across restarts. See README section 19 "
            "to configure PostgreSQL.", exc
        )
    return _db_available


def db_available() -> bool:
    return _db_available


@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
