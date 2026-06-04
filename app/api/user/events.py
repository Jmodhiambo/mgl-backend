#!/usr/bin/env python3
"""
Public event routes for MGLTickets.

Both unauthenticated (Events.tsx / EventDetails.tsx) and authenticated
(BrowseEvents.tsx / BrowseEventDetails.tsx) users hit these same endpoints.
The frontend decides which component to render; the backend doesn't
distinguish between the two — both call require_user.

Route ordering rules applied here:
  1. Fixed paths (/events/latest, /events/search/, etc.) MUST be
     registered BEFORE parameterised paths (/events/{identifier}).
     FastAPI matches routes top-to-bottom; if /{identifier} comes
     first, the word "latest" is treated as the identifier value.
  2. The original file had TWO conflicting parameterised routes:
       GET /events/{event_id}   (int)
       GET /events/{slug}       (str)
     FastAPI cannot distinguish these — both match any path segment.
     They are merged into a single smart route that checks whether
     the identifier is numeric.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from app.schemas.event import EventOut
import app.services.event_services as event_services
from app.core.security import require_user, get_current_user_optional

router = APIRouter()


# ── Fixed paths first ─────────────────────────────────────────────────────────

@router.get("/events", response_model=list[EventOut])
async def get_all_approved_events(user=Depends(get_current_user_optional)):
    """Get all approved events."""
    return await event_services.get_approved_events_service()


@router.get("/events/latest", response_model=list[EventOut])
async def get_latest_events(limit: int = 10, user=Depends(get_current_user_optional)):
    """Get the latest approved events."""
    return await event_services.get_latest_events_service(limit)


@router.get("/events/count", response_model=int)
async def get_total_events(user=Depends(require_user)):
    """Get the total number of approved events."""
    return await event_services.count_events_service()


@router.get("/events/search/", response_model=list[EventOut])
async def search_events(
    title: Optional[str] = None,
    venue: Optional[str] = None,
    country: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    user=Depends(get_current_user_optional),
):
    """Search approved events by title, venue, country, or date range."""
    if title:
        return await event_services.search_events_by_title_service(title)
    if venue:
        return await event_services.search_events_by_venue_service(venue)
    if country:
        return await event_services.get_events_by_country_service(country)
    if start_date and end_date:
        return await event_services.get_events_in_date_range_service(
            datetime.fromisoformat(start_date),
            datetime.fromisoformat(end_date),
        )
    return []


@router.get("/events/sorted/", response_model=list[EventOut])
async def get_events_sorted(
    order: str = "asc",
    sort_by: str = "start_time",
    user=Depends(require_user),
):
    """Get approved events sorted by start_time or end_time."""
    ascending = order.lower() != "desc"
    if sort_by == "end_time":
        return await event_services.get_events_sorted_by_end_time_service(ascending)
    return await event_services.get_events_sorted_by_start_time_service(ascending)


# ── Parameterised path last ───────────────────────────────────────────────────

@router.get("/events/{identifier}", response_model=EventOut)
async def get_event(identifier: str, user=Depends(require_user)):
    """
    Get an event by its numeric ID or its slug.

    FastAPI cannot have two separate routes for /events/{event_id} (int)
    and /events/{slug} (str) because both match the same URL shape.
    This single route handles both: if the identifier is all digits it
    is treated as an ID, otherwise as a slug.
    """
    if identifier.isdigit():
        return await event_services.get_event_by_id_service(int(identifier))
    return await event_services.get_event_by_slug_service(identifier)