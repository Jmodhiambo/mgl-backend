#!/usr/bin/env python3
"""Async Repository for Event model operations."""

from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.models.event import Event
from app.db.models.user import User
from app.db.models.booking import Booking
from app.db.session import get_async_session
from app.schemas.event import (
    EventOut,
    OrganizerEventOut,
    AdminEventOut,
    EventCreateWithFlyer,
    EventUpdate,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _admin_row_to_schema(row) -> AdminEventOut:
    """Map a raw SQLAlchemy result row to AdminEventOut."""
    event, organizer_name, total_bookings, total_revenue = row
    return AdminEventOut(
        id=event.id,
        title=event.title,
        slug=event.slug,
        description=event.description,
        venue=event.venue,
        city=event.city,
        country=event.country,
        category=event.category,
        start_time=event.start_time,
        end_time=event.end_time,
        original_filename=event.original_filename,
        flyer_url=event.flyer_url,
        status=event.status,
        is_approved=event.is_approved,
        is_active=event.is_active,
        organizer_id=event.organizer_id,
        organizer_name=organizer_name or "Unknown",
        total_bookings=total_bookings or 0,
        total_revenue=float(total_revenue or 0),
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


def _organizer_row_to_schema(row) -> OrganizerEventOut:
    """Map a raw SQLAlchemy result row to OrganizerEventOut."""
    event, total_bookings, total_revenue = row
    return OrganizerEventOut(
        id=event.id,
        title=event.title,
        slug=event.slug,
        description=event.description,
        venue=event.venue,
        city=event.city,
        country=event.country,
        category=event.category,
        start_time=event.start_time,
        end_time=event.end_time,
        original_filename=event.original_filename,
        flyer_url=event.flyer_url,
        status=event.status,
        is_approved=event.is_approved,
        is_active=event.is_active,
        total_bookings=total_bookings or 0,
        total_revenue=float(total_revenue or 0),
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


# ─── Base CRUD ────────────────────────────────────────────────────────────────

async def create_event_repo(event_data: EventCreateWithFlyer) -> EventOut:
    """Create a new event in the database."""
    async with get_async_session() as session:
        new_event = Event(
            title=event_data.title,
            slug=event_data.slug,
            description=event_data.description,
            venue=event_data.venue,
            city=event_data.city,
            country=event_data.country,
            category=event_data.category,
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


async def get_event_by_id_repo(event_id: int) -> Optional[EventOut]:
    """Get a public EventOut by ID."""
    async with get_async_session() as session:
        stmt = select(Event).where(Event.id == event_id)
        event = await session.scalar(stmt)
        return EventOut.model_validate(event) if event else None


async def get_event_by_slug_repo(slug: str) -> Optional[EventOut]:
    """Get a public EventOut by slug."""
    async with get_async_session() as session:
        stmt = select(Event).where(Event.slug == slug)
        event = await session.scalar(stmt)
        return EventOut.model_validate(event) if event else None


async def update_event_repo(event_id: int, event_data: EventUpdate) -> Optional[EventOut]:
    """Update an event. Only sets fields that are not None."""
    async with get_async_session() as session:
        stmt = select(Event).where(Event.id == event_id)
        event = await session.scalar(stmt)
        if not event:
            return None

        update_fields = event_data.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(event, field, value)

        await session.commit()
        await session.refresh(event)
        return EventOut.model_validate(event)


async def delete_event_repo(event_id: int) -> bool:
    """Hard-delete an event."""
    async with get_async_session() as session:
        stmt = select(Event).where(Event.id == event_id)
        event = await session.scalar(stmt)
        if not event:
            return False
        await session.delete(event)
        await session.commit()
        return True


async def update_event_status_repo(event_id: int, new_status: str) -> Optional[AdminEventOut]:
    """Update the status field of an event."""
    async with get_async_session() as session:
        stmt = select(Event).where(Event.id == event_id)
        event = await session.scalar(stmt)
        if not event:
            return None
        event.status = new_status
        await session.commit()
        await session.refresh(event)
        return AdminEventOut.model_validate(event)


# ─── Approval ────────────────────────────────────────────────────────────────

async def approve_event_repo(event_id: int) -> Optional[AdminEventOut]:
    """
    Approve an event. Returns AdminEventOut so the router can send
    notifications using organizer_name and pass back a fully-typed object.
    """
    async with get_async_session() as session:
        stmt = (
            select(
                Event,
                User.name.label("organizer_name"),
                func.count(Booking.id).label("total_bookings"),
                func.coalesce(func.sum(Booking.total_price), 0).label("total_revenue"),
            )
            .outerjoin(User, Event.organizer_id == User.id)
            .outerjoin(
                Booking,
                (Booking.event_id == Event.id) & (Booking.status == "confirmed"),
            )
            .where(Event.id == event_id)
            .group_by(Event.id, User.name)
        )
        row = (await session.execute(stmt)).one_or_none()
        if not row:
            return None

        event = row[0]
        event.is_approved = True
        await session.commit()
        await session.refresh(event)

        # Re-fetch the row after commit to get accurate data
        row2 = (await session.execute(stmt)).one_or_none()
        return _admin_row_to_schema(row2) if row2 else None


async def reject_event_repo(event_id: int) -> Optional[AdminEventOut]:
    """
    Reject an event. Returns AdminEventOut (not bool) so the router can
    use event.title / event.slug for notifications.

    Previously returned bool — this was a bug: the router tried to access
    event.title on the return value and would raise AttributeError.
    """
    async with get_async_session() as session:
        stmt = (
            select(
                Event,
                User.name.label("organizer_name"),
                func.count(Booking.id).label("total_bookings"),
                func.coalesce(func.sum(Booking.total_price), 0).label("total_revenue"),
            )
            .outerjoin(User, Event.organizer_id == User.id)
            .outerjoin(
                Booking,
                (Booking.event_id == Event.id) & (Booking.status == "confirmed"),
            )
            .where(Event.id == event_id)
            .group_by(Event.id, User.name)
        )
        row = (await session.execute(stmt)).one_or_none()
        if not row:
            return None

        event = row[0]
        event.is_approved = False
        event.is_active = False
        await session.commit()
        await session.refresh(event)

        row2 = (await session.execute(stmt)).one_or_none()
        return _admin_row_to_schema(row2) if row2 else None


# ─── Admin queries (with joins + aggregates) ──────────────────────────────────

async def get_all_events_admin_repo() -> list[AdminEventOut]:
    """
    Return ALL events (approved and unapproved) with organizer name and
    aggregated confirmed booking stats. Used by GET /admin/all-events.
    """
    async with get_async_session() as session:
        stmt = (
            select(
                Event,
                User.name.label("organizer_name"),
                func.count(Booking.id).label("total_bookings"),
                func.coalesce(func.sum(Booking.total_price), 0).label("total_revenue"),
            )
            .outerjoin(User, Event.organizer_id == User.id)
            .outerjoin(
                Booking,
                (Booking.event_id == Event.id) & (Booking.status == "confirmed"),
            )
            .group_by(Event.id, User.name)
            .order_by(Event.created_at.desc())
        )
        rows = (await session.execute(stmt)).all()
        return [_admin_row_to_schema(row) for row in rows]


async def get_approved_events_admin_repo() -> list[AdminEventOut]:
    """Approved events only, with joins. Used by GET /admin/events."""
    async with get_async_session() as session:
        stmt = (
            select(
                Event,
                User.name.label("organizer_name"),
                func.count(Booking.id).label("total_bookings"),
                func.coalesce(func.sum(Booking.total_price), 0).label("total_revenue"),
            )
            .outerjoin(User, Event.organizer_id == User.id)
            .outerjoin(
                Booking,
                (Booking.event_id == Event.id) & (Booking.status == "confirmed"),
            )
            .where(Event.is_approved.is_(True))
            .group_by(Event.id, User.name)
            .order_by(Event.created_at.desc())
        )
        rows = (await session.execute(stmt)).all()
        return [_admin_row_to_schema(row) for row in rows]


async def get_unapproved_events_admin_repo() -> list[AdminEventOut]:
    """Unapproved events only, with joins."""
    async with get_async_session() as session:
        stmt = (
            select(
                Event,
                User.name.label("organizer_name"),
                func.count(Booking.id).label("total_bookings"),
                func.coalesce(func.sum(Booking.total_price), 0).label("total_revenue"),
            )
            .outerjoin(User, Event.organizer_id == User.id)
            .outerjoin(
                Booking,
                (Booking.event_id == Event.id) & (Booking.status == "confirmed"),
            )
            .where(Event.is_approved.is_(False))
            .group_by(Event.id, User.name)
            .order_by(Event.created_at.desc())
        )
        rows = (await session.execute(stmt)).all()
        return [_admin_row_to_schema(row) for row in rows]


async def get_event_by_id_admin_repo(event_id: int) -> Optional[AdminEventOut]:
    """Single event with joins, for admin detail view."""
    async with get_async_session() as session:
        stmt = (
            select(
                Event,
                User.name.label("organizer_name"),
                func.count(Booking.id).label("total_bookings"),
                func.coalesce(func.sum(Booking.total_price), 0).label("total_revenue"),
            )
            .outerjoin(User, Event.organizer_id == User.id)
            .outerjoin(
                Booking,
                (Booking.event_id == Event.id) & (Booking.status == "confirmed"),
            )
            .where(Event.id == event_id)
            .group_by(Event.id, User.name)
        )
        row = (await session.execute(stmt)).one_or_none()
        return _admin_row_to_schema(row) if row else None


async def get_events_by_organizer_admin_repo(organizer_id: int) -> list[AdminEventOut]:
    """Events by a specific organizer, with joins."""
    async with get_async_session() as session:
        stmt = (
            select(
                Event,
                User.name.label("organizer_name"),
                func.count(Booking.id).label("total_bookings"),
                func.coalesce(func.sum(Booking.total_price), 0).label("total_revenue"),
            )
            .outerjoin(User, Event.organizer_id == User.id)
            .outerjoin(
                Booking,
                (Booking.event_id == Event.id) & (Booking.status == "confirmed"),
            )
            .where(Event.organizer_id == organizer_id)
            .group_by(Event.id, User.name)
            .order_by(Event.created_at.desc())
        )
        rows = (await session.execute(stmt)).all()
        return [_admin_row_to_schema(row) for row in rows]


# ─── Organizer queries (with aggregates, no organizer name join needed) ───────

async def get_events_by_organizer_with_stats_repo(organizer_id: int) -> list[OrganizerEventOut]:
    """
    Organizer's own events with booking/revenue stats.
    Used by GET /organizers/me/events.
    """
    async with get_async_session() as session:
        stmt = (
            select(
                Event,
                func.count(Booking.id).label("total_bookings"),
                func.coalesce(func.sum(Booking.total_price), 0).label("total_revenue"),
            )
            .outerjoin(
                Booking,
                (Booking.event_id == Event.id) & (Booking.status == "confirmed"),
            )
            .where(Event.organizer_id == organizer_id)
            .group_by(Event.id)
            .order_by(Event.created_at.desc())
        )
        rows = (await session.execute(stmt)).all()
        return [_organizer_row_to_schema(row) for row in rows]


async def get_event_by_id_organizer_repo(event_id: int) -> Optional[OrganizerEventOut]:
    """Single event with stats for organizer detail view."""
    async with get_async_session() as session:
        stmt = (
            select(
                Event,
                func.count(Booking.id).label("total_bookings"),
                func.coalesce(func.sum(Booking.total_price), 0).label("total_revenue"),
            )
            .outerjoin(
                Booking,
                (Booking.event_id == Event.id) & (Booking.status == "confirmed"),
            )
            .where(Event.id == event_id)
            .group_by(Event.id)
        )
        row = (await session.execute(stmt)).one_or_none()
        return _organizer_row_to_schema(row) if row else None


# ─── Public queries (EventOut only) ──────────────────────────────────────────

async def get_approved_events_repo() -> list[EventOut]:
    """All approved events — public facing."""
    async with get_async_session() as session:
        stmt = select(Event).where(Event.is_approved.is_(True))
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(e) for e in events]


async def get_latest_events_repo(limit: int = 5) -> list[EventOut]:
    """Latest approved events."""
    async with get_async_session() as session:
        stmt = (
            select(Event)
            .where(Event.is_approved.is_(True))
            .order_by(Event.created_at.desc())
            .limit(limit)
        )
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(e) for e in events]


async def search_events_by_title_repo(keyword: str) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(
            Event.is_approved.is_(True),
            Event.title.ilike(f"%{keyword}%"),
        )
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(e) for e in events]


async def search_events_by_venue_repo(venue: str) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(
            Event.is_approved.is_(True),
            Event.venue.ilike(f"%{venue}%"),
        )
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(e) for e in events]


