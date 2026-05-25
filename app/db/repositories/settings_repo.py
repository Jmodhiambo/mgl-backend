#!/usr/bin/env python3
"""
Repository layer for the Settings feature.

Two concerns, cleanly separated:
  1. PlatformSettings  — singleton row (id = 1)
  2. AdminNotificationPrefs — one row per admin user_id

Both use the shared async session pattern from the rest of the codebase.
"""

from sqlalchemy import select
from datetime import datetime, timezone
from typing import Optional

from app.db.session import get_async_session
from app.db.models.platform_settings import PlatformSettings
from app.db.models.admin_notification_prefs import AdminNotificationPrefs
from app.schemas.settings import (
    PlatformSettingsOut,
    PlatformSettingsUpdate,
    AdminNotificationPrefsOut,
    AdminNotificationPrefsUpdate,
)


# ─── Singleton helpers ────────────────────────────────────────────────────────

_SETTINGS_ID = 1  # The one and only row


# ─── Platform Settings ────────────────────────────────────────────────────────

async def get_platform_settings_repo() -> Optional[PlatformSettingsOut]:
    """
    Fetch the singleton settings row.
    Returns None only if the database has never been seeded —
    the service layer raises a 500 in that case.
    """
    async with get_async_session() as session:
        result = await session.execute(
            select(PlatformSettings).where(PlatformSettings.id == _SETTINGS_ID)
        )
        platform_settings = result.scalar_one_or_none()

        return PlatformSettingsOut.model_validate(platform_settings) if platform_settings else None


async def update_platform_settings_repo(
    updates: dict,
    updated_by_user_id: Optional[int] = None,
) -> Optional[PlatformSettingsOut]:
    """
    Apply a partial dict of updates to the singleton row.

    Only keys present in `updates` are written; everything else is left
    unchanged.  This lets the frontend send only the fields on the
    currently-visible settings tab.

    Args:
        updates:             Dict of column_name → new_value pairs.
                             Keys that don't correspond to model columns
                             are silently ignored.
        updated_by_user_id:  ID of the admin performing the change
                             (written to the audit column).

    Returns:
        The updated PlatformSettings ORM object, or None if the
        singleton row is missing.
    """
    async with get_async_session() as session:
        result = await session.execute(
            select(PlatformSettings).where(PlatformSettings.id == _SETTINGS_ID)
        )
        settings = result.scalar_one_or_none()
        if not settings:
            return None

        # Apply only supplied keys
        allowed_columns = {c.key for c in PlatformSettings.__table__.columns}
        for key, value in updates.items():
            if key in allowed_columns and key not in ("id", "updated_at"):
                setattr(settings, key, value)

        if updated_by_user_id is not None:
            settings.updated_by_user_id = updated_by_user_id

        settings.updated_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(settings)
        return PlatformSettingsOut.model_validate(settings) if settings else None


# ─── Admin Notification Preferences ──────────────────────────────────────────

async def get_admin_notification_prefs_repo(
    user_id: int,
) -> Optional[AdminNotificationPrefsOut]:
    """
    Fetch notification prefs for a specific admin.
    Returns None if no row exists yet (service layer returns all-True defaults).
    """
    async with get_async_session() as session:
        result = await session.execute(
            select(AdminNotificationPrefs).where(
                AdminNotificationPrefs.user_id == user_id
            )
        )
        prefs = result.scalar_one_or_none()
        return AdminNotificationPrefsOut.model_validate(prefs) if prefs else None


async def upsert_admin_notification_prefs_repo(
    user_id: int,
    updates: dict,
) -> AdminNotificationPrefsOut:
    """
    Create or update notification prefs for an admin.

    INSERT on first call; partial UPDATE on subsequent calls.
    Only keys present in `updates` are written.

    Args:
        user_id:  The admin's user ID (FK to users.id).
        updates:  Dict of toggle_name → bool.

    Returns:
        The upserted AdminNotificationPrefs ORM object.
    """
    async with get_async_session() as session:
        result = await session.execute(
            select(AdminNotificationPrefs).where(
                AdminNotificationPrefs.user_id == user_id
            )
        )
        prefs = result.scalar_one_or_none()

        allowed_columns = {c.key for c in AdminNotificationPrefs.__table__.columns}

        if prefs is None:
            # First time — create with defaults then override supplied keys
            prefs = AdminNotificationPrefs(user_id=user_id)
            for key, value in updates.items():
                if key in allowed_columns and key not in ("id", "user_id", "updated_at"):
                    setattr(prefs, key, value)
            session.add(prefs)
        else:
            # Subsequent calls — partial update
            for key, value in updates.items():
                if key in allowed_columns and key not in ("id", "user_id", "updated_at"):
                    setattr(prefs, key, value)

        prefs.updated_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(prefs)
        
        return AdminNotificationPrefsOut.model_validate(prefs) if prefs else None