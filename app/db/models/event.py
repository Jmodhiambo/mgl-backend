#!/usr/bin/env python3
"""Database Event model for MGLTickets."""

from sqlalchemy import ForeignKey, Integer, String, Boolean, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
from app.db.session import Base

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.order import Order
    from app.db.models.booking import Booking
    from app.db.models.ticket_type import TicketType
    from app.db.models.favorites import Favorite
    from app.db.models.co_organizer import CoOrganizer
    from app.db.models.organizer_emails import OrganizerEmails


class Event(Base):
    """Event model representing an event in the system."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True, default=None)
    venue: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── Location fields ───────────────────────────────────────────────────────
    city: Mapped[str] = mapped_column(String(100), nullable=False, default="Nairobi")
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="Kenya")

    # ── Category ──────────────────────────────────────────────────────────────
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="Other")

    # ── Schedule ──────────────────────────────────────────────────────────────
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # ── Flyer ─────────────────────────────────────────────────────────────────
    original_filename: Mapped[str] = mapped_column(String(200), nullable=False)
    flyer_url: Mapped[str] = mapped_column(String(500), nullable=False)

    # ── Status / approval ─────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="upcoming")
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rejected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # is_active: Show if the event is currently happening. When time is in-between start and end, is_active=True.
    # When the event is cancelled or deleted, is_active=False. This is the primary signal for whether the event is currently active.
    @property
    def is_active(self) -> bool:
        """Determine if the event is currently active based on its status and approval."""
        now = datetime.now(timezone.utc)
        return (
            self.is_approved
            and self.status not in ["deleted", "cancelled"]  # "deleted" and "cancelled"
            and self.start_time <= now <= self.end_time
        )

    # ── Commission ────────────────────────────────────────────────────────────
    # commission_rate is copied from platform_settings.platform_fee_percent at
    # event creation time so that a later change to the platform default does
    # not retroactively alter existing events.
    commission_rate: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, default=7.0,
        comment="Platform fee % locked in at event creation time",
    )
    commission_source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="platform_default",
        comment="platform_default | negotiated",
    )
    # Populated only when commission_source == 'negotiated'
    commission_approved_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Admin user ID who approved a negotiated rate",
    )
    commission_approved_by_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="Denormalised admin display name — avoids a join on every read",
    )
    commission_approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Timestamp when the negotiated rate was approved",
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    organizer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    organizer: Mapped["User"] = relationship(
        "User", back_populates="events", foreign_keys=[organizer_id]
    )
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="event")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="event")
    ticket_types: Mapped[list["TicketType"]] = relationship(
        "TicketType", back_populates="event"
    )
    favorites: Mapped[list["Favorite"]] = relationship(
        "Favorite", back_populates="event"
    )
    co_organizers: Mapped[list["CoOrganizer"]] = relationship(
        "CoOrganizer", back_populates="event"
    )
    organizer_emails: Mapped[list["OrganizerEmails"]] = relationship(
        "OrganizerEmails", back_populates="event"
    )

    def __repr__(self) -> str:
        return (
            f"<Event id={self.id} title={self.title!r} "
            f"venue={self.venue!r} start={self.start_time}>"
        )