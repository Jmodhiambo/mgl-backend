#!/usr/bin/env python3
"""Events organizer routes for MGLTickets."""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status

from app.schemas.user import UserOut
from app.schemas.event import EventOut, EventCreate, EventCreateWithFlyer, EventStats, EventDetails, TopEvent
import app.services.event_services as event_services
import app.services.event_organizer_services as event_organizer_services

from app.core.security import require_organizer
from app.utils.generate_image_url import save_flyer_and_get_url
from app.utils.generate_slug import generate_unique_slug


router = APIRouter()

@router.post("/organizers/me/events", response_model=EventOut, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    flyer: UploadFile = File(...),
    organizer: UserOut =Depends(require_organizer)
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
    event_dict["organizer_id"] = organizer.id

    event_with_flyer = EventCreateWithFlyer(**event_dict)

    return await event_services.create_event_service(event_with_flyer)


@router.get("/organizers/me/events/{event_id}/stats", response_model=EventStats, status_code=status.HTTP_200_OK)
async def get_event_stats(event_id: int, organizer: UserOut=Depends(require_organizer)):
    """
    Get statistics for a specific event.
    
    Returns:
        - total_bookings: Total number of bookings
        - total_revenue: Total revenue from confirmed bookings
        - tickets_sold: Total tickets sold
        - tickets_remaining: Remaining tickets available
    """
    return await event_organizer_services.get_event_stats_service(event_id)


@router.get("/organizers/me/events/{event_id}/details", response_model=EventDetails, status_code=status.HTTP_200_OK)
async def get_event_details(event_id: int, organizer: UserOut=Depends(require_organizer)):
    """"
    Get complete event details including stats, ticket types, and recent bookings.
    This endpoint is useful for the EventDetails page in the frontend.
    
    Returns:
        - event: Event information
        - stats: Event statistics (bookings, revenue, tickets)
        - ticket_types: List of ticket types with their data
        - recent_bookings: Last 5 bookings for this event
    """
    return await event_organizer_services.get_event_details_service(event_id)


@router.get("/organizers/me/top-events", response_model=list[TopEvent], status_code=status.HTTP_200_OK)
async def get_top_events(limit: int = 5, organizer: UserOut=Depends(require_organizer)):
    """
    Get the top events of the current organizer.
    /organizers/me/top-events?limit=5
    """
    return await event_organizer_services.get_top_events_by_organizer_service(organizer.id, limit)


@router.put("/organizers/me/events/{event_id}", response_model=EventOut, status_code=status.HTTP_200_OK)
async def update_event(event_id: int, event_data: EventOut, organizer: UserOut=Depends(require_organizer)):
    """
    Update an event by its ID.
    """
    return await event_services.update_event_service(event_id, event_data)

@router.patch("/organizers/me/events/{event_id}", response_model=bool, status_code=status.HTTP_200_OK)
async def update_event_status(event_id: int, state: str, organizer: UserOut=Depends(require_organizer)):
    """
    Update the status of an event by its ID. 
    Allows the organizer to cancel, and delete events.
    """   
    event = await event_services.get_event_by_id_service(event_id)
    
    if event.state == "deleted":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Event has already been deleted.")
    return await event_services.update_event_status_service(event_id, state)

@router.get("/organizers/me/events", response_model=list[EventOut], status_code=status.HTTP_200_OK)
async def get_events_by_organizer(organizer: UserOut=Depends(require_organizer)):
    """
    Get events by the organizer.
    """
    return await event_services.get_events_by_organizer_service(organizer.id)

@router.get("/organizers/me/events/count", response_model=int, status_code=status.HTTP_200_OK)
async def get_total_events_by_organizer(organizer: UserOut=Depends(require_organizer)):
    """
    Get the total number of events.
    """
    return await event_services.count_events_by_organizer_service(organizer.id)
