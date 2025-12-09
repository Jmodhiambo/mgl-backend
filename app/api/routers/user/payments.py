#!/usr/bin/env python3
"""API routes for Payment operations."""

from fastapi import APIRouter, Depends, status, HTTPException
from app.schemas.payment import PaymentOut, PaymentCreate, PaymentUpdate
import app.services.payment_services as payment_services
from app.core.security import require_user

router = APIRouter()

@router.post("/users/{user_id}/payments", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
def create_payment(user_id: int, payment: PaymentCreate, user=Depends(require_user)):
    """Create a new payment."""
    if user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create payment for this user.")
    return payment_services.create_payment_service(payment)

@router.get("/users/{user_id}/payments/{payment_id}", response_model=PaymentOut, status_code=status.HTTP_200_OK)
def get_payment_by_id(user_id: int, payment_id: int, user=Depends(require_user)):
    """Get a payment by ID."""
    if user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this payment.")
    return payment_services.get_payment_by_id_service(payment_id)

# @router.get("/user/{user_id}/payments", response_model=list[PaymentOut])
# def get_payments_by_user(user_id: int, user=Depends(get_current_user)):
#     """Get all payments for a specific user."""
#     return payment_services.get_payments_by_user_service(user_id)

@router.get("/users/{user_id}/bookings/{booking_id}/payments", response_model=list[PaymentOut])
def get_payments_by_booking(user_id: int, booking_id: int, user=Depends(require_user)):
    """Get all payments for a specific booking."""
    if user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view these payments.")
    return payment_services.get_payments_by_booking_id_service(booking_id)

# @router.get("/payments/mpesa/{mpesa_ref}", response_model=list[PaymentOut])
# def get_payments_by_mpesa_ref(mpesa_ref: str, user=Depends(require_user)):
#     """Get all payments for a specific Mpesa reference."""
#     return payment_services.get_payments_by_mpesa_ref_service(mpesa_ref)

@router.put("/users/{user_id}/payments/{payment_id}", response_model=PaymentOut, status_code=status.HTTP_200_OK)
def update_payment_by_id(user_id: int, payment_id: int, payment_update: PaymentUpdate, user=Depends(require_user)):
    """Update payment details."""
    if user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this payment.")
    return payment_services.update_payment_service(payment_id, payment_update)