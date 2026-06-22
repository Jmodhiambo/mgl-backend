#!/usr/bin/env python3
"""Async Repository for Event model operations.

Key changes vs original:
- _organizer_row_to_schema and _admin_row_to_schema now compute
  platform_cut and organizer_net from each event's commission_rate.
- get_event_by_slug_organizer_repo added for the new slug-based detail endpoint.
- All other functions are unchanged.
"""

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

def _compute_commission(total_revenue: float, commission_rate: float) -> tuple[float, float]:
    """Return (platform_cut, organizer_net) for a given revenue and rate."""
    platform_cut  = round(total_revenue * commission_rate / 100, 2)
    organizer_net = round(total_revenue - platform_cut, 2)
    return platform_cut, organizer_net


def _admin_row_to_schema(row) -> AdminEventOut:
    """Map a raw SQLAlchemy result row to AdminEventOut."""
    event, organizer_name, total_bookings, total_revenue = row
    commission_rate = float(event.commission_rate)
    total_revenue   = float(total_revenue or 0)
    platform_cut, organizer_net = _compute_commission(total_revenue, commission_rate)

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
        total_revenue=total_revenue,
        commission_rate=commission_rate,
        commission_source=event.commission_source,
        commission_approved_by=event.commission_approved_by,
        commission_approved_by_name=event.commission_approved_by_name,
        commission_approved_at=event.commission_approved_at,
        platform_cut=platform_cut,
        organizer_net=organizer_net,
        created_at=event.created_at,
        updated_at=event.updated_at,
    )


def _organizer_row_to_schema(row) -> OrganizerEventOut:
    """Map a raw SQLAlchemy result row to OrganizerEventOut."""
    event, total_bookings, total_revenue = row
    commission_rate = float(event.commission_rate)
    total_revenue   = float(total_revenue or 0)
    platform_cut, organizer_net = _compute_commission(total_revenue, commission_rate)

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
        total_revenue=total_revenue,
        commission_rate=commission_rate,
        commission_source=event.commission_source,
        commission_approved_by=event.commission_approved_by,
        commission_approved_by_name=event.commission_approved_by_name,
        commission_approved_at=event.commission_approved_at,
        platform_cut=platform_cut,
        organizer_net=organizer_net,
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
            commission_rate=event_data.commission_rate,
            commission_source=event_data.commission_source,
        )
        session.add(new_event)
        await session.commit()
        await session.refresh(new_event)
        return EventOut.model_validate(new_event)


async def get_event_by_id_repo(event_id: int) -> Optional[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.id == event_id)
        event = await session.scalar(stmt)
        return EventOut.model_validate(event) if event else None


async def get_event_by_slug_repo(slug: str) -> Optional[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.slug == slug)
        event = await session.scalar(stmt)
        return EventOut.model_validate(event) if event else None


async def update_event_repo(event_id: int, event_data: EventUpdate) -> Optional[EventOut]:
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
    async with get_async_session() as session:
        stmt = select(Event).where(Event.id == event_id)
        event = await session.scalar(stmt)
        if not event:
            return False
        await session.delete(event)
        await session.commit()
        return True


async def update_event_status_repo(event_id: int, new_status: str) -> Optional[AdminEventOut]:
    async with get_async_session() as session:
        stmt = _approval_stmt(event_id)
        row  = (await session.execute(stmt)).one_or_none()
        if not row:
            return None
        event = row[0]
        event.status = new_status
        await session.commit()
        await session.refresh(event)
        row2 = (await session.execute(stmt)).one_or_none()
        return _admin_row_to_schema(row2) if row2 else None


# ─── Approval ────────────────────────────────────────────────────────────────

