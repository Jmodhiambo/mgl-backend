#!/usr/bin/env python3
"""Schemas for Order model in MGLTickets."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.schemas.booking import BookingOut


class OrderItemCreate(BaseModel):
    """A single line item in an order — one ticket type and quantity.
    Price is NEVER taken from the frontend; the backend looks up
    TicketType.price for each item."""
    ticket_type_id: int
    quantity: int


class OrderCreate(BaseModel):
    """Schema for creating a new Order.
    event_id ensures all items belong to the same event (one checkout = one event).
    The backend computes total_price server-side from current ticket type prices —
    never trust a price or total sent by the client."""
    event_id: int
    items: list[OrderItemCreate]


class OrderOut(BaseModel):
    """Schema for outputting Order data, including its line-item bookings."""
    id: int
    user_id: int
    event_id: int
    total_price: int
    status: str
    created_at: datetime
    updated_at: datetime
    bookings: list[BookingOut] = []

    class Config:
        from_attributes = True

class OrderBookingLineOut(BaseModel):
    """One ticket-type line item within an enriched Order — used by the
    admin Orders page's expandable detail rows."""
    id: int                    # Booking.id
    ticket_type_id: int
    ticket_type_name: str
    quantity: int
    total_price: int           # line total for this ticket type
    status: str
 
    class Config:
        from_attributes = True
 
 
class OrderEnrichedOut(BaseModel):
    """Enriched order schema for the admin Orders page.
    Merges Order + Payment (1:1) + customer/event display fields,
    with its Booking line items nested for the expandable row."""
    id: int
    user_id: int
    customer_name: str
    customer_email: str
    event_id: int
    event_title: str
    total_price: int
    status: str                # order status: pending | confirmed | cancelled
    manual_review_status: str = "none"   # none | pending | approved | rejected
    user_reported_mpesa_code: Optional[str] = None
    user_reported_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
 
    # Payment fields (Order:Payment is 1:1 — null until STK push is initiated)
    payment_id: Optional[int] = None
    payment_method: Optional[str] = None
    payment_status: Optional[str] = None     # pending | completed | failed
    mpesa_ref: Optional[str] = None
    mpesa_phone: Optional[str] = None
 
    bookings: list[OrderBookingLineOut] = []
 
    class Config:
        from_attributes = True