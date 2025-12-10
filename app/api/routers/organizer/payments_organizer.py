#!/usr/bin/env python3
"""Payment routes for MGLTickets."""

from fastapi import APIRouter, Depends
from app.schemas.payment import PaymentOut
import app.services.payment_services as payment_services
from app.core.security import require_organizer

router = APIRouter()

@router.get("/organizer/payments", response_model=list[PaymentOut])
async def list_all_payments(user=Depends(require_organizer)):
    """List all payments (Organizer access only)."""
    return payment_services.list_payments_service()

@router.get("/organizer/payments/status/{status}", response_model=list[PaymentOut])
async def list_payments_by_status(status: str, user=Depends(require_organizer)):
    """List payments by status (Organizer access only)."""
    return payment_services.list_payments_by_status_service(status)

@router.get("/organizer/payments/latest", response_model=list[PaymentOut])
async def list_latest_payments(latest: int = 10, user=Depends(require_organizer)):
    """List latest payments (Organizer access only)."""
    return payment_services.get_latest_payments_service(latest)