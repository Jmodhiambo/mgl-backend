#!/usr/bin/env python3
"""TicketType model for MGLTickets."""

from sqlalchemy import ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional
from datetime import datetime, timezone
from app.db.session import Base

if TYPE_CHECKING:
    from app.db.models.booking import Booking
    from app.db.models.event import Event
    from app.db.models.ticket_instance import TicketInstance

class TicketType(Base):
    """TicketType model representing different types of tickets for events."""

    __tablename__ = "ticket_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # CASCADE: a ticket type only exists to be sold for its event. If the
    # event is gone, the ticket type definition has nothing left to describe.
    event_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, default=None)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    total_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_sold: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── Admin suspension (accountability trail) ─────────────────────────
    # suspended_by_admin_id being non-NULL IS the "is suspended" flag — no
    # separate boolean, so there's no way for a bool and the admin identity
    # to drift out of sync with each other.
    #
    # ondelete="SET NULL": if the admin account is later deleted, that
    # shouldn't cascade into deleting/corrupting the ticket type — the
    # denormalized suspended_by_admin_name below preserves who it was even
    # after the admin's row is gone.
    suspended_by_admin_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, default=None
    )
    suspended_by_admin_name: Mapped[Optional[str]] = mapped_column(
        String(150), nullable=True, default=None
    )
    suspension_reason: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, default=None
    )
    suspended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

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

    @property
    def quantity_available(self) -> int:
        """Remaining tickets: total minus sold. Never goes below zero."""
        return max(0, self.total_quantity - self.quantity_sold)

    @property
    def is_suspended(self) -> bool:
        """True if an admin has suspended this ticket type."""
        return self.suspended_by_admin_id is not None

    # Relationships
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="ticket_type")
    event: Mapped["Event"] = relationship("Event", back_populates="ticket_types")
    ticket_instances: Mapped[list["TicketInstance"]] = relationship("TicketInstance", back_populates="ticket_type")

    def __repr__(self) -> str:
        return (
            f"<TicketType id={self.id} event_id={self.event_id} name={self.name!r} "
            f"price={self.price} total={self.total_quantity} "
            f"sold={self.quantity_sold} available={self.quantity_available} "
            f"suspended={self.is_suspended}>"
        )