#!/usr/bin/env python3
"""Organizer-Payment routes for MGLTickets."""

"""
I do not see the need why an organizer should be able to see payments, since they already see the bookings made plus the status of the booking.
I also do not see the need for an organizer to see the payments for a specific event, since the organizer can see the bookings for that event.
"""
# from fastapi import APIRouter, Depends
# from app.schemas.payment import PaymentOut
# import app.services.payment_services as payment_services
# from app.core.security import require_organizer

# router = APIRouter()

# @router.get("/organizers/me/payments", response_model=list[PaymentOut])
# async def list_all_payments(user=Depends(require_organizer)):
#     """List all payments (Organizer access only)."""
#     return payment_services.list_payments_service()

# @router.get("/organizers/me/payments/status/{status}", response_model=list[PaymentOut])
# async def list_payments_by_status(status: str, user=Depends(require_organizer)):
#     """List payments by status (Organizer access only)."""
#     return payment_services.list_payments_by_status_service(status)

# @router.get("/organizers/me/payments/latest", response_model=list[PaymentOut])
# async def list_latest_payments(latest: int = 10, user=Depends(require_organizer)):
#     """List latest payments (Organizer access only)."""
#     return payment_services.get_latest_payments_service(latest)