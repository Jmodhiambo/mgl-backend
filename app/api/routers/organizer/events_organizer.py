#!/usr/bin/env python3
"""Events organizer routes for MGLTickets."""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status

from app.schemas.event import EventOut, EventCreate, EventCreateWithFlyer
import app.services.event_services as event_services

from app.core.security import require_organizer
from app.utils.images import save_flyer_and_get_url
from app.utils.generate_slug import generate_unique_slug


router = APIRouter()

@router.post("/organizers/me/events", response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    flyer: UploadFile = File(...),
    user=Depends(require_organizer)
):
    """
    Create a new event by the organizer.
    """ 
    # Generate unique slug
    slug = await generate_unique_slug(event_data.title)

    # Save flyer
    flyer_url = await save_flyer_and_get_url(flyer)

    # Prepare event data for service layer
    event_dict = event_data.model_dump()
    event_dict["slug"] = slug
    event_dict["flyer_url"] = flyer_url
    event_dict["original_filename"] = flyer.filename
    event_dict["organizer_id"] = user.id

    event_with_flyer = EventCreateWithFlyer(**event_dict)

    return event_services.create_event_service(event_with_flyer)

@router.put("/organizers/me/events/{event_id}", response_model=EventOut, status_code=status.HTTP_200_OK)
async def update_event(event_id: int, event_data: EventOut, user=Depends(require_organizer)):
    """
    Update an event by its ID.
    """
    return event_services.update_event_service(event_id, event_data)

@router.patch("/organizers/me/events/{event_id}", response_model=bool, status_code=status.HTTP_200_OK)
async def update_event_status(event_id: int, state: str, user=Depends(require_organizer)):
    """
    Update the status of an event by its ID. 
    Allows the organizer to cancel, and delete events.
    """   
    event = event_services.get_event_by_id_service(event_id)
    
    if event.state == "deleted":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Event has already been deleted.")
    return event_services.update_event_status_service(event_id, state)

@router.get("/organizers/me/events", response_model=list[EventOut], status_code=status.HTTP_200_OK)
async def get_events_by_organizer(user=Depends(require_organizer)):
    """
    Get events by the organizer.
    """
    return event_services.get_events_by_organizer_service(user.id)

@router.get("/organizers/me/events/count", response_model=int, status_code=status.HTTP_200_OK)
async def get_total_events_by_organizer(user=Depends(require_organizer)):
    """
    Get the total number of events.
    """
    return event_services.count_events_by_organizer_service(user.id)
