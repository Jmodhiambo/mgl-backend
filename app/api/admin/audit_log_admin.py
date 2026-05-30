#!/usr/bin/env python3
"""FastAPI router — Audit Logs.

Place at:  app/routers/audit_log_router.py

Mount in main.py / app factory:
    app.include_router(audit_log_router, tags=["Audit Logs"])

All routes require require_admin.

Covered endpoints
-----------------
GET  /admin/audit-logs                 → paginated + filtered list  (AuditLogs.tsx)
GET  /admin/audit-logs/{log_id}        → single entry detail
GET  /admin/audit-logs/my              → activity feed for current admin (MyProfile.tsx)
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.security import require_admin
from app.schemas.audit_log import AuditLogListResponse, AuditLogOut
import app.services.audit_log_services as audit_log_services

router = APIRouter()


# ─── Main Audit Logs page ─────────────────────────────────────────────────────

@router.get(
    "/admin/audit-logs",
    response_model=AuditLogListResponse,
    summary="List audit logs (filtered + paginated)",
    description=(
        "Returns a paginated list of audit-log entries with an optional set of "
        "filters.  All query params are optional — omitting them returns all "
        "entries ordered newest-first.\n\n"
        "**Used by:** AuditLogs.tsx main table."
    ),
)
async def list_audit_logs(
    admin_id: Optional[int] = Query(
        default=None,
        description="Filter by the admin who performed the action.",
    ),
    action: Optional[str] = Query(
        default=None,
        description=(
            "Filter by action string, e.g. 'event_approved', 'user_deactivated'."
        ),
    ),
    target_type: Optional[str] = Query(
        default=None,
        description="Filter by target resource type: 'user', 'event', 'booking', etc.",
    ),
    from_dt: Optional[datetime] = Query(
        default=None,
        alias="from",
        description="ISO-8601 datetime — return entries created on or after this time.",
    ),
    to_dt: Optional[datetime] = Query(
        default=None,
        alias="to",
        description="ISO-8601 datetime — return entries created on or before this time.",
    ),
    limit: int = Query(default=200, ge=1, le=500, description="Max rows to return."),
    offset: int = Query(default=0, ge=0, description="Rows to skip for pagination."),
    _current_user=Depends(require_admin),
):
    return await audit_log_services.list_audit_logs_service(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        from_dt=from_dt,
        to_dt=to_dt,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/admin/audit-logs/{log_id}",
    response_model=AuditLogOut,
    summary="Get a single audit-log entry",
    description="Fetch full details of one audit-log entry by its ID.",
)
async def get_audit_log(
    log_id: int,
    _current_user=Depends(require_admin),
):
    return await audit_log_services.get_audit_log_service(log_id)


# ─── My Activity (Profile page — My Activity tab) ────────────────────────────

@router.get(
    "/admin/audit-logs/my",
    response_model=list[AuditLogOut],
    summary="My admin activity feed",
    description=(
        "Returns all audit-log entries created by the currently authenticated "
        "admin, ordered newest-first.  Used by the 'My Activity' tab on the "
        "My Profile page."
    ),
)
async def get_my_activity(current_user=Depends(require_admin)):
    """Return all activity for the current admin."""
    return await audit_log_services.list_my_activity_service(admin_id=current_user.id)