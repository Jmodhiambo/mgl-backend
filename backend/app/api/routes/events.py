#!/usr/bin/env python3
"""Events routes for MGLTickets."""

from fastapi import APIRouter, Depends, UploadFile, File, Body, HTTPException, status
from typing import Optional

from app.schemas.event import EventOut, EventCreate, EventCreateWithFlyer
import app.services.event_services as event_services
import app.services.user_services as user_services

from app.core.security import get_current_user, require_organizer
from app.utils.flyer import save_flyer_and_get_url


router = APIRouter()

@router.get("/events", response_model=list[EventOut])
async def get_all_events(user=Depends(get_current_user)):
    """
    Get all events.
    """
    return event_services.get_all_events_service()

@router.get("/events/test", response_model=list[EventOut])
async def get_latest_events(): # user=Depends(get_current_user)
    """
    Test the route.
    """
    return [
        {
            "id": 1,
            "title": "Exciting Music Festival Tonight",
            "organizer_id": 42,
            "description": "A fantastic show with live bands and food trucks.",
            "venue": "123 Main Street, Springfield",
            "start_time": "2025-11-21T18:00:00",
            "end_time": "2025-11-21T21:00:00",
            "flyer_url": "http://example.com/flyer1.png",
            "status": "active",
            "created_at": "2025-10-21T14:30:00",
            "updated_at": "2025-11-21T12:00:00"
        }
    ]


@router.get("/events/{event_id}", response_model=EventOut)
async def get_event_by_id(event_id: int, user=Depends(get_current_user)):
    """
    Get an event by its ID.
    """
    return event_services.get_event_by_id_service(event_id)

@router.post("/events", response_model=EventOut)
async def create_event(
    event_data: EventCreate,
    flyer: UploadFile = File(...),
    organizer_id: Optional[int] = Body(None, description="Admin can specify the organizer id"), 
    user=Depends(require_organizer)
):
    """
    Create a new event.
    If organizer_id is provided (admin creating for someone), use it.
    """
    if organizer_id:  # Check if organizer exists
        organizer = user_services.get_user_by_id_service(organizer_id)
        if not organizer or organizer.role != "organizer":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organizer not found.")
        
        if user.role not in ("admin", "superadmin"): # Only admins and superadmins can create events for other organizers
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You must be an admin or superadmin to create an event for another organizer.")
    
    # Save flyer
    flyer_url = await save_flyer_and_get_url(flyer)

    # Prepare event data for service layer
    event_dict = event_data.dict()
    event_dict["flyer_url"] = flyer_url
    event_dict["original_filename"] = flyer.filename
    event_dict["organizer_id"] = organizer_id if organizer_id else user.id

    event_with_flyer = EventCreateWithFlyer(**event_dict)

    return event_services.create_event_service(event_with_flyer)

@router.put("/events/{event_id}", response_model=EventOut)
async def update_event(event_id: int, event_data: EventOut, user=Depends(get_current_user)):
    """
    Update an event by its ID.
    """
    return event_services.update_event_service(event_id, event_data)

@router.post("/events/{event_id}/approve", response_model=EventOut)
async def approve_event(event_id: int, user=Depends(get_current_user)):
    """
    Approve an event by its ID.
    """
    return event_services.approve_event_service(event_id)

@router.post("/events/{event_id}/reject", response_model=EventOut)
async def reject_event(event_id: int, user=Depends(get_current_user)):
    """
    Reject an event by its ID.
    """
    return event_services.reject_event_service(event_id)

@router.delete("/events/{event_id}", response_model=EventOut)
async def delete_event(event_id: int, user=Depends(get_current_user)):
    """
    Delete an event by its ID.
    """
    return event_services.delete_event_service(event_id)

@router.put("/events/{event_id}/status/{status}", response_model=EventOut)
async def update_event_status(event_id: int, status: str, user=Depends(get_current_user)):
    """
    Update the status of an event by its ID.
    """
    return event_services.update_event_status_service(event_id, status)

@router.get("/events/status/{status}", response_model=list[EventOut])
async def get_events_by_status(status: str, user=Depends(get_current_user)):
    """
    Get events by their status.
    """
    return event_services.get_events_by_status_service(status)