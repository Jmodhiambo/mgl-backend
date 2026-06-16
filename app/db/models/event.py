#!/usr/bin/env python3
"""Database Event model for MGLTickets."""

from sqlalchemy import ForeignKey, Integer, String, Boolean, DateTime
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
    # status tracks lifecycle: upcoming | ongoing | completed | cancelled | deleted
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="upcoming")

    # is_approved: admin approval gate
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # is_active: Show if the event is currently happening. When time is in-between start and end, is_active=True.
    # When the event is cancelled or deleted, is_active=False. This is the primary signal for whether the event is currently active.
    @property
    def is_active(self) -> bool:
        """Determine if the event is currently active based on its status and approval."""
        now = datetime.now(timezone.utc)
        return (
            self.is_approved
            and self.status != "cancelled"
            and self.start_time <= now <= self.end_time
        )
    
    # rejected: kept for backwards compatibility. When the admin rejects an
    # event the repo sets is_approved=False AND is_active=False, so this
    # column is no longer the primary rejection signal. It can be used as an
    # audit flag. Will be removed in a future migration.
    rejected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

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
    organizer: Mapped["User"] = relationship("User", back_populates="events")
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