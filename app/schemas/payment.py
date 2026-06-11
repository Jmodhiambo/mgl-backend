#!/usr/bin/env python3
"""Schemas for Payment model in MGLTickets."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PaymentOut(BaseModel):
    """Schema for outputting Payment data."""
    id: int
    booking_id: int
    amount: int
    currency: str
    method: str
    status: str
    mpesa_phone: Optional[str] = None
    mpesa_checkout_request_id: Optional[str] = None
    mpesa_ref: Optional[str] = None
    callback_payload: Optional[str] = None
    created_at: datetime
    updated_at: datetime
 
    class Config:
        from_attributes = True
 
 
class PaymentCreate(BaseModel):
    """Schema for creating a new Payment record (internal use — not directly called by frontend)."""
    booking_id: int
    amount: int
    currency: str = "KES"
    method: str
    mpesa_phone: Optional[str] = None
    mpesa_checkout_request_id: Optional[str] = None
    mpesa_ref: Optional[str] = None
    callback_payload: Optional[str] = None
 
    class Config:
        from_attributes = True
 
 
class PaymentUpdate(BaseModel):
    """Schema for updating an existing Payment."""
    amount: Optional[int] = None
    currency: Optional[str] = None
    method: Optional[str] = None
    status: Optional[str] = None
    mpesa_phone: Optional[str] = None
    mpesa_checkout_request_id: Optional[str] = None
    mpesa_ref: Optional[str] = None
    callback_payload: Optional[str] = None
 
    class Config:
        from_attributes = True

class PaymentEnrichedOut(BaseModel):
    """Enriched payment schema with user name via booking join.
    Returned by GET /admin/payments."""
    id: int
    booking_id: int
    amount: int
    currency: str
    method: str
    status: str
    mpesa_phone: Optional[str] = None
    mpesa_checkout_request_id: Optional[str] = None
    mpesa_ref: Optional[str] = None
    callback_payload: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # enriched
    user_name: str

    class Config:
        from_attributes = True
 
 
# ── M-Pesa specific request/response schemas ──────────────────────────────────
 
class MpesaStkPushRequest(BaseModel):
    """Frontend sends this to trigger an STK push."""
    booking_id: int
    phone_number: str   # format: 2547XXXXXXXX
 
 
class MpesaStkPushResponse(BaseModel):
    """Returned to frontend after STK push is initiated."""
    payment_id: int
    checkout_request_id: str
    message: str        # e.g. "STK push sent to 2547XXXXXXXX"
 
 
class MpesaCallbackRequest(BaseModel):
    """Daraja sends this to our callback URL — raw Daraja B2C/C2B structure."""
    Body: dict          # Daraja wraps everything in a Body key