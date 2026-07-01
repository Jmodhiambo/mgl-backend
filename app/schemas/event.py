#!/usr/bin/env python3
"""Event schemas for MGLTickets."""

from datetime import datetime
from pydantic import BaseModel
from typing import Optional


# ─── Commission breakdown (computed, not stored) ───────────────────────────────
 
class CommissionBreakdown(BaseModel):
    """
    Revenue split for a single event, computed server-side from
    total_revenue and commission_rate.
 
    gross_revenue   = total confirmed booking revenue
    platform_cut    = gross_revenue * (commission_rate / 100)
    organizer_net   = gross_revenue - platform_cut
    commission_rate = the rate that was locked in at event creation
    """
    gross_revenue: float
    platform_cut: float
    organizer_net: float
    commission_rate: float
    commission_source: str
 
    class Config:
        from_attributes = True


# ─── Public / User-facing ─────────────────────────────────────────────────────

class EventOut(BaseModel):
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
    category: str
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


class OrganizerEventOut(BaseModel):
    """
    Organizer event schema — returned to the organizer portal for their own
    events. Includes approval state, aggregated booking/revenue stats, and
    the commission breakdown so the organizer can see gross / platform cut /
    their net payout.
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
    original_filename: str
    flyer_url: str
    status: str
    is_approved: bool
    is_active: bool
 
    # ── Aggregated stats ──────────────────────────────────────────────────────
    total_bookings: int = 0
    total_revenue: float = 0.0          # gross confirmed revenue
    unresolved_bookings_count: int = 0  # confirmed + pending bookings - key in refund queue

    # ── Commission ────────────────────────────────────────────────────────────
    commission_rate: float
    commission_source: str = "platform_default"
    # Negotiation fields — only populated when commission_source == 'negotiated'
    commission_approved_by: Optional[int] = None
    commission_approved_by_name: Optional[str] = None
    commission_approved_at: Optional[datetime] = None
 
    # ── Computed revenue split (populated by the repo/service layer) ──────────
    platform_cut: float = 0.0          # total_revenue * (commission_rate / 100)
    organizer_net: float = 0.0         # total_revenue - platform_cut
 
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

class EventCreate(BaseModel):
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
    commission_rate: float
    commission_source: str = "platform_default"


class EventUpdate(BaseModel):
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

class EventStats(BaseModel):
    """Aggregated statistics for a single event."""
    total_bookings: int
    total_revenue: float
    tickets_sold: int
    tickets_remaining: int
    # Commission breakdown
    commission_rate: float = 0.0
    platform_cut: float = 0.0
    organizer_net: float = 0.0

    class Config:
        from_attributes = True


class TicketTypeOut(BaseModel):
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


class BookingOut(BaseModel):
    """Booking data used inside EventDetails."""
    id: int
    user_id: int
    order_id: int
    event_id: int
    ticket_type_id: int
    quantity: int
    status: str
    total_price: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventDetails(BaseModel):
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


class TopEvent(BaseModel):
    """Top-performing event summary for the organizer dashboard."""
    id: int
    title: str
    bookings: int
    revenue: float
    tickets_sold: int
    platform_cut: float
    organizer_net: float

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
CommissionBreakdown.model_rebuild()