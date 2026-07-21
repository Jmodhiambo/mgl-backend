#!/usr/bin/env python3
"""Schemas for TicketType model in MGLTickets."""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

class TicketTypeBase(BaseModel):
    """Fields every role's view of a TicketType shares."""
    id: int
    event_id: int
    name: str
    description: Optional[str] = None
    price: int
    is_active: bool = True
    total_quantity: int        # the ceiling — never changes after creation
    quantity_available: int    # computed property: total_quantity - quantity_sold
    quantity_sold: int
    max_per_booking: int       # cap on units of this type per single order
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TicketTypePublicOut(TicketTypeBase):
    """
    Buyer-facing (public router). No suspension internals at all —
    buyers never need to know why a type is unavailable, and the public
    endpoint already excludes suspended/inactive types, so these fields
    would only ever be null noise here anyway.
    """
    pass


class TicketTypeOrganizerOut(TicketTypeBase):
    """
    Organizer-facing. Enough suspension context to explain a locked
    reactivate toggle (who, why, when) — but not the raw admin user ID,
    which the organizer has no use for.
    """
    suspended_by_admin_name: Optional[str] = None
    suspension_reason: Optional[str] = None
    suspended_at: Optional[datetime] = None


class TicketTypeOut(TicketTypeOrganizerOut):
    """
    Full representation — used as the admin router's response_model AND
    as the internal type the repo/service layer builds via model_validate().
    Narrower schemas above simply drop fields at serialization time; they
    don't need their own repo/service path.
    """
    suspended_by_admin_id: Optional[int] = None
 
 
class TicketTypeCreate(BaseModel):
    """Schema for creating a new TicketType."""
    event_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    price: int
    is_active: Optional[bool] = True
    total_quantity: int        # maps directly to the model column
    max_per_booking: int = 10  # prefilled default — organizer/admin may override
 
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
    max_per_booking: Optional[int] = None
 
    class Config:
        from_attributes = True


class TicketTypeSuspendRequest(BaseModel):
    """
    Admin-only request body for suspending a TicketType.
    reason is required — a suspension with no stated reason defeats the
    point of the accountability trail.
    """
    reason: str = Field(..., min_length=3, max_length=500)