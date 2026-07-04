#!/usr/bin/env python3
"""Schemas for Booking model in MGLTickets."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BookingOut(BaseModel):
    """Schema for outputting Booking data."""
    id: int
    order_id: int              # groups this booking with sibling line items under one Order
    user_id: int
    event_id: int              # was missing — model has it NOT NULL, needed by frontend
    ticket_type_id: int
    quantity: int
    status: str
    total_price: int
    created_at: datetime
    updated_at: datetime
 
    class Config:
        from_attributes = True
 
 
class BookingCreate(BaseModel):
    """Internal schema — used by order_repo when creating Booking rows for an Order.
    Not exposed directly via any user-facing endpoint; POST /users/me/orders is
    the entry point for creating bookings now."""
    order_id: int
    event_id: int
    ticket_type_id: int
    quantity: int
    total_price: int
 
    class Config:
        from_attributes = True
 
 
class BookingUpdate(BaseModel):
    """Schema for updating an existing Booking."""
    quantity: int
    status: str
    total_price: int
 
    class Config:
        from_attributes = True


# Enriched output schemas for admin and organizer pages

class BookingEnrichedOut(BaseModel):
    """Enriched booking schema with denormalized display fields.
    Returned by admin list and organizer event booking endpoints."""
    id: int
    user_id: int
    event_id: int
    ticket_type_id: int
    customer_name: str
    customer_email: str
    event_title: str
    ticket_type_name: str
    venue: Optional[str] = None
    event_date: Optional[str] = None
    quantity: int
    status: str
    total_price: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
