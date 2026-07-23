#!/usr/bin/env python3
"""API routes for Payment operations."""

from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from app.schemas.payment import (
    PaymentOut,
    PaymentUpdate,
    PaymentEnrichedOut,
    ReconcileStuckPaymentsResponse,
    ManualPaymentReviewRequest,
)
import app.services.payment_services as payment_services
from app.core.security import require_admin
from app.services.audit_log_services import log_admin_action_service
from app.services.notification_services import notify_manual_payment_resolved

router = APIRouter()

@router.get("/admin/payments", response_model=list[PaymentEnrichedOut])
async def list_all_payments_admin(user=Depends(require_admin)):
    """List all payments with customer name (Admin access only)."""
    return await payment_services.list_payments_enriched_service()

@router.put("/admin/payments/{payment_id}", response_model=PaymentOut)
async def update_payment_admin(
    payment_id: int, payment_update: PaymentUpdate, user=Depends(require_admin)
):
    """Update payment details (Admin access only)."""
    return await payment_services.update_payment_service(payment_id, payment_update)

@router.patch("/admin/payments/{payment_id}/status", response_model=PaymentOut)
async def update_payment_status_admin(
    payment_id: int, status: str, background_tasks: BackgroundTasks, user=Depends(require_admin)
):
    """Update payment status (Admin access only)."""
    payment = await payment_services.update_payment_status_service(payment_id, status)

    background_tasks.add_task(
        log_admin_action_service,
        admin_id=user.id,
        admin_name=user.name,
        action="update_payment_status",
        target_type="payment",
        target_id=payment_id,
        details={"payment_id": payment_id, "status": status},
    )

    return payment

@router.delete("/admin/payments/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment_admin(
    payment_id: int, background_tasks: BackgroundTasks, user=Depends(require_admin)
):
    """Delete a payment (Admin access only)."""
    await payment_services.delete_payment_service(payment_id)

    background_tasks.add_task(
        log_admin_action_service,
        admin_id=user.id,
        admin_name=user.name,
        action="delete_payment",
        target_type="payment",
        target_id=payment_id,
        details={"deleted_payment_id": payment_id},
    )

    return None

@router.get("/admin/payments/updated_after/{date_time}", response_model=list[PaymentOut])
async def list_payments_updated_after_admin(date_time: datetime, user=Depends(require_admin)):
    """List payments updated after a specific date and time (Admin access only)."""
    return await payment_services.get_payments_updated_after_service(date_time)

@router.get("/admin/payments/created_after/{date_time}", response_model=list[PaymentOut])
async def list_payments_created_after_admin(date_time: datetime, user=Depends(require_admin)):
    """List payments created after a specific date and time (Admin access only)."""
    return await payment_services.get_payments_created_after_service(date_time)

@router.get("/admin/payments/latest", response_model=list[PaymentOut])
async def list_latest_payments_admin(latest: int = 10, user=Depends(require_admin)):
    """List latest payments (Admin access only)."""
    return await payment_services.get_latest_payments_service(latest)

@router.get("/admin/payments/count", response_model=int)
async def count_payments_admin(user=Depends(require_admin)):
    """Count total payments (Admin access only)."""
    return await payment_services.count_payments_service()


# ── Layer 1: reconciliation sweep ─────────────────────────────────────────────

@router.post("/admin/payments/reconcile-stuck", response_model=ReconcileStuckPaymentsResponse)
async def reconcile_stuck_payments_admin(
    older_than_minutes: int = 5,
    user=Depends(require_admin),
):
    """
    Sweeps Payments stuck in 'pending' for longer than `older_than_minutes`
    and resolves each via the Daraja STK status query — no user input,
    same lookup the check-status endpoint uses.

    No scheduler is wired up yet — point a cron job or APScheduler task at
    this endpoint (e.g. every 2-5 minutes) once you set one up. Manually
    triggerable from the admin UI in the meantime.
    """
    return await payment_services.reconcile_stuck_payments_service(older_than_minutes)


# ── Layer 2: manual review ────────────────────────────────────────────────────

@router.get("/admin/payments/manual-review", response_model=list[PaymentOut])
async def list_manual_review_payments_admin(user=Depends(require_admin)):
    """
    Payments with a user-submitted M-Pesa code report awaiting a decision.
    Doesn't include payments an admin might resolve proactively without a
    user report — those are just any pending mpesa order on the Orders page.
    """
    return await payment_services.list_manual_review_payments_service()


@router.patch("/admin/payments/{payment_id}/manual-review", response_model=PaymentOut)
async def review_manual_payment_admin(
    payment_id: int,
    review: ManualPaymentReviewRequest,
    background_tasks: BackgroundTasks,
    user=Depends(require_admin),
):
    """
    Approve or reject a payment by M-Pesa code.

    Works two ways:
      - review.mpesa_code omitted, approving a code the user already
        reported (payment.user_reported_mpesa_code is used).
      - review.mpesa_code supplied directly — for a payment nobody
        reported, resolved by the admin off the till statement.

    Approving confirms the order and issues tickets via the same shared
    path the real Daraja callback uses. Rejecting only applies to an
    actual user-submitted report and leaves the payment exactly where it
    was so the user can be told to try again.
    """
    if review.approve:
        result = await payment_services.approve_manual_payment_service(
            payment_id, mpesa_code=review.mpesa_code, admin_notes=review.admin_notes
        )
        action = "manual_payment_approved"
    else:
        result = await payment_services.reject_manual_payment_service(
            payment_id, admin_notes=review.admin_notes
        )
        action = "manual_payment_rejected"

    background_tasks.add_task(
        log_admin_action_service,
        admin_id=user.id,
        admin_name=user.name,
        action=action,
        target_type="payment",
        target_id=payment_id,
        details={"admin_notes": review.admin_notes, "mpesa_code": review.mpesa_code},
    )
    background_tasks.add_task(
        notify_manual_payment_resolved,
        payment_id,
        review.approve,
    )

    payment = await payment_services.get_payment_by_id_service(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment