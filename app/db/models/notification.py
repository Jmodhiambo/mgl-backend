#!/usr/bin/env python3
"""Notification model for MGLTickets.

Each row represents one notification delivered to one recipient (admin or user).
The table is written to by every domain service that needs to surface an alert
(events, bookings, payments, contact messages, user management, system tasks).

Schema decisions
────────────────
• recipient_id / recipient_role  – who the notification is for.
  Admin-targeted notifications use recipient_role = 'admin' and recipient_id = NULL
  so every admin sees them.  User-targeted ones set both fields.
• category       – maps 1-to-1 with the frontend NotifCategory union type.
• priority       – 'high' | 'medium' | 'low'  (same as frontend).
• source_type    – the domain entity that triggered the notification
                   (event, booking, payment, message, user, system).
• source_id      – the PK of that entity, useful for deep-linking.
• action_url     – optional relative URL for the frontend "View →" link.
• is_read        – toggled by the recipient; never deleted automatically.
• expires_at     – optional hard expiry; the cleanup job prunes expired rows.
"""

from sqlalchemy import ForeignKey, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional
from datetime import datetime, timezone
from app.db.session import Base

if TYPE_CHECKING:
    from app.db.models.user import User


class Notification(Base):
    """Notification model – one row per recipient per event."""

    __tablename__ = "notifications"

    # ── Primary key ──────────────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ── Recipient ─────────────────────────────────────────────────────────────
    recipient_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    """FK to users.id.  NULL means "all admins" (broadcast)."""

    recipient_role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="admin", index=True
    )
    """'admin' | 'user' | 'organizer'  – used for role-based fan-out."""

    # ── Content ───────────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Classification ────────────────────────────────────────────────────────
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    """'event' | 'user' | 'payment' | 'message' | 'system'"""

    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default="medium"
    )
    """'high' | 'medium' | 'low'"""

    # ── Source entity (for deep-linking & dedup) ──────────────────────────────
    source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    """'event' | 'booking' | 'payment' | 'message' | 'user' | 'system'"""

    source_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    """PK of the source entity."""

    action_url: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    """Relative frontend URL, e.g. '/events/{slug}' or '/payments'."""

    # ── State ─────────────────────────────────────────────────────────────────
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    """Optional hard expiry. Rows past this date are pruned by cleanup job."""

    # ── Relationship (optional – useful for ORM joins) ────────────────────────
    recipient: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="notifications",
    )

    def __repr__(self) -> str:
        return (
            f"<Notification id={self.id} category={self.category} "
            f"priority={self.priority} is_read={self.is_read}>"
        )