#!/usr/bin/env python3
"""Booking model for MGLTickets."""

from sqlalchemy import ForeignKey, Integer, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from datetime import datetime, timezone
from app.db.session import Base

if TYPE_CHECKING:
    # Avoid circular imports. User and Event are only imported for type hints, not executed at runtime.
    from app.db.models.user import User
    from app.db.models.event import Event
    from app.db.models.ticket_type import TicketType
    from app.db.models.payment import Payment
    from app.db.models.ticket_instance import TicketInstance

class Booking(Base):
    """Booking model representing a ticket booking in the system."""

    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"), nullable=False)
    ticket_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("ticket_types.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")  # e.g., pending, confirmed, cancelled
    total_price: Mapped[int] = mapped_column(nullable=False)
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

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="bookings")
    event: Mapped["Event"] = relationship("Event", back_populates="bookings")
    payment: Mapped["Payment"] = relationship("Payment", back_populates="booking", uselist=False)
    ticket_type: Mapped["TicketType"] = relationship("TicketType", back_populates="bookings")
    ticket_instances: Mapped[list["TicketInstance"]] = relationship("TicketInstance", back_populates="booking")

    def __repr__(self) -> str:
        return f"<Booking id={self.id} user_id={self.user_id} ticket_type_id={self.ticket_type_id} quantity={self.quantity} status={self.status} total_price={self.total_price} created_at={self.created_at} updated_at={self.updated_at}>"