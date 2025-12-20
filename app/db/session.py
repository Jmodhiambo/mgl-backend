#!/usr/bin/env python3
"""Async database connection and session management for MGLTickets."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from app.core.config import DATABASE_URL, SQLALCHEMY_ECHO

# Use async driver in DATABASE_URL, e.g., postgresql+asyncpg://user:pass@host/db
async_engine = create_async_engine(DATABASE_URL, echo=SQLALCHEMY_ECHO)

# Async session factory
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
)

class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass

@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional scope around async operations."""
    session: AsyncSession = AsyncSessionLocal()
    try:
        yield session  # Give the session to the caller
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()