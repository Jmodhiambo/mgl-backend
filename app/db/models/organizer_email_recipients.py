#!/usr/bin/env python3
"""
OrganizerEmailsRecipients model.
Detailed tracking for each individual recipient (optional, for detailed analytics).
"""

from sqlalchemy import Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    # Avoid circular imports. User and Event are only imported for type hints, not executed at runtime.
    from app.db.models.organizer_emails import OrganizerEmails
    from app.db.models.booking import Booking


class OrganizerEmailRecipients(Base):
    __tablename__ = "organizer_email_recipients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # References
    email_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizer_emails.id"), nullable=False, index=True)
    booking_id: Mapped[int] = mapped_column(Integer, ForeignKey("bookings.id"), nullable=False, index=True)

    # Recipient
    recipient_name: Mapped[str] = mapped_column(String(100), nullable=False)
    recipient_email: Mapped[str] = mapped_column(String(150), nullable=False)

    # Status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)  # 'pending', 'sent', 'failed', 'bounced'
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)  # Optional (email tracking)
    clicked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)  # Optional (email tracking)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    # Relationships
    email: Mapped["OrganizerEmails"] = relationship("OrganizerEmails", back_populates="recipients")
    booking: Mapped["Booking"] = relationship("Booking", back_populates="organizer_email_recipients")

    def __repr__(self):
        return f"<OrganizerEmailsRecipients id={self.id} recipient_name={self.recipient_name} recipient_email={self.recipient_email} status={self.status}>"