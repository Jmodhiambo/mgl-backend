#!/usr/bin/env python3
"""
Events + Orders organizer routes for MGLTickets.

Route ordering rules (FastAPI matches top-to-bottom):
  Fixed literal paths MUST come before parameterised paths.
  e.g.  /organizers/me/events/by-slug/{slug}/details
        must appear BEFORE /organizers/me/events/{event_id}/details
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
from app.schemas.organizer import DashboardStats, OrganizerOrderOut
import app.services.event_services as event_services
import app.services.organizer_analytics_services as oa_services
from app.services.notification_services import notify_event_submitted
from app.core.security import require_organizer
from app.utils.generate_image_url import save_flyer_and_get_url
from app.utils.generate_slug import generate_unique_slug


router = APIRouter()


# ── Fixed paths ───────────────────────────────────────────────────────────────
# All literal-segment routes must appear BEFORE any /{event_id} routes.

@router.get(
    "/organizers/me/events",
    response_model=list[OrganizerEventOut],
    status_code=status.HTTP_200_OK,
)
async def get_events_by_organizer(organizer: UserOut = Depends(require_organizer)):
    """All events for the current organizer with stats + commission breakdown."""
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
    """Top events by confirmed revenue for the organizer dashboard widget."""
    return await event_services.get_top_events_by_organizer_service(organizer.id, limit)


@router.get(
    "/organizers/me/stats",
    response_model=DashboardStats,
    status_code=status.HTTP_200_OK,
)
async def get_organizer_dashboard_stats(organizer: UserOut = Depends(require_organizer)):
    """
    KPI cards for the organizer dashboard.
    Returns event counts, booking totals, and the full revenue split
    (gross / platform_cut / organizer_net) across all confirmed bookings.
    """
    return await oa_services.get_dashboard_stats_service(organizer.id)


@router.get(
    "/organizers/me/orders",
    response_model=list[OrganizerOrderOut],
    status_code=status.HTTP_200_OK,
)
async def get_organizer_orders(organizer: UserOut = Depends(require_organizer)):
    """
    All orders for the current organizer's events, newest first.
    Each order contains its nested booking line items and commission breakdown.
    Used by the BookingsView — Orders tab.
    """
    return await oa_services.list_orders_by_organizer_service(organizer.id)


@router.get(
    "/organizers/me/orders/recent",
    response_model=list[OrganizerOrderOut],
    status_code=status.HTTP_200_OK,
)
async def get_recent_organizer_orders(
    limit: int = 10,
    organizer: UserOut = Depends(require_organizer),
):
    """
    Most recent N orders for the dashboard activity widget.
    IMPORTANT: this route must stay above /organizers/me/orders/{order_id}
    so FastAPI does not try to cast 'recent' as an integer.
    """
    return await oa_services.get_recent_orders_by_organizer_service(organizer.id, limit)


# ── Slug-based event detail ───────────────────────────────────────────────────
# Must appear BEFORE /{event_id} routes.

@router.get(
    "/organizers/me/events/by-slug/{slug}/details",
    response_model=EventDetails,
    status_code=status.HTTP_200_OK,
)
async def get_event_details_by_slug(
    slug: str,
    organizer: UserOut = Depends(require_organizer),
):
    """
    Full event detail bundle (event + stats + ticket types + recent bookings)
    looked up by slug.

    Preferred over the numeric-ID variant for the organizer portal because:
      - Slugs are URL-safe and human-readable in the browser.
      - The frontend never needs to separately resolve a slug → ID.
    """
    return await event_services.get_event_details_by_slug_service(slug)


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
    Create a new event (multipart/form-data).
    The commission_rate is injected by the service layer from platform settings —
    the client never sends it.
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
        # commission_rate and commission_source will be overwritten
        # by create_event_service from live platform settings
    )
    event = await event_services.create_event_service(event_with_flyer)

    background_tasks.add_task(
        notify_event_submitted, event.id, event.title, event.slug, organizer.name
    )
    return event


# ── Parameterised routes — AFTER all fixed paths ──────────────────────────────

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
    Full event detail bundle by numeric ID.
    Kept for backwards-compatibility. Prefer the slug variant for new work.
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
    """Update event status (cancel / delete)."""
    event = await event_services.update_event_status_service(event_id, state)
    return True if event.status == "cancelled" else False