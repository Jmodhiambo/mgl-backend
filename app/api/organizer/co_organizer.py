#!/usr/bin/env python3
"""Co-organizer routes for the organizer app."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.schemas.co_organizer import CoOrganizerOut, CoOrganizerWithUserAndEvent, CoOrganizerWithEvent
from app.schemas.pagination import PaginatedResponse
import app.services.co_organizer_services as co_services
from app.core.security import require_organizer

router = APIRouter()


@router.post(
    "/organizers/me/events/{event_id}/co-organizers/{email}",
    response_model=CoOrganizerOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_co_organizer(event_id: int, email: str, organizer=Depends(require_organizer)):
    """Invite a user by email to co-organise a specific event."""
    return await co_services.create_co_organizer_service(
        email=email,
        organizer_id=organizer.id,
        event_id=event_id,
        invited_by=organizer.id,
    )


@router.patch(
    "/organizers/me/co-organizers/{co_organizer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_create_co_organizer_status(
    co_organizer_id: int,
    create_co_organizer: bool,
    organizer=Depends(require_organizer),
):
    """Grant or revoke the delegated-invite privilege. Only the original inviter may do this."""
    record = await co_services.get_co_organizer_by_id_service(co_organizer_id)
    if record.invited_by != organizer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorised to update this co-organizer.",
        )
    await co_services.update_create_co_organizer_status_service(co_organizer_id, create_co_organizer)


@router.get(
    "/organizers/me/co-organizers",
    response_model=PaginatedResponse[CoOrganizerWithUserAndEvent],
    status_code=status.HTTP_200_OK,
)
async def get_all_co_organizers(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    organizer=Depends(require_organizer),
):
    """
    List co-organizers across ALL of the current organizer's events, paginated.
    One row per co-organizer/event pair — a user co-organising two events
    appears twice, matching the frontend table's event-name column.
    """
    return await co_services.get_all_co_organizers_service(
        organizer.id, limit=limit, offset=offset
    )


@router.get(
    "/organizers/me/co-organizers/event/{event_id}",
    response_model=PaginatedResponse[CoOrganizerWithUserAndEvent],
    status_code=status.HTTP_200_OK,
)
async def get_co_organizers_for_event(
    event_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    organizer=Depends(require_organizer),
):
    """
    List co-organizers for a single event owned by the current organizer, paginated.
    Path uses /event/{event_id} to avoid ambiguity with /{co_organizer_id}.
    """
    return await co_services.get_co_organizers_for_event_service(
        organizer.id, event_id, limit=limit, offset=offset
    )


@router.delete(
    "/organizers/me/co-organizers/{co_organizer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_co_organizer(co_organizer_id: int, organizer=Depends(require_organizer)):
    """Remove a co-organizer. Only the original inviter or the event organizer can do this."""
    record = await co_services.get_co_organizer_by_id_service(co_organizer_id)
    if record.organizer_id != organizer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorised to remove this co-organizer.",
        )
    await co_services.delete_co_organizer_service(co_organizer_id)