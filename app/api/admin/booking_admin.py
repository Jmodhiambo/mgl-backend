#!/usr/bin/env python3
"""Admin booking routes."""

from fastapi import APIRouter, BackgroundTasks, Depends, status
from datetime import datetime
from app.schemas.booking import BookingOut
import app.services.booking_services as booking_services
from app.core.security import require_admin
from app.services.audit_log_services import log_admin_action_service

router = APIRouter()

# Core admin operations
@router.get("/admin/bookings", response_model=list[BookingOut])
async def list_bookings(user=Depends(require_admin)):
    """
    List all bookings.
    """
    return booking_services.list_bookings_service()

@router.get("/admin/bookings/{booking_id}", response_model=BookingOut)
async def get_booking(booking_id: int, user=Depends(require_admin)):
    """
    Get a specific booking by its ID.
    """
    return booking_services.get_booking_by_id_service(booking_id)

@router.put("/admin/bookings/{booking_id}", response_model=BookingOut)
async def update_booking(booking_id: int, booking: BookingOut, background_tasks: BackgroundTasks, user=Depends(require_admin)):
    """
    Update an existing booking.
    """
    res = await booking_services.update_booking_service(booking_id, booking)

    if res is not None:
        # Log the booking update action
        background_tasks.add_task(
            log_admin_action_service,
            admin_id=user.id,
            admin_name=user.name,
            action="update_booking",
            target_type="booking",
            target_id=booking_id,
            details={"updated_booking": booking}
        )

    return res

@router.patch("/admin/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_booking_status(booking_id: int, status: str, background_tasks: BackgroundTasks, user=Depends(require_admin)):
    """
    Update the status of an existing booking.
    """
    res = await booking_services.update_booking_status_service(booking_id, status)

    if res is not None:
        # Log the booking status update action
        background_tasks.add_task(
            log_admin_action_service,
            admin_id=user.id,
            admin_name=user.name,
            action="update_booking_status",
            target_type="booking",
            target_id=booking_id,
            details={"updated_status": status}
        )

    return res

@router.delete("/admin/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_booking(booking_id: int, background_tasks: BackgroundTasks, user=Depends(require_admin)):
    """
    Delete a specific booking by its ID.
    """
    res = await booking_services.delete_booking_service(booking_id)

    if res is not None:
        # Log the booking deletion action
        background_tasks.add_task(
            log_admin_action_service,
            admin_id=user.id,
            admin_name=user.name,
            action="delete_booking",
            target_type="booking",
            target_id=booking_id,
            details={"deleted_booking_id": booking_id}
        )

    return res

# Booking analytics and reports
@router.get("/admin/bookings/status/{status}", response_model=list[BookingOut])
async def list_bookings_by_status(status: str, user=Depends(require_admin)):
    """
    List all bookings with a specific status.
    """
    return booking_services.list_bookings_by_status_service(status)

@router.get("/admin/bookings/user/{user_id}", response_model=list[BookingOut])
async def list_bookings_by_user(user_id: int, user=Depends(require_admin)):
    """
    List all bookings for a specific user.
    """
    return booking_services.list_bookings_by_user_service(user_id)

@router.get("/admin/bookings/user/{user_id}/status/{status}", response_model=list[BookingOut])
async def list_bookings_by_user_and_status(user_id: int, status: str, user=Depends(require_admin)):
    """
    List all bookings for a specific user with a specific status.
    """
    return booking_services.list_bookings_status_by_user_service(user_id, status)

@router.get("/admin/bookings/ticket_type/{ticket_type_id}/status/{status}", response_model=list[BookingOut])
async def list_bookings_by_ticket_type_and_status(ticket_type_id: int, status: str, user=Depends(require_admin)):
    """
    List all bookings for a specific ticket type with a specific status.
    """
    return booking_services.list_bookings_by_ticket_type_and_status_service(ticket_type_id, status)

@router.get("/admin/bookings/recent", response_model=list[BookingOut])
async def list_recent_bookings(limit: int = 10, user=Depends(require_admin)):
    """
    List the most recent bookings in the database.
    """
    return booking_services.list_recent_bookings_service(limit)

@router.get("/admin/bookings/date-range/{start_date}/{end_date}", response_model=list[BookingOut])
async def list_bookings_in_date_range(start_date: datetime, end_date: datetime, user=Depends(require_admin)):
    """
    List all bookings within a specific date range.
    """
    return booking_services.list_bookings_in_date_range_service(start_date, end_date)