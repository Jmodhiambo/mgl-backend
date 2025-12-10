#!/usr/bin/env python3
"""Database Event model for MGLTickets."""

from sqlalchemy import ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
from app.db.session import Base

if TYPE_CHECKING:
    # Avoid circular imports. User is only imported for type hints, not executed at runtime.
    from app.db.models.user import User
    from app.db.models.booking import Booking
    from app.db.models.ticket_type import TicketType

class Event(Base):
    """Event model representing an event in the system."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True, default=None)
    venue: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="Kenya")
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(200), nullable=False, default=None)
    flyer_url: Mapped[str] = mapped_column(String(500), nullable=False, default=None)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="upcoming")  # e.g., upcoming, ongoing, completed, cancelled, deleted
    approved: Mapped[bool] = mapped_column(nullable=False, default=False)
    rejected: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Foreign key relationship to User (organizer)
    organizer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    organizer: Mapped["User"] = relationship("User", back_populates="events")

    # Foreign key relationship to Booking (bookings)
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="event")
    ticket_types: Mapped[list["TicketType"]] = relationship("TicketType", back_populates="event")    

    def __repr__(self) -> str:
        return f"<Event id={self.id} title={self.title} location={self.venue} start_time={self.start_time}>"