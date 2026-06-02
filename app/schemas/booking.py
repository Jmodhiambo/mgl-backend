#!/usr/bin/env python3
"""Schemas for Booking model in MGLTickets."""

from datetime import datetime

from pydantic import BaseModel
# from app.schemas.ticket_type import TicketTypeOut
# from app.schemas.user import UserOut

class BookingOut(BaseModel):
    """Schema for outputting Booking data."""
    id: int
    user_id: int
    ticket_type_id: int
    quantity: int
    status: str
    total_price: int
    created_at: datetime
    updated_at: datetime
    # user: UserOut
    # ticket_type: list[TicketTypeOut]

    class Config:
        from_attributes = True

class BookingCreate(BaseModel):
    """Schema for creating a new Booking."""
    user_id: int
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