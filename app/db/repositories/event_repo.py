#!/usr/bin/env python3
"""Async Repository for Event model operations."""

from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.models.event import Event
from app.db.session import get_async_session
from app.schemas.event import (
    EventOut,
    EventCreateWithFlyer,
    EventUpdate,
)


async def create_event_repo(event_data: EventCreateWithFlyer) -> EventOut:
    """Create a new event in the database."""
    async with get_async_session() as session:
        new_event = Event(
            title=event_data.title,
            description=event_data.description,
            venue=event_data.venue,
            start_time=event_data.start_time,
            end_time=event_data.end_time,
            original_filename=event_data.original_filename,
            flyer_url=event_data.flyer_url,
            organizer_id=event_data.organizer_id,
        )

        session.add(new_event)
        await session.commit()
        await session.refresh(new_event)

        return EventOut.model_validate(new_event)


async def update_event_repo(event_id: int, event_data: EventUpdate) -> Optional[EventOut]:
    """Update an event in the database."""
    async with get_async_session() as session:
        stmt = select(Event).where(Event.id == event_id)
        event = await session.scalar(stmt)

        if not event:
            return None

        event.title = event_data.title
        event.description = event_data.description
        event.venue = event_data.venue
        event.start_time = event_data.start_time
        event.end_time = event_data.end_time

        await session.commit()
        await session.refresh(event)

        return EventOut.model_validate(event)


async def get_approved_events_repo() -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.approved.is_(True))
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(event) for event in events]


async def get_unapproved_events_repo() -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.approved.is_(False))
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(event) for event in events]


async def get_all_events_repo() -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event)
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(event) for event in events]


async def get_event_by_id_repo(event_id: int) -> Optional[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.id == event_id)
        event = await session.scalar(stmt)
        return EventOut.model_validate(event) if event else None


async def approve_event_repo(event_id: int) -> Optional[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.id == event_id)
        event = await session.scalar(stmt)

        if not event:
            return None

        event.approved = True
        await session.commit()
        await session.refresh(event)

        return EventOut.model_validate(event)


async def reject_event_repo(event_id: int) -> bool:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.id == event_id)
        event = await session.scalar(stmt)

        if not event:
            return False

        event.rejected = True
        await session.commit()
        return True


async def delete_event_repo(event_id: int) -> bool:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.id == event_id)
        event = await session.scalar(stmt)

        if not event:
            return False

        await session.delete(event)
        await session.commit()
        return True


async def update_event_status_repo(event_id: int, new_status: str) -> Optional[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.id == event_id)
        event = await session.scalar(stmt)

        if not event:
            return None

        event.status = new_status
        await session.commit()
        await session.refresh(event)

        return EventOut.model_validate(event)


async def get_events_by_organizer_repo(organizer_id: int) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.organizer_id == organizer_id)
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(event) for event in events]


async def get_events_in_date_range_repo(start_date: datetime, end_date: datetime) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(
            Event.start_time >= start_date,
            Event.end_time <= end_date,
        )
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(event) for event in events]


async def search_events_by_title_repo(keyword: str) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.title.ilike(f"%{keyword}%"))
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(event) for event in events]


async def count_events_by_organizer_repo(organizer_id: int) -> int:
    async with get_async_session() as session:
        stmt = select(func.count()).where(Event.organizer_id == organizer_id)
        count = await session.scalar(stmt)
        return count or 0


async def count_events_repo() -> int:
    async with get_async_session() as session:
        stmt = select(func.count()).select_from(Event)
        count = await session.scalar(stmt)
        return count or 0


async def get_latest_events_repo(limit: int = 5) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = (
            select(Event)
            .where(Event.approved.is_(True))
            .order_by(Event.created_at.desc())
            .limit(limit)
        )
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(event) for event in events]


async def get_events_by_status_repo(status: str) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.status == status)
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(event) for event in events]


async def get_events_with_bookings_repo() -> list[EventOut]:
    async with get_async_session() as session:
        stmt = (
            select(Event)
            .options(selectinload(Event.bookings))
            .join(Event.bookings)
        )
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(event) for event in events]


async def get_events_without_bookings_repo() -> list[EventOut]:
    async with get_async_session() as session:
        stmt = (
            select(Event)
            .outerjoin(Event.bookings)
            .where(Event.bookings.is_(None))
        )
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(event) for event in events]


async def search_events_by_venue_repo(venue: str) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(
            Event.approved.is_(True),
            Event.venue.ilike(f"%{venue}%"),
        )
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(event) for event in events]


async def get_events_created_after_repo(date: datetime) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.created_at > date)
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(event) for event in events]


async def get_events_created_before_repo(date: datetime) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.created_at < date)
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(event) for event in events]


async def get_events_updated_after_repo(date: datetime) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.updated_at > date)
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(event) for event in events]


async def get_events_updated_before_repo(date: datetime) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.updated_at < date)
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(event) for event in events]


async def get_events_sorted_by_start_time_repo(ascending: bool = True) -> list[EventOut]:
    async with get_async_session() as session:
        order = Event.start_time.asc() if ascending else Event.start_time.desc()
        stmt = select(Event).order_by(order)
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(event) for event in events]


async def get_events_sorted_by_end_time_repo(ascending: bool = True) -> list[EventOut]:
    async with get_async_session() as session:
        order = Event.end_time.asc() if ascending else Event.end_time.desc()
        stmt = select(Event).order_by(order)
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(event) for event in events]


async def get_events_sorted_by_creation_date_repo(ascending: bool = True) -> list[EventOut]:
    async with get_async_session() as session:
        order = Event.created_at.asc() if ascending else Event.created_at.desc()
        stmt = select(Event).order_by(order)
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(event) for event in events]


async def get_events_by_country_repo(country: str) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.country.ilike(f"%{country}%"))
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(event) for event in events]