def _approval_stmt(event_id: int):
    return (
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


async def approve_event_repo(event_id: int) -> Optional[AdminEventOut]:
    async with get_async_session() as session:
        stmt = _approval_stmt(event_id)
        row  = (await session.execute(stmt)).one_or_none()
        if not row:
            return None
        event = row[0]
        event.is_approved = True
        await session.commit()
        await session.refresh(event)
        row2 = (await session.execute(stmt)).one_or_none()
        return _admin_row_to_schema(row2) if row2 else None


async def reject_event_repo(event_id: int) -> Optional[AdminEventOut]:
    async with get_async_session() as session:
        stmt = _approval_stmt(event_id)
        row  = (await session.execute(stmt)).one_or_none()
        if not row:
            return None
        event = row[0]
        event.is_approved = False
        # is_active is a computed property derived from is_approved/status/
        # start_time/end_time — it has no setter, and none is needed: setting
        # is_approved=False already makes is_active resolve to False.
        await session.commit()
        await session.refresh(event)
        row2 = (await session.execute(stmt)).one_or_none()
        return _admin_row_to_schema(row2) if row2 else None


# ─── Admin queries ────────────────────────────────────────────────────────────

def _admin_list_stmt(where_clause=None):
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
    if where_clause is not None:
        stmt = stmt.where(where_clause)
    return stmt


async def get_all_events_admin_repo() -> list[AdminEventOut]:
    async with get_async_session() as session:
        rows = (await session.execute(_admin_list_stmt())).all()
        return [_admin_row_to_schema(r) for r in rows]


async def get_approved_events_admin_repo() -> list[AdminEventOut]:
    async with get_async_session() as session:
        rows = (await session.execute(_admin_list_stmt(Event.is_approved.is_(True)))).all()
        return [_admin_row_to_schema(r) for r in rows]


async def get_unapproved_events_admin_repo() -> list[AdminEventOut]:
    async with get_async_session() as session:
        rows = (await session.execute(_admin_list_stmt(Event.is_approved.is_(False)))).all()
        return [_admin_row_to_schema(r) for r in rows]


async def get_event_by_id_admin_repo(event_id: int) -> Optional[AdminEventOut]:
    async with get_async_session() as session:
        stmt = _admin_list_stmt(Event.id == event_id)
        row  = (await session.execute(stmt)).one_or_none()
        return _admin_row_to_schema(row) if row else None


async def get_events_by_organizer_admin_repo(organizer_id: int) -> list[AdminEventOut]:
    async with get_async_session() as session:
        rows = (await session.execute(_admin_list_stmt(Event.organizer_id == organizer_id))).all()
        return [_admin_row_to_schema(r) for r in rows]


# ─── Organizer queries ────────────────────────────────────────────────────────

def _organizer_list_stmt(where_clause=None):
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
        .group_by(Event.id)
        .order_by(Event.created_at.desc())
    )
    if where_clause is not None:
        stmt = stmt.where(where_clause)
    return stmt


async def get_events_by_organizer_with_stats_repo(organizer_id: int) -> list[OrganizerEventOut]:
    async with get_async_session() as session:
        rows = (await session.execute(
            _organizer_list_stmt(Event.organizer_id == organizer_id)
        )).all()
        return [_organizer_row_to_schema(r) for r in rows]


async def get_event_by_id_organizer_repo(event_id: int) -> Optional[OrganizerEventOut]:
    async with get_async_session() as session:
        row = (await session.execute(
            _organizer_list_stmt(Event.id == event_id)
        )).one_or_none()
        return _organizer_row_to_schema(row) if row else None


async def get_event_by_slug_organizer_repo(slug: str) -> Optional[OrganizerEventOut]:
    """
    Fetch a single event by slug as OrganizerEventOut (with stats + commission).
    Used by the slug-based detail endpoint.
    """
    async with get_async_session() as session:
        row = (await session.execute(
            _organizer_list_stmt(Event.slug == slug)
        )).one_or_none()
        return _organizer_row_to_schema(row) if row else None


# ─── Public queries ───────────────────────────────────────────────────────────

async def get_approved_events_repo() -> list[EventOut]:
    async with get_async_session() as session:
        stmt   = select(Event).where(Event.is_approved.is_(True))
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(e) for e in events]


async def get_latest_events_repo(limit: int = 5) -> list[EventOut]:
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
            Event.is_approved.is_(True), Event.title.ilike(f"%{keyword}%")
        )
        return [EventOut.model_validate(e) for e in (await session.scalars(stmt)).all()]


async def search_events_by_venue_repo(venue: str) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(
            Event.is_approved.is_(True), Event.venue.ilike(f"%{venue}%")
        )
        return [EventOut.model_validate(e) for e in (await session.scalars(stmt)).all()]


