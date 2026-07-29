#!/usr/bin/env python3
"""Async database connection and session management for MGLTickets."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import DATABASE_URL, SQLALCHEMY_ECHO


engine_kwargs = {"echo": SQLALCHEMY_ECHO}


# Use async driver in DATABASE_URL, e.g., postgresql+asyncpg://user:pass@host/db
async_engine = create_async_engine(
    DATABASE_URL,
    **engine_kwargs,
)

# Async session factory.
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional scope around async operations."""
    session: AsyncSession = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()