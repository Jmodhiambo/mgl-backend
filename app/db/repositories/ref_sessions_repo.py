#!/usr/bin/env python3
"""Async repository for RefreshSession model operations."""

from sqlalchemy import select, func, delete
from datetime import datetime, timezone, timedelta
from app.db.models.refresh_sessions import RefreshSession
from app.db.session import get_async_session
from typing import Optional
from app.schemas.refresh_session import RefreshSessionOut, RefreshSessionCreate, RefreshSessionUpdate


# ─── Create ───────────────────────────────────────────────────────────────────

async def create_refresh_session_repo(session_create: RefreshSessionCreate) -> RefreshSessionOut:
    """Create a new RefreshSession."""
    async with get_async_session() as session:
        refresh_session = RefreshSession(
            session_id=session_create.session_id,
            user_id=session_create.user_id,
            refresh_token_hash=session_create.refresh_token_hash,
            expires_at=session_create.expires_at,
            device_info=session_create.device_info,
            ip_address=session_create.ip_address,
            location=session_create.location,
        )
        session.add(refresh_session)
        await session.commit()
        await session.refresh(refresh_session)
        return RefreshSessionOut.model_validate(refresh_session)


# ─── Read ─────────────────────────────────────────────────────────────────────

async def get_refresh_session_repo(session_id: str) -> Optional[RefreshSessionOut]:
    """Get a RefreshSession by session_id."""
    async with get_async_session() as session:
        result = await session.execute(
            select(RefreshSession).where(RefreshSession.session_id == session_id)
        )
        refresh_session = result.scalar_one_or_none()
        return RefreshSessionOut.model_validate(refresh_session) if refresh_session else None


async def get_refresh_session_by_user_id_repo(user_id: int) -> list[RefreshSessionOut]:
    """Get ALL RefreshSessions for a user.

    FIXED: was scalar_one_or_none() which silently dropped every session
    after the first.  Now returns the full list so callers can choose
    which session they need.
    """
    async with get_async_session() as session:
        result = await session.execute(
            select(RefreshSession).where(RefreshSession.user_id == user_id)
        )
        rows = result.scalars().all()
        return [RefreshSessionOut.model_validate(r) for r in rows]


async def list_active_sessions_for_user_repo(user_id: int) -> list[RefreshSessionOut]:
    """Return all non-revoked, non-expired sessions for one user.

    NEW — used by GET /admin/profile/sessions and
    GET /auth/my-sessions (regular users) to power the
    'Active Sessions' tab on the profile page.
    """
    async with get_async_session() as session:
        result = await session.execute(
            select(RefreshSession).where(
                RefreshSession.user_id == user_id,
                RefreshSession.revoked_at.is_(None),
                RefreshSession.expires_at > datetime.now(timezone.utc),
            )
        )
        rows = result.scalars().all()
        return [RefreshSessionOut.model_validate(r) for r in rows]


async def get_refresh_session_by_verification_token_repo(token: str) -> Optional[RefreshSessionOut]:
    """Retrieve a user by their verification token."""
    async with get_async_session() as session:
        result = await session.execute(
            select(RefreshSession).where(RefreshSession.session_id == token)
        )
        refresh_session = result.scalar_one_or_none()
        return RefreshSessionOut.model_validate(refresh_session) if refresh_session else None


async def get_refresh_session_by_password_reset_token_repo(token: str) -> Optional[RefreshSessionOut]:
    """Retrieve a user by their password reset token."""
    async with get_async_session() as session:
        result = await session.execute(
            select(RefreshSession).where(RefreshSession.session_id == token)
        )
        refresh_session = result.scalar_one_or_none()
        return RefreshSessionOut.model_validate(refresh_session) if refresh_session else None


# ─── Update ───────────────────────────────────────────────────────────────────