async def get_events_by_country_repo(country: str) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(
            Event.is_approved.is_(True),
            Event.country.ilike(f"%{country}%"),
        )
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(e) for e in events]


async def get_events_in_date_range_repo(start_date: datetime, end_date: datetime) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(
            Event.is_approved.is_(True),
            Event.start_time >= start_date,
            Event.end_time <= end_date,
        )
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(e) for e in events]


async def get_events_sorted_by_start_time_repo(ascending: bool = True) -> list[EventOut]:
    async with get_async_session() as session:
        order = Event.start_time.asc() if ascending else Event.start_time.desc()
        stmt = select(Event).where(Event.is_approved.is_(True)).order_by(order)
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(e) for e in events]


async def get_events_sorted_by_end_time_repo(ascending: bool = True) -> list[EventOut]:
    async with get_async_session() as session:
        order = Event.end_time.asc() if ascending else Event.end_time.desc()
        stmt = select(Event).where(Event.is_approved.is_(True)).order_by(order)
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(e) for e in events]


async def count_events_repo() -> int:
    async with get_async_session() as session:
        stmt = select(func.count()).select_from(Event).where(Event.is_approved.is_(True))
        return await session.scalar(stmt) or 0


# ─── Organizer count helpers ──────────────────────────────────────────────────
async def get_events_by_organizer_repo(organizer_id: int) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.organizer_id == organizer_id)
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(e) for e in events]
    

