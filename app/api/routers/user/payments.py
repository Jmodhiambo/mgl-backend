#!/usr/bin/env python3
"""API routes for Payment operations."""

from fastapi import APIRouter, Depends, status
from app.schemas.payment import PaymentOut, PaymentCreate, PaymentUpdate
import app.services.payment_services as payment_services
from app.core.security import require_user

router = APIRouter()

@router.post("/users/me/payments", response_model=PaymentOut, status_code=status.HTTP_201_CREATED)
async def create_payment(payment: PaymentCreate, user=Depends(require_user)):
    """Create a new payment."""
    return await payment_services.create_payment_service(payment)

@router.get("/users/me/payments/{payment_id}", response_model=PaymentOut, status_code=status.HTTP_200_OK)
async def get_payment_by_id(payment_id: int, user=Depends(require_user)):
    """Get a payment by ID."""
    return await payment_services.get_payment_by_id_service(payment_id)

# @router.get("/user/me/payments", response_model=list[PaymentOut])
# async def get_payments_by_user(user_id: int, user=Depends(get_current_user)):
#     """Get all payments for a specific user."""
#     return payment_services.get_payments_by_user_service(user.id)

@router.get("/users/me/bookings/{booking_id}/payments", response_model=list[PaymentOut])
async def get_payments_by_booking(booking_id: int, user=Depends(require_user)):
    """Get all payments for a specific booking."""
    return await payment_services.get_payments_by_booking_id_service(booking_id)

# @router.get("/payments/mpesa/{mpesa_ref}", response_model=list[PaymentOut])
# async def get_payments_by_mpesa_ref(mpesa_ref: str, user=Depends(require_user)):
#     """Get all payments for a specific Mpesa reference."""
#     return payment_services.get_payments_by_mpesa_ref_service(mpesa_ref)

@router.put("/users/me/payments/{payment_id}", response_model=PaymentOut, status_code=status.HTTP_200_OK)
async def update_payment_by_id(payment_id: int, payment_update: PaymentUpdate, user=Depends(require_user)):
    """Update payment details."""
    return await payment_services.update_payment_service(payment_id, payment_update)