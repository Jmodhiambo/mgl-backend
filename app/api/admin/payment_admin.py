#!/usr/bin/env python3
"""API routes for Payment operations."""

from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, status
from app.schemas.payment import PaymentOut, PaymentUpdate
import app.services.payment_services as payment_services
from app.core.security import require_admin
from app.services.audit_log_services import log_admin_action_service

router = APIRouter()
@router.get("/admin/payments", response_model=PaymentOut)
def list_all_payments_admin(user=Depends(require_admin)):
    """List all payments (Admin access only)."""
    return payment_services.list_payments_service()

@router.put("/admin/payments/{payment_id}", response_model=PaymentOut)
def update_payment_admin(payment_id: int, payment_update: PaymentUpdate, user=Depends(require_admin)):
    """Update payment details (Admin access only)."""
    return payment_services.update_payment_service(payment_id, payment_update)

@router.patch("/admin/payments/{payment_id}/status", response_model=PaymentOut)
def update_payment_status_admin(payment_id: int, status: str, background_tasks: BackgroundTasks, user=Depends(require_admin)):
    """Update payment status (Admin access only)."""
    payment = payment_services.update_payment_status_service(payment_id, status)

    # Create admin log entry for payment status update
    background_tasks.add_task(
        log_admin_action_service,
        admin_id=user.id,
        admin_name=user.name,
        action="update_payment_status",
        target_type="payment",
        target_id=payment_id,
        details={"updated_payment": payment.title, "status": status},
    )

    return payment

@router.delete("/admin/payments/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_admin(payment_id: int, background_tasks: BackgroundTasks, user=Depends(require_admin)):
    """Delete a payment (Admin access only)."""
    payment = payment_services.delete_payment_service(payment_id)

    # Create admin log entry for payment deletion
    background_tasks.add_task(
        log_admin_action_service,
        admin_id=user.id,
        admin_name=user.name,
        action="delete_payment",
        target_type="payment",
        target_id=payment_id,
        details={"deleted_payment": payment.title},
    )

    return None

@router.get("/admin/payments/updated_after/{date_time}", response_model=list[PaymentOut])
def list_payments_updated_after_admin(date_time: datetime, user=Depends(require_admin)):
    """List payments updated after a specific date and time (Admin access only)."""
    return payment_services.get_payments_updated_after_service(date_time)

@router.get("/admin/payments/created_after/{date_time}", response_model=list[PaymentOut])
def list_payments_created_after_admin(date_time: datetime, user=Depends(require_admin)):
    """List payments created after a specific date and time (Admin access only)."""
    return payment_services.get_payments_created_after_service(date_time)

@router.get("/admin/payments/latest", response_model=list[PaymentOut])
def list_latest_payments_admin(latest: int = 10, user=Depends(require_admin)):
    """List latest payments (Admin access only)."""
    return payment_services.get_latest_payments_service(latest)

@router.get("/admin/payments/count", response_model=int)
def count_payments_admin(user=Depends(require_admin)):
    """Count total payments (Admin access only)."""
    return payment_services.count_payments_service()