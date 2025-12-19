#!/usr/bin/env python3
"""Async repository for RefreshSession model operations."""

from sqlalchemy import select, func
from datetime import datetime
from app.db.models.refresh_sessions import RefreshSession
from app.db.session import get_async_session
from typing import Optional
from app.schemas.refresh_session import RefreshSessionOut, RefreshSessionCreate, RefreshSessionUpdate


async def create_refresh_session_repo(session_create: RefreshSessionCreate) -> RefreshSessionOut:
    """Create a new RefreshSession."""
    async with get_async_session() as session:
        refresh_session = RefreshSession(
            session_id=session_create.session_id,
            user_id=session_create.user_id,
            refresh_token_hash=session_create.refresh_token_hash,
            expires_at=session_create.expires_at
        )
        session.add(refresh_session)
        await session.commit()
        await session.refresh(refresh_session)
        return refresh_session
    

async def get_refresh_session_repo(session_id: str) -> Optional[RefreshSessionOut]:
    """Get a RefreshSession by session_id."""
    async with get_async_session() as session:
        result = await session.execute(select(RefreshSession).where(RefreshSession.session_id == session_id))
        refresh_session = result.scalar_one_or_none()
        if refresh_session:
            return RefreshSessionOut.model_validate(refresh_session)
        return None


async def get_refresh_session_by_user_id_repo(user_id: int) -> Optional[RefreshSessionOut]:
    """Get a RefreshSession by user_id."""
    async with get_async_session() as session:
        result = await session.execute(select(RefreshSession).where(RefreshSession.user_id == user_id))
        refresh_session = result.scalar_one_or_none()
        if refresh_session:
            return RefreshSessionOut.model_validate(refresh_session)
        return None


async def update_refresh_session_repo(session_id: str, refresh_session_update: RefreshSessionUpdate) -> Optional[RefreshSessionOut]:
    """Update a RefreshSession by session_id."""
    async with get_async_session() as session:
        result = await session.execute(select(RefreshSession).where(RefreshSession.session_id == session_id))
        refresh_session = result.scalar_one_or_none()
        if refresh_session:
            refresh_session.session_id = refresh_session_update.session_id or refresh_session.session_id
            refresh_session.user_id = refresh_session_update.user_id or refresh_session.user_id
            refresh_session.refresh_token_hash = refresh_session_update.refresh_token_hash or refresh_session.refresh_token_hash
            refresh_session.expires_at = refresh_session_update.expires_at or refresh_session.expires_at
            await session.commit()
            await session.refresh(refresh_session)
            return RefreshSessionOut.model_validate(refresh_session)
        return None


async def delete_refresh_session_repo(session_id: str) -> bool:
    """Delete a RefreshSession by session_id."""
    async with get_async_session() as session:
        result = await session.execute(select(RefreshSession).where(RefreshSession.session_id == session_id))
        refresh_session = result.scalar_one_or_none()
        if refresh_session:
            await session.delete(refresh_session)
            await session.commit()
            return True
        return False