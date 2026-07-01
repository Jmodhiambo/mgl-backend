#!/usr/bin/env python3
"""FastAPI router — Audit Logs.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.security import require_admin
from app.schemas.audit_log import AuditLogListResponse, AuditLogOut
import app.services.audit_log_services as audit_log_services

router = APIRouter()


# ─── My Activity (Profile page — My Activity tab) ────────────────────────────
# IMPORTANT: this route MUST come before /{log_id} so FastAPI does not try to
# cast the literal "my" to an integer and return 422.

@router.get(
    "/admin/audit-logs/my",
    response_model=AuditLogListResponse,
    summary="My admin activity feed",
    description=(
        "Returns the currently authenticated admin's most recent audit-log "
        "entries, ordered newest-first, capped by `limit` (default 15), "
        "along with the admin's total lifetime action count. "
        "Used by the 'My Activity' tab on the My Profile page."
    ),
)
async def get_my_activity(
    limit: int = Query(default=15, ge=1, le=100, description="Max rows to return."),
    current_user=Depends(require_admin),
):
    """Return the current admin's most recent activity, newest-first, with total count."""
    return await audit_log_services.list_my_activity_service(
        admin_id=current_user.id, limit=limit
    )


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


# ─── Single entry ─────────────────────────────────────────────────────────────
# Declared LAST so "my" is never mistaken for a log_id integer.

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