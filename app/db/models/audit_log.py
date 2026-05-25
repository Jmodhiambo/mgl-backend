#!/usr/bin/env python3
"""AuditLog model — immutable record of every admin action.

Rows are INSERT-only; never updated or deleted.  The admin panel
"Audit Logs" page and "My Activity" tab both read from this table.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.db.models.user import User


class AuditLog(Base):
    """One row per admin action.  Append-only; never mutate existing rows."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ── Who performed the action ──────────────────────────────────────────────
    admin_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,   # nullable so rows survive if the admin account is deleted
        index=True,
    )
    admin_name: Mapped[str] = mapped_column(String(150), nullable=False)
    """Snapshot of the admin's display name at the time of the action.
    Stored denormalised so the log stays readable even if the user is renamed."""

    # ── What was done ─────────────────────────────────────────────────────────
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    """Snake-case action identifier, e.g. 'user_deactivated', 'event_approved'."""

    # ── What it was done to ───────────────────────────────────────────────────
    target_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    """Resource type: 'user', 'event', 'booking', 'payment', 'message', etc."""

    target_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    """Primary-key of the affected resource.  NULL for platform-level actions."""

    # ── Extra context ─────────────────────────────────────────────────────────
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    """JSON string with action-specific metadata, e.g. {"reason": "spam"}.
    Stored as TEXT to avoid a JSON column type dependency."""

    # ── When ──────────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # ── Relationship ──────────────────────────────────────────────────────────
    admin: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<AuditLog id={self.id} admin={self.admin_name} "
            f"action={self.action} target={self.target_type}#{self.target_id}>"
        )