#!/usr/bin/env python3
"""Admin auth routes."""

from fastapi import APIRouter, BackgroundTasks, Depends, status
from app.core.security import require_admin
from app.services.ref_session_services import cleanup_expired_and_revoked_sessions_service
from app.services.audit_log_services import log_admin_action_service

router = APIRouter()


@router.post("/admin/auth/cleanup-sessions", response_model=dict, status_code=status.HTTP_200_OK)
async def manual_cleanup_sessions(hours: int = 24, background_tasks: BackgroundTasks = None, admin=Depends(require_admin)):
    """Cleanup expired and revoked sessions."""
    res = await cleanup_expired_and_revoked_sessions_service(hours)

    if res is not None and background_tasks is not None:
        # Log the session cleanup action
        background_tasks.add_task(
            log_admin_action_service,
            admin_id=admin.id,
            admin_name=admin.name,
            action="manual_cleanup_sessions",
            target_type="session",
            target_id=None,
            details={"cleanup_hours": hours}
        )

    return res