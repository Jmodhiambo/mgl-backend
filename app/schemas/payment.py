#!/usr/bin/env python3
"""Schemas for Payment model in MGLTickets."""

from datetime import datetime
from typing import Optional
from app.schemas.base import BaseModelEAT
from app.schemas.booking import BookingOut

class PaymentOut(BaseModelEAT):
    """Schema for outputting Payment data."""
    id: int
    booking_id: int
    amount: int
    currency: str
    method: str
    status: str
    mpesa_ref: str
    callback_payload: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # booking: BookingOut

    class Config:
        from_attributes = True

class PaymentCreate(BaseModelEAT):
    """Schema for creating a new Payment."""
    booking_id: int
    amount: int
    currency: str
    method: str
    mpesa_ref: str
    callback_payload: Optional[str] = None

    class Config:
        from_attributes = True

class PaymentUpdate(BaseModelEAT):
    """Schema for updating an existing Payment."""
    amount: Optional[int] = None
    currency: Optional[str] = None
    method: Optional[str] = None
    status: Optional[str] = None
    mpesa_ref: Optional[str] = None
    callback_payload: Optional[str] = None

    class Config:
        from_attributes = True