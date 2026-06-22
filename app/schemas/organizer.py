#!/usr/bin/env python3
"""
Pydantic schemas for organizer-specific views:
  - DashboardStats  (GET /organizers/me/stats)
  - RecentBooking   (embedded in dashboard)
  - TopEvent        (GET /organizers/me/top-events)
  - OrganizerOrder  (GET /organizers/me/orders)
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ─── Dashboard ────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    """
    KPI cards for the organizer dashboard.

    Revenue figures reflect CONFIRMED bookings only.
    monthly_growth is the % change in events created vs the previous month.
    commission_rate is the organizer's most-recently-used rate (from their
    latest event) — shown as context for the revenue split displayed on the
    dashboard. Gross / platform_cut / organizer_net are aggregate totals
    across ALL confirmed bookings on the organizer's events.
    """
    # Events
    total_events: int
    active_events: int
    upcoming_events: int
    completed_events: int
    monthly_growth: float           # % change in events created this month vs last

    # Bookings & tickets
    total_bookings: int
    tickets_sold: int

    # Revenue split (confirmed bookings only)
    total_revenue: float            # gross
    platform_cut: float             # gross × weighted avg commission rate
    organizer_net: float            # gross − platform_cut

    class Config:
        from_attributes = True


class RecentBooking(BaseModel):
    """
    Enriched booking row for the dashboard recent-bookings widget.
    Matches the BookingEnrichedOut shape from bookings_organizer endpoints.
    """
    id: int
    event_title: str
    customer_name: str
    quantity: int
    total_price: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Orders (organizer view) ──────────────────────────────────────────────────

class OrganizerOrderBookingLine(BaseModel):
    """
    One ticket-type line item within an organizer Order —
    used in the expandable BookingsView order rows.
    """
    id: int                     # Booking.id
    ticket_type_id: int
    ticket_type_name: str
    quantity: int
    total_price: int            # line total
    status: str

    class Config:
        from_attributes = True


class OrganizerOrderOut(BaseModel):
    """
    Order as seen by the organizer — includes customer display fields,
    payment status, and the nested booking line items.
    Mirrors the admin OrderEnrichedOut but scoped to the organizer's events.
    """
    id: int
    user_id: int
    customer_name: str
    customer_email: str
    event_id: int
    event_title: str
    event_slug: str
    total_price: int
    status: str                 # pending | confirmed | cancelled
    created_at: datetime
    updated_at: datetime

    # Payment (1:1 with Order — null until STK push is initiated)
    payment_id: Optional[int] = None
    payment_status: Optional[str] = None    # pending | completed | failed
    mpesa_ref: Optional[str] = None
    mpesa_phone: Optional[str] = None

    # Commission breakdown for this order's event
    commission_rate: float = 7.0
    platform_cut: float = 0.0       # total_price * (commission_rate / 100)
    organizer_net: float = 0.0      # total_price - platform_cut

    bookings: list[OrganizerOrderBookingLine] = []

    class Config:
        from_attributes = True