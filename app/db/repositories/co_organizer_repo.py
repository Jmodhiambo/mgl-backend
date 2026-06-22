#!/usr/bin/env python3
"""Repository for CoOrganizer model operations."""

from typing import Optional
from sqlalchemy import select, delete, update
from app.db.session import get_async_session
from app.db.models.co_organizer import CoOrganizer
from app.schemas.co_organizer import CoOrganizerOut


async def create_co_organizer_repo(user_id: int, organizer_id: int, event_id: int, invited_by: int) -> CoOrganizerOut:
    """Create a new event co-organizer in the database."""
    async with get_async_session() as session:
        co_organizer = CoOrganizer(user_id=user_id, organizer_id=organizer_id, event_id=event_id, invited_by=invited_by)
        session.add(co_organizer)
        await session.commit()
        await session.refresh(co_organizer)
        return CoOrganizerOut.model_validate(co_organizer)
    
async def get_co_organizer_by_id_repo(co_organizer_id: int) -> Optional[CoOrganizerOut]:
    """Get a co-organizer by ID."""
    async with get_async_session() as session:
        result = await session.execute(select(CoOrganizer).where(CoOrganizer.id == co_organizer_id))
        co_organizer = result.scalars().unique().one_or_none()
        return CoOrganizerOut.model_validate(co_organizer)
    
async def delete_co_organizer_repo(co_organizer_id: int) -> None:
    """Delete a co-organizer from the database."""
    async with get_async_session() as session:
        await session.execute(delete(CoOrganizer).where(CoOrganizer.id == co_organizer_id))
        await session.commit()

async def update_create_co_organizer_status_repo(co_organizer_id: int, create_co_organizer: bool) -> None:
    """Update the create_co_organizer status of a co-organizer.
    If True the user can invite co-organizers to the event.
    The previlage is only given to by the organizer.
    """
    async with get_async_session() as session:
        await session.execute(update(CoOrganizer).where(CoOrganizer.id == co_organizer_id).values(create_co_organizer=create_co_organizer))
        await session.commit()

async def get_all_event_co_organizers_repo(event_id: int) -> Optional[list[CoOrganizerOut]]:
    """Get all co-organizers for a single event (no organizer-ownership check —
    callers must verify the event belongs to the requesting organizer first,
    or prefer get_co_organizers_by_organizer_repo for a self-scoped query)."""
    async with get_async_session() as session:
        result = await session.execute(select(CoOrganizer).where(CoOrganizer.event_id == event_id))
        co_organizers = result.scalars().unique().all()
        return [CoOrganizerOut.model_validate(co_organizer) for co_organizer in co_organizers]
    
async def get_co_organizers_by_organizer_repo(organizer_id: int, event_id: Optional[int] = None) -> list[CoOrganizerOut]:
    """
    Get co-organizers belonging to a specific organizer, optionally filtered
    to a single event.

    organizer_id is always required and comes from the authenticated
    organizer's own ID — this is the ownership boundary. event_id is an
    optional additional filter; when None, returns co-organizers across
    ALL of the organizer's events ("All Events" view on the frontend).

    This replaces the previous unscoped get_all_event_co_organizers_repo
    call site in the GET /organizers/me/co-organizers route, which accepted
    any event_id with no check that it belonged to the requesting organizer.
    """
    async with get_async_session() as session:
        stmt = select(CoOrganizer).where(CoOrganizer.organizer_id == organizer_id)
        if event_id is not None:
            stmt = stmt.where(CoOrganizer.event_id == event_id)
        result = await session.execute(stmt)
        co_organizers = result.scalars().unique().all()
        return [CoOrganizerOut.model_validate(co_organizer) for co_organizer in co_organizers]
    
async def get_user_co_organizing_events_repo(user_id: int) -> Optional[list[CoOrganizerOut]]:
    """Get all events that a user is co-organizing."""
    async with get_async_session() as session:
        result = await session.execute(select(CoOrganizer).where(CoOrganizer.user_id == user_id))
        co_organizers = result.scalars().unique().all()
        return [CoOrganizerOut.model_validate(co_organizer) for co_organizer in co_organizers]

    
async def check_if_co_organizer_repo(user_id: int, event_id: int) -> bool:
    """Check if a user is a co-organizer for an event."""
    async with get_async_session() as session:
        result = await session.execute(select(CoOrganizer).where(CoOrganizer.user_id == user_id).where(CoOrganizer.event_id == event_id))
        co_organizer = result.scalars().unique().one_or_none()
        
        return True if co_organizer else False