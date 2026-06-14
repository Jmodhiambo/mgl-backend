#!/usr/bin/env python3
"""Order model for MGLTickets.

An Order represents a single checkout — one or more ticket types for one
event, paid for with a single payment (one STK push). Each ticket type in
the order becomes its own Booking row (order_id FK), preserving the
existing per-ticket-type Booking shape that admin/organizer pages rely on.
"""

from sqlalchemy import ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
from datetime import datetime, timezone
from app.db.session import Base

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.event import Event
    from app.db.models.booking import Booking
    from app.db.models.payment import Payment


class Order(Base):
    """Order model — groups one or more Bookings (one per ticket type)
    under a single payment."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"), nullable=False)
    total_price: Mapped[int] = mapped_column(Integer, nullable=False)  # sum of all line totals (no processing fee)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")  # pending, confirmed, cancelled
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

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")
    event: Mapped["Event"] = relationship("Event")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="order")
    payment: Mapped["Payment"] = relationship("Payment", back_populates="order", uselist=False)

    def __repr__(self) -> str:
        return (
            f"<Order id={self.id} user_id={self.user_id} event_id={self.event_id} "
            f"total_price={self.total_price} status={self.status!r}>"
        )