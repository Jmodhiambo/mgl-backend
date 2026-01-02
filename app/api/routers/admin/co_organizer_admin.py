#!/usr/bin/env python3
"""Favorite routes for MGLTickets."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.event import EventOut
from app.schemas.user import UserOut
from app.schemas.co_organizer import CoOrganizerOut
import app.services.co_organizer_services as co_services
import app.services.user_services as user_services
from app.services.event_services import get_event_by_id_service
from app.core.security import require_admin

router = APIRouter()


@router.post("/admin/me/co-organizers", response_model=CoOrganizerOut, status_code=status.HTTP_201_CREATED)
async def create_co_organizer(user_id: int, event_id: int, invited_by: int, admin=Depends(require_admin)):
    """Create a new co-organizer."""
    # Get the event to have access to the organizer
    event = await get_event_by_id_service(event_id)
    organizer = event.organizer_id
    return await co_services.create_co_organizer_service(user_id, organizer, event_id, invited_by)

@router.patch("/admin/me/co-organizers/{co_organizer_id}", status_code=status.HTTP_200_OK)
async def update_create_co_organizer_status(co_organizer_id: int, create_co_organizer: bool, admin=Depends(require_admin)):
    """Update the create_co_organizer status of a co-organizer."""
    co_organizer = await co_services.get_co_organizer_by_id_service(co_organizer_id)
    return await co_services.update_create_co_organizer_status_service(co_organizer_id, create_co_organizer)


@router.get("/admin/me/co-organizers", response_model=list[UserOut], status_code=status.HTTP_200_OK)
async def get_all_co_organizers(event_id: int, admin=Depends(require_admin)):
    """List all co-organizers (User access only)."""
    co_organizers = await co_services.get_all_event_co_organizers_service(event_id)
    return [await user_services.get_user_by_id_service(co_organizer.user_id) for co_organizer in co_organizers]


@router.get("/admin/me/events/co-organizing", response_model=list[EventOut], status_code=status.HTTP_200_OK)
async def get_user_co_organizing_events(user_id: int, admin=Depends(require_admin)):
    """List all events that a user is co-organizing."""
    co_organizing = await co_services.get_user_co_organizing_events_service(user_id)

    return [await get_event_by_id_service(co_organizer.event_id) for co_organizer in co_organizing]


@router.delete("/admin/me/co-organizers/{co_organizer_id}", response_model=bool, status_code=status.HTTP_200_OK)
async def delete_co_organizer(co_organizer_id: int, admin=Depends(require_admin)):
    """Delete a co-organizer from the database."""
    return await co_services.delete_co_organizer_service(co_organizer_id)