#!/usr/bin/env python3
"""Events admin routes for MGLTickets."""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, BackgroundTasks
from typing import Optional
from datetime import datetime

from app.schemas.event import EventOut, AdminEventOut, EventCreateWithFlyer
import app.services.event_services as event_services
import app.services.user_services as user_services
from app.services.notification_services import (
    notify_event_submitted,
    notify_event_approved,
    notify_event_rejected,
    notify_event_cancelled,
)
from app.services.audit_log_services import log_admin_action_service
from app.core.security import require_admin
from app.utils.generate_image_url import save_flyer_and_get_url
from app.utils.generate_slug import generate_unique_slug


router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# WHY Form() instead of Body() / Pydantic model here?
#
# The endpoint accepts a file upload (multipart/form-data).  FastAPI cannot
# parse a JSON body *and* a multipart form in the same request — mixing
# Body()/Pydantic with File() silently drops the Pydantic model, producing a
# 422 "field required" error for every EventCreate field.
#
# Solution: declare every field individually with Form().  The frontend
# already sends them this way (FormData.append per field), so no client
# changes are needed.
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/admin/events", response_model=AdminEventOut)
async def create_event(
    background_tasks: BackgroundTasks,
    # ── File ──────────────────────────────────────────────────────────────────
    flyer: UploadFile = File(...),
    # ── EventCreate fields (all Form, not Body) ───────────────────────────────
    title: str                    = Form(...),
    venue: str                    = Form(...),
    city: str                     = Form(...),
    country: str                  = Form(...),
    category: str                 = Form(...),
    start_time: datetime          = Form(...),
    end_time: datetime            = Form(...),
    description: Optional[str]   = Form(None),
    # ── Admin-only extra ──────────────────────────────────────────────────────
    organizer_id: Optional[int]  = Form(None, description="Admin can specify the organizer id"),
    user=Depends(require_admin),
):
    """
    Create a new event on behalf of an organizer.

    Accepts multipart/form-data — all event fields must be sent as form
    fields alongside the flyer file.  organizer_id is optional; if omitted
    the event is attributed to the calling admin.
    """
    # Resolve the organizer
    target_organizer_id = organizer_id if organizer_id else user.id
    organizer = await user_services.get_user_by_id_service(target_organizer_id)
    if not organizer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organizer with ID {target_organizer_id} not found.",
        )

    # Generate slug + save flyer
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
        organizer_id=target_organizer_id,
    )

    event = await event_services.create_event_service(event_with_flyer)

    # Notify organizer about event submission
    background_tasks.add_task(
        notify_event_submitted,
        event.id, event.title, event.slug, organizer.name, user.name,
    )

    # Audit log
    background_tasks.add_task(
        log_admin_action_service,
        admin_id=user.id,
        admin_name=user.name,
        action="create_event",
        target_type="event",
        target_id=event.id,
        details={"event_title": event.title, "status": "created"},
    )

    return event


@router.get("/admin/events", response_model=list[AdminEventOut])
async def get_all_approved_events(user=Depends(require_admin)):
    """Get all approved events."""
    return await event_services.get_approved_events_service()


@router.get("/admin/events/approved", response_model=list[AdminEventOut])
async def get_approved_events(user=Depends(require_admin)):
    """Get all approved events."""
    return await event_services.get_approved_events_service()


@router.get("/admin/events/unapproved", response_model=list[AdminEventOut])
async def get_all_unapproved_events(user=Depends(require_admin)):
    """Get all unapproved events."""
    return await event_services.get_unapproved_events_service()


@router.get("/admin/all-events", response_model=list[AdminEventOut])
async def get_all_events(user=Depends(require_admin)):
    """Get all events (approved and unapproved)."""
    return await event_services.get_all_events_service()


@router.get("/admin/events/slug/{slug}", response_model=AdminEventOut)
async def get_event_by_slug(slug: str, user=Depends(require_admin)):
    """Get an event by its slug."""
    return await event_services.get_event_by_slug_admin_service(slug)


# ── Fixed-path advanced queries (MUST come before /{event_id}) ───────────────

@router.get("/admin/events/with-bookings", response_model=list[EventOut])
async def get_events_with_bookings(user=Depends(require_admin)):
    """Get all events that have bookings."""
    return await event_services.get_events_with_bookings_service()


@router.get("/admin/events/without-bookings", response_model=list[EventOut])
async def get_events_without_bookings(user=Depends(require_admin)):
    """Get all events without any bookings."""
    return await event_services.get_events_without_bookings_service()


@router.get("/admin/events/by-status/{status}", response_model=list[EventOut])
async def get_events_by_status(status: str, user=Depends(require_admin)):
    """Get events by their status."""
    return await event_services.get_events_by_status_service(status)


