#!/usr/bin/env python3
"""Event schemas for MGLTickets."""

from datetime import datetime
from app.schemas.base import BaseModelEAT
from typing import Optional


# ─── Public / User-facing ─────────────────────────────────────────────────────

class EventOut(BaseModelEAT):
    """
    Public event schema — returned to unauthenticated and authenticated users
    browsing events. Only contains what a ticket buyer needs to see.
    """
    id: int
    title: str
    slug: str
    organizer_id: int
    description: Optional[str] = None
    venue: str
    start_time: datetime
    end_time: datetime
    original_filename: str
    flyer_url: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Organizer portal ─────────────────────────────────────────────────────────

class OrganizerEventOut(BaseModelEAT):
    """
    Organizer event schema — returned to the organizer portal for their own
    events. Includes approval state and aggregated booking/revenue stats.
    Does NOT include organizer identity fields (the organizer already knows
    who they are).
    """
    id: int
    title: str
    slug: str
    description: Optional[str] = None
    venue: str
    city: str
    country: str
    category: str
    start_time: datetime
    end_time: datetime
    flyer_url: str
    status: str
    is_approved: bool
    is_active: bool
    total_bookings: int = 0
    total_revenue: float = 0.0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Admin portal ─────────────────────────────────────────────────────────────

class AdminEventOut(OrganizerEventOut):
    """
    Admin event schema — everything in OrganizerEventOut plus organizer
    identity. Used by all admin event endpoints.
    """
    organizer_id: int
    organizer_name: str  # joined from the users table


# ─── Create / Update ──────────────────────────────────────────────────────────

class EventCreate(BaseModelEAT):
    """Schema for creating a new Event (user-supplied fields only)."""
    title: str
    description: Optional[str] = None
    venue: str
    city: str
    country: str
    category: str
    start_time: datetime
    end_time: datetime

    class Config:
        from_attributes = True


class EventCreateWithFlyer(EventCreate):
    """
    Internal schema used by the service layer after the flyer has been
    uploaded and the slug generated. Never sent directly by the client.
    """
    slug: str
    organizer_id: int
    original_filename: str
    flyer_url: str


class EventUpdate(BaseModelEAT):
    """Schema for updating an existing Event. All fields optional."""
    title: Optional[str] = None
    description: Optional[str] = None
    venue: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    category: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Organizer detail views ───────────────────────────────────────────────────

class EventStats(BaseModelEAT):
    """Aggregated statistics for a single event."""
    total_bookings: int
    total_revenue: float
    tickets_sold: int
    tickets_remaining: int

    class Config:
        from_attributes = True


class TicketTypeOut(BaseModelEAT):
    """TicketType data returned to the frontend."""
    id: int
    event_id: int
    name: str
    description: Optional[str] = None
    price: int
    is_active: bool = True
    quantity_available: int
    quantity_sold: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookingOut(BaseModelEAT):
    """Booking data used inside EventDetails."""
    id: int
    user_id: int
    ticket_type_id: int
    quantity: int
    status: str
    total_price: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventDetails(BaseModelEAT):
    """
    Full event detail bundle returned by the organizer
    GET /organizers/me/events/{id}/details endpoint.
    """
    event: OrganizerEventOut
    stats: EventStats
    ticket_types: list[TicketTypeOut]
    recent_bookings: list[BookingOut]

    class Config:
        from_attributes = True


class TopEvent(BaseModelEAT):
    """Top-performing event summary for the organizer dashboard."""
    id: int
    title: str
    bookings: int
    revenue: float
    tickets_sold: int

    class Config:
        from_attributes = True


# ─── Model rebuilds ───────────────────────────────────────────────────────────
# Must come after all class definitions to resolve forward references.

EventOut.model_rebuild()
OrganizerEventOut.model_rebuild()
AdminEventOut.model_rebuild()
TicketTypeOut.model_rebuild()
BookingOut.model_rebuild()
EventCreate.model_rebuild()
EventCreateWithFlyer.model_rebuild()
EventUpdate.model_rebuild()
EventStats.model_rebuild()
EventDetails.model_rebuild()
TopEvent.model_rebuild()