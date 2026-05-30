#!/usr/bin/env python3
"""
Events organizer routes for MGLTickets.

Route ordering fix applied:
  GET /organizers/me/events/count  must be registered BEFORE
  GET /organizers/me/events/{event_id}/...
  Otherwise FastAPI matches the literal word "count" as an event_id
  parameter and the count route is never reachable.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, BackgroundTasks

from app.schemas.user import UserOut
from app.schemas.event import (
    OrganizerEventOut,
    EventCreate,
    EventCreateWithFlyer,
    EventStats,
    EventDetails,
    TopEvent,
    EventUpdate,
)
import app.services.event_services as event_services
import app.services.event_organizer_services as event_organizer_services
from app.services.notification_services import notify_event_submitted
from app.core.security import require_organizer
from app.utils.generate_image_url import save_flyer_and_get_url
from app.utils.generate_slug import generate_unique_slug


router = APIRouter()


# ── Fixed paths first (before any /{event_id} routes) ────────────────────────

@router.get(
    "/organizers/me/events",
    response_model=list[OrganizerEventOut],
    status_code=status.HTTP_200_OK,
)
async def get_events_by_organizer(organizer: UserOut = Depends(require_organizer)):
    """Get all events for the current organizer with booking/revenue stats."""
    return await event_organizer_services.get_events_by_organizer_service(organizer.id)


@router.get(
    "/organizers/me/events/count",
    response_model=int,
    status_code=status.HTTP_200_OK,
)
async def get_total_events_by_organizer(organizer: UserOut = Depends(require_organizer)):
    """
    Get the total number of events for the current organizer.
    MUST be registered before /{event_id} routes or FastAPI
    treats 'count' as an event_id value.
    """
    return await event_services.count_events_by_organizer_service(organizer.id)


@router.get(
    "/organizers/me/top-events",
    response_model=list[TopEvent],
    status_code=status.HTTP_200_OK,
)
async def get_top_events(limit: int = 5, organizer: UserOut = Depends(require_organizer)):
    """Get the top events of the current organizer by revenue."""
    return await event_organizer_services.get_top_events_by_organizer_service(
        organizer.id, limit
    )


# ── Create ────────────────────────────────────────────────────────────────────

@router.post(
    "/organizers/me/events",
    response_model=OrganizerEventOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_event(
    event_data: EventCreate,
    background_tasks: BackgroundTasks,
    flyer: UploadFile = File(...),
    organizer: UserOut = Depends(require_organizer),
):
    """Create a new event by the organizer."""
    slug = await generate_unique_slug(event_data.title)
    flyer_url = await save_flyer_and_get_url(flyer)

    event_dict = event_data.model_dump()
    event_dict["slug"] = slug
    event_dict["flyer_url"] = flyer_url
    event_dict["original_filename"] = flyer.filename
    event_dict["organizer_id"] = organizer.id

    event_with_flyer = EventCreateWithFlyer(**event_dict)
    event = await event_services.create_event_service(event_with_flyer)

    background_tasks.add_task(
        notify_event_submitted, event.id, event.title, event.slug, organizer.name
    )
    return event


# ── Parameterised routes (/{event_id}) AFTER fixed paths ─────────────────────

@router.get(
    "/organizers/me/events/{event_id}/stats",
    response_model=EventStats,
    status_code=status.HTTP_200_OK,
)
async def get_event_stats(
    event_id: int, organizer: UserOut = Depends(require_organizer)
):
    """Get statistics for a specific event."""
    return await event_organizer_services.get_event_stats_service(event_id)


@router.get(
    "/organizers/me/events/{event_id}/details",
    response_model=EventDetails,
    status_code=status.HTTP_200_OK,
)
async def get_event_details(
    event_id: int, organizer: UserOut = Depends(require_organizer)
):
    """
    Get complete event details: event info, stats, ticket types,
    and the 5 most recent bookings. Single call for the EventDetails page.
    """
    return await event_organizer_services.get_event_details_service(event_id)


@router.put(
    "/organizers/me/events/{event_id}",
    response_model=OrganizerEventOut,
    status_code=status.HTTP_200_OK,
)
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    organizer: UserOut = Depends(require_organizer),
):
    """Update event details."""
    return await event_services.update_event_service(event_id, event_data)


@router.patch(
    "/organizers/me/events/{event_id}",
    response_model=bool,
    status_code=status.HTTP_200_OK,
)
async def update_event_status(
    event_id: int,
    state: str,
    organizer: UserOut = Depends(require_organizer),
):
    """
    Update event status. Organizer can cancel or mark deleted.
    Guards against acting on an already-deleted event.
    """
    event = await event_services.get_event_by_id_service(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found."
        )
    if event.status == "deleted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event has already been deleted.",
        )
    return await event_services.update_event_status_service(event_id, state)