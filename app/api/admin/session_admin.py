#!/usr/bin/env python3
"""FastAPI router — Admin Sessions.

Endpoints
---------
GET    /admin/sessions                  → list my active sessions
DELETE /admin/sessions/{session_id}     → revoke one session
DELETE /admin/sessions                  → sign out all other devices

"""

from fastapi import APIRouter, BackgroundTasks, Depends

from app.core.security import require_admin
from app.schemas.refresh_session import RefreshSessionOut, RevokeAllOtherSessionsRequest, RevokeAllOtherSessionsResponse
from app.services.ref_session_services import (
    get_my_sessions_service,
    revoke_single_session_service,
    revoke_all_other_sessions_service,
)
from app.services.audit_log_services import log_admin_action_service

router = APIRouter()


@router.get(
    "/admin/sessions",
    response_model=list[RefreshSessionOut],
    summary="List my active sessions",
    description=(
        "Returns all non-revoked, non-expired RefreshSessions for the "
        "currently authenticated admin.  Feeds the 'Active Sessions' tab "
        "on the My Profile page.\n\n"
        "Data source: RefreshSession table (no separate AdminSession table)."
    ),
)
async def get_my_sessions(current_user=Depends(require_admin)):
    """Return only the ACTIVE sessions for the current admin."""
    return await get_my_sessions_service(user_id=current_user.id)


@router.delete(
    "/admin/sessions/{session_id}",
    status_code=204,
    summary="Revoke one session",
    description=(
        "Soft-revokes a single RefreshSession by setting revoked_at.  "
        "Admins may only revoke their own sessions from this endpoint.  "
        "Returns 204 on success, 404 if not found or not owned."
    ),
)
async def revoke_session(
    session_id: str,
    background_tasks: BackgroundTasks,
    current_user=Depends(require_admin),
):
    """Revoke one specific session, ownership-checked."""
    await revoke_single_session_service(
        user_id=current_user.id,
        session_id=session_id,
    )

    background_tasks.add_task(
        log_admin_action_service,
        admin_id=current_user.id,
        admin_name=current_user.name,
        action="revoke_session",
        target_type="session",
        target_id=None,
        details={"session_id": session_id},
    )


@router.delete(
    "/admin/sessions",
    response_model=RevokeAllOtherSessionsResponse,
    summary="Sign out all other devices",
    description=(
        "Revokes every active RefreshSession for the current admin EXCEPT "
        "the one passed in current_session_id.  "
        "The frontend reads current_session_id from the JWT 'sid' claim."
    ),
)
async def revoke_all_other_sessions(
    body: RevokeAllOtherSessionsRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(require_admin),
):
    """Revoke all sessions EXCEPT the one currently in use."""
    result = await revoke_all_other_sessions_service(
        user_id=current_user.id,
        current_session_id=body.current_session_id,
    )

    background_tasks.add_task(
        log_admin_action_service,
        admin_id=current_user.id,
        admin_name=current_user.name,
        action="revoke_all_other_sessions",
        target_type="session",
        target_id=None,
        details={"revoked_count": result.get("revoked_count")},
    )

    return RevokeAllOtherSessionsResponse(**result)