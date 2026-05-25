#!/usr/bin/env python3
"""FastAPI router — Admin Sessions.

Place at:  app/routers/admin_profile_router.py

All session data comes from RefreshSession (no separate AdminSession
table).  Prefix is /admin/sessions — this router serves only session
management, not the full profile page.

Endpoints
---------
GET    /admin/sessions                  → list my active sessions
DELETE /admin/sessions/{session_id}     → revoke one session
DELETE /admin/sessions                  → sign out all other devices

The current_session_id used in the 'revoke all others' call is the `sid`
claim embedded in the admin's JWT.  Make sure your require_admin dependency
exposes it as current_user.session_id (or read it from the token directly).
"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.core.security import require_admin
from app.schemas.refresh_session import RefreshSessionOut
from app.services.ref_session_services import (
    get_my_sessions_service,
    revoke_single_session_service,
    revoke_all_other_sessions_service,
)

router = APIRouter()


# ─── Response models ──────────────────────────────────────────────────────────

class RevokeAllOtherSessionsRequest(BaseModel):
    current_session_id: str
    """The caller's own session_id (from their JWT 'sid' claim).
    This one will be kept; all others are revoked."""


class RevokeAllOtherSessionsResponse(BaseModel):
    revoked_count: int
    message: str


# ─── Routes ───────────────────────────────────────────────────────────────────

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
    current_user=Depends(require_admin),
):
    await revoke_single_session_service(
        user_id=current_user.id,
        session_id=session_id,
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
    current_user=Depends(require_admin),
):
    result = await revoke_all_other_sessions_service(
        user_id=current_user.id,
        current_session_id=body.current_session_id,
    )
    return RevokeAllOtherSessionsResponse(**result)