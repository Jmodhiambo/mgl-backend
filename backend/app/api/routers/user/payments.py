#!/usr/bin/env python3
"""API routes for Payment operations."""

from fastapi import APIRouter, Depends, status
from app.schemas.payment import PaymentOut, PaymentCreate, PaymentUpdate
import app.services.payment_services as payment_services
from app.core.security import get_current_user

router = APIRouter()

@router.post("/payments", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def create_payment(payment: PaymentCreate, user=Depends(get_current_user)):
    """Create a new payment."""
    return payment_services.create_payment_service(payment)

@router.get("/payments/{payment_id}", response_model=PaymentOut)
def get_payment(payment_id: int, user=Depends(get_current_user)):
    """Get a payment by ID."""
    return payment_services.get_payment_by_id_service(payment_id)

# @router.get("/user/{user_id}/payments", response_model=list[PaymentOut])
# def get_payments_by_user(user_id: int, user=Depends(get_current_user)):
#     """Get all payments for a specific user."""
#     return payment_services.get_payments_by_user_service(user_id)

@router.get("/bookings/{booking_id}/payments", response_model=list[PaymentOut])
def get_payments_by_booking(booking_id: int, user=Depends(get_current_user)):
    """Get all payments for a specific booking."""
    return payment_services.get_payments_by_booking_id_service(booking_id)

# @router.get("/payments/mpesa/{mpesa_ref}", response_model=list[PaymentOut])
# def get_payments_by_mpesa_ref(mpesa_ref: str, user=Depends(get_current_user)):
#     """Get all payments for a specific Mpesa reference."""
#     return payment_services.get_payments_by_mpesa_ref_service(mpesa_ref)

@router.put("/payments/{payment_id}", response_model=PaymentOut)
def update_payment(payment_id: int, payment_update: PaymentUpdate, user=Depends(get_current_user)):
    """Update payment details."""
    return payment_services.update_payment_service(payment_id, payment_update)