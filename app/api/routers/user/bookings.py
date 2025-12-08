#/usr/bin/env python3
"""Booking routes for MGLTickets."""

from fastapi import APIRouter, Depends, status, HTTPException
from app.schemas.booking import BookingOut, BookingCreate, BookingUpdate
from app.core.security import get_current_user
import app.services.booking_services as booking_services


router = APIRouter()

@router.post("/users/{user_id}/bookings", response_model=list[BookingOut], status_code=status.HTTP_201_CREATED)
async def create_bookings(user_id: int, booking: BookingCreate, user=Depends(get_current_user)):
    """
    Create a new booking.
    """
    if user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create this booking")
    return booking_services.create_booking_service(booking)


@router.get("/users/{user_id}/bookings", response_model=list[BookingOut], status_code=status.HTTP_200_OK)
async def list_bookings(user_id: int, user=Depends(get_current_user)):
    """
    List all bookings for a specific user.
    """
    if user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view these bookings")
    return booking_services.list_bookings_by_user_service(user_id)

@router.get("/users/{user_id}/bookings/{booking_id}", response_model=BookingOut, status_code=status.HTTP_200_OK)
async def get_booking_by_id(user_id: int, booking_id: int, user=Depends(get_current_user)):
    """
    Get a specific booking by its ID.
    """
    if user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this booking")
    return booking_services.get_booking_by_id_service(booking_id)

@router.put("/users/{user_id}/bookings/{booking_id}", response_model=BookingOut, status_code=status.HTTP_200_OK)
async def update_booking_by_id(user_id: int, booking_id: int, booking: BookingUpdate, user=Depends(get_current_user)):
    """
    Update an existing booking.
    """
    if user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this booking")
    return booking_services.update_booking_service(booking_id, booking)

@router.patch("/users/{user_id}/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_booking_by_id(user_id: int, booking_id: int, user=Depends(get_current_user)):
    """
    Delete (Mark as Cancelled) a specific booking by its ID.
    """
    if user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to cancel this booking")
    booking_services.update_booking_status_service(booking_id, "Cancelled")

@router.get("/users/{user_id}/bookings/status/{booking_status}", response_model=list[BookingOut], status_code=status.HTTP_200_OK)
async def list_bookings_by_status(user_id: int, booking_status: str, user=Depends(get_current_user)):
    """
    List all bookings with a specific status for a specific user.
    """
    if user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view these bookings")
    return booking_services.list_bookings_status_by_user_service(user_id, booking_status)

@router.get("/users/{user_id}/bookings/count", response_model=int, status_code=status.HTTP_200_OK)
async def get_total_bookings(user_id: int, user=Depends(get_current_user)):
    """
    Get the total number of bookings for a specific user.
    """
    if user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this information")
    return booking_services.get_total_bookings_by_user_service(user_id)