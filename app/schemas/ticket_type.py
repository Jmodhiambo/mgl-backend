#!/usr/bin/env python3
"""Schemas for TicketType model in MGLTickets."""

from datetime import datetime
from typing import Optional

from app.schemas.base import BaseModelEAT
# from app.schemas.event import EventOut
# from app.schemas.booking import BookingOut
# from app.schemas.ticket_instance import TicketInstanceOut

class TicketTypeOut(BaseModelEAT):
    """Schema for outputting TicketType data."""
    id: int
    event_id: int
    name: str
    description: Optional[str] = None
    price: int
    quantity_available: int
    quantity_sold: int
    created_at: datetime
    updated_at: datetime
    # event: EventOut
    # bookings: list[BookingOut] = []
    # ticket_instances: list[TicketInstanceOut] = []

    class Config:
        from_attributes = True

class TicketTypeCreate(BaseModelEAT):
    """Schema for creating a new TicketType."""
    event_id: int
    name: str
    description: Optional[str] = None
    price: int
    quantity_available: int

    class Config:
        from_attributes = True

class TicketTypeUpdate(BaseModelEAT):
    """Schema for updating an existing TicketType."""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    quantity_available: Optional[int] = None

    class Config:
        from_attributes = True