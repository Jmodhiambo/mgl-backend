#!/usr/bin/env python3
"""Payment model for MGLTickets."""

from sqlalchemy import ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional
from datetime import datetime, timezone
from app.db.session import Base

if TYPE_CHECKING:
    from app.db.models.booking import Booking

class Payment(Base):
    """Payment model representing a payment in the system."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    booking_id: Mapped[int] = mapped_column(Integer, ForeignKey("bookings.id"), nullable=False)
    amount: Mapped[float] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="KES")
    method: Mapped[str] = mapped_column(String(50), nullable=False)  # mpesa | card (future)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    # M-Pesa specific — nullable because card payments won't have these
    mpesa_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default=None)
    mpesa_checkout_request_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, default=None)
    mpesa_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, default=None)  # MpesaReceiptNumber from callback
    callback_payload: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True, default=None)
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

    booking: Mapped["Booking"] = relationship("Booking", back_populates="payment")

    def __repr__(self) -> str:
        return (
            f"<Payment id={self.id} booking_id={self.booking_id} "
            f"amount={self.amount} method={self.method!r} status={self.status!r}>"
        )