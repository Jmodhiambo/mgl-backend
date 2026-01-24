#!/usr/bin/env python3
"""Organizer routes for Booking operations."""

from datetime import datetime
from fastapi import APIRouter, Depends
from app.schemas.booking import BookingOut
import app.services.booking_services as booking_services
from app.core.security import require_organizer

router = APIRouter()

@router.get("/organizers/me/events/{event_id}/bookings", response_model=list[BookingOut])
async def get_bookings_by_event_organizer(event_id: int, organizer=Depends(require_organizer)):
    """Get Bookings for a specific event for an organizer."""
    return await booking_services.list_bookings_by_event_id_service(event_id)

@router.get("/organizers/me/bookings/{booking_id}", response_model=BookingOut)
async def get_booking_organizer(booking_id: int, organizer=Depends(require_organizer)):
    """Get a specific Booking by ID for organizers."""
    return await booking_services.get_booking_by_id_service(booking_id)

@router.get("/organizers/me/events/{event_id}/ticket-types/{ticket_type_id}/bookings", response_model=list[BookingOut])
async def get_bookings_by_ticket_type_organizer(event_id: int, ticket_type_id: int, organizer=Depends(require_organizer)):
    """Get Bookings for a specific ticket type within an event for organizers."""
    return await booking_services.list_bookings_for_an_event_by_ticket_type_service(event_id, ticket_type_id)

@router.get("/organizers/me/events/{event_id}/bookings", response_model=list[BookingOut])
async def get_all_bookings_for_an_event_organizer(event_id: int, organizer=Depends(require_organizer)):
    """Get all Bookings for a specific event for organizers."""
    return await booking_services.list_all_bookings_for_an_event_service(event_id)

@router.get("/organizers/me/events/{event_id}/latest-bookings", response_model=list[BookingOut])
async def get_latest_bookings_by_event_organizer(event_id: int, organizer=Depends(require_organizer)):
    """Get latest Bookings for a specific event for organizers."""
    return await booking_services.list_recent_bookings_by_event_service(event_id)

@router.get("/organizer/me/bookings/date-range/{start_date}-{end_date}", response_model=list[BookingOut])
async def list_bookings_in_date_range_organizer(start_date: datetime, end_date: datetime, organizer=Depends(require_organizer)):
    """List Bookings created within a specific date range for organizers."""    
    return await booking_services.list_bookings_in_date_range_service(start_date, end_date)