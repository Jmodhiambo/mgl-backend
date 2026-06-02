#!/usr/bin/env python3
"""Schemas for TicketInstance model in MGLTickets."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel
# from app.schemas.booking import BookingOut
# from app.schemas.ticket_type import TicketTypeOut
# from app.schemas.user import UserOut

class TicketInstanceOut(BaseModel):
    """Schema for outputting TicketInstance data."""
    id: int
    booking_id: int
    ticket_type_id: int
    user_id: int
    code: str
    status: str
    price: int
    issued_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    used_at: Optional[datetime] = None
    # booking: BookingOut
    # ticket_type: TicketTypeOut
    # user: UserOut

    class Config:
        from_attributes = True

class TicketInstanceCreate(BaseModel):
    """Schema for creating a new TicketInstance."""
    booking_id: int
    ticket_type_id: int
    user_id: int
    price: int
    status: Optional[str] = "issued"  # Default status is issued
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