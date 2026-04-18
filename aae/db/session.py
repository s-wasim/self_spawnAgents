"""SQLAlchemy engine + session factory."""
from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from aae.config.settings import get_settings

_engine: Engine | None = None
_Session: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine, _Session
    if _engine is None:
        dsn = get_settings().postgres_dsn
        _engine = create_engine(dsn, pool_size=10, pool_pre_ping=True, future=True)
        _Session = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
    return _engine


def get_sessionmaker() -> sessionmaker[Session]:
    get_engine()
    assert _Session is not None
    return _Session


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    sm = get_sessionmaker()
    session = sm()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_engine_for_tests(dsn: str) -> Engine:
    """Test-only helper: swap the engine to an in-memory SQLite URL."""
    global _engine, _Session
    _engine = create_engine(dsn, future=True)
    _Session = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
    return _engine
