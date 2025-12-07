#!/usr/bin/env python3
"""Event routes for MGLTickets."""

from fastapi import Request, APIRouter, Depends
from app.schemas.event import EventOut
import app.services.event_services as event_services
from datetime import datetime
from app.core.security import get_current_user

router = APIRouter()


@router.get("/events", response_model=list[EventOut])
async def get_all_approved_events(user=Depends(get_current_user)):
    """
    Get all events.
    """
    return event_services.get_approved_events_service()


@router.get("/events/{event_id}", response_model=EventOut)
async def get_event_by_id(event_id: int, user=Depends(get_current_user)):
    """
    Get an event by its ID.
    """
    return event_services.get_event_by_id_service(event_id)


@router.get("/events/latest", response_model=list[EventOut])
async def get_latest_events(limit: int = 10, user=Depends(get_current_user)):
    """
    Get the latest added events.
    """
    return event_services.get_latest_events_service(limit)


@router.get("/events/search/", response_model=list[EventOut])
async def search_events_by_title(request: Request, user=Depends(get_current_user)):
    """
    Search events by different parameters.
    """
    # Search by title
    title: str = request.query_params.get("title")
    if title:
        return event_services.search_events_by_title_service(title)
    
    # Search by venue
    venue: str = request.query_params.get("venue")
    if venue:
        return event_services.search_events_by_venue_service(venue)
    
    # Search by country
    country: str = request.query_params.get("country")
    if country:
        return event_services.get_events_by_country_service(country)
    
    # Search by date range
    start_date: str = request.query_params.get("start_date")
    end_date: str = request.query_params.get("end_date")
    if start_date and end_date:
        return event_services.get_events_in_date_range_service(
            datetime.fromisoformat(start_date), datetime.fromisoformat(end_date)
        )
    return []

@router.get("/events/sorted/start-time", response_model=list[EventOut])
async def get_events_sorted_by_start_time(request: Request, ascending: bool = True, user=Depends(get_current_user)):
    """
    Get events sorted by start time.
    """
    # Determine sorting order
    order: str = request.query_params.get("order")
    if order == "desc":
        ascending = False

    # Sort by start time
    start_time: str = request.query_params.get("start_time")
    if start_time:
        return event_services.get_events_sorted_by_start_time_service(ascending)
    
    # Sort by end time
    end_time: str = request.query_params.get("end_time")
    if end_time:
        return event_services.get_events_sorted_by_end_time_service(ascending)

    return []

@router.get("/events/count", response_model=int)
async def get_total_events(user=Depends(get_current_user)):
    """
    Get the total number of events.
    """
    return event_services.count_events_service()