#!/usr/bin/env python3
"""
Admin Settings routes.

Endpoints
─────────
GET  /admin/settings                    → full platform settings object
PUT  /admin/settings                    → partial or full update
GET  /admin/settings/notifications      → notification prefs for calling admin
PUT  /admin/settings/notifications      → upsert notification prefs

The session-cleanup endpoint already exists elsewhere:
  POST /admin/auth/cleanup-sessions     (referenced by Settings.tsx)
"""

from fastapi import APIRouter, Depends
from app.schemas.settings import (
    PlatformSettingsOut,
    PlatformSettingsUpdate,
    AdminNotificationPrefsOut,
    AdminNotificationPrefsUpdate,
)
from app.core.security import require_admin
import app.services.settings_services as settings_services

router = APIRouter()


# ─── Platform Settings ────────────────────────────────────────────────────────

@router.get("/admin/settings", response_model=PlatformSettingsOut)
async def get_platform_settings(user=Depends(require_admin)):
    """
    Return the current platform-wide settings.

    Called on Settings page mount so the form is pre-populated with
    the real values rather than the frontend's hardcoded defaults.
    """
    return await settings_services.get_platform_settings_service()


@router.put("/admin/settings", response_model=PlatformSettingsOut)
async def update_platform_settings(
    payload: PlatformSettingsUpdate,
    user=Depends(require_admin),
):
    """
    Partial or full update of platform settings.

    The frontend sends all fields from the active tab; omitted fields
    keep their current values.  Returns the full updated object so the
    frontend can sync its local state.
    """
    return await settings_services.update_platform_settings_service(
        payload=payload,
        admin_user_id=user.id,
    )


# ─── Admin Notification Preferences ──────────────────────────────────────────

@router.get("/admin/settings/notifications", response_model=AdminNotificationPrefsOut)
async def get_notification_prefs(user=Depends(require_admin)):
    """
    Return the calling admin's notification-toggle preferences.

    If the admin has never saved their prefs, returns all-True defaults
    (no row is created until the first PUT).
    """
    return await settings_services.get_admin_notification_prefs_service(
        user_id=user.id
    )


@router.put("/admin/settings/notifications", response_model=AdminNotificationPrefsOut)
async def update_notification_prefs(
    payload: AdminNotificationPrefsUpdate,
    user=Depends(require_admin),
):
    """
    Create or update the calling admin's notification preferences.

    Partial update — only supplied toggles are changed.
    """
    return await settings_services.update_admin_notification_prefs_service(
        user_id=user.id,
        payload=payload,
    )