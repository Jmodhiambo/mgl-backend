#!/usr/bin/env python3
"""User-facing booking routes for MGLTickets.
 
NOTE: There is no POST endpoint here. Bookings are created as part of an
Order — see orders_user_router.py (POST /users/me/orders), which creates
one Booking per ticket type line item in a single transaction.
"""

from fastapi import APIRouter, Depends, status
from app.schemas.booking import BookingOut, BookingUpdate
from app.core.security import require_user
import app.services.booking_services as booking_services

router = APIRouter()

# Specific paths BEFORE /{booking_id} to prevent route shadowing
@router.get("/users/me/bookings/count", response_model=int, status_code=status.HTTP_200_OK)
async def get_total_bookings(user=Depends(require_user)):
    """Get the total number of bookings for the current user."""
    return await booking_services.get_total_bookings_by_user_service(user.id)

@router.get("/users/me/bookings/status/{booking_status}", response_model=list[BookingOut], status_code=status.HTTP_200_OK)
async def list_bookings_by_status(booking_status: str, user=Depends(require_user)):
    """List all bookings with a specific status for the current user."""
    return await booking_services.list_bookings_status_by_user_service(user.id, booking_status)

@router.get("/users/me/bookings", response_model=list[BookingOut], status_code=status.HTTP_200_OK)
async def list_bookings(user=Depends(require_user)):
    """List all bookings for the current user."""
    return await booking_services.list_bookings_by_user_service(user.id)

@router.get("/users/me/bookings/{booking_id}", response_model=BookingOut, status_code=status.HTTP_200_OK)
async def get_booking_by_id(booking_id: int, user=Depends(require_user)):
    """Get a specific booking by its ID."""
    return await booking_services.get_booking_by_id_service(booking_id)

@router.put("/users/me/bookings/{booking_id}", response_model=BookingOut, status_code=status.HTTP_200_OK)
async def update_booking_by_id(booking_id: int, booking: BookingUpdate, user=Depends(require_user)):
    """Update an existing booking."""
    return await booking_services.update_booking_service(booking_id, booking)

@router.patch("/users/me/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_booking_by_id(booking_id: int, user=Depends(require_user)):
    """Cancel a booking (marks status as Cancelled)."""
    await booking_services.update_booking_status_service(booking_id, "cancelled")