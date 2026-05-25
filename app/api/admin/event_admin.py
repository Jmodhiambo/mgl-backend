#!/usr/bin/env python3
"""Events admin routes for MGLTickets."""

from fastapi import APIRouter, Depends, UploadFile, File, Body, HTTPException, status, BackgroundTasks
from typing import Optional
from datetime import datetime

from app.schemas.event import EventOut, EventCreate, EventCreateWithFlyer
import app.services.event_services as event_services
import app.services.user_services as user_services
from app.services.notification_services import notify_event_submitted, notify_event_approved, notify_event_rejected, notify_event_cancelled
from app.core.security import require_admin
from app.utils.generate_image_url import save_flyer_and_get_url


router = APIRouter()

# Admin creation, moderation, approvals, audit and special queries
@router.post("/admin/events", response_model=EventOut)
async def create_event(
    event_data: EventCreate,
    background_tasks: BackgroundTasks,
    flyer: UploadFile = File(...),
    organizer_id: Optional[int] = Body(None, description="Admin can specify the organizer id"), 
    user=Depends(require_admin)
):
    """
    Create a new event.
    If organizer_id is provided (admin creating for someone), use it.
    """

    organizer = await user_services.get_user_by_id_service(organizer_id)
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

    event = await event_services.create_event_service(event_with_flyer)

    # Notify organizer about event submission
    background_tasks.add_task(notify_event_submitted, event.id, event.title, event.slug, organizer.name, user.name)

    return event


@router.get("/admin/events", response_model=list[EventOut])
async def get_all_approved_events(user=Depends(require_admin)):
    """
    Get all events.
    """
    return await event_services.get_approved_events_service()


@router.get("/admin/events/{event_id}", response_model=EventOut)
async def get_event_by_id(event_id: int, user=Depends(require_admin)):
    """
    Get an event by its ID.
    """
    return await event_services.get_event_by_id_service(event_id)

@router.get("/admin/events/slug/{slug}", response_model=EventOut)
async def get_event_by_slug(slug: str, user=Depends(require_admin)):
    """
    Get an event by its slug.
    """
    return await event_services.get_event_by_slug_service(slug)

@router.get("/admin/all-events", response_model=list[EventOut])
async def get_all_events(user=Depends(require_admin)):
    """
    Get all events (approved and unapproved).
    """
    return await event_services.get_all_events_service()

@router.get("/admin/events/approved", response_model=list[EventOut])
async def get_all_approved_events(user=Depends(require_admin)):
    """
    Get all approved events.
    """
    return await event_services.get_approved_events_service()


@router.get("/admin/events/unapproved", response_model=list[EventOut])
async def get_all_unapproved_events(user=Depends(require_admin)):
    """
    Get all unapproved events.
    """
    return await event_services.get_unapproved_events_service()

@router.patch("/admin/events/{event_id}/approve", response_model=bool)
async def approve_event(event_id: int, background_tasks: BackgroundTasks, user=Depends(require_admin)):
    """
    Approve an event by its ID.
    """
    event =  await event_services.approve_event_service(event_id)

    # Notify organizer about event approval
    background_tasks.add_task(notify_event_approved, event.id, event.title, event.slug, user.name, event.organizer_id)

    return event

@router.patch("/admin/events/{event_id}/reject", response_model=bool)
async def reject_event(event_id: int, background_tasks: BackgroundTasks, user=Depends(require_admin)):
    """
    Reject an event by its ID.
    """
    event = await event_services.reject_event_service(event_id)

    # Notify organizer about event rejection
    background_tasks.add_task(notify_event_rejected, event.id, event.title, event.slug, user.name, event.organizer_id, reason="Your event did not meet our guidelines. Please review and resubmit.")

    return event

@router.patch("/admin/events/{event_id}/status/{status}", response_model=bool)
async def update_event_status(event_id: int, status: str, background_tasks: BackgroundTasks, user=Depends(require_admin)):
    """
    Update the status of an event by its ID.
    """
    event = await event_services.update_event_status_service(event_id, status)

    if status.lower() == "cancelled":
        # Notify organizer about event cancellation
        background_tasks.add_task(notify_event_cancelled, event.id, event.title, role="admin", name=user.name)

    return event

@router.delete("/admin/events/{event_id}", response_model=bool)
async def delete_event(event_id: int, user=Depends(require_admin)):
    """
    Delete an event by its ID.
    """
    return await event_services.delete_event_service(event_id)


# Admin Advanced Queries
@router.get("/admin/events/organizer/{organizer_id}", response_model=list[EventOut])
async def get_events_by_organizer(organizer_id: int, user=Depends(require_admin)):
    """
    Get events by the organizer.
    """
    return await event_services.get_events_by_organizer_service(organizer_id)

@router.get("/admin/events/organizer/{organizer_id}/count", response_model=int)
async def count_events_by_organizer(organizer_id: int, user=Depends(require_admin)):
    """
    Get the total number of events for a specific organizer.
    """
    return await event_services.count_events_by_organizer_service(organizer_id)

@router.get("/admin/events/by-status/{status}", response_model=list[EventOut])
async def get_events_by_status(status: str, user=Depends(require_admin)):
    """
    Get events by their status.
    """
    return await event_services.get_events_by_status_service(status)

@router.get("/admin/events/with-bookings", response_model=list[EventOut])
async def get_events_with_bookings(user=Depends(require_admin)):
    """
    Get all events that have bookings.
    """
    return await event_services.get_events_with_bookings_service()

@router.get("/admin/events/without-bookings", response_model=list[EventOut])
async def get_events_without_bookings(user=Depends(require_admin)):
    """
    Get all events that do not have any bookings.
    """
    return await event_services.get_events_without_bookings_service()

@router.get("/admin/events/date-range/{start_date}/{end_date}", response_model=list[EventOut])
async def get_events_in_date_range(start_date: datetime, end_date: datetime, user=Depends(require_admin)):
    """
    Get all events within a specific date range.
    """
    return await event_services.get_events_in_date_range_service(start_date, end_date)

@router.get("/admin/events/created-after/{date}", response_model=list[EventOut])
async def get_events_created_after(date: datetime, user=Depends(require_admin)):
    """
    Get events created after a specific date.
    """
    return await event_services.get_events_created_after_service(date)

@router.get("/admin/events/created-before/{date}", response_model=list[EventOut])
async def get_events_created_before(date: datetime, user=Depends(require_admin)):
    """
    Get events created before a specific date.
    """
    return await event_services.get_events_created_before_service(date)

@router.get("/admin/events/updated-after/{date}", response_model=list[EventOut])
async def get_events_updated_after(date: datetime, user=Depends(require_admin)):
    """
    Get events updated after a specific date.
    """
    return await event_services.get_events_updated_after_service(date)

@router.get("/admin/events/updated-before/{date}", response_model=list[EventOut])
async def get_events_updated_before(date: datetime, user=Depends(require_admin)):
    """
    Get events updated before a specific date.
    """
    return await event_services.get_events_updated_before_service(date)