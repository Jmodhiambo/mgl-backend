#!/usr/bin/env python3
"""Database User model for MGLTickets."""

from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional
from datetime import datetime, timezone
from app.db.session import Base

if TYPE_CHECKING:
    # Avoid circular imports. Event is only imported for type hints, not executed at runtime.
    from app.db.models.event import Event
    from app.db.models.booking import Booking
    from app.db.models.ticket_instance import TicketInstance

class User(Base):
    """User model representing a user in the system."""

    __tablename__ = "users"

        # Basic account info
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="attendee")  # attendee, organizer, admin
    is_verified: Mapped[bool] = mapped_column(nullable=False, default=False)

    # Timestamps
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

    # Optional organizer-specific fields
    bio: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    """Short description or introduction of the organizer."""

    organization_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    """Name of the organizer's business or organization."""

    website: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    """Link to organizer's website."""

    profile_picture: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    """URL to organizer's profile image."""

    address: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    """Organizer's business or event address."""

    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    """Tax identification number for legal or payout purposes."""

    area_of_specialty: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    """The type of events the organizer specializes in (e.g., Music, Workshops)."""

    # Relationships
    events: Mapped[list["Event"]] = relationship("Event", back_populates="organizer")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="user")
    ticket_instances: Mapped[list["TicketInstance"]] = relationship("TicketInstance", back_populates="user")

    def __repr__(self) -> str:
        return f"<User id={self.id} name={self.name} email={self.email} role={self.role}>"