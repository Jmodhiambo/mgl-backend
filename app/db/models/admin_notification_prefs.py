#!/usr/bin/env python3
"""
Admin Notification Preferences model.

Lower layer of the "Settings" feature, alongside Platform Settings.

One row per admin user.  Tracks which email-notification events that
admin has enabled.  Stored separately from PlatformSettings because
these are per-user, not platform-wide.

If a row doesn't exist for an admin, the service layer treats every
toggle as True (opted-in by default).
"""

from sqlalchemy import Integer, Boolean, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from app.db.session import Base


class AdminNotificationPrefs(Base):
    """Per-admin email-notification preferences."""

    __tablename__ = "admin_notification_prefs"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_admin_notif_prefs_user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # FK to users.id (plain int — see note in platform_settings.py)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # ── Notification toggles ──────────────────────────────────────────────────
    notify_new_event: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    """Fire when a new event is submitted for approval."""

    notify_new_message: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    """Fire when a new contact message arrives."""

    notify_payment_failure: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    """Fire when a payment fails or a dispute is opened."""

    notify_new_organizer: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    """Fire when a new organizer application is submitted."""

    notify_refund_request: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    """Fire when a booking refund is requested."""

    # ── Audit timestamp ───────────────────────────────────────────────────────
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AdminNotificationPrefs user_id={self.user_id}>"