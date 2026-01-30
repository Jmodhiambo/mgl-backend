#!/usr/bin/env python3
"""Event schemas for MGLTickets."""

from datetime import datetime
from app.schemas.base import BaseModelEAT
from typing import Optional

class EventOut(BaseModelEAT):
    """Base schema for Event."""
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

class EventCreate(BaseModelEAT):
    """Schema for creating a new Event."""
    title: str
    description: Optional[str] = None
    venue: str
    start_time: datetime
    end_time: datetime

    class Config:
        from_attributes = True

class EventCreateWithFlyer(EventCreate):
    """Schema for creating a new Event with a flyer."""
    slug: str
    organizer_id: int
    original_filename: str
    flyer_url: str

class EventUpdate(BaseModelEAT):
    """Schema for updating an existing Event."""
    title: Optional[str] = None
    description: Optional[str] = None
    venue: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class EventStats(BaseModelEAT):
    """Schema for outputting Event stats."""
    total_bookings: int
    total_revenue: float
    tickets_sold: int
    tickets_remaining: int

    class Config:
        from_attributes = True


class TicketTypeOut(BaseModelEAT):
    """Schema for outputting TicketType data."""
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
    """Schema for outputting Booking data."""
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
    """Schema for outputting Event details."""
    event: EventOut
    stats: EventStats
    ticket_types: list[TicketTypeOut]
    recent_bookings: list[BookingOut]

    class Config:
        from_attributes = True


class TopEvent(BaseModelEAT):
    """Schema for outputting TopEvent data."""
    id: int
    title: str
    bookings: int
    revenue: float
    tickets_sold: int

    class Config:
        from_attributes = True


# Rebuild models after changes. Imported here to avoid circular imports
EventOut.model_rebuild()
TicketTypeOut.model_rebuild()
BookingOut.model_rebuild()
EventCreate.model_rebuild()
EventCreateWithFlyer.model_rebuild()
EventUpdate.model_rebuild()
EventStats.model_rebuild()
EventDetails.model_rebuild()