async def count_events_by_organizer_repo(organizer_id: int) -> int:
    async with get_async_session() as session:
        result = await session.execute(
            select(func.count())
            .select_from(Event)
            .where(Event.organizer_id == organizer_id)
            .where(Event.status != "deleted")
        )
        return result.scalar_one()


async def count_active_events_by_organizer_repo(organizer_id: int) -> int:
    async with get_async_session() as session:
        result = await session.execute(
            select(func.count())
            .select_from(Event)
            .where(Event.organizer_id == organizer_id)
            .where(
                Event.start_time <= datetime.now(timezone.utc),
                Event.end_time >= datetime.now(timezone.utc),
            )
        )
        return result.scalar_one()


async def count_upcoming_events_by_organizer_repo(organizer_id: int) -> int:
    async with get_async_session() as session:
        result = await session.execute(
            select(func.count())
            .select_from(Event)
            .where(Event.organizer_id == organizer_id)
            .where(Event.status == "upcoming")
        )
        return result.scalar_one()


async def count_completed_events_by_organizer_repo(organizer_id: int) -> int:
    async with get_async_session() as session:
        result = await session.execute(
            select(func.count())
            .select_from(Event)
            .where(Event.organizer_id == organizer_id)
            .where(Event.status == "completed")
        )
        return result.scalar_one()


