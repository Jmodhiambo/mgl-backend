#!/usr/bin/env python3
"""FastAPI router — User Sessions.

Endpoints
---------
GET    /user/sessions                   → list my active sessions
DELETE /user/sessions/{session_id}      → revoke one session
DELETE /user/sessions                   → sign out all other devices

"""

from fastapi import APIRouter, Depends

from app.core.security import require_user
from app.schemas.refresh_session import (
    RefreshSessionOut,
    RevokeAllOtherSessionsRequest,
    RevokeAllOtherSessionsResponse,
)
from app.services.ref_session_services import (
    get_my_sessions_service,
    revoke_single_session_service,
    revoke_all_other_sessions_service,
)

router = APIRouter()


@router.get(
    "/user/sessions",
    response_model=list[RefreshSessionOut],
    summary="List my active sessions",
    description=(
        "Returns all non-revoked, non-expired RefreshSessions for the "
        "currently authenticated user.  Feeds the 'Active Sessions' tab "
        "on the user profile page."
    ),
)
async def get_my_sessions(current_user=Depends(require_user)):
    """Return only the ACTIVE sessions for the current user."""
    return await get_my_sessions_service(user_id=current_user.id)


@router.delete(
    "/user/sessions/{session_id}",
    status_code=204,
    summary="Revoke one session",
    description=(
        "Soft-revokes a single RefreshSession by setting revoked_at.  "
        "Users may only revoke their own sessions.  "
        "Returns 204 on success, 404 if not found or not owned."
    ),
)
async def revoke_session(
    session_id: str,
    current_user=Depends(require_user),
):
    """Revoke one specific session, ownership-checked."""
    await revoke_single_session_service(
        user_id=current_user.id,
        session_id=session_id,
    )


@router.delete(
    "/user/sessions",
    response_model=RevokeAllOtherSessionsResponse,
    summary="Sign out all other devices",
    description=(
        "Revokes every active session for the current user EXCEPT the one "
        "identified by current_session_id in the request body."
    ),
)
async def revoke_all_other_sessions(
    body: RevokeAllOtherSessionsRequest,
    current_user=Depends(require_user),
):
    """Revoke all sessions EXCEPT the one currently in use."""
    result = await revoke_all_other_sessions_service(
        user_id=current_user.id,
        current_session_id=body.current_session_id,
    )
    return RevokeAllOtherSessionsResponse(**result)