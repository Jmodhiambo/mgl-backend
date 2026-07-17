#!/usr/bin/env python3
# app/services/co_organizer_services.py
"""Service layer for the CoOrganizer model in MGLTickets."""
 
import asyncio
from typing import Optional
 
from fastapi import HTTPException, status
 
from app.core.config import FRONTEND_URL
from app.core.logging_config import logger
from app.emails.email_manager import email_manager
from app.schemas.co_organizer import CoOrganizerOut, CoOrganizerWithEvent, CoOrganizerWithUserAndEvent
import app.db.repositories.co_organizer_repo as co_repo
import app.db.repositories.event_repo as event_repo
import app.db.repositories.user_repo as user_repo
from app.db.repositories.user_repo import get_user_by_email_repo


# ── Email background helper ───────────────────────────────────────────────────
 
def _bg_email(coro) -> None:
    """
    Schedule an email coroutine as a background task.
    Falls back to direct await if no running event loop exists (tests, CLI).
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        asyncio.run(coro)
 
 
def _accept_url(event_id: int) -> str:
    return f"{FRONTEND_URL}/organizer/co-organizer/accept?event_id={event_id}"
 
 
def _signup_url(email: str, event_id: int) -> str:
    return f"{FRONTEND_URL}/register?email={email}&co_organizer_event={event_id}"
 
 
# ── Write operations ──────────────────────────────────────────────────────────
 
async def create_co_organizer_service(
    email: str, organizer_id: int, event_id: int, invited_by: int
) -> CoOrganizerOut:
    """
    Validate and create a co-organizer record.
 
    Two email paths (both dispatched in background):
    - Existing user → co_organizer_invitation (log in and accept)
    - New user      → co_organizer_invitation_new_user (sign up first, then 404 raised)
    """
    event = await event_repo.get_event_by_id_repo(event_id)
    inviter = await user_repo.get_user_by_id_repo(invited_by)
 
    event_title = event.title if event else "an event"
    venue = event.venue if event else "TBA"
    event_date = event.start_date.strftime("%d %b %Y") if event and event.start_date else "TBA"
    inviter_name = inviter.name if inviter else "An organizer"
 
    user = await get_user_by_email_repo(email=email)
 
    if not user:
        logger.info(f"Co-organizer invite: {email} not found — sending sign-up invitation")
        _bg_email(email_manager.send_from_template(
            template_id="organizer.co_organizer_invitation_new_user",
            to_email=email,
            variables={
                "recipient_name": email.split("@")[0].capitalize(),
                "inviter_name": inviter_name,
                "event_title": event_title,
                "venue": venue,
                "event_date": event_date,
                "signup_url": _signup_url(email, event_id),
            },
        ))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. An invitation to sign up has been sent to their email.",
        )
 
    if await co_repo.check_if_co_organizer_repo(user_id=user.id, event_id=event_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a co-organizer for this event.",
        )
 
    logger.info(f"Creating co-organizer: email={email}, event_id={event_id}")
    result = await co_repo.create_co_organizer_repo(
        user_id=user.id,
        organizer_id=organizer_id,
        event_id=event_id,
        invited_by=invited_by,
    )
 
    _bg_email(email_manager.send_from_template(
        template_id="organizer.co_organizer_invitation",
        to_email=user.email,
        variables={
            "recipient_name": user.name,
            "inviter_name": inviter_name,
            "event_title": event_title,
            "venue": venue,
            "event_date": event_date,
            "accept_url": _accept_url(event_id),
        },
    ))
 
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