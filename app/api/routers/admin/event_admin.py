#!/usr/bin/env python3
"""Events admin routes for MGLTickets."""

from fastapi import APIRouter, Depends, UploadFile, File, Body, HTTPException, status
from typing import Optional
from datetime import datetime

from app.schemas.event import EventOut, EventCreate, EventCreateWithFlyer
import app.services.event_services as event_services
import app.services.user_services as user_services

from app.core.security import require_admin
from app.utils.generate_image_url import save_flyer_and_get_url


router = APIRouter()

# Admin creation, moderation, approvals, audit and special queries
@router.post("/admin/events", response_model=EventOut)
async def create_event(
    event_data: EventCreate,
    flyer: UploadFile = File(...),
    organizer_id: Optional[int] = Body(None, description="Admin can specify the organizer id"), 
    user=Depends(require_admin)
):
    """
    Create a new event.
    If organizer_id is provided (admin creating for someone), use it.
    """

    organizer = user_services.get_user_by_id_service(organizer_id)
    if not organizer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Organizer with ID {organizer_id} not found.")
    
    # Save flyer
    flyer_url = await save_flyer_and_get_url(flyer)

    # Prepare event data for service layer
    event_dict = event_data.dict()
    event_dict["flyer_url"] = flyer_url
    event_dict["original_filename"] = flyer.filename
    event_dict["organizer_id"] = organizer_id if organizer_id else user.id

    event_with_flyer = EventCreateWithFlyer(**event_dict)

    return event_services.create_event_service(event_with_flyer)


@router.get("/admin/events", response_model=list[EventOut])
async def get_all_approved_events(user=Depends(require_admin)):
    """
    Get all events.
    """
    return event_services.get_approved_events_service()


@router.get("/admin/events/{event_id}", response_model=EventOut)
async def get_all_events(event_id: int, user=Depends(require_admin)):
    """
    Get an event by its ID.
    """
    return event_services.get_all_events_service()

@router.get("/admin/events/approved", response_model=list[EventOut])
async def get_all_approved_events(user=Depends(require_admin)):
    """
    Get all approved events.
    """
    return event_services.get_approved_events_service()


@router.get("/admin/events/unapproved", response_model=list[EventOut])
async def get_all_unapproved_events(user=Depends(require_admin)):
    """
    Get all unapproved events.
    """
    return event_services.get_unapproved_events_service()

@router.patch("/admin/events/{event_id}/approve", response_model=bool)
async def approve_event(event_id: int, user=Depends(require_admin)):
    """
    Approve an event by its ID.
    """
    return event_services.approve_event_service(event_id)

@router.patch("/admin/events/{event_id}/reject", response_model=bool)
async def reject_event(event_id: int, user=Depends(require_admin)):
    """
    Reject an event by its ID.
    """
    return event_services.reject_event_service(event_id)

@router.patch("/admin/events/{event_id}/activate", response_model=bool)
async def activate_event(event_id: int, user=Depends(require_admin)):
    """
    Activate an event by its ID.
    """
    return event_services.activate_event_service(event_id)

@router.patch("/admin/events/{event_id}/deactivate", response_model=bool)
async def deactivate_event(event_id: int, user=Depends(require_admin)):
    """
    Deactivate an event by its ID.
    """
    return event_services.deactivate_event_service(event_id)

@router.patch("/admin/events/{event_id}/status/{status}", response_model=bool)
async def update_event_status(event_id: int, status: str, user=Depends(require_admin)):
    """
    Update the status of an event by its ID.
    """
    return event_services.update_event_status_service(event_id, status)

@router.delete("/admin/events/{event_id}", response_model=bool)
async def delete_event(event_id: int, user=Depends(require_admin)):
    """
    Delete an event by its ID.
    """
    return event_services.delete_event_service(event_id)


# Admin Advanced Queries
@router.get("/admin/events/organizer/{organizer_id}", response_model=list[EventOut])
async def get_events_by_organizer(organizer_id: int, user=Depends(require_admin)):
    """
    Get events by the organizer.
    """
    return event_services.get_events_by_organizer_service(organizer_id)

@router.get("/admin/events/organizer/{organizer_id}/count", response_model=int)
async def count_events_by_organizer(organizer_id: int, user=Depends(require_admin)):
    """
    Get the total number of events for a specific organizer.
    """
    return event_services.count_events_by_organizer_service(organizer_id)

@router.get("/admin/events/by-status/{status}", response_model=list[EventOut])
async def get_events_by_status(status: str, user=Depends(require_admin)):
    """
    Get events by their status.
    """
    return event_services.get_events_by_status_service(status)

@router.get("/admin/events/with-bookings", response_model=list[EventOut])
async def get_events_with_bookings(user=Depends(require_admin)):
    """
    Get all events that have bookings.
    """
    return event_services.get_events_with_bookings_service()

@router.get("/admin/events/without-bookings", response_model=list[EventOut])
async def get_events_without_bookings(user=Depends(require_admin)):
    """
    Get all events that do not have any bookings.
    """
    return event_services.get_events_without_bookings_service()

@router.get("/admin/events/date-range/{start_date}/{end_date}", response_model=list[EventOut])
async def get_events_in_date_range(start_date: datetime, end_date: datetime, user=Depends(require_admin)):
    """
    Get all events within a specific date range.
    """
    return event_services.get_events_in_date_range_service(start_date, end_date)

@router.get("/admin/events/created-after/{date}", response_model=list[EventOut])
async def get_events_created_after(date: datetime, user=Depends(require_admin)):
    """
    Get events created after a specific date.
    """
    return event_services.get_events_created_after_service(date)

@router.get("/admin/events/created-before/{date}", response_model=list[EventOut])
async def get_events_created_before(date: datetime, user=Depends(require_admin)):
    """
    Get events created before a specific date.
    """
    return event_services.get_events_created_before_service(date)

@router.get("/admin/events/updated-after/{date}", response_model=list[EventOut])
async def get_events_updated_after(date: datetime, user=Depends(require_admin)):
    """
    Get events updated after a specific date.
    """
    return event_services.get_events_updated_after_service(date)

@router.get("/admin/events/updated-before/{date}", response_model=list[EventOut])
async def get_events_updated_before(date: datetime, user=Depends(require_admin)):
    """
    Get events updated before a specific date.
    """
    return event_services.get_events_updated_before_service(date)