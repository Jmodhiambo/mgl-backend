#!/usr/bin/env python3
"""
Service layer for the Settings feature.

Handles business-logic validation, builds the response objects, and calls
the repository.  Follows the same pattern as user_services.py.
"""

from fastapi import HTTPException, status
from typing import Optional

from app.core.logging_config import logger
import app.db.repositories.settings_repo as settings_repo
from app.schemas.settings import (
    PlatformSettingsOut,
    PlatformSettingsUpdate,
    AdminNotificationPrefsOut,
    AdminNotificationPrefsUpdate,
)
from app.db.models.admin_notification_prefs import AdminNotificationPrefs


# ─── Default notification prefs (used when no DB row exists yet) ──────────────

_DEFAULT_NOTIF_PREFS = {
    "notify_new_event": True,
    "notify_new_message": True,
    "notify_payment_failure": True,
    "notify_new_organizer": True,
    "notify_refund_request": True,
}


def _default_notif_prefs_out(user_id: int) -> AdminNotificationPrefsOut:
    """Build an all-True prefs response without hitting the database."""
    from datetime import datetime, timezone
    return AdminNotificationPrefsOut(
        user_id=user_id,
        updated_at=datetime.now(timezone.utc),
        **_DEFAULT_NOTIF_PREFS,
    )


# ─── Platform Settings ────────────────────────────────────────────────────────

async def get_platform_settings_service() -> PlatformSettingsOut:
    """
    Return the current platform settings.

    Raises HTTP 503 if the singleton row is missing (database not seeded).
    """
    logger.info("Fetching platform settings...")
    settings = await settings_repo.get_platform_settings_repo()

    if settings is None:
        logger.error("Platform settings row missing — database may not be seeded.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Platform settings not initialised. Please run the database seed.",
        )

    return settings


async def update_platform_settings_service(
    payload: PlatformSettingsUpdate,
    admin_user_id: int,
) -> PlatformSettingsOut:
    """
    Apply a partial settings update.

    Validates email fields before persisting, then returns the full
    updated settings object.

    Args:
        payload:        Partial update from the frontend PUT body.
        admin_user_id:  ID of the admin making the change (for audit trail).
    """
    logger.info(f"Admin {admin_user_id} updating platform settings...")

    # Convert to dict, dropping None values so we only write supplied fields
    updates = payload.model_dump(exclude_none=True)

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields supplied for update.",
        )

    # Validate emails if supplied
    for email_field in ("platform_email", "support_email"):
        if email_field in updates:
            val = updates[email_field]
            if "@" not in val or "." not in val:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid email format for '{email_field}'.",
                )

    # Validate platform_fee_percent range (Pydantic catches this too, but belt-and-braces)
    if "platform_fee_percent" in updates:
        fee = updates["platform_fee_percent"]
        if not (0 <= fee <= 100):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="platform_fee_percent must be between 0 and 100.",
            )

    updated = await settings_repo.update_platform_settings_repo(
        updates=updates,
        updated_by_user_id=admin_user_id,
    )

    if updated is None:
        logger.error("Platform settings row missing during update attempt.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Platform settings not initialised. Please run the database seed.",
        )

    logger.info(f"Platform settings updated successfully by admin {admin_user_id}.")
    return updated


# ─── Admin Notification Preferences ──────────────────────────────────────────

async def get_admin_notification_prefs_service(
    user_id: int,
) -> AdminNotificationPrefsOut:
    """
    Return notification preferences for a specific admin.

    If no row exists yet (new admin, never saved prefs), returns the
    all-True defaults without writing to the database.
    """
    logger.info(f"Fetching notification prefs for admin {user_id}...")
    prefs = await settings_repo.get_admin_notification_prefs_repo(user_id)

    if prefs is None:
        logger.info(
            f"No notification prefs row for admin {user_id} — returning defaults."
        )
        return _default_notif_prefs_out(user_id)

    return prefs


async def update_admin_notification_prefs_service(
    user_id: int,
    payload: AdminNotificationPrefsUpdate,
) -> AdminNotificationPrefsOut:
    """
    Upsert notification preferences for a specific admin.

    Works as both create (first save) and partial update (subsequent saves).
    Returns the full prefs object after saving.
    """
    logger.info(f"Upserting notification prefs for admin {user_id}...")

    updates = payload.model_dump(exclude_none=True)

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields supplied for update.",
        )

    prefs = await settings_repo.upsert_admin_notification_prefs_repo(
        user_id=user_id,
        updates=updates,
    )

    logger.info(f"Notification prefs updated for admin {user_id}.")
    return prefs