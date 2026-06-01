#!/usr/bin/env python3
"""Service layer for the CoOrganizer model in MGLTickets."""

from fastapi import HTTPException, status
import app.db.repositories.co_organizer_repo as co_repo
from app.schemas.co_organizer import CoOrganizerOut, CoOrganizerWithEvent
from app.schemas.event import EventOut
from typing import Optional
from app.db.repositories.user_repo import get_user_by_email_repo
from app.services.event_services import get_event_by_id_service
from app.core.logging_config import logger


async def create_co_organizer_service(
    email: str, organizer_id: int, event_id: int, invited_by: int
) -> CoOrganizerOut:
    """Create a new event co-organizer in the database."""
    user = await get_user_by_email_repo(email=email)

    if not user:
        logger.info(f"User with email {email} not found. Sending invitation email…")
        # TODO: send_co_organizer_invitation_email_to_non_existing_user(...)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if await co_repo.check_if_co_organizer_repo(user_id=user.id, event_id=event_id):
        logger.info(f"User {email} is already a co-organizer for event {event_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a co-organizer for this event"
        )

    logger.info(
        f"Creating co-organizer: email={email}, organizer_id={organizer_id}, event_id={event_id}"
    )
    result = await co_repo.create_co_organizer_repo(
        user_id=user.id,
        organizer_id=organizer_id,
        event_id=event_id,
        invited_by=invited_by,
    )
    if result:
        # TODO: send_co_organizer_invitation_email_to_existing_user(email, invited_by)
        pass
    return result


async def get_co_organizer_by_id_service(co_organizer_id: int) -> Optional[CoOrganizerOut]:
    """Get a co-organizer record by its own ID."""
    logger.info(f"Getting co-organizer {co_organizer_id}")
    return await co_repo.get_co_organizer_by_id_repo(co_organizer_id=co_organizer_id)


async def update_create_co_organizer_status_service(
    co_organizer_id: int, create_co_organizer: bool
) -> None:
    """
    Grant or revoke the delegated-invite privilege for a co-organizer.
    Only the original inviter (organizer) should call this.
    """
    logger.info(
        f"Updating create_co_organizer={create_co_organizer} for co_organizer {co_organizer_id}"
    )
    return await co_repo.update_create_co_organizer_status_repo(
        co_organizer_id=co_organizer_id,
        create_co_organizer=create_co_organizer,
    )


async def get_all_event_co_organizers_service(event_id: int) -> Optional[list[CoOrganizerOut]]:
    """Get all co-organizer records for a given event."""
    logger.info(f"Getting all co-organizers for event {event_id}")
    return await co_repo.get_all_event_co_organizers_repo(event_id=event_id)


async def get_user_co_organizing_events_service(user_id: int) -> Optional[list[CoOrganizerOut]]:
    """Get all CoOrganizer records for a given user (bare records, no event data)."""
    logger.info(f"Getting co-organizer records for user {user_id}")
    return await co_repo.get_user_co_organizing_events_repo(user_id=user_id)


async def get_user_co_organizing_events_with_details_service(
    user_id: int,
) -> list[CoOrganizerWithEvent]:
    """
    Return enriched CoOrganizerWithEvent objects for every event the user
    is co-organizing.  This bundles the full EventOut alongside the co-organizer
    relationship metadata so the frontend can render everything in one call.
    """
    logger.info(f"Getting co-organizing events with details for user {user_id}")
    co_records = await co_repo.get_user_co_organizing_events_repo(user_id=user_id)

    if not co_records:
        return []

    results: list[CoOrganizerWithEvent] = []
    for record in co_records:
        event = await get_event_by_id_service(record.event_id)
        if event is None:
            # Event was deleted; skip orphaned co-organizer record
            logger.warning(
                f"Co-organizer record {record.id} references missing event {record.event_id} — skipping"
            )
            continue

        results.append(
            CoOrganizerWithEvent(
                co_organizer_id=record.id,
                invited_by=record.invited_by,
                create_co_organizer=record.create_co_organizer,
                joined_at=record.created_at,
                event=event,
            )
        )

    return results


async def delete_co_organizer_service(co_organizer_id: int) -> None:
    """Delete a co-organizer record from the database."""
    logger.info(f"Deleting co-organizer {co_organizer_id}")
    return await co_repo.delete_co_organizer_repo(co_organizer_id=co_organizer_id)