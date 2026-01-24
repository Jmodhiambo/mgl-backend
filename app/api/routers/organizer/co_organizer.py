#!/usr/bin/env python3
"""Favorite routes for MGLTickets."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.user import UserOut
from app.schemas.co_organizer import CoOrganizerOut
import app.services.co_organizer_services as co_services
import app.services.user_services as user_services
from app.core.security import require_organizer

router = APIRouter()


@router.post("/organizers/me/events/{event_id}/co-organizers/{email}", response_model=CoOrganizerOut, status_code=status.HTTP_201_CREATED)
async def create_co_organizer(email: str, event_id: int, organizer=Depends(require_organizer)):
    """Create a new co-organizer."""
    invited_by = organizer.id
    organizer_id = organizer.id
    return await co_services.create_co_organizer_service(email, organizer_id, event_id, invited_by)

@router.patch("/organizers/me/co-organizers/{co_organizer_id}", status_code=status.HTTP_200_OK)
async def update_create_co_organizer_status(co_organizer_id: int, create_co_organizer: bool, organizer=Depends(require_organizer)):
    """Update the create_co_organizer status of a co-organizer."""
    co_organizer = await co_services.get_co_organizer_by_id_service(co_organizer_id)

    # Only the user that invited the co-organizer can update the status
    if co_organizer.invited_by != organizer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to update this co-organizer.")

    return await co_services.update_create_co_organizer_status_service(co_organizer_id, create_co_organizer)


@router.get("/organizers/me/co-organizers", response_model=list[UserOut], status_code=status.HTTP_200_OK)
async def get_all_co_organizers(event_id: int, organizer=Depends(require_organizer)):
    """List all co-organizers (User access only)."""
    co_organizers = await co_services.get_all_event_co_organizers_service(event_id)
    return [await user_services.get_user_by_id_service(co_organizer.user_id) for co_organizer in co_organizers]


@router.delete("/organizers/me/co-organizers/{co_organizer_id}", response_model=bool, status_code=status.HTTP_200_OK)
async def delete_co_organizer(co_organizer_id: int, organizer=Depends(require_organizer)):
    """Delete a co-organizer from the database."""
    co_organizer = await co_services.get_co_organizer_by_id_service(co_organizer_id)

    # Only the user that invited the co-organizer can delete the co-organizer
    if co_organizer.invited_by != organizer.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to delete this co-organizer.")
    return await co_services.delete_co_organizer_service(co_organizer_id)