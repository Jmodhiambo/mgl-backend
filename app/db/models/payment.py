#!/usr/bin/env python3
"""Payment model for MGLTickets.

A Payment belongs to an Order (which may contain multiple Bookings —
one per ticket type). One STK push pays for the entire Order.
"""

from sqlalchemy import ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional
from datetime import datetime, timezone
from app.db.session import Base

if TYPE_CHECKING:
    from app.db.models.order import Order

class Payment(Base):
    """Payment model representing a payment for an Order."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
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

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="payment")

    def __repr__(self) -> str:
        return (
            f"<Payment id={self.id} order_id={self.order_id} "
            f"amount={self.amount} method={self.method!r} status={self.status!r}>"
        )