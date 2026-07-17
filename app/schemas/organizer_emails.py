#!/usr/bin/env python3
# app/schemas/organizer_emails.py
"""Pydantic schemas for organizer email operations."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ── Send request / response ───────────────────────────────────────────────────

class SendEmailRequest(BaseModel):
    """
    Payload for POST /organizers/me/emails/send.

    booking_ids    — Booking IDs whose attendees receive the email. The service
                     resolves customer_name, customer_email, order_id,
                     ticket_type, quantity, venue, event_date from each row.
    template_used  — registered template suffix after 'organizer.'
                     e.g. 'reminder', 'update', 'cancellation', 'venue_change',
                     'time_change', 'thank_you', 'custom'
    subject        — required only for 'custom'; ignored for named templates.
    custom_message — body text for 'custom' only.
    extra_variables — additional variables merged into the template context
                      e.g. update_message, cancellation_reason, old_venue,
                      new_venue, old_date_time, new_date_time.
    """
    booking_ids: list[int]
    template_used: str
    subject: Optional[str] = None
    custom_message: Optional[str] = None
    extra_variables: Optional[dict] = None


class SendEmailResponse(BaseModel):
    """Summary returned after a bulk send attempt."""
    total_recipients: int
    queued: int
    failed: int
    email_id: Optional[int] = None
    message: str


# ── Recipient schemas ─────────────────────────────────────────────────────────

class OrganizerEmailRecipientOut(BaseModel):
    """One row from organizer_email_recipients."""
    id: int
    email_id: int
    booking_id: int
    recipient_name: str
    recipient_email: str
    status: str                         # 'pending' | 'sent' | 'failed' | 'bounced'
    sent_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrganizerEmailRecipientUpdate(BaseModel):
    """For updating a recipient record."""
    status: Optional[str] = None
    sent_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    error_message: Optional[str] = None


# ── Email log schemas ─────────────────────────────────────────────────────────

class OrganizerEmailOut(BaseModel):
    """One row from organizer_emails — used in list views."""
    id: int
    organizer_id: int
    event_id: Optional[int] = None
    recipient_type: str
    recipient_count: int
    subject: str
    message: str
    template_used: str
    status: str                         # 'pending' | 'sent' | 'failed' | 'partially_sent'
    sent_at: Optional[datetime] = None
    failed_count: int
    success_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrganizerEmailDetail(OrganizerEmailOut):
    """OrganizerEmailOut with extra fields for detail views."""
    booking_ids: Optional[list[int]] = None
    recipient_emails: Optional[list[str]] = None


class EmailDetailWithRecipients(OrganizerEmailDetail):
    """Full detail with per-recipient rows — used by GET /emails/{email_id}."""
    recipients: list[OrganizerEmailRecipientOut] = []


class EmailHistoryResponse(BaseModel):
    """Paginated email history."""
    total: int
    limit: int
    offset: int
    emails: list[OrganizerEmailOut]


# ── Stats ─────────────────────────────────────────────────────────────────────

class EmailStatsResponse(BaseModel):
    total_sent: int
    total_recipients: int
    success_rate: float
    emails_this_month: int
    recipients_this_month: int
    by_template: dict[str, int]
    by_status: dict[str, int]