#!/usr/bin/env python3
"""TicketType model for MGLTickets."""

from sched import Event
from sqlalchemy import ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional
from datetime import datetime, timezone
from app.db.session import Base

if TYPE_CHECKING:
    # Avoid circular imports. Booking is only imported for type hints, not executed at runtime.
    from app.db.models.booking import Booking
    from app.db.models.event import Event
    from app.db.models.ticket_instance import TicketInstance

class TicketType(Base):
    """TicketType model representing different types of tickets for events."""

    __tablename__ = "ticket_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # i.e Standard, VIP, Early Bird, VVIP, Regular
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, default=None)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    total_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_sold: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
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

    # Relationship to Booking model
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="ticket_type")

    # Relationship to Event model
    event: Mapped["Event"] = relationship("Event", back_populates="ticket_types")

    # Relationship to TicketInstance model
    ticket_instances: Mapped[list["TicketInstance"]] = relationship("TicketInstance", back_populates="ticket_type")

    def __repr__(self) -> str:
        return f"<TicketType id={self.id} event_id={self.event_id} name={self.name} price={self.price} available_quantity={self.quantity_available} created_at={self.created_at} updated_at={self.updated_at}>"