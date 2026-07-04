#!/usr/bin/env python3
"""Schemas for TicketType model in MGLTickets."""

from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class TicketTypeOut(BaseModel):
    """Schema for outputting TicketType data."""
    id: int
    event_id: int
    name: str
    description: Optional[str] = None
    price: int
    is_active: bool = True
    total_quantity: int        # the ceiling — never changes after creation
    quantity_available: int    # computed property: total_quantity - quantity_sold
    quantity_sold: int
    created_at: datetime
    updated_at: datetime
 
    class Config:
        from_attributes = True
 
 
class TicketTypeCreate(BaseModel):
    """Schema for creating a new TicketType."""
    event_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    price: int
    is_active: Optional[bool] = True
    total_quantity: int        # maps directly to the model column
 
    class Config:
        from_attributes = True
 
 
class TicketTypeUpdate(BaseModel):
    """Schema for updating an existing TicketType."""
    event_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    is_active: Optional[bool] = None
    total_quantity: Optional[int] = None   # organizer can raise/lower the ceiling
 
    class Config:
        from_attributes = True