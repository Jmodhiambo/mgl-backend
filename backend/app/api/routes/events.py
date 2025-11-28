#!/usr/bin/env python3
"""Event routes for MGLTickets."""

from fastapi import APIRouter, Depends
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


@router.get("/events/search/title", response_model=list[EventOut])
async def search_events_by_title(title: str, user=Depends(get_current_user)):
    """
    Search events by title.
    """
    return event_services.search_events_by_title_service(title)


@router.get("/events/search/venue", response_model=list[EventOut])
async def search_events_by_venue(venue: str, user=Depends(get_current_user)):
    """
    Search events by venue.
    """
    return event_services.search_events_by_venue_service(venue)


@router.get("/events/search/country", response_model=list[EventOut])
async def get_events_by_country(country: str, user=Depends(get_current_user)):
    """
    Get events by country.
    """
    return event_services.get_events_by_country_service(country)


@router.get("/events/date-range", response_model=list[EventOut])
async def get_events_in_date_range(start_date: datetime, end_date: datetime, user=Depends(get_current_user)):
    """
    Get all events within a specific date range.
    """
    return event_services.get_events_in_date_range_service(start_date, end_date)


@router.get("/events/sorted/start-time", response_model=list[EventOut])
async def get_events_sorted_by_start_time(ascending: bool = True, user=Depends(get_current_user)):
    """
    Get events sorted by start time.
    """
    return event_services.get_events_sorted_by_start_time_service(ascending)


@router.get("/events/sorted/end-time", response_model=list[EventOut])
async def get_events_sorted_by_end_time(ascending: bool = True, user=Depends(get_current_user)):
    """
    Get events sorted by end time.
    """
    return event_services.get_events_sorted_by_end_time_service(ascending)

@router.get("/events/count", response_model=int)
async def get_total_events(user=Depends(get_current_user)):
    """
    Get the total number of events.
    """
    return event_services.count_events_service()