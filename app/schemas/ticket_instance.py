#!/usr/bin/env python3
"""Schemas for TicketInstance model in MGLTickets."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TicketInstanceOut(BaseModel):
    """Schema for outputting TicketInstance data."""
    id: int
    booking_id: int
    event_id: int
    ticket_type_id: int
    user_id: int
    code: str
    qr_payload: str          # signed JSON, computed on read via ticket_signing.py
    status: str
    price: int
    issued_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    used_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TicketInstanceCreate(BaseModel):
    """Schema for creating a new TicketInstance."""
    booking_id: int
    event_id: int
    ticket_type_id: int
    user_id: int
    price: int
    code: str
    status: Optional[str] = "issued"
    issued_to: Optional[str] = None
    seat_number: Optional[int] = None

    class Config:
        from_attributes = True


class TicketInstanceUpdate(BaseModel):
    """Schema for updating an existing TicketInstance."""
    status: Optional[str] = None
    issued_to: Optional[str] = None
    seat_number: Optional[int] = None
    used_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TicketInstanceEnrichedOut(BaseModel):
    """Enriched ticket instance schema with event context.
    Returned by GET /users/me/ticket-instances."""
    id: int
    booking_id: int
    event_id: int
    ticket_type_id: int
    user_id: int
    code: str
    qr_payload: str
    status: str
    price: int
    issued_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    used_at: Optional[datetime] = None
    # enriched
    event_title: str
    venue: str
    event_date: Optional[str] = None
    ticket_type_name: str

    class Config:
        from_attributes = True


# ── Check-in schemas ──────────────────────────────────────────────────────────

class CheckInRequest(BaseModel):
    """Body for POST /organizers/me/check-in.
    `payload` is the raw scanned QR string — the signed JSON produced by
    build_ticket_qr_payload() at issuance time. Never a bare ticket code."""
    payload: str


class CheckInTicketInfo(BaseModel):
    """Ticket + event context returned on any check-in outcome so the
    scanner UI can render a result card without a second query."""
    ticket_instance_id: int
    code: str
    event_id: int
    event_title: str
    ticket_type_name: str
    holder_name: Optional[str] = None

    class Config:
        from_attributes = True


class CheckInResponse(BaseModel):
    """
    Response for POST /organizers/me/check-in.

    accepted=True  → ticket was 'issued' and is now marked 'used'.
    accepted=False → rejected; reason is one of:
        'already_used'      — scanned before; first_used_at is populated
        'cancelled'         — ticket was cancelled
        'not_found'         — id+code combo doesn't exist
        'invalid_signature' — QR payload failed HMAC verification
    """
    accepted: bool
    reason: Optional[str] = None
    ticket: Optional[CheckInTicketInfo] = None
    first_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True