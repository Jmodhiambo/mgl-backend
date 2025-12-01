#!/usr/bin/env python3
"""Database connection and session management for MGLTickets."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from collections.abc import Generator
from contextlib import contextmanager

from app.core.config import DATABASE_URL, SQLALCHEMY_ECHO

engine = create_engine(DATABASE_URL, echo=SQLALCHEMY_ECHO)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autocommit=False,
    autoflush=False,
)

class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass

@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()