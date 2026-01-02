#!/usr/bin/env python3
"""Favorite routes for MGLTickets."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.event import EventOut
from app.schemas.user import UserOut
from app.schemas.co_organizer import CoOrganizerOut
import app.services.co_organizer_services as co_services
import app.services.user_services as user_services
from app.services.event_services import get_event_by_id_service
from app.core.security import require_user

router = APIRouter()


@router.post("/users/me/co-organizers", response_model=CoOrganizerOut, status_code=status.HTTP_201_CREATED)
async def create_co_organizer(user_id: int, event_id: int, user=Depends(require_user)):
    """Create a new co-organizer."""
    # Get the event to have access to the organizer
    event = await get_event_by_id_service(event_id)
    organizer = event.organizer_id
    return await co_services.create_co_organizer_service(user_id, organizer, event_id)


@router.get("/users/me/co-organizers", response_model=list[UserOut], status_code=status.HTTP_200_OK)
async def get_all_co_organizers(event_id: int, user=Depends(require_user)):
    """List all co-organizers (User access only)."""
    co_organizers = await co_services.get_all_event_co_organizers_service(event_id)
    return [await user_services.get_user_by_id_service(co_organizer.user_id) for co_organizer in co_organizers]


