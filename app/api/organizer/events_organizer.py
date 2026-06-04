#!/usr/bin/env python3
"""
Events organizer routes for MGLTickets.
"""

from fastapi import (
    APIRouter, Depends, UploadFile, File, Form,
    HTTPException, status, BackgroundTasks,
)
from datetime import datetime
from typing import Optional

from app.schemas.user import UserOut
from app.schemas.event import (
    OrganizerEventOut,
    EventCreateWithFlyer,
    EventDetails,
    TopEvent,
    EventUpdate,
)
import app.services.event_services as event_services
from app.services.notification_services import notify_event_submitted
from app.core.security import require_organizer
from app.utils.generate_image_url import save_flyer_and_get_url
from app.utils.generate_slug import generate_unique_slug


router = APIRouter()


# ── Fixed paths (before any /{event_id} routes) ───────────────────────────────

@router.get(
    "/organizers/me/events",
    response_model=list[OrganizerEventOut],
    status_code=status.HTTP_200_OK,
)
async def get_events_by_organizer(organizer: UserOut = Depends(require_organizer)):
    """
    Get all events for the current organizer.
    Returns OrganizerEventOut which already includes total_bookings and
    total_revenue — no separate stats call needed on the list page.
    """
    return await event_services.get_events_by_organizer_service(organizer.id)


@router.get(
    "/organizers/me/top-events",
    response_model=list[TopEvent],
    status_code=status.HTTP_200_OK,
)
async def get_top_events(
    limit: int = 5,
    organizer: UserOut = Depends(require_organizer),
):
    """Top events for the organizer dashboard widget, ordered by revenue."""
    return await event_services.get_top_events_by_organizer_service(organizer.id, limit)


# ── Create ────────────────────────────────────────────────────────────────────

@router.post(
    "/organizers/me/events",
    response_model=OrganizerEventOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_event(
    background_tasks: BackgroundTasks,
    flyer: UploadFile = File(...),
    title: str               = Form(...),
    venue: str               = Form(...),
    city: str                = Form(...),
    country: str             = Form(...),
    category: str            = Form(...),
    start_time: datetime     = Form(...),
    end_time: datetime       = Form(...),
    description: Optional[str] = Form(None),
    organizer: UserOut = Depends(require_organizer),
):
    """
    Create a new event.
    All fields are sent as multipart/form-data alongside the flyer file.
    Returns OrganizerEventOut (re-fetched after insert to include stats).
    """
    slug      = await generate_unique_slug(title)
    flyer_url = await save_flyer_and_get_url(flyer)

    event_with_flyer = EventCreateWithFlyer(
        title=title,
        description=description,
        venue=venue,
        city=city,
        country=country,
        category=category,
        start_time=start_time,
        end_time=end_time,
        slug=slug,
        original_filename=flyer.filename,
        flyer_url=flyer_url,
        organizer_id=organizer.id,
    )
    event = await event_services.create_event_service(event_with_flyer)

    background_tasks.add_task(
        notify_event_submitted, event.id, event.title, event.slug, organizer.name
    )
    return event


# ── Parameterised routes (/{event_id}) — AFTER all fixed paths ───────────────

@router.get(
    "/organizers/me/events/{event_id}/details",
    response_model=EventDetails,
    status_code=status.HTTP_200_OK,
)
async def get_event_details(
    event_id: int,
    organizer: UserOut = Depends(require_organizer),
):
    """
    Full event detail bundle for the EventDetails page.
    Returns: event (OrganizerEventOut) + stats + ticket_types + recent_bookings.
    Single endpoint — no need for separate stats or ticket-type calls.

    Note: the /stats endpoint has been removed. Stats (total_bookings,
    total_revenue) are available on OrganizerEventOut from the list endpoint,
    and the full breakdown (tickets_sold, tickets_remaining) is included here
    inside EventDetails.stats. The only place a standalone stats endpoint is
    useful is the user/co-organizer app.
    """
    return await event_services.get_event_details_service(event_id)


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
    """Update event details. Returns updated OrganizerEventOut."""
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
    Update event status (cancel / delete).
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