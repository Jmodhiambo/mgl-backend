#!/usr/bin/env python3
"""Database RefreshSession model for MGLTickets.
"""

from sqlalchemy import ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional, List
from datetime import datetime, timezone
from app.db.session import Base

if TYPE_CHECKING:
    from app.db.models.user import User


class RefreshSession(Base):
    """One row per issued refresh token.  Revoked rows are soft-deleted."""

    __tablename__ = "refresh_sessions"

    session_id: Mapped[str] = mapped_column(String(255), primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    refresh_token_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by_sid: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Device / network fingerprint ──────────────────────────────────────────
    device_info: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    """User-Agent string captured at login, e.g. 'Chrome/124 on macOS'."""

    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    """IPv4 or IPv6 of the login request.
    Populated from X-Real-IP (set by your reverse proxy).
    Falls back to request.client.host if the header is absent."""

    location: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    """Human-readable geo string, e.g. 'Nairobi, KE'.
    Populated by an optional GeoIP lookup in the login service.
    Leave NULL until you wire up a GeoIP library — the column is already
    there so no future migration is required."""

    # ── Relationship ──────────────────────────────────────────────────────────
    user: Mapped[List["User"]] = relationship("User", back_populates="refresh_sessions")

    # ── Computed helpers ──────────────────────────────────────────────────────
    @property
    def is_active(self) -> bool:
        """True when the session has not been revoked and has not expired.

        Used by the profile 'Active Sessions' endpoint so the frontend
        can distinguish the current live session from historical ones.
        """
        if self.revoked_at is not None:
            return False
        if datetime.now(timezone.utc) > self.expires_at:
            return False
        return True

    def __repr__(self) -> str:
        return (
            f"<RefreshSession session_id={self.session_id!r} "
            f"user_id={self.user_id!r} active={self.is_active}>"
        )