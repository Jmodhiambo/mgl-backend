#!/usr/bin/env python3
"""Organizer routes for Booking operations."""

from fastapi import status
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from app.schemas.booking import BookingOut, BookingEnrichedOut
from app.schemas.pagination import PaginatedResponse
from app.schemas.user import UserOut
import app.services.booking_services as booking_services
from app.core.security import require_organizer

router = APIRouter()

@router.get("/organizers/me/events/{event_id}/bookings",
            response_model=PaginatedResponse[BookingEnrichedOut], status_code=status.HTTP_200_OK)
async def get_bookings_by_event_organizer(
    event_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    organizer: UserOut = Depends(require_organizer),
):
    """Get enriched, paginated Bookings for a specific event for an organizer.
    Data source for the BookingsView "Bookings" tab when scoped to one event.

    NOTE: this used to be declared twice in this router (an identical
    `get_all_bookings_for_an_event_organizer` handler further down shared the
    exact same path/method). Since FastAPI only ever routes to the
    first-registered match, that second handler was unreachable dead code —
    it's been removed rather than updated in step with this pagination
    change, since keeping it around with a stale, non-paginated signature
    would've been misleading."""
    return await booking_services.list_event_bookings_enriched_service(
        event_id, limit=limit, offset=offset
    )

@router.get("/organizers/me/bookings/{booking_id}",
            response_model=BookingOut, status_code=status.HTTP_200_OK)
async def get_booking_organizer(booking_id: int, organizer: UserOut=Depends(require_organizer)):
    """Get a specific Booking by ID for organizers."""
    return await booking_services.get_booking_by_id_service(booking_id)

@router.get("/organizers/me/events/{event_id}/ticket-types/{ticket_type_id}/bookings",
            response_model=list[BookingOut], status_code=status.HTTP_200_OK)
async def get_bookings_by_ticket_type_organizer(event_id: int, ticket_type_id: int, organizer: UserOut=Depends(require_organizer)):
    """Get Bookings for a specific ticket type within an event for organizers."""
    return await booking_services.list_bookings_for_an_event_by_ticket_type_service(event_id, ticket_type_id)

@router.get("/organizers/me/recent-bookings",
            response_model=PaginatedResponse[BookingEnrichedOut], status_code=status.HTTP_200_OK)
async def get_recent_bookings(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    organizer: UserOut = Depends(require_organizer),
):
    """Get paginated, enriched bookings across all of the current organizer's
    events, newest first. Data source for the BookingsView "Bookings" tab
    when no event filter is applied.

    NOTE: despite the "recent" name (kept for URL backwards-compat), this is
    a full paginated listing now, not a fixed top-N — the frontend used to
    work around the lack of real pagination by requesting limit=100 and
    filtering client-side."""
    return await booking_services.get_recent_bookings_by_organizer_service(
        organizer.id, limit=limit, offset=offset
    )

@router.get("/organizers/me/events/{event_id}/latest-bookings",
            response_model=list[BookingEnrichedOut], status_code=status.HTTP_200_OK)
async def get_latest_bookings_by_event_organizer(event_id: int, organizer: UserOut=Depends(require_organizer)):
    """Get latest enriched Bookings for a specific event for organizers."""
    return await booking_services.list_recent_bookings_by_event_service(event_id)

@router.get("/organizers/me/bookings/date-range/{start_date}-{end_date}",
            response_model=list[BookingOut], status_code=status.HTTP_200_OK)
async def list_bookings_in_date_range_organizer(start_date: datetime, end_date: datetime, organizer: UserOut=Depends(require_organizer)):
    """List Bookings created within a specific date range for organizers."""
    return await booking_services.list_bookings_in_date_range_service(start_date, end_date)