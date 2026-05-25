#!/usr/bin/env python3
"""RefreshSession services for MGLTickets."""

from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status

from app.core.logging_config import logger
import app.db.repositories.ref_sessions_repo as ref_sessions_repo
from app.schemas.refresh_session import (
    RefreshSessionCreate,
    RefreshSessionOut,
    RefreshSessionUpdate,
)


# ─── Create ───────────────────────────────────────────────────────────────────

async def create_refresh_session_service(
    session_id: str,
    user_id: int,
    refresh_token_hash: str,
    expires_at: datetime,
    device_info: Optional[str],
    ip_address: Optional[str],
    location: Optional[str],
) -> RefreshSessionOut:
    """Create a new RefreshSession on login or token rotation."""
    logger.info(f"Creating RefreshSession for user_id={user_id}")
    return await ref_sessions_repo.create_refresh_session_repo(
        RefreshSessionCreate(
            session_id=session_id,
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
            device_info=device_info,
            ip_address=ip_address,
            location=location,
        )
    )


# ─── Read ─────────────────────────────────────────────────────────────────────

async def get_refresh_session_service(session_id: str) -> Optional[RefreshSessionOut]:
    """Get a RefreshSession by session_id."""
    logger.info(f"Getting RefreshSession for session_id={session_id}")
    return await ref_sessions_repo.get_refresh_session_repo(session_id)


async def get_refresh_session_by_user_id_service(user_id: int) -> list[RefreshSessionOut]:
    """Get ALL RefreshSessions for a user.

    NOTE: This now returns a list, not a single object.
    The repo fix (scalar → scalars) is what makes this correct.
    """
    logger.info(f"Getting all RefreshSessions for user_id={user_id}")
    return await ref_sessions_repo.get_refresh_session_by_user_id_repo(user_id)


async def get_my_sessions_service(user_id: int) -> list[RefreshSessionOut]:
    """Return only the ACTIVE sessions for the current user.

    NEW — used by both:
      GET /admin/profile/sessions  (admin profile page)
      GET /auth/sessions           (regular user profile, if you add one later)

    Filters out revoked and expired rows so the frontend only shows
    sessions the user can actually use right now.
    """
    logger.info(f"Fetching active sessions for user_id={user_id}")
    return await ref_sessions_repo.list_active_sessions_for_user_repo(user_id)


# ─── Update ───────────────────────────────────────────────────────────────────

async def update_refresh_session_service(
    session_id: str,
    token_hash: str,
    expires_at: datetime,
    device_info: Optional[str],
    ip_address: Optional[str],
    location: Optional[str],
) -> Optional[RefreshSessionOut]:
    """Update a RefreshSession by session_id."""
    logger.info(f"Updating RefreshSession for session_id={session_id}")
    return await ref_sessions_repo.update_refresh_session_repo(
        session_id,
        RefreshSessionUpdate(
            session_id=session_id,
            refresh_token_hash=token_hash,
            expires_at=expires_at,
            device_info=device_info,
            ip_address=ip_address,
            location=location,
        ),
    )


# ─── Revoke ───────────────────────────────────────────────────────────────────

async def revoke_refresh_session_service(
    session_id: str, new_session_id: str
) -> Optional[RefreshSessionOut]:
    """Soft-revoke a session during token rotation."""
    logger.info(f"Revoking RefreshSession {session_id} → replaced by {new_session_id}")
    return await ref_sessions_repo.revoke_refresh_session_repo(session_id, new_session_id)


async def revoke_single_session_service(user_id: int, session_id: str) -> None:
    """Revoke one specific session, ownership-checked.

    NEW — used by DELETE /admin/profile/sessions/{session_id}.
    The user may only revoke their own sessions.
    Raises 404 if not found/not owned, 400 if already revoked.
    """
    success = await ref_sessions_repo.revoke_single_session_for_user_repo(user_id, session_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found, already revoked, or does not belong to you.",
        )
    logger.info(f"Session {session_id} revoked by user_id={user_id}")


async def revoke_all_other_sessions_service(
    user_id: int, current_session_id: str
) -> dict:
    """Revoke all sessions for a user EXCEPT the one currently in use.

    NEW — used by DELETE /admin/profile/sessions (sign out all other devices).
    Returns a summary dict for the response body.
    """
    logger.info(
        f"Revoking all other sessions for user_id={user_id}, "
        f"keeping {current_session_id}"
    )
    sessions = await ref_sessions_repo.list_active_sessions_for_user_repo(user_id)
    count = 0
    for s in sessions:
        if s.session_id == current_session_id:
            continue
        await ref_sessions_repo.revoke_single_session_for_user_repo(user_id, s.session_id)
        count += 1

    logger.info(f"{count} other session(s) revoked for user_id={user_id}")
    return {
        "revoked_count": count,
        "message": f"{count} other session(s) have been signed out.",
    }


async def delete_refresh_session_service(session_id: str) -> bool:
    """Hard-delete a session by session_id (used on logout)."""
    logger.info(f"Deleting RefreshSession for session_id={session_id}")
    return await ref_sessions_repo.delete_refresh_session_repo(session_id)


# ─── Cleanup ──────────────────────────────────────────────────────────────────

async def cleanup_expired_and_revoked_sessions_service(hours: int = 24) -> dict:
    """Hard-delete expired and revoked sessions older than `hours`.

    Called by POST /admin/auth/cleanup-sessions.
    """
    logger.info(f"Starting session cleanup (threshold: {hours}h)...")
    deleted_count = await ref_sessions_repo.cleanup_expired_and_revoked_sessions_repo(hours)
    active_count = await ref_sessions_repo.get_active_session_count_repo()
    logger.info(
        f"Cleanup done: {deleted_count} deleted, {active_count} active remaining"
    )
    return {
        "deleted_count": deleted_count,
        "active_sessions": active_count,
        "cleanup_threshold_hours": hours,
    }


async def cleanup_user_sessions_service(user_id: int) -> dict:
    """Hard-delete ALL sessions for a user ('logout from all devices').

    FIXED: parameter was typed `str`, now correctly `int`.
    Called by POST /auth/logout-all-devices.
    """
    logger.info(f"Cleaning up all sessions for user_id={user_id}...")
    deleted_count = await ref_sessions_repo.cleanup_all_user_sessions_repo(user_id)
    logger.info(f"Deleted {deleted_count} sessions for user_id={user_id}")
    return {
        "deleted_count": deleted_count,
        "user_id": user_id,
    }


# ─── Stats ────────────────────────────────────────────────────────────────────

async def get_user_session_stats_service(user_id: int) -> dict:
    """Session stats for a specific user.

    FIXED: was missing user_id parameter — the original always failed
    because the repo function requires it.
    Called by GET /auth/session-stats.
    """
    active_sessions = await ref_sessions_repo.get_user_active_sessions_repo(user_id)
    return {
        "user_id": user_id,
        "active_sessions": active_sessions,
    }