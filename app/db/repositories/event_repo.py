#!/usr/bin/env python3
"""Async Repository for Event model operations."""

from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
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

def _commission_split(total_revenue: float, commission_rate: float) -> tuple[float, float]:
    """
    Compute (platform_cut, organizer_net) from gross revenue and the rate
    that was locked in on the event at creation time.

    Shared by both row-to-schema helpers below so the math only lives in
    one place.
    """
    platform_cut = float(total_revenue) * (float(commission_rate) / 100)
    organizer_net = float(total_revenue) - platform_cut
    return platform_cut, organizer_net


def _admin_row_to_schema(row) -> AdminEventOut:
    """Map a raw SQLAlchemy result row to AdminEventOut."""
    event, organizer_name, total_bookings, total_revenue = row
    total_revenue = float(total_revenue or 0)
    platform_cut, organizer_net = _commission_split(total_revenue, event.commission_rate)
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
        commission_rate=float(event.commission_rate),
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
    total_revenue = float(total_revenue or 0)
    platform_cut, organizer_net = _commission_split(total_revenue, event.commission_rate)
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
        commission_rate=float(event.commission_rate),
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


async def get_event_by_slug_organizer_repo(slug: str) -> Optional[OrganizerEventOut]:
    """
    Get a single event by slug, with stats, as OrganizerEventOut.

    Added to support get_event_details_by_slug_service(), which is the
    preferred slug-based lookup for the organizer portal (slugs are
    URL-safe and human-readable, so the frontend never has to separately
    resolve slug → numeric ID before fetching event details).

    Mirrors get_event_by_id_organizer_repo exactly, just keyed by slug.
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
            .where(Event.slug == slug)
            .group_by(Event.id)
        )
        row = (await session.execute(stmt)).one_or_none()
        return _organizer_row_to_schema(row) if row else None


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
    """
    Hard-delete an event.

    Raises ValueError (NOT a raw IntegrityError) if the event has any
    orders or bookings attached — those FKs are intentionally left as
    RESTRICT (see app/db/models/order.py and booking.py for the reasoning:
    this is financial data and must never be silently destroyed or
    orphaned by an event deletion).

    Favorites, co-organizers, and ticket types are safe to lose — their
    FKs cascade at the database level (ON DELETE CASCADE), and
    organizer_emails.event_id is ON DELETE SET NULL — so none of those
    will raise here. Only orders/bookings will.

    This mirrors order_repo.delete_order_repo's existing pattern of
    catching the "can't safely delete" case and raising ValueError for
    the service layer to translate into a clean HTTP 400, instead of a
    raw 500 IntegrityError leaking to the frontend.
    """
    async with get_async_session() as session:
        stmt = select(Event).where(Event.id == event_id)
        event = await session.scalar(stmt)
        if not event:
            return False

        await session.delete(event)
        await session.commit()
        # try:
        #     await session.delete(event)
        #     await session.commit()
        # except IntegrityError as exc:
        #     await session.rollback()
        #     # asyncpg surfaces this as a ForeignKeyViolationError wrapped in
        #     # an IntegrityError. We don't need to parse which exact table —
        #     # orders/bookings are the only RESTRICT FKs left on events.id,
        #     # so any IntegrityError here means one of those.
        #     raise ValueError(
        #         "This event has existing orders or bookings and cannot be "
        #         "deleted. Cancel the event instead to preserve payment and "
        #         "booking history."
        #     ) from exc

        return True


async def update_event_status_repo(event_id: int, new_status: str) -> Optional[AdminEventOut]:
    """
    Update the status field of an event.

    Returns AdminEventOut via the joined admin query, NOT via a bare
    AdminEventOut.model_validate(event) — AdminEventOut needs organizer_name,
    total_bookings, total_revenue, platform_cut, and organizer_net, none of
    which exist as plain columns on the Event model. Validating the raw ORM
    object directly would raise the same "Field required" error this whole
    fix addresses, just for a different set of fields.
    """
    async with get_async_session() as session:
        stmt = select(Event).where(Event.id == event_id)
        event = await session.scalar(stmt)
        if not event:
            return None
        event.status = new_status
        await session.commit()

    # Re-fetch through the joined query so organizer_name + stats +
    # commission breakdown are all populated correctly.
    return await get_event_by_id_admin_repo(event_id)


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
            .where(
                Event.organizer_id == organizer_id,
                Event.status != "deleted",
            )
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
            .where(
                Event.is_approved.is_(True),
                or_(Event.status == "upcoming", Event.status == "ongoing"),

            )
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
    """
    Top events by confirmed revenue for an organizer.

    Returns platform_cut/organizer_net alongside revenue — TopEvent now
    requires both fields, computed via the same _commission_split() helper
    used by the row-to-schema mappers above, so the math stays in one place.
    """
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
            revenue = float(revenue)
            platform_cut, organizer_net = _commission_split(revenue, commission_rate)
            rows.append({
                "id": event_id,
                "title": title,
                "bookings": bookings,
                "revenue": revenue,
                "tickets_sold": tickets_sold,
                "platform_cut": platform_cut,
                "organizer_net": organizer_net,
            })
        return rows


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