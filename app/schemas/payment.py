#!/usr/bin/env python3
"""Schemas for Payment model in MGLTickets."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PaymentOut(BaseModel):
    """Schema for outputting Payment data."""
    id: int
    order_id: int
    amount: int
    currency: str
    method: str
    status: str
    mpesa_phone: Optional[str] = None
    mpesa_checkout_request_id: Optional[str] = None
    mpesa_ref: Optional[str] = None
    callback_payload: Optional[str] = None
    manual_review_status: str = "none"
    user_reported_mpesa_code: Optional[str] = None
    user_reported_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    """Schema for creating a new Payment record (internal use — not directly called by frontend)."""
    order_id: int
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
    manual_review_status: Optional[str] = None
    user_reported_mpesa_code: Optional[str] = None
    user_reported_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentEnrichedOut(BaseModel):
    """Enriched payment schema with user name via booking join.
    Returned by GET /admin/payments."""
    id: int
    order_id: int
    amount: int
    currency: str
    method: str
    status: str
    mpesa_phone: Optional[str] = None
    mpesa_checkout_request_id: Optional[str] = None
    mpesa_ref: Optional[str] = None
    callback_payload: Optional[str] = None
    manual_review_status: str = "none"
    user_reported_mpesa_code: Optional[str] = None
    user_reported_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    # enriched
    user_name: str

    class Config:
        from_attributes = True


# ── M-Pesa specific request/response schemas ──────────────────────────────────

class MpesaStkPushRequest(BaseModel):
    """Frontend sends this to trigger an STK push."""
    order_id: int
    phone_number: str   # format: 2547XXXXXXXX


class MpesaStkPushResponse(BaseModel):
    """Returned to frontend after STK push is initiated."""
    payment_id: int
    checkout_request_id: Optional[str] = None
    message: str        # e.g. "STK push sent to 2547XXXXXXXX"


class MpesaCallbackRequest(BaseModel):
    """Daraja sends this to our callback URL — raw Daraja B2C/C2B structure."""
    Body: dict          # Daraja wraps everything in a Body key


# ── Layer 1: automated STK status check / reconciliation ─────────────────────

class PaymentStatusCheckResponse(BaseModel):
    """Returned by GET /users/me/payments/{payment_id}/check-status.

    `resolved` tells the frontend whether it can stop polling and show a
    final state. `status` mirrors the Payment row's status after the check.
    """
    payment_id: int
    resolved: bool
    status: str                 # pending | completed | failed
    order_status: Optional[str] = None
    message: str


class ReconcileStuckPaymentsResponse(BaseModel):
    """Returned by POST /admin/payments/reconcile-stuck — summary of a sweep."""
    checked: int
    resolved_completed: int
    resolved_failed: int
    still_pending: int


# ── Layer 2: manual review fallback ───────────────────────────────────────────

class ReportManualPaymentRequest(BaseModel):
    """User-submitted fallback when STK push polling + status check both
    come back inconclusive. Does NOT auto-confirm the order — it only
    queues the payment for admin review."""
    payment_id: int
    mpesa_code: str = Field(..., min_length=6, max_length=20)
    phone_number: Optional[str] = None
    note: Optional[str] = None


class ManualPaymentReviewRequest(BaseModel):
    """Admin decision on a manual payment.

    mpesa_code is optional: if the user already reported one, the admin can
    approve without retyping it. If nobody reported one yet — e.g. the admin
    spotted the payment on the M-Pesa till statement themselves — they can
    supply the code directly here and approve in one step."""
    approve: bool
    mpesa_code: Optional[str] = Field(None, min_length=6, max_length=20)
    admin_notes: Optional[str] = None