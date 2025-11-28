#/usr/bin/env python3
"""Booking routes for MGLTickets."""

from fastapi import APIRouter, Depends, status
from app.schemas.booking import BookingOut, BookingCreate
from app.core.security import get_current_user
import app.services.booking_services as booking_services


router = APIRouter()

@router.post("/user/bookings", response_model=list[BookingOut])
async def create_bookings(booking: BookingCreate, user=Depends(get_current_user)):
    """
    Create a new booking.
    """
    return booking_services.create_booking_service(booking)


@router.get("/user/bookings", response_model=list[BookingOut])
async def list_bookings(user=Depends(get_current_user)):
    """
    List all bookings for a specific user.
    """
    return booking_services.list_bookings_by_user_service(user.id)

@router.get("/user/bookings/{booking_id}", response_model=BookingOut)
async def get_booking(booking_id: int, user=Depends(get_current_user)):
    """
    Get a specific booking by its ID.
    """
    return booking_services.get_booking_by_id_service(booking_id)

@router.put("/user/bookings/{booking_id}", response_model=BookingOut)
async def update_booking(booking_id: int, booking: BookingCreate, user=Depends(get_current_user)):
    """
    Update an existing booking.
    """
    return booking_services.update_booking_service(booking_id, booking)

@router.patch("/user/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_booking(booking_id: int, user=Depends(get_current_user)):
    """
    Delete (Mark as Cancelled) a specific booking by its ID.
    """
    return booking_services.update_booking_status_service(booking_id, "Cancelled")

@router.get("/user/bookings/status/{status}", response_model=list[BookingOut])
async def list_bookings_by_status(status: str, user=Depends(get_current_user)):
    """
    List all bookings with a specific status for a specific user.
    """
    return booking_services.list_bookings_status_by_user_service(user.id, status)