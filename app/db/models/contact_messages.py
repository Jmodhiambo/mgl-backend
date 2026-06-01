#!/usr/bin/env python3
"""ContactMessage model."""

from sqlalchemy import Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
from app.db.session import Base

if TYPE_CHECKING:
    from app.db.models.user import User  # pylint: disable=cyclic-import


class ContactMessage(Base):
    """Database ContactMessage model for MGLTickets."""

    __tablename__ = "contact_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    reference_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)

    # Source distinguishes which form submitted this message.
    # Values: "user" | "organizer"
    source: Mapped[str] = mapped_column(String(20), index=True, nullable=False, default="user")

    # User Information
    # Fix: Mapped[str] on nullable columns — must be Mapped[Optional[str]]
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Message Details
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    message: Mapped[str] = mapped_column(String(2000), nullable=False)

    # Organizer-specific field — human-readable event title for easy admin reference.
    # Null for user-sourced messages.
    event_title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Status Tracking
    status: Mapped[str] = mapped_column(String(50), index=True, nullable=False, default="new")   # new, pending, responded, closed, spam
    priority: Mapped[str] = mapped_column(String(50), nullable=False, default="normal")          # low, normal, high, urgent

    # Assignment (for future use)
    assigned_to: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Metadata
    client_ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    recaptcha_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
    )
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="contact_messages")

    def __repr__(self) -> str:
        return f"<ContactMessage id={self.id} source={self.source} ref={self.reference_id} event_title={self.event_title}>"