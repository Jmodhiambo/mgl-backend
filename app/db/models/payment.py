#!/usr/bin/env python3

"""Payment model for MGLTickets."""

from sqlalchemy import ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional
from datetime import datetime, timezone
from app.db.session import Base

if TYPE_CHECKING:
    # Avoid circular imports. Booking is only imported for type hints, not executed at runtime.
    from app.db.models.booking import Booking

class Payment(Base):
    """Payment model representing a payment in the system."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    booking_id: Mapped[int] = mapped_column(Integer, ForeignKey("bookings.id"), nullable=False)
    amount: Mapped[float] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="KES")
    method: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., credit_card, paypal, m-pesa
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")  # e.g., pending, completed, failed, refunded
    mpesa_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    callback_payload: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True, default=None)  # Full M-Pesa response (for auditing)
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
    booking: Mapped["Booking"] = relationship("Booking", back_populates="payment")

    def __repr__(self) -> str:
        return f"<Payment id={self.id} booking_id={self.booking_id} amount={self.amount} status={self.status} created_at={self.created_at} updated_at={self.updated_at}>"