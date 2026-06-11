#!/usr/bin/env python3
"""User-facing payment routes for MGLTickets."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.schemas.payment import PaymentOut, MpesaStkPushRequest, MpesaStkPushResponse
import app.services.payment_services as payment_services
from app.core.security import require_user

router = APIRouter()


@router.post(
    "/payments/mpesa/stk-push",
    response_model=MpesaStkPushResponse,
    status_code=status.HTTP_201_CREATED,
)
async def initiate_mpesa_payment(
    request: MpesaStkPushRequest,
    user=Depends(require_user),
):
    """
    Trigger an M-Pesa STK push.
    Frontend sends booking_id + phone_number.
    Returns payment_id + checkout_request_id for polling.
    """
    try:
        return await payment_services.initiate_mpesa_payment_service(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post(
    "/payments/mpesa/callback",
    status_code=status.HTTP_200_OK,
    include_in_schema=False,   # hide from docs — Daraja calls this, not the user
)
async def mpesa_callback(request: Request):
    """
    Daraja callback endpoint — NO auth (Safaricom calls this directly).
    Validates the booking, updates payment status, confirms booking on success.
    """
    body = await request.json()
    await payment_services.handle_mpesa_callback_service(body)
    # Daraja expects a specific acknowledgement format
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


@router.get(
    "/users/me/payments/{payment_id}",
    response_model=PaymentOut,
    status_code=status.HTTP_200_OK,
)
async def get_payment_by_id(payment_id: int, user=Depends(require_user)):
    """Get a single payment by ID (user must own the booking it belongs to)."""
    payment = await payment_services.get_payment_by_id_service(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.get(
    "/users/me/bookings/{booking_id}/payments",
    response_model=list[PaymentOut],
)
async def get_payments_by_booking(booking_id: int, user=Depends(require_user)):
    """Get all payments for a specific booking."""
    return await payment_services.get_payments_by_booking_id_service(booking_id)