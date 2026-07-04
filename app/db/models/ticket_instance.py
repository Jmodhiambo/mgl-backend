#!/usr/bin/env python3
"""TicketInstance model for MGLTickets."""

from sqlalchemy import ForeignKey, Integer, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional
from datetime import datetime, timezone
from app.db.session import Base

if TYPE_CHECKING:
    from app.db.models.booking import Booking
    from app.db.models.ticket_type import TicketType
    from app.db.models.user import User
    from app.db.models.event import Event

class TicketInstance(Base):
    """TicketInstance model representing individual ticket instances issued for bookings."""

    __tablename__ = "ticket_instances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    ticket_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("ticket_types.id"), nullable=False)
    booking_id: Mapped[int] = mapped_column(Integer, ForeignKey("bookings.id"), nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="issued")
    issued_to: Mapped[Optional[str]] = mapped_column(String(150), nullable=True, default=None)
    seat_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=None)
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
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )

    # Relationships
    booking: Mapped["Booking"] = relationship("Booking", back_populates="ticket_instances")
    ticket_type: Mapped["TicketType"] = relationship("TicketType", back_populates="ticket_instances")
    user: Mapped["User"] = relationship("User", back_populates="ticket_instances")
    event: Mapped["Event"] = relationship("Event", back_populates="ticket_instances")

    def __repr__(self) -> str:
        return (
            f"<TicketInstance id={self.id} code={self.code!r} "
            f"status={self.status!r} event_id={self.event_id} used_at={self.used_at}>"
        )