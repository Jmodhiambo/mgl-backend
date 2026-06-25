#!/usr/bin/env python3
"""Co-organizer admin routes for MGLTickets."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from app.schemas.co_organizer import CoOrganizerOut, CoOrganizerWithUserAndEvent, CoOrganizerWithEvent
import app.services.co_organizer_services as co_services
from app.services.event_services import get_event_by_id_service
from app.core.security import require_admin
from app.services.audit_log_services import log_admin_action_service

router = APIRouter()


@router.post(
    "/admin/me/co-organizers",
    response_model=CoOrganizerOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_co_organizer(
    email: str,
    event_id: int,
    background_tasks: BackgroundTasks,
    admin=Depends(require_admin),
):
    """
    Add a co-organizer to any event by email address.
    invited_by is set to the acting admin's ID.
    """
    event = await get_event_by_id_service(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")

    result = await co_services.create_co_organizer_service(
        email=email,
        organizer_id=event.organizer_id,
        event_id=event_id,
        invited_by=admin.id,
    )
    background_tasks.add_task(
        log_admin_action_service,
        admin_id=admin.id,
        admin_name=admin.name,
        action="create_co_organizer",
        target_type="co_organizer",
        target_id=result.id,
        details={"email": email, "event_id": event_id},
    )
    return result


@router.patch(
    "/admin/me/co-organizers/{co_organizer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_create_co_organizer_status(
    co_organizer_id: int,
    create_co_organizer: bool,
    background_tasks: BackgroundTasks,
    admin=Depends(require_admin),
):
    """Grant or revoke the delegated-invite privilege for a co-organizer."""
    await co_services.update_create_co_organizer_status_service(co_organizer_id, create_co_organizer)
    background_tasks.add_task(
        log_admin_action_service,
        admin_id=admin.id,
        admin_name=admin.name,
        action="update_create_co_organizer_status",
        target_type="co_organizer",
        target_id=co_organizer_id,
        details={"create_co_organizer": create_co_organizer},
    )


@router.get(
    "/admin/me/co-organizers",
    response_model=list[CoOrganizerWithUserAndEvent],
    status_code=status.HTTP_200_OK,
)
async def get_co_organizers_for_event(event_id: int, admin=Depends(require_admin)):
    """
    List all co-organizers for any event (no ownership filter — admin view).
    Returns enriched rows; one query, no N+1 lookups.
    """
    return await co_services.get_all_event_co_organizers_service(event_id)


@router.get(
    "/admin/me/events/co-organizing",
    response_model=list[CoOrganizerWithEvent],
    status_code=status.HTTP_200_OK,
)
async def get_user_co_organizing_events(user_id: int, admin=Depends(require_admin)):
    """
    List all events a user is co-organising, bundled with relationship metadata.
    Returns CoOrganizerWithEvent (full EventOut per row) — same shape as
    the user-facing endpoint, so the admin gets identical event card data.
    """
    return await co_services.get_user_co_organizing_events_service(user_id)


@router.delete(
    "/admin/me/co-organizers/{co_organizer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_co_organizer(
    co_organizer_id: int,
    background_tasks: BackgroundTasks,
    admin=Depends(require_admin),
):
    """Remove a co-organizer record."""
    await co_services.delete_co_organizer_service(co_organizer_id)
    background_tasks.add_task(
        log_admin_action_service,
        admin_id=admin.id,
        admin_name=admin.name,
        action="delete_co_organizer",
        target_type="co_organizer",
        target_id=co_organizer_id,
        details={"deleted_co_organizer_id": co_organizer_id},
    )