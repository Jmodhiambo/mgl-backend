#!/usr/bin/env python3
"""
Pydantic schemas for the Settings feature (PlatformSettings, AdminNotificationPrefs).

Naming convention matches the rest of the project:
  - *Out   → response shape sent to the frontend
  - *Update → request body for PUT/PATCH endpoints
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


# ─── Platform Settings ────────────────────────────────────────────────────────

class PlatformSettingsOut(BaseModel):
    """
    Full settings object returned by GET /admin/settings.
    Mirrors the PlatformSettings model exactly so the frontend
    can replace its defaultSettings object wholesale.
    """

    model_config = ConfigDict(from_attributes=True)

    # General
    platform_name: str
    platform_email: str
    support_email: str

    # Locale
    default_currency: str
    timezone: str

    # Platform rules
    platform_fee_percent: float
    require_event_approval: bool
    allow_user_registration: bool
    allow_organizer_signup: bool
    enable_refunds: bool
    max_tickets_per_booking: int

    # Security
    session_timeout_hours: int

    # Maintenance
    maintenance_mode: bool

    # Audit
    updated_at: datetime
    updated_by_user_id: Optional[int] = None

    class Config:
        from_attributes = True


class PlatformSettingsUpdate(BaseModel):
    """
    Request body for PUT /admin/settings.

    Every field is optional so the frontend can send a partial object
    (e.g. only the fields on the active tab).  The service layer applies
    only the supplied keys to the singleton row.
    """

    platform_name: Optional[str] = Field(None, min_length=1, max_length=100)
    platform_email: Optional[str] = None          # validated as email in service
    support_email: Optional[str] = None

    default_currency: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=60)

    platform_fee_percent: Optional[float] = Field(None, ge=0, le=100)
    require_event_approval: Optional[bool] = None
    allow_user_registration: Optional[bool] = None
    allow_organizer_signup: Optional[bool] = None
    enable_refunds: Optional[bool] = None
    max_tickets_per_booking: Optional[int] = Field(None, ge=1, le=100)

    session_timeout_hours: Optional[int] = Field(None, ge=1, le=720)

    maintenance_mode: Optional[bool] = None

    class Config:
        from_attributes = True


# ─── Admin Notification Preferences ──────────────────────────────────────────

class AdminNotificationPrefsOut(BaseModel):
    """
    Notification preferences for the currently-authenticated admin.
    Returned by GET /admin/settings/notifications.
    """

    model_config = ConfigDict(from_attributes=True)

    user_id: int
    notify_new_event: bool
    notify_new_message: bool
    notify_payment_failure: bool
    notify_new_organizer: bool
    notify_refund_request: bool
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminNotificationPrefsUpdate(BaseModel):
    """
    Request body for PUT /admin/settings/notifications.
    All fields optional for partial updates.
    """

    notify_new_event: Optional[bool] = None
    notify_new_message: Optional[bool] = None
    notify_payment_failure: Optional[bool] = None
    notify_new_organizer: Optional[bool] = None
    notify_refund_request: Optional[bool] = None

    class Config:
        from_attributes = True