async def update_refresh_session_repo(
    session_id: str, refresh_session_update: RefreshSessionUpdate
) -> Optional[RefreshSessionOut]:
    """Update a RefreshSession by session_id."""
    async with get_async_session() as session:
        result = await session.execute(
            select(RefreshSession).where(RefreshSession.session_id == session_id)
        )
        refresh_session = result.scalar_one_or_none()
        if refresh_session:
            refresh_session.session_id = refresh_session_update.session_id or refresh_session.session_id
            refresh_session.refresh_token_hash = (
                refresh_session_update.refresh_token_hash or refresh_session.refresh_token_hash
            )
            refresh_session.expires_at = refresh_session_update.expires_at or refresh_session.expires_at
            await session.commit()
            await session.refresh(refresh_session)
            return RefreshSessionOut.model_validate(refresh_session)
        return None


# ─── Revoke / Delete ──────────────────────────────────────────────────────────

async def revoke_refresh_session_repo(session_id: str, new_session_id: str) -> Optional[RefreshSessionOut]:
    """Soft-revoke a RefreshSession during token rotation."""
    async with get_async_session() as session:
        result = await session.execute(
            select(RefreshSession).where(RefreshSession.session_id == session_id)
        )
        refresh_session = result.scalar_one_or_none()
        if refresh_session:
            refresh_session.revoked_at = datetime.now(timezone.utc)
            refresh_session.replaced_by_sid = new_session_id
            await session.commit()
            await session.refresh(refresh_session)
            return RefreshSessionOut.model_validate(refresh_session)
        return None


async def revoke_single_session_for_user_repo(
    user_id: int, session_id: str
) -> bool:
    """Soft-revoke one specific session, but only if it belongs to user_id."""
    async with get_async_session() as session:
        result = await session.execute(
            select(RefreshSession).where(
                RefreshSession.session_id == session_id,
                RefreshSession.user_id == user_id,
                RefreshSession.revoked_at.is_(None),
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            return False
        row.revoked_at = datetime.now(timezone.utc)
        row.replaced_by_sid = None  # manual revoke, not a rotation
        await session.commit()
        return True


async def delete_refresh_session_repo(session_id: str) -> bool:
    """Hard-delete a RefreshSession by session_id."""
    async with get_async_session() as session:
        result = await session.execute(
            select(RefreshSession).where(RefreshSession.session_id == session_id)
        )
        refresh_session = result.scalar_one_or_none()
        if refresh_session:
            await session.delete(refresh_session)
            await session.commit()
            return True
        return False


async def cleanup_expired_and_revoked_sessions_repo(hours: int = 24) -> int:
    """Hard-delete expired and revoked sessions older than `hours`."""
    async with get_async_session() as session:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        expired = await session.execute(
            delete(RefreshSession).where(RefreshSession.expires_at < cutoff_time)
        )
        revoked = await session.execute(
            delete(RefreshSession).where(RefreshSession.revoked_at < cutoff_time)
        )
        await session.commit()
        return expired.rowcount + revoked.rowcount


async def cleanup_all_user_sessions_repo(user_id: int) -> int:
    """Hard-delete ALL sessions for a user (logout all devices)."""
    async with get_async_session() as session:
        result = await session.execute(
            delete(RefreshSession).where(RefreshSession.user_id == user_id)
        )
        await session.commit()
        return result.rowcount


# ─── Counts ───────────────────────────────────────────────────────────────────

async def get_active_session_count_repo() -> int:
    """Count of all active (non-revoked, non-expired) sessions platform-wide."""
    async with get_async_session() as session:
        now = datetime.now(timezone.utc)
        stmt = select(func.count(RefreshSession.session_id)).where(
            RefreshSession.revoked_at.is_(None),
            RefreshSession.expires_at > now,
        )
        result = await session.execute(stmt)
        return result.scalar() or 0


async def get_user_active_sessions_repo(user_id: int) -> int:
    """Count of active sessions for a specific user."""
    async with get_async_session() as session:
        now = datetime.now(timezone.utc)
        stmt = select(func.count(RefreshSession.session_id)).where(
            RefreshSession.user_id == user_id,
            RefreshSession.revoked_at.is_(None),
            RefreshSession.expires_at > now,
        )
        result = await session.execute(stmt)
        return result.scalar() or 0