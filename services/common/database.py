"""
Sync SQLAlchemy database layer for users and jobs persistence.

Uses DATABASE_URL (postgresql://...) for persistent storage. Tables are
created on first use. Used by auth (users) and job_store (jobs).
"""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.sql import func

from services.common.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


# =============================================================================
# Table definitions
# =============================================================================


class UserModel(Base):
    """SQLAlchemy model for users (auth service)."""

    __tablename__ = "users"

    id = Column(Integer(), primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    role = Column(String(64), nullable=False, default="user")
    is_active = Column(Integer(), nullable=False, default=1)  # 1=True, 0=False
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(), nullable=True, onupdate=func.now())


class JobModel(Base):
    """SQLAlchemy model for jobs (data/train services)."""

    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True)  # job_id UUID
    job_type = Column(String(128), nullable=False, index=True)
    status = Column(String(32), nullable=False, index=True)
    created_at = Column(DateTime(), nullable=False, server_default=func.now())
    started_at = Column(DateTime(), nullable=True)
    completed_at = Column(DateTime(), nullable=True)
    progress = Column(Float(), nullable=False, default=0.0)
    message = Column(Text(), nullable=True)
    result = Column(JSON(), nullable=True)
    error = Column(Text(), nullable=True)
    created_by = Column(String(255), nullable=True, index=True)
    parameters = Column(JSON(), nullable=True)
    logs = Column(JSON(), nullable=True)  # list of strings


# =============================================================================
# Engine and session (lazy init when DATABASE_URL is postgresql)
# =============================================================================

_engine = None
_SessionLocal = None


def _is_postgres() -> bool:
    url = (settings.DATABASE_URL or "").strip().lower()
    return url.startswith("postgresql") and "+asyncpg" not in url


def get_engine():
    """Return sync SQLAlchemy engine for Postgres. Creates tables on first use."""
    global _engine, _SessionLocal
    if not _is_postgres():
        return None
    if _engine is None:
        _engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        _create_tables_locked(_engine)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
        logger.info("Postgres engine and tables ready (users, jobs)")
    return _engine


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context manager for a sync DB session. Only works when DATABASE_URL is postgresql."""
    get_engine()
    if _SessionLocal is None:
        raise RuntimeError("Database not configured (DATABASE_URL is not postgresql)")
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_tables_if_postgres() -> None:
    """Create users and jobs tables if using Postgres. Call from auth/data/train startup."""
    if _is_postgres():
        get_engine()


def _create_tables_locked(engine) -> None:
    """Create tables with an advisory lock to avoid concurrent DDL."""
    with engine.begin() as connection:
        # Serialize create_all across services to avoid pg_type duplicate errors.
        connection.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": 917305})
        Base.metadata.create_all(bind=connection)