async def get_events_by_country_repo(country: str) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(
            Event.is_approved.is_(True), Event.country.ilike(f"%{country}%")
        )
        return [EventOut.model_validate(e) for e in (await session.scalars(stmt)).all()]


async def get_events_in_date_range_repo(start_date: datetime, end_date: datetime) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(
            Event.is_approved.is_(True),
            Event.start_time >= start_date,
            Event.end_time   <= end_date,
        )
        return [EventOut.model_validate(e) for e in (await session.scalars(stmt)).all()]


async def get_events_sorted_by_start_time_repo(ascending: bool = True) -> list[EventOut]:
    async with get_async_session() as session:
        order = Event.start_time.asc() if ascending else Event.start_time.desc()
        stmt  = select(Event).where(Event.is_approved.is_(True)).order_by(order)
        return [EventOut.model_validate(e) for e in (await session.scalars(stmt)).all()]


async def get_events_sorted_by_end_time_repo(ascending: bool = True) -> list[EventOut]:
    async with get_async_session() as session:
        order = Event.end_time.asc() if ascending else Event.end_time.desc()
        stmt  = select(Event).where(Event.is_approved.is_(True)).order_by(order)
        return [EventOut.model_validate(e) for e in (await session.scalars(stmt)).all()]


async def count_events_repo() -> int:
    async with get_async_session() as session:
        return await session.scalar(
            select(func.count()).select_from(Event).where(Event.is_approved.is_(True))
        ) or 0


async def get_events_by_organizer_repo(organizer_id: int) -> list[EventOut]:
    async with get_async_session() as session:
        stmt   = select(Event).where(Event.organizer_id == organizer_id)
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(e) for e in events]


async def count_events_by_organizer_repo(organizer_id: int) -> int:
    async with get_async_session() as session:
        return (await session.execute(
            select(func.count()).select_from(Event)
            .where(Event.organizer_id == organizer_id)
            .where(Event.status != "deleted")
        )).scalar_one()


async def get_top_events_by_organizer_repo(organizer_id: int, limit: int = 5) -> list:
    """Top events by confirmed revenue for an organizer, with commission breakdown."""
    async with get_async_session() as session:
        result = await session.execute(
            select(
                Event.id,
                Event.title,
                Event.commission_rate,
                func.count(Booking.id).label("bookings"),
                func.coalesce(func.sum(Booking.total_price), 0).label("revenue"),
                func.coalesce(func.sum(Booking.quantity), 0).label("tickets_sold"),
            )
            .select_from(Event)
            .join(Booking, Event.id == Booking.event_id)
            .where(Event.organizer_id == organizer_id)
            .where(Booking.status == "confirmed")
            .group_by(Event.id, Event.title, Event.commission_rate)
            .order_by(func.sum(Booking.total_price).desc())
            .limit(limit)
        )
        rows = []
        for event_id, title, commission_rate, bookings, revenue, tickets_sold in result:
            rev           = float(revenue)
            rate          = float(commission_rate)
            platform_cut  = round(rev * rate / 100, 2)
            organizer_net = round(rev - platform_cut, 2)
            rows.append({
                "id":            event_id,
                "title":         title,
                "bookings":      bookings,
                "revenue":       rev,
                "tickets_sold":  tickets_sold,
                "platform_cut":  platform_cut,
                "organizer_net": organizer_net,
            })
        return rows


# ─── Misc filters ─────────────────────────────────────────────────────────────

async def get_events_by_status_repo(status: str) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.status == status)
        return [EventOut.model_validate(e) for e in (await session.scalars(stmt)).all()]


async def get_events_created_after_repo(date: datetime) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.created_at > date)
        return [EventOut.model_validate(e) for e in (await session.scalars(stmt)).all()]


async def get_events_created_before_repo(date: datetime) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.created_at < date)
        return [EventOut.model_validate(e) for e in (await session.scalars(stmt)).all()]


async def get_events_updated_after_repo(date: datetime) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.updated_at > date)
        return [EventOut.model_validate(e) for e in (await session.scalars(stmt)).all()]


async def get_events_updated_before_repo(date: datetime) -> list[EventOut]:
    async with get_async_session() as session:
        stmt = select(Event).where(Event.updated_at < date)
        return [EventOut.model_validate(e) for e in (await session.scalars(stmt)).all()]