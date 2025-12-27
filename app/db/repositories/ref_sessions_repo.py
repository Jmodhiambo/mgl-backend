#!/usr/bin/env python3
"""Async repository for RefreshSession model operations."""

from sqlalchemy import select, func, delete
from datetime import datetime, timezone, timedelta
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
            refresh_session.refresh_token_hash = refresh_session_update.refresh_token_hash or refresh_session.refresh_token_hash
            refresh_session.expires_at = refresh_session_update.expires_at or refresh_session.expires_at
            await session.commit()
            await session.refresh(refresh_session)
            return RefreshSessionOut.model_validate(refresh_session)
        return None
    
async def revoke_refresh_session_repo(session_id: str, new_session_id: str) -> Optional[RefreshSessionOut]:
    """Revoke a RefreshSession by session_id."""
    async with get_async_session() as session:
        result = await session.execute(select(RefreshSession).where(RefreshSession.session_id == session_id))
        refresh_session = result.scalar_one_or_none()
        if refresh_session:
            refresh_session.revoked_at = datetime.utcnow()
            refresh_session.replaced_by_sid = new_session_id
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
    
async def cleanup_expired_and_revoked_sessions_repo(hours: int = 24) -> int:
    """Cleanup expired and revoked sessions after 24 hours."""
    async with get_async_session() as session:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        expired_sessions = await session.execute(delete(RefreshSession).where(
            RefreshSession.expires_at < cutoff_time)
        )
        revoked_sessions = await session.execute(delete(RefreshSession).where(
            RefreshSession.revoked_at < cutoff_time)
        )

        await session.commit()
        
        return expired_sessions.rowcount + revoked_sessions.rowcount

async def cleanup_all_user_sessions_repo(user_id: int) -> int:
    """Cleanup all sessions for a user."""
    async with get_async_session() as session:
        result = await session.execute(delete(RefreshSession).where(RefreshSession.user_id == user_id))
        await session.commit()
        return result.rowcount
    
async def get_active_session_count_repo() -> int:
    """Get count of active (non-revoked, non-expired) sessions"""
    async with get_async_session() as session:
        
        now = datetime.now(timezone.utc)
        stmt = select(func.count(RefreshSession.session_id)).where(
            RefreshSession.revoked_at.is_(None),
            RefreshSession.expires_at > now
        )
        
        result = await session.execute(stmt)
        return result.scalar() or 0


async def get_user_active_sessions_repo(user_id: str) -> int:
    """Get count of active sessions for a specific user"""
    async with get_async_session() as session:
        from sqlalchemy import select, func
        
        now = datetime.now(timezone.utc)
        stmt = select(func.count(RefreshSession.session_id)).where(
            RefreshSession.user_id == user_id,
            RefreshSession.revoked_at.is_(None),
            RefreshSession.expires_at > now
        )
        
        result = await session.execute(stmt)
        return result.scalar() or 0