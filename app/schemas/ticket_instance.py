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
    scanned_by: Optional[str] = None   # name of staff who checked this ticket in
    scan_method: Optional[str] = None  # qr_scan | manual_code | None if not yet scanned
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
    scanned_by: Optional[str] = None
    scan_method: Optional[str] = None

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
    qr_payload: str          # signed JSON — encode this in QR, not bare code
    status: str
    price: int
    issued_to: Optional[str] = None
    scanned_by: Optional[str] = None   # populated once the ticket is checked in
    scan_method: Optional[str] = None  # qr_scan | manual_code | None if not yet scanned
    created_at: datetime
    updated_at: datetime
    used_at: Optional[datetime] = None
    # enriched fields
    event_title: str
    venue: str
    event_date: Optional[str] = None
    ticket_type_name: str

    class Config:
        from_attributes = True


# ── Check-in schemas ──────────────────────────────────────────────────────────

class CheckInRequest(BaseModel):
    """Body for QR-based check-in endpoints.

    payload   : raw scanned QR string (signed JSON from build_ticket_qr_payload).
                Never a bare ticket code.
    event_id  : the event currently being scanned for. Required by admin
                endpoint to validate the QR payload's embedded event_id;
                optional for organizer (scoping TODO once ownership helper
                exists).
    """
    payload: str
    event_id: Optional[int] = None


class CheckInByCodeRequest(BaseModel):
    """Body for manual code fallback check-in endpoints.
    Used when the camera can't scan the QR — staff type the printed code."""
    code: str       # e.g. TKT-101-A3F9B2C1 (stripped + uppercased server-side)
    event_id: int   # scopes lookup — cross-event acceptance impossible


class CheckInTicketInfo(BaseModel):
    """Ticket + event context returned on any check-in outcome so the
    scanner UI can render a result card without a second query."""
    ticket_instance_id: int
    code: str
    event_id: int
    event_title: str
    ticket_type_name: str
    holder_name: Optional[str] = None    # issued_to if set
    scanned_by: Optional[str] = None     # name of the staff member who scanned
    scan_method: Optional[str] = None   # qr_scan | manual_code

    class Config:
        from_attributes = True


class CheckInResponse(BaseModel):
    """
    Response for all check-in endpoints.

    accepted=True  -> ticket was 'issued' and is now marked 'used'.
    accepted=False -> rejected; reason is one of:
        'already_used'      — scanned before; first_used_at + scanned_by populated
        'cancelled'         — ticket was cancelled
        'not_found'         — ticket doesn't exist or wrong event
        'invalid_signature' — QR payload failed HMAC verification
        'wrong_event'       — QR payload event_id != admin's selected event
    """
    accepted: bool
    reason: Optional[str] = None
    ticket: Optional[CheckInTicketInfo] = None
    first_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True