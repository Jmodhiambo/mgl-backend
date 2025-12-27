#!/usr/bin/env python3
"""Admin auth routes."""

from fastapi import APIRouter, Depends, status
from app.core.security import require_admin
from app.services.ref_session_services import cleanup_expired_and_revoked_sessions_service

router = APIRouter()


@router.post("/admin/auth/cleanup-sessions", response_model=dict, status_code=status.HTTP_200_OK)
async def manual_cleanup_sessions(hours: int = 24, admin=Depends(require_admin)) -> dict:
    """Cleanup expired and revoked sessions."""
    return await cleanup_expired_and_revoked_sessions_service(hours)