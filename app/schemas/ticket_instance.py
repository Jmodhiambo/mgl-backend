#!/usr/bin/env python3
"""Schemas for TicketInstance model in MGLTickets."""

from datetime import datetime
from typing import Optional
from app.schemas.base import BaseModelEAT
# from app.schemas.booking import BookingOut
# from app.schemas.ticket_type import TicketTypeOut
# from app.schemas.user import UserOut

class TicketInstanceOut(BaseModelEAT):
    """Schema for outputting TicketInstance data."""
    id: int
    booking_id: int
    ticket_type_id: int
    user_id: int
    code: str
    status: str
    issued_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    used_at: Optional[datetime] = None
    # booking: BookingOut
    # ticket_type: TicketTypeOut
    # user: UserOut

    class Config:
        from_attributes = True

class TicketInstanceCreate(BaseModelEAT):
    """Schema for creating a new TicketInstance."""
    booking_id: int
    ticket_type_id: int
    user_id: int
    code: str
    status: Optional[str] = "issued"  # Default status is issued
    issued_to: Optional[str] = None

    class Config:
        from_attributes = True

class TicketInstanceUpdate(BaseModelEAT):
    """Schema for updating an existing TicketInstance."""
    status: Optional[str] = None
    issued_to: Optional[str] = None
    used_at: Optional[datetime] = None

    class Config:
        from_attributes = True