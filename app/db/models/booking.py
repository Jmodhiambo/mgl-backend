#!/usr/bin/env python3
"""Booking model for MGLTickets.

Each Booking represents ONE ticket type + quantity within an Order.
A single checkout (Order) with 2 ticket types produces 2 Booking rows,
both sharing the same order_id, all paid for by one Payment on the Order.
"""

from sqlalchemy import ForeignKey, Integer, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from datetime import datetime, timezone
from app.db.session import Base

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.event import Event
    from app.db.models.ticket_type import TicketType
    from app.db.models.order import Order
    from app.db.models.ticket_instance import TicketInstance
    from app.db.models.organizer_email_recipients import OrganizerEmailRecipients

class Booking(Base):
    """Booking model representing one ticket-type line item within an Order."""

    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"), nullable=False)
    ticket_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("ticket_types.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")  # mirrors Order.status
    total_price: Mapped[int] = mapped_column(nullable=False)  # line total: ticket_type.price * quantity, at time of booking
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
    order: Mapped["Order"] = relationship("Order", back_populates="bookings")
    user: Mapped["User"] = relationship("User", back_populates="bookings")
    event: Mapped["Event"] = relationship("Event", back_populates="bookings")
    ticket_type: Mapped["TicketType"] = relationship("TicketType", back_populates="bookings")
    ticket_instances: Mapped[list["TicketInstance"]] = relationship("TicketInstance", back_populates="booking")
    organizer_email_recipients: Mapped[list["OrganizerEmailRecipients"]] = relationship("OrganizerEmailRecipients", back_populates="booking")

    def __repr__(self) -> str:
        return (
            f"<Booking id={self.id} order_id={self.order_id} user_id={self.user_id} "
            f"ticket_type_id={self.ticket_type_id} quantity={self.quantity} "
            f"status={self.status!r} total_price={self.total_price}>"
        )