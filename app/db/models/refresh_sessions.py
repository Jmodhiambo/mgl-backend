#!/usr/bin/env python3
"""Database RefreshSession model for MGLTickets."""

from sqlalchemy import ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional, List
from datetime import datetime, timezone
from app.db.session import Base

if TYPE_CHECKING:
    from app.db.models.user import User  # pylint: disable=cyclic-import


class RefreshSession(Base):
    """Database RefreshSession model for MGLTickets."""

    __tablename__ = "refresh_sessions"

    session_id: Mapped[str] = mapped_column(String(255), primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    refresh_token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
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

    user: Mapped[List["User"]] = relationship("User", back_populates="refresh_sessions")

    def __repr__(self) -> str:
        """Return a string representation of the RefreshSession model."""
        return f"RefreshSession(session_id={self.session_id!r}, user_id={self.user_id!r})"