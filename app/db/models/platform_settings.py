#!/usr/bin/env python3
"""
Platform Settings model — singleton table (always one row, id=1). 

Lower layer of the "Settings" feature alongside Admin Notification Preferences.

Stores all platform-wide configuration that the admin panel can read/write.
Intentionally kept as one flat table so a single GET/PUT covers every tab
in the Settings page without joins.
"""

from sqlalchemy import Integer, String, Boolean, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING, Optional
from datetime import datetime, timezone

from app.db.session import Base

if TYPE_CHECKING:
    from app.db.models.user import User

class PlatformSettings(Base):
    """
    Singleton configuration table.

    Usage contract:
      - There is exactly ONE row in this table (id = 1).
      - On first startup, a database seed / Alembic data-migration inserts
        that row with the defaults shown below.
      - All reads use  SELECT … WHERE id = 1.
      - All writes use UPDATE … WHERE id = 1.
      - No INSERT is ever issued from the application layer after seeding.
    """

    __tablename__ = "platform_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    # ── General / Identity ────────────────────────────────────────────────────
    platform_name: Mapped[str] = mapped_column(
        String(100), nullable=False, default="MGLTickets"
    )
    platform_email: Mapped[str] = mapped_column(
        String(150), nullable=False, default="admin@mgltickets.com"
    )
    support_email: Mapped[str] = mapped_column(
        String(150), nullable=False, default="support@mgltickets.com"
    )

    # ── Locale & Currency ─────────────────────────────────────────────────────
    default_currency: Mapped[str] = mapped_column(
        String(10), nullable=False, default="KES"
    )
    timezone: Mapped[str] = mapped_column(
        String(60), nullable=False, default="Africa/Nairobi"
    )

    # ── Platform / Business rules ─────────────────────────────────────────────
    platform_fee_percent: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=7.0
    )
    require_event_approval: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    allow_user_registration: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    allow_organizer_signup: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    enable_refunds: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    max_tickets_per_booking: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10
    )

    # ── Security ──────────────────────────────────────────────────────────────
    session_timeout_hours: Mapped[int] = mapped_column(
        Integer, nullable=False, default=24
    )

    # ── Maintenance ───────────────────────────────────────────────────────────
    maintenance_mode: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # ── Audit timestamps ──────────────────────────────────────────────────────
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_by_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # ── Relationships ──────────────────────────────────────────────────────
    updated_by_user: Mapped[Optional["User"]] = relationship("User", back_populates="platform_settings_updates")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<PlatformSettings platform_name={self.platform_name!r} "
            f"maintenance_mode={self.maintenance_mode}>"
        )