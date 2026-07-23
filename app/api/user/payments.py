#!/usr/bin/env python3
"""User-facing payment routes for MGLTickets."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from app.schemas.payment import (
    PaymentOut,
    MpesaStkPushRequest,
    MpesaStkPushResponse,
    PaymentStatusCheckResponse,
    ReportManualPaymentRequest,
)
import app.services.payment_services as payment_services
from app.services.notification_services import notify_manual_payment_reported
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
    Trigger an M-Pesa STK push for an Order (covers all ticket types in the order).
    Frontend sends order_id + phone_number.
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
    On success: confirms the Order and all its Bookings, then issues
    TicketInstances for every line item.
    """
    body = await request.json()
    await payment_services.handle_mpesa_callback_service(body)
    # Daraja expects a specific acknowledgement format
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


@router.get(
    "/users/me/payments/{payment_id}/check-status",
    response_model=PaymentStatusCheckResponse,
)
async def check_payment_status(payment_id: int, user=Depends(require_user)):
    """
    Layer 1 — called by the frontend when its own STK-push polling times
    out, before ever surfacing the "report your M-Pesa code" fallback.
    Queries Daraja directly by CheckoutRequestID — resolves the payment
    automatically in most cases where the callback itself was delayed
    or dropped, with no user input involved.
    """
    return await payment_services.check_payment_status_service(payment_id, user.id)


@router.post(
    "/users/me/payments/report-manual",
    response_model=PaymentOut,
    status_code=status.HTTP_201_CREATED,
)
async def report_manual_payment(
    request: ReportManualPaymentRequest,
    background_tasks: BackgroundTasks,
    user=Depends(require_user),
):
    """
    Layer 2 — last-resort fallback: user submits their M-Pesa confirmation
    code when both polling and the status check above are inconclusive.
    This queues the payment for admin review — it does NOT auto-confirm
    the order.
    """
    payment = await payment_services.report_manual_payment_service(user.id, request)

    background_tasks.add_task(
        notify_manual_payment_reported,
        payment.id,
        payment.order_id,
        user.name,
        request.mpesa_code,
    )

    return payment


@router.get(
    "/users/me/payments/{payment_id}",
    response_model=PaymentOut,
    status_code=status.HTTP_200_OK,
)
async def get_payment_by_id(payment_id: int, user=Depends(require_user)):
    """Get a single payment by ID (user must own the order it belongs to)."""
    payment = await payment_services.get_payment_by_id_service(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.get(
    "/users/me/orders/{order_id}/payments",
    response_model=list[PaymentOut],
)
async def get_payments_by_order(order_id: int, user=Depends(require_user)):
    """Get all payments for a specific order."""
    return await payment_services.get_payments_by_order_id_service(order_id)