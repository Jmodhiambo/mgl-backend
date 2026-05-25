#!/usr/bin/env python3
"""Service layer for AdminSession.

Business logic for the profile-page 'Active Sessions' tab and
the login flow that records a new session on every admin sign-in.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status

from app.core.logging_config import logger
from app.schemas.admin_session import (
    AdminSessionCreate,
    AdminSessionOut,
    RevokeAllOtherSessionsResponse,
)
import app.db.repositories.admin_session_repo as admin_session_repo

# Default session lifetime — overridden by platform settings when that table exists.
DEFAULT_SESSION_TIMEOUT_HOURS = 24


async def create_admin_session_service(
    user_id: int,
    device_info: Optional[str] = None,
    ip_address: Optional[str] = None,
    location: Optional[str] = None,
    timeout_hours: int = DEFAULT_SESSION_TIMEOUT_HOURS,
) -> AdminSessionOut:
    """Record a new admin session on login.

    Call this from the admin login endpoint immediately after the JWT
    is issued so the profile 'Sessions' tab can show all active devices.

    Example usage in your login route::

        session = await create_admin_session_service(
            user_id=user.id,
            device_info=request.headers.get("User-Agent"),
            ip_address=request.client.host,
        )
        # store session.id in the JWT payload or a cookie so that
        # touch_session_service() can be called on subsequent requests
    """
    logger.info(f"Creating admin session for user_id={user_id} ip={ip_address}")

    expires_at = datetime.now(timezone.utc) + timedelta(hours=timeout_hours)
    data = AdminSessionCreate(
        user_id=user_id,
        device_info=device_info,
        ip_address=ip_address,
        location=location,
        expires_at=expires_at,
    )
    session = await admin_session_repo.create_admin_session_repo(data)
    logger.info(f"Admin session {session.id} created for user_id={user_id}")
    return session


async def get_my_active_sessions_service(user_id: int) -> list[AdminSessionOut]:
    """Return all active sessions for the currently logged-in admin.

    Used by GET /admin/profile/sessions.
    """
    logger.info(f"Fetching active sessions for admin user_id={user_id}")
    return await admin_session_repo.list_active_sessions_for_user_repo(user_id)


async def revoke_session_service(
    requesting_user_id: int,
    session_id: int,
    reason: str = "admin_revoked",
) -> None:
    """Revoke a specific session.

    Admins may only revoke their own sessions via the profile page.
    Raises 404 if not found, 403 if they don't own it,
    400 if it is already inactive.
    """
    existing = await admin_session_repo.get_admin_session_by_id_repo(session_id)

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found."
        )
    if existing.user_id != requesting_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only revoke your own sessions.",
        )
    if not existing.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is already inactive.",
        )

    await admin_session_repo.revoke_admin_session_repo(session_id, reason)
    logger.info(
        f"Session {session_id} revoked by user_id={requesting_user_id} "
        f"reason={reason}"
    )


async def revoke_all_other_sessions_service(
    user_id: int,
    current_session_id: int,
) -> RevokeAllOtherSessionsResponse:
    """Sign out of every device except the current one.

    Used by DELETE /admin/profile/sessions — revokes all but current_session_id.
    Returns a response with the count of sessions revoked.
    """
    logger.info(
        f"Revoking all other sessions for user_id={user_id} "
        f"keeping session {current_session_id}"
    )
    count = await admin_session_repo.revoke_all_sessions_for_user_repo(
        user_id=user_id,
        except_session_id=current_session_id,
    )
    logger.info(f"{count} sessions revoked for user_id={user_id}")
    return RevokeAllOtherSessionsResponse(
        revoked_count=count,
        message=f"{count} other session(s) have been signed out.",
    )


async def touch_session_service(session_id: int) -> None:
    """Bump last_active_at to now.

    Wire this into your admin auth middleware so it fires on every
    authenticated request, e.g.::

        @app.middleware("http")
        async def update_admin_session_activity(request, call_next):
            session_id = extract_session_id_from_jwt(request)
            if session_id:
                await touch_session_service(session_id)
            return await call_next(request)
    """
    await admin_session_repo.touch_admin_session_repo(session_id)