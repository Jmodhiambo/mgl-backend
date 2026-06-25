#!/usr/bin/env python3
"""Repository for CoOrganizer model operations."""

from typing import Optional
from sqlalchemy import select, delete, update
from sqlalchemy.orm import joinedload
from app.db.session import get_async_session
from app.db.models.co_organizer import CoOrganizer
from app.schemas.co_organizer import CoOrganizerOut, CoOrganizerWithUserAndEvent, CoOrganizerWithEvent
from app.schemas.event import EventOut


# ── Simple CRUD ───────────────────────────────────────────────────────────────

async def create_co_organizer_repo(
    user_id: int, organizer_id: int, event_id: int, invited_by: int
) -> CoOrganizerOut:
    """Create a new event co-organizer record."""
    async with get_async_session() as session:
        co_organizer = CoOrganizer(
            user_id=user_id,
            organizer_id=organizer_id,
            event_id=event_id,
            invited_by=invited_by,
        )
        session.add(co_organizer)
        await session.commit()
        await session.refresh(co_organizer)
        return CoOrganizerOut.model_validate(co_organizer)


async def get_co_organizer_by_id_repo(co_organizer_id: int) -> Optional[CoOrganizerOut]:
    """Get a bare co-organizer record by PK. Used for auth checks before PATCH/DELETE."""
    async with get_async_session() as session:
        result = await session.execute(
            select(CoOrganizer).where(CoOrganizer.id == co_organizer_id)
        )
        co_organizer = result.scalars().unique().one_or_none()
        return CoOrganizerOut.model_validate(co_organizer) if co_organizer else None


async def delete_co_organizer_repo(co_organizer_id: int) -> None:
    """Hard-delete a co-organizer record."""
    async with get_async_session() as session:
        await session.execute(
            delete(CoOrganizer).where(CoOrganizer.id == co_organizer_id)
        )
        await session.commit()


async def update_create_co_organizer_status_repo(
    co_organizer_id: int, create_co_organizer: bool
) -> None:
    """Grant or revoke the delegated-invite privilege for a co-organizer."""
    async with get_async_session() as session:
        await session.execute(
            update(CoOrganizer)
            .where(CoOrganizer.id == co_organizer_id)
            .values(create_co_organizer=create_co_organizer)
        )
        await session.commit()


async def check_if_co_organizer_repo(user_id: int, event_id: int) -> bool:
    """Return True if the user is already a co-organizer for this event."""
    async with get_async_session() as session:
        result = await session.execute(
            select(CoOrganizer)
            .where(CoOrganizer.user_id == user_id)
            .where(CoOrganizer.event_id == event_id)
        )
        return result.scalars().unique().one_or_none() is not None


# ── Joined queries ────────────────────────────────────────────────────────────

async def get_co_organizers_with_details_repo(
    organizer_id: Optional[int] = None,
    event_id: Optional[int] = None,
) -> list[CoOrganizerWithUserAndEvent]:
    """
    Return enriched co-organizer rows via a single JOIN across
    CoOrganizer → User and CoOrganizer → Event.

    Calling conventions:
      • organizer_id only  → all co-organizers across that organizer's events
      • organizer_id + event_id → co-organizers for one event, ownership-scoped
      • event_id only      → admin mode: co-organizers for any event, no ownership filter

    The ownership boundary for organizer calls is enforced here by filtering on
    organizer_id; admin callers omit it and rely on require_admin at the router.

    The schema is built inside the session context so the eagerly-loaded
    related objects are still accessible after execute().
    """
    async with get_async_session() as session:
        stmt = select(CoOrganizer).options(
            joinedload(CoOrganizer.user),
            joinedload(CoOrganizer.event),
        )
        if organizer_id is not None:
            stmt = stmt.where(CoOrganizer.organizer_id == organizer_id)
        if event_id is not None:
            stmt = stmt.where(CoOrganizer.event_id == event_id)

        result = await session.execute(stmt)
        rows = result.scalars().unique().all()
        return [
            CoOrganizerWithUserAndEvent(
                id=row.id,
                event_id=row.event_id,
                event_title=row.event.title,
                invited_by=row.invited_by,
                create_co_organizer=row.create_co_organizer,
                created_at=row.created_at,
                user_id=row.user_id,
                name=row.user.name,
                email=row.user.email,
                phone_number=row.user.phone_number,
                role=row.user.role,
            )
            for row in rows
        ]


async def get_user_co_organizing_events_with_details_repo(
    user_id: int,
) -> list[CoOrganizerWithEvent]:
    """
    Return all events a user is co-organizing, each bundled with the
    co-organizer relationship metadata, via a single JOIN.

    This is the reverse of get_co_organizers_with_details_repo: instead of
    "who are my co-organizers?" it answers "what events am I co-organising?"
    The full EventOut is needed here (date, venue, image, etc.) so the
    My Events page can render event cards — which is why CoOrganizerWithEvent
    carries a nested EventOut rather than just event_title.

    Orphaned records (event deleted but co-organizer row still exists) are
    silently skipped — the joinedload returns None for row.event in that case.
    """
    async with get_async_session() as session:
        stmt = (
            select(CoOrganizer)
            .options(joinedload(CoOrganizer.event))
            .where(CoOrganizer.user_id == user_id)
        )
        result = await session.execute(stmt)
        rows = result.scalars().unique().all()

        output: list[CoOrganizerWithEvent] = []
        for row in rows:
            if row.event is None:
                continue  # event deleted, skip orphan
            output.append(
                CoOrganizerWithEvent(
                    co_organizer_id=row.id,
                    invited_by=row.invited_by,
                    create_co_organizer=row.create_co_organizer,
                    created_at=row.created_at,
                    event=EventOut.model_validate(row.event),
                )
            )
        return output