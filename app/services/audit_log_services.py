#!/usr/bin/env python3
"""Service layer for AuditLog.

Place at:  app/services/audit_log_services.py

Two consumers:
  1. Other admin services call log_admin_action_service() to write entries.
  2. The router calls list_audit_logs_service() / list_my_activity_service()
     to read them back to the frontend.
"""
# Make sure to add all the action to the frontend filter list in AuditLogs.tsx when you add new ones here. This helps with filtering and display on the frontend.
from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.core.logging_config import logger
from app.schemas.audit_log import AuditLogCreate, AuditLogListResponse, AuditLogOut
import app.db.repositories.audit_log_repo as repo


# ─── Write ────────────────────────────────────────────────────────────────────

async def log_admin_action_service(
    admin_id: int,
    admin_name: str,
    action: str,
    target_type: str,
    target_id: Optional[int] = None,
    details: Optional[dict] = None,
) -> AuditLogOut:
    """Append one entry to the audit log.

    Call this from every admin service that mutates data.  Example::

        await log_admin_action_service(
            admin_id=current_user.id,
            admin_name=current_user.name,
            action="event_approved",
            target_type="event",
            target_id=event.id,
            details={"event_title": event.title},
        )

    Recognised action strings (extend freely — the frontend filter list
    in AuditLogs.tsx must stay in sync):

        user_deactivated    user_activated      user_role_changed
        user_verified       user_deleted        user_created
        event_approved      event_rejected      event_deleted
        booking_refunded    booking_deleted
        message_marked_spam message_closed      message_responded
        session_revoked     settings_updated
    """
    data = AuditLogCreate(
        admin_id=admin_id,
        admin_name=admin_name,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details or {},
    )
    entry = await repo.create_audit_log_repo(data)
    logger.info(
        f"Audit #{entry.id}: {admin_name} → {action} "
        f"{target_type}#{target_id}"
    )
    return entry


# ─── Read ─────────────────────────────────────────────────────────────────────

async def list_audit_logs_service(
    admin_id: Optional[int] = None,
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
    limit: int = 200,
    offset: int = 0,
) -> AuditLogListResponse:
    """Filtered + paginated list with a total count.

    Used by GET /admin/audit-logs (the main Audit Logs admin page).
    All query params are optional — omitting them returns everything.
    """
    logger.info("Listing audit logs...")
    items = await repo.list_audit_logs_repo(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        from_dt=from_dt,
        to_dt=to_dt,
        limit=limit,
        offset=offset,
    )
    total = await repo.count_audit_logs_repo(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        from_dt=from_dt,
        to_dt=to_dt,
    )
    return AuditLogListResponse(total=total, items=items)


async def list_my_activity_service(admin_id: int, limit: int = 15) -> AuditLogListResponse:
    """Most recent actions performed by one admin, newest-first, plus the
    admin's total lifetime action count (for display purposes — the list
    itself stays capped at `limit`).

    Used by GET /admin/audit-logs/my (the 'My Activity' profile tab).
    """
    logger.info(f"Fetching activity for admin_id={admin_id} (limit={limit})")
    items = await repo.list_audit_logs_for_admin_repo(admin_id, limit=limit)
    total = await repo.count_audit_logs_repo(admin_id=admin_id)
    return AuditLogListResponse(total=total, items=items)


async def get_audit_log_service(log_id: int) -> AuditLogOut:
    """Fetch a single audit-log entry by ID.

    Used by GET /admin/audit-logs/{log_id}.
    """
    entry = await repo.get_audit_log_by_id_repo(log_id)
    if not entry:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit log #{log_id} not found.",
        )
    return entry