async def count_events_created_this_month_repo(organizer_id: int) -> int:
    now = datetime.now(timezone.utc)
    first_day = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    async with get_async_session() as session:
        result = await session.execute(
            select(func.count())
            .select_from(Event)
            .where(Event.organizer_id == organizer_id)
            .where(Event.created_at >= first_day)
            .where(Event.status != "deleted")
        )
        return result.scalar_one()


async def count_events_created_last_month_repo(organizer_id: int) -> int:
    now = datetime.now(timezone.utc)
    first_of_current = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    last_of_previous = first_of_current - timedelta(days=1)
    first_of_previous = datetime(
        last_of_previous.year, last_of_previous.month, 1, tzinfo=timezone.utc
    )
    async with get_async_session() as session:
        result = await session.execute(
            select(func.count())
            .select_from(Event)
            .where(Event.organizer_id == organizer_id)
            .where(Event.created_at >= first_of_previous)
            .where(Event.created_at < first_of_current)
            .where(Event.status != "deleted")
        )
        return result.scalar_one()


async def get_top_events_by_organizer_repo(organizer_id: int, limit: int = 5) -> list:
    """Top events by confirmed revenue for an organizer."""
    async with get_async_session() as session:
        result = await session.execute(
            select(
                Event.id,
                Event.title,
                func.count(Booking.id).label("bookings"),
                func.coalesce(func.sum(Booking.total_price), 0).label("revenue"),
                func.coalesce(func.sum(Booking.quantity), 0).label("tickets_sold"),
            )
            .select_from(Event)
            .join(Booking, Event.id == Booking.event_id)
            .where(Event.organizer_id == organizer_id)
            .where(Booking.status == "confirmed")
            .group_by(Event.id, Event.title)
            .order_by(func.sum(Booking.total_price).desc())
            .limit(limit)
        )
        return [
            {
                "id": event_id,
                "title": title,
                "bookings": bookings,
                "revenue": float(revenue),
                "tickets_sold": tickets_sold,
            }
            for event_id, title, bookings, revenue, tickets_sold in result
        ]


# ─── Misc admin filters (kept from original, now all filter to approved) ──────

async def get_events_by_status_repo(status: str) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.status == status)
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(e) for e in events]


async def get_events_created_after_repo(date: datetime) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.created_at > date)
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(e) for e in events]


async def get_events_created_before_repo(date: datetime) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.created_at < date)
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(e) for e in events]


async def get_events_updated_after_repo(date: datetime) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.updated_at > date)
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(e) for e in events]


async def get_events_updated_before_repo(date: datetime) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.updated_at < date)
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(e) for e in events]