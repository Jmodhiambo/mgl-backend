#!/usr/bin/env python3
"""Event routes for MGLTickets."""

from fastapi import APIRouter, Depends
from app.schemas.event import EventOut
import app.services.event_services as event_services
from datetime import datetime
from app.core.security import require_user

from typing import Optional

router = APIRouter()


@router.get("/events", response_model=list[EventOut])
async def get_all_approved_events(user=Depends(require_user)):
    """
    Get all events.
    """
    return await event_services.get_approved_events_service()


@router.get("/events/{event_id}", response_model=EventOut)
async def get_event_by_id(event_id: int, user=Depends(require_user)):
    """
    Get an event by its ID.
    """
    return await event_services.get_event_by_id_service(event_id)


@router.get("/events/{slug}", response_model=EventOut)
async def get_event_by_slug(slug: str, user=Depends(require_user)):
    """
    Get an event by its slug.
    """
    return await event_services.get_event_by_slug_service(slug)


@router.get("/events/latest", response_model=list[EventOut])
async def get_latest_events(limit: int = 10, user=Depends(require_user)):
    """
    Get the latest added events.
    """
    return await event_services.get_latest_events_service(limit)


@router.get("/events/search/", response_model=list[EventOut])
async def search_events(
    title: Optional[str] = None,
    venue: Optional[str] = None,
    country: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user=Depends(require_user)
):
    """
    Search events by different parameters.
    """
    # Search by title
    if title:
        return await event_services.search_events_by_title_service(title)
    
    # Search by venue
    if venue:
        return await event_services.search_events_by_venue_service(venue)
    
    # Search by country
    if country:
        return await event_services.get_events_by_country_service(country)
    
    # Search by date range
    if start_date and end_date:
        return await event_services.get_events_in_date_range_service(
            datetime.fromisoformat(start_date), datetime.fromisoformat(end_date)
        )
    return []

@router.get("/events/sorted/", response_model=list[EventOut])
async def get_events_sorted_by_start_time(
    order: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    ascending: bool = True,
    user=Depends(require_user)
):
    """
    Get events sorted by start time.
    """
    #
    if order == "desc":
        ascending = False

    # Sort by start time
    if start_time:
        return await event_services.get_events_sorted_by_start_time_service(ascending)
    
    # Sort by end time
    if end_time:
        return await event_services.get_events_sorted_by_end_time_service(ascending)

    return []

@router.get("/events/count", response_model=int)
async def get_total_events(user=Depends(require_user)):
    """
    Get the total number of events.
    """
    return await event_services.count_events_service()