@router.get("/admin/events/organizer/{organizer_id}", response_model=list[AdminEventOut])
async def get_events_by_organizer(organizer_id: int, user=Depends(require_admin)):
    """Get events by a specific organizer."""
    return await event_services.get_events_by_organizer_admin_service(organizer_id)


@router.get("/admin/events/organizer/{organizer_id}/count", response_model=int)
async def count_events_by_organizer(organizer_id: int, user=Depends(require_admin)):
    """Get the total number of events for a specific organizer."""
    return await event_services.count_events_by_organizer_service(organizer_id)


@router.get("/admin/events/date-range/{start_date}/{end_date}", response_model=list[EventOut])
async def get_events_in_date_range(
    start_date: datetime, end_date: datetime, user=Depends(require_admin)
):
    """Get all events within a specific date range."""
    return await event_services.get_events_in_date_range_service(start_date, end_date)


@router.get("/admin/events/created-after/{date}", response_model=list[EventOut])
async def get_events_created_after(date: datetime, user=Depends(require_admin)):
    """Get events created after a specific date."""
    return await event_services.get_events_created_after_service(date)


@router.get("/admin/events/created-before/{date}", response_model=list[EventOut])
async def get_events_created_before(date: datetime, user=Depends(require_admin)):
    """Get events created before a specific date."""
    return await event_services.get_events_created_before_service(date)


@router.get("/admin/events/updated-after/{date}", response_model=list[EventOut])
async def get_events_updated_after(date: datetime, user=Depends(require_admin)):
    """Get events updated after a specific date."""
    return await event_services.get_events_updated_after_service(date)


@router.get("/admin/events/updated-before/{date}", response_model=list[EventOut])
async def get_events_updated_before(date: datetime, user=Depends(require_admin)):
    """Get events updated before a specific date."""
    return await event_services.get_events_updated_before_service(date)


# ── Parameterised routes (/{event_id}) — AFTER all fixed paths ───────────────

@router.get("/admin/events/{event_id}", response_model=AdminEventOut)
async def get_event_by_id(event_id: int, user=Depends(require_admin)):
    """Get an event by its ID."""
    return await event_services.get_event_by_id_admin_service(event_id)


@router.patch("/admin/events/{event_id}/approve", response_model=bool)
async def approve_event(
    event_id: int, background_tasks: BackgroundTasks, user=Depends(require_admin)
):
    """Approve an event by its ID."""
    event = await event_services.approve_event_service(event_id)

    background_tasks.add_task(
        notify_event_approved, event.id, event.title, event.slug, user.name, event.organizer_id
    )
    background_tasks.add_task(
        log_admin_action_service,
        admin_id=user.id,
        admin_name=user.name,
        action=f"Approved an event: {event.title}",
        target_type="event",
        target_id=event.id,
        details={"approved_event": event.title},
    )
    return True if event else False


@router.patch("/admin/events/{event_id}/reject", response_model=bool)
async def reject_event(
    event_id: int, background_tasks: BackgroundTasks, user=Depends(require_admin)
):
    """Reject an event by its ID."""
    event = await event_services.reject_event_service(event_id)

    background_tasks.add_task(
        notify_event_rejected,
        event.id, event.title, event.slug, user.name, event.organizer_id,
        reason="Your event did not meet our guidelines. Please review and resubmit.",
    )
    background_tasks.add_task(
        log_admin_action_service,
        admin_id=user.id,
        admin_name=user.name,
        action=f"Rejected an event: {event.title}",
        target_type="event",
        target_id=event.id,
        details={"rejected_event": event.title},
    )
    return True if event else False


@router.patch("/admin/events/{event_id}/status/{status}", response_model=bool)
async def update_event_status(
    event_id: int, status: str, background_tasks: BackgroundTasks, user=Depends(require_admin)
):
    """Update the status of an event by its ID."""
    event = await event_services.update_event_status_service(event_id, status)

    if status.lower() == "cancelled":
        background_tasks.add_task(
            notify_event_cancelled, event.id, event.title, role="admin", name=user.name
        )
    background_tasks.add_task(
        log_admin_action_service,
        admin_id=user.id,
        admin_name=user.name,
        action=f"Updated an event's status: {event.title}",
        target_type="event",
        target_id=event.id,
        details={"updated_event": event.title, "status": status},
    )
    return True if event else False


@router.delete("/admin/events/{event_id}", response_model=bool)
async def delete_event(
    event_id: int, background_tasks: BackgroundTasks, user=Depends(require_admin)
):
    """Delete an event by its ID."""
    event = await event_services.delete_event_service(event_id)

    if event:
        background_tasks.add_task(
            log_admin_action_service,
            admin_id=user.id,
            admin_name=user.name,
            action=f"Deleted an event: {event.title}",
            target_type="event",
            target_id=event_id,
            details={"deleted_event": event_id},
        )
    return True if event else False