#!/usr/bin/env python3
"""
OrganizerEmails model.
Stores all emails sent by organizers to attendees/customers.
"""

from sqlalchemy import Integer, String, ForeignKey, DateTime, Text, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    # Avoid circular imports. User and Event are only imported for type hints, not executed at runtime.
    from app.db.models.user import User
    from app.db.models.event import Event
    from app.db.models.organizer_email_recipients import OrganizerEmailRecipients

class OrganizerEmails(Base):
    """OrganizerEmails model for MGLTickets."""

    __tablename__ = "organizer_emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Sender Information
    organizer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    event_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("events.id"), nullable=True, index=True)  # NULL if sent to multiple events or general email

    # Recipient Information
    recipient_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'single', 'bulk', or 'all'
    recipient_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # Number of recipients

    # Email Content
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    template_used: Mapped[str] = mapped_column(String(50), nullable=False)  # 'reminder', 'update', 'thank_you', 'custom'

    # Recipient (for tracking)
    booking_ids: Mapped[list[int]] = mapped_column(BigInteger, nullable=True, index=True)
    recipient_emails: Mapped[list[str]] = mapped_column(Text, nullable=True)  # Array of recipient emails using Text

    # Status
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)  # 'pending', 'sent', 'failed', 'partially_sent', 'cancelled'
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_count: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=True, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="organizer_emails")
    event: Mapped["Event"] = relationship("Event", back_populates="organizer_emails")
    recipients: Mapped[list["OrganizerEmailRecipients"]] = relationship("OrganizerEmailRecipients", back_populates="email")

    def __repr__(self):
        return f"OrganizerEmails(id={self.id}, subject={self.subject}, status={self.status}, created_at={self.created_at}, updated_at={self.updated_at})"