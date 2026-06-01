#!/usr/bin/env python3
"""Co-organizer routes accessible to any authenticated user in MGLTickets."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.event import EventOut
from app.schemas.user import UserOut
from app.schemas.co_organizer import CoOrganizerOut, CoOrganizerWithEvent
import app.services.co_organizer_services as co_services
import app.services.user_services as user_services
from app.services.event_services import get_event_by_id_service
from app.core.security import require_user

router = APIRouter()


@router.post(
    "/users/me/co-organizers",
    response_model=CoOrganizerOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_co_organizer(user_id: int, event_id: int, user=Depends(require_user)):
    """Add a co-organizer to an event (any authenticated user who is the inviter)."""
    event     = await get_event_by_id_service(event_id)
    organizer = event.organizer_id
    invited_by = user.id
    return await co_services.create_co_organizer_service(user_id, organizer, event_id, invited_by)


@router.patch(
    "/users/me/co-organizers/{co_organizer_id}",
    status_code=status.HTTP_200_OK,
)
async def update_create_co_organizer_status(
    co_organizer_id: int, create_co_organizer: bool, user=Depends(require_user)
):
    """Grant or revoke delegated-invite privilege. Only the original inviter may do this."""
    co_organizer = await co_services.get_co_organizer_by_id_service(co_organizer_id)
    if co_organizer.invited_by != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this co-organizer.",
        )
    return await co_services.update_create_co_organizer_status_service(
        co_organizer_id, create_co_organizer
    )


@router.get(
    "/users/me/co-organizers",
    response_model=list[UserOut],
    status_code=status.HTTP_200_OK,
)
async def get_all_co_organizers(event_id: int, user=Depends(require_user)):
    """List all co-organizers for a given event."""
    co_organizers = await co_services.get_all_event_co_organizers_service(event_id)
    return [
        await user_services.get_user_by_id_service(co.user_id)
        for co in co_organizers
    ]


@router.get(
    "/users/me/events/co-organizing",
    response_model=list[CoOrganizerWithEvent],   # ← enriched response
    status_code=status.HTTP_200_OK,
)
async def get_user_co_organizing_events(user=Depends(require_user)):
    """
    Return all events the current user is co-organizing, bundled with the
    co-organizer relationship metadata (invited_by, create_co_organizer, joined_at).

    Previously this returned list[EventOut] which lost the relationship data.
    The enriched CoOrganizerWithEvent lets the frontend show who invited this
    user and whether they can invite others, without extra round-trips.
    """
    return await co_services.get_user_co_organizing_events_with_details_service(user.id)


@router.delete(
    "/users/me/co-organizers/{co_organizer_id}",
    response_model=bool,
    status_code=status.HTTP_200_OK,
)
async def delete_co_organizer(co_organizer_id: int, user=Depends(require_user)):
    """Remove a co-organizer. Only the original inviter may do this."""
    co_organizer = await co_services.get_co_organizer_by_id_service(co_organizer_id)
    if co_organizer.invited_by != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to remove this co-organizer.",
        )
    return await co_services.delete_co_organizer_service(co_organizer_id)