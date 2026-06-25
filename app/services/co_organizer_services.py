#!/usr/bin/env python3
"""Service layer for the CoOrganizer model in MGLTickets."""

from fastapi import HTTPException, status
from typing import Optional

import app.db.repositories.co_organizer_repo as co_repo
from app.schemas.co_organizer import CoOrganizerOut, CoOrganizerWithUserAndEvent, CoOrganizerWithEvent
from app.db.repositories.user_repo import get_user_by_email_repo
from app.core.logging_config import logger


# ── Write operations ──────────────────────────────────────────────────────────

async def create_co_organizer_service(
    email: str, organizer_id: int, event_id: int, invited_by: int
) -> CoOrganizerOut:
    """Validate and create a new co-organizer record."""
    user = await get_user_by_email_repo(email=email)
    if not user:
        logger.info(f"Co-organizer invite: user {email} not found")
        # TODO: send_co_organizer_invitation_email_to_non_existing_user(email)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if await co_repo.check_if_co_organizer_repo(user_id=user.id, event_id=event_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a co-organizer for this event.",
        )

    logger.info(f"Creating co-organizer: email={email}, organizer_id={organizer_id}, event_id={event_id}")
    result = await co_repo.create_co_organizer_repo(
        user_id=user.id,
        organizer_id=organizer_id,
        event_id=event_id,
        invited_by=invited_by,
    )
    # TODO: send_co_organizer_invitation_email_to_existing_user(email, invited_by)
    return result


async def update_create_co_organizer_status_service(
    co_organizer_id: int, create_co_organizer: bool
) -> None:
    """Grant or revoke the delegated-invite privilege for a co-organizer."""
    logger.info(f"Setting create_co_organizer={create_co_organizer} on record {co_organizer_id}")
    await co_repo.update_create_co_organizer_status_repo(
        co_organizer_id=co_organizer_id,
        create_co_organizer=create_co_organizer,
    )


async def delete_co_organizer_service(co_organizer_id: int) -> None:
    """Delete a co-organizer record."""
    logger.info(f"Deleting co-organizer {co_organizer_id}")
    await co_repo.delete_co_organizer_repo(co_organizer_id=co_organizer_id)


# ── Read — auth helper ────────────────────────────────────────────────────────

async def get_co_organizer_by_id_service(co_organizer_id: int) -> CoOrganizerOut:
    """
    Fetch a bare co-organizer record by PK.
    Used exclusively for ownership/auth checks in PATCH and DELETE handlers
    before the actual operation is performed.
    """
    logger.info(f"Fetching co-organizer record {co_organizer_id} for auth check")
    record = await co_repo.get_co_organizer_by_id_repo(co_organizer_id=co_organizer_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Co-organizer not found.")
    return record


# ── Read — enriched lists ─────────────────────────────────────────────────────
#
# All three functions below delegate to the same repo function
# (get_co_organizers_with_details_repo) with different filter arguments.
# The repo handles the JOIN in one query regardless of which args are provided.

async def get_all_co_organizers_service(
    organizer_id: int,
) -> list[CoOrganizerWithUserAndEvent]:
    """
    All co-organizers across every event owned by this organizer.
    Used by GET /organizers/me/co-organizers ("All Events" view).
    """
    logger.info(f"Listing all co-organizers for organizer {organizer_id}")
    return await co_repo.get_co_organizers_with_details_repo(organizer_id=organizer_id)


async def get_co_organizers_for_event_service(
    organizer_id: int, event_id: int
) -> list[CoOrganizerWithUserAndEvent]:
    """
    Co-organizers for one event, scoped to the requesting organizer.
    Used by GET /organizers/me/co-organizers/event/{event_id}.
    """
    logger.info(f"Listing co-organizers for organizer {organizer_id}, event {event_id}")
    return await co_repo.get_co_organizers_with_details_repo(
        organizer_id=organizer_id, event_id=event_id
    )


async def get_all_event_co_organizers_service(
    event_id: int,
) -> list[CoOrganizerWithUserAndEvent]:
    """
    All co-organizers for any event — no organizer ownership filter.
    Admin-only; access control is enforced by require_admin at the router.
    Used by GET /admin/me/co-organizers?event_id=X.
    """
    logger.info(f"Admin: listing co-organizers for event {event_id}")
    return await co_repo.get_co_organizers_with_details_repo(event_id=event_id)


# ── Read — user's co-organising events ───────────────────────────────────────

async def get_user_co_organizing_events_service(
    user_id: int,
) -> list[CoOrganizerWithEvent]:
    """
    All events a user is co-organising, each bundled with the full EventOut
    and the co-organizer relationship metadata.

    Returns CoOrganizerWithEvent (not CoOrganizerWithUserAndEvent) because
    the shape is fundamentally different: the caller IS the user, so user
    fields are irrelevant — what they need is the full event details (dates,
    venue, image) to render event cards on My Events. The repo handles the
    JOIN and eliminates the previous N+1 loop.

    Used by GET /users/me/events/co-organizing.
    """
    logger.info(f"Listing co-organising events for user {user_id}")
    return await co_repo.get_user_co_organizing_events_with_details_repo(user_id=user_id)