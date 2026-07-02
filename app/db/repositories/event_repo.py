#!/usr/bin/env python3
"""Async Repository for Event model operations."""

from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, func, or_
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


# IMPORTANT — why this is a correlated subquery, not a join column:
# every query below already outerjoins Booking with
# (Booking.event_id == Event.id) & (Booking.status == "confirmed") to
# compute total_bookings/total_revenue. Adding a plain aggregate column
# to that SAME join would silently be wrong: the join itself already
# excludes every non-confirmed row, so a count expressed as "status not
# in (cancelled, refunded)" evaluated against that pre-filtered join can
# never see a 'pending' booking either — it would just collapse to being
# identical to total_bookings, quietly missing pending bookings (payment
# in flight, STK push sent, no Daraja callback yet) that absolutely
# should still block deletion.
#
# A correlated subquery is independent of that join entirely — it runs
# its own count against Booking with its own WHERE clause, uncoupled
# from whatever the outer query's join condition happens to be. This
# also avoids the func.distinct() correction a second outerjoin would
# need (see the comment history on this function for why a prior version
# of this same idea, joining Order instead, needed that).
_UNRESOLVED_BOOKINGS_COUNT = (
    select(func.count(Booking.id))
    .where(Booking.event_id == Event.id)
    .where(Booking.status.notin_(["cancelled", "refunded"]))
    .correlate(Event)
    .scalar_subquery()
    .label("unresolved_bookings_count")
)


def _admin_row_to_schema(row) -> AdminEventOut:
    """Map a raw SQLAlchemy result row to AdminEventOut."""
    event, organizer_name, total_bookings, total_revenue, unresolved_bookings_count = row
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
        unresolved_bookings_count=unresolved_bookings_count or 0,
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
    event, total_bookings, total_revenue, unresolved_bookings_count = row
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
        unresolved_bookings_count=unresolved_bookings_count or 0,
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


def _admin_events_stmt():
    """
    Base SELECT for every AdminEventOut-shaped query: Event joined with the
    organizer's name and aggregated confirmed-booking stats.

    get_all_events_admin_repo, get_approved_events_admin_repo,
    get_unapproved_events_admin_repo, get_event_by_id_admin_repo, and
    get_events_by_organizer_admin_repo all used to declare this exact same
    select/outerjoin/outerjoin/group_by block independently, differing only
    in their .where() clause (or lack of one) and .order_by(). Same story
    for approve_event_repo/reject_event_repo, which each built it a second
    time just to re-read the row they'd already fetched moments earlier.
    Centralizing it here means the join shape only has to be right in one
    place — add a field to AdminEventOut and there's exactly one query to
    touch, not six.

    Callers chain their own .where()/.order_by() onto the returned
    statement; SQLAlchemy doesn't care that those get added after
    .group_by() in the Python call chain, the generated SQL clause order
    is unaffected.
    """
    return (
        select(
            Event,
            User.name.label("organizer_name"),
            func.count(Booking.id).label("total_bookings"),
            func.coalesce(func.sum(Booking.total_price), 0).label("total_revenue"),
            _UNRESOLVED_BOOKINGS_COUNT,
        )
        .outerjoin(User, Event.organizer_id == User.id)
        .outerjoin(
            Booking,
            (Booking.event_id == Event.id) & (Booking.status == "confirmed"),
        )
        .group_by(Event.id, User.name)
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
    """Get a public EventOut by ID. Excludes deleted and cancelled events."""
    async with get_async_session() as session:
        stmt = select(Event).where(Event.id == event_id)
        event = await session.scalar(stmt)
        return EventOut.model_validate(event) if event else None


async def get_event_by_slug_repo(slug: str) -> Optional[EventOut]:
    """Get a public EventOut by slug. Excludes deleted and cancelled events."""
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
    No status filter here — the organizer portal needs to access any of
    their own events including cancelled ones.
    """
    async with get_async_session() as session:
        stmt = (
            select(
                Event,
                func.count(Booking.id).label("total_bookings"),
                func.coalesce(func.sum(Booking.total_price), 0).label("total_revenue"),
                _UNRESOLVED_BOOKINGS_COUNT,
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
    Hard-delete an event. Apparently done by admins only.
    The organizer only soft deletes by changing the status to deleted
    (or, if the event has bookings, to pending_deletion — see
    update_event_status_service).

    Raises ValueError — NOT a raw IntegrityError — if the event still has
    orders or bookings attached. Those FKs are RESTRICT at the DB level
    (see app/db/models/order.py and booking.py: this is financial data and
    must never be silently destroyed or orphaned by an event deletion).

    This guard existed in an earlier version of this function and was
    missing here — restoring it. Without it, attempting to hard-delete an
    event with bookings raises a raw IntegrityError that propagates as an
    unhandled 500, instead of the clean 400 that event_services.delete_event_service
    is written to expect and translate for the frontend.
    """
    async with get_async_session() as session:
        stmt = select(Event).where(Event.id == event_id)
        event = await session.scalar(stmt)
        if not event:
            return False

        try:
            await session.delete(event)
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise ValueError(
                "This event has existing orders or bookings and cannot be "
                "deleted. Cancel the event instead to preserve payment and "
                "booking history."
            ) from exc

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

    Mutates the plain Event row (no join needed for that part), commits,
    then delegates to get_event_by_id_admin_repo for the enriched read —
    same pattern update_event_status_repo already uses below, instead of
    declaring the full admin join twice in this function just to read back
    what was written a moment earlier.
    """
    async with get_async_session() as session:
        stmt = select(Event).where(Event.id == event_id)
        event = await session.scalar(stmt)
        if not event:
            return None
        event.is_approved = True
        await session.commit()

    return await get_event_by_id_admin_repo(event_id)


async def reject_event_repo(event_id: int) -> Optional[AdminEventOut]:
    """
    Reject an event. Returns AdminEventOut (not bool) so the router can
    use event.title / event.slug for notifications.

    Note: is_active is a @property on the Event model (not a column), so
    it cannot be set directly. Setting is_approved=False is sufficient —
    is_active derives from is_approved + status + time window at read time.

    Same mutate-then-refetch pattern as approve_event_repo above.
    """
    async with get_async_session() as session:
        stmt = select(Event).where(Event.id == event_id)
        event = await session.scalar(stmt)
        if not event:
            return None
        event.is_approved = False
        await session.commit()

    return await get_event_by_id_admin_repo(event_id)


# ─── Admin queries (with joins + aggregates) ──────────────────────────────────

# ─── Admin queries (with joins + aggregates) ──────────────────────────────────

async def get_all_events_admin_repo() -> list[AdminEventOut]:
    """
    Return ALL events (approved and unapproved, all statuses) with organizer
    name and aggregated confirmed booking stats. Used by GET /admin/all-events.
    Admins have unrestricted visibility.
    """
    async with get_async_session() as session:
        stmt = _admin_events_stmt().order_by(Event.created_at.desc())
        rows = (await session.execute(stmt)).all()
        return [_admin_row_to_schema(row) for row in rows]


async def get_approved_events_admin_repo() -> list[AdminEventOut]:
    """Approved events only, with joins. Used by GET /admin/events.
    Admins see all statuses within approved events."""
    async with get_async_session() as session:
        stmt = (
            _admin_events_stmt()
            .where(Event.is_approved.is_(True))
            .order_by(Event.created_at.desc())
        )
        rows = (await session.execute(stmt)).all()
        return [_admin_row_to_schema(row) for row in rows]


async def get_unapproved_events_admin_repo() -> list[AdminEventOut]:
    """Unapproved events only, with joins."""
    async with get_async_session() as session:
        stmt = (
            _admin_events_stmt()
            .where(Event.is_approved.is_(False))
            .order_by(Event.created_at.desc())
        )
        rows = (await session.execute(stmt)).all()
        return [_admin_row_to_schema(row) for row in rows]


async def get_event_by_id_admin_repo(event_id: int) -> Optional[AdminEventOut]:
    """Single event with joins, for admin detail view. No status filter — admins see all."""
    async with get_async_session() as session:
        stmt = _admin_events_stmt().where(Event.id == event_id)
        row = (await session.execute(stmt)).one_or_none()
        return _admin_row_to_schema(row) if row else None


async def get_events_by_organizer_admin_repo(organizer_id: int) -> list[AdminEventOut]:
    """Events by a specific organizer, with joins. No status filter — admins see all."""
    async with get_async_session() as session:
        stmt = (
            _admin_events_stmt()
            .where(Event.organizer_id == organizer_id)
            .order_by(Event.created_at.desc())
        )
        rows = (await session.execute(stmt)).all()
        return [_admin_row_to_schema(row) for row in rows]


# ─── Organizer queries (with aggregates, no organizer name join needed) ───────

async def get_events_by_organizer_with_stats_repo(organizer_id: int) -> list[OrganizerEventOut]:
    """
    Organizer's own events with booking/revenue stats.

    Shows upcoming, ongoing, completed, cancelled, AND pending_deletion —
    but NOT plain deleted. The single `!= "deleted"` filter already covers
    this correctly: pending_deletion is a distinct status value from
    deleted, so it isn't excluded by this clause. It's deliberately kept
    visible here — pending_deletion means "this organizer asked to delete
    an event that still has bookings," and they need to keep seeing it
    while refunds are processed, rather than have it vanish the moment
    they hit delete. Plain 'deleted' (no bookings, safe to purge,
    admin-only) is the only status actually hidden from organizers.
    Used by GET /organizers/me/events.
    """
    async with get_async_session() as session:
        stmt = (
            select(
                Event,
                func.count(Booking.id).label("total_bookings"),
                func.coalesce(func.sum(Booking.total_price), 0).label("total_revenue"),
                _UNRESOLVED_BOOKINGS_COUNT,
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
    """
    Single event with stats for organizer detail view.
    No status filter — organizer needs to access any of their own events
    including cancelled ones (e.g. viewing stats after cancellation).
    """
    async with get_async_session() as session:
        stmt = (
            select(
                Event,
                func.count(Booking.id).label("total_bookings"),
                func.coalesce(func.sum(Booking.total_price), 0).label("total_revenue"),
                _UNRESOLVED_BOOKINGS_COUNT,
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
    """Approved upcoming/ongoing events — public facing. Excludes completed, cancelled, deleted."""
    async with get_async_session() as session:
        stmt = select(Event).where(
            Event.is_approved.is_(True),
            or_(Event.status == "upcoming", Event.status == "ongoing"),
        )
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(e) for e in events]


async def get_latest_events_repo(limit: int = 5) -> list[EventOut]:
    """Latest approved upcoming/ongoing events — public facing."""
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
    """Search approved upcoming/ongoing events by title — public facing."""
    async with get_async_session() as session:
        stmt = select(Event).where(
            Event.is_approved.is_(True),
            or_(Event.status == "upcoming", Event.status == "ongoing"),
            Event.title.ilike(f"%{keyword}%"),
        )
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(e) for e in events]


async def search_events_by_venue_repo(venue: str) -> list[EventOut]:
    """Search approved upcoming/ongoing events by venue — public facing."""
    async with get_async_session() as session:
        stmt = select(Event).where(
            Event.is_approved.is_(True),
            or_(Event.status == "upcoming", Event.status == "ongoing"),
            Event.venue.ilike(f"%{venue}%"),
        )
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(e) for e in events]


async def get_events_by_country_repo(country: str) -> list[EventOut]:
    """Get approved upcoming/ongoing events by country — public facing."""
    async with get_async_session() as session:
        stmt = select(Event).where(
            Event.is_approved.is_(True),
            or_(Event.status == "upcoming", Event.status == "ongoing"),
            Event.country.ilike(f"%{country}%"),
        )
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(e) for e in events]


async def get_events_in_date_range_repo(start_date: datetime, end_date: datetime) -> list[EventOut]:
    """Get approved upcoming/ongoing events within a date range — public facing."""
    async with get_async_session() as session:
        stmt = select(Event).where(
            Event.is_approved.is_(True),
            or_(Event.status == "upcoming", Event.status == "ongoing"),
            Event.start_time >= start_date,
            Event.end_time <= end_date,
        )
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(e) for e in events]


async def get_events_sorted_by_start_time_repo(ascending: bool = True) -> list[EventOut]:
    """Get approved upcoming/ongoing events sorted by start time — public facing."""
    async with get_async_session() as session:
        order = Event.start_time.asc() if ascending else Event.start_time.desc()
        stmt = select(Event).where(
            Event.is_approved.is_(True),
            or_(Event.status == "upcoming", Event.status == "ongoing"),
        ).order_by(order)
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(e) for e in events]


async def get_events_sorted_by_end_time_repo(ascending: bool = True) -> list[EventOut]:
    """Get approved upcoming/ongoing events sorted by end time — public facing."""
    async with get_async_session() as session:
        order = Event.end_time.asc() if ascending else Event.end_time.desc()
        stmt = select(Event).where(
            Event.is_approved.is_(True),
            or_(Event.status == "upcoming", Event.status == "ongoing"),
        ).order_by(order)
        events = (await session.scalars(stmt)).all()
        return [EventOut.model_validate(e) for e in events]


async def count_events_repo() -> int:
    """Count approved upcoming/ongoing events — public facing."""
    async with get_async_session() as session:
        stmt = select(func.count()).select_from(Event).where(
            Event.is_approved.is_(True),
            or_(Event.status == "upcoming", Event.status == "ongoing"),
        )
        return await session.scalar(stmt) or 0


# ─── Organizer count helpers ──────────────────────────────────────────────────

async def get_events_by_organizer_repo(organizer_id: int) -> list[EventOut]:
    """Raw list of an organizer's events excluding deleted. Used internally."""
    async with get_async_session() as session:
        stmt = select(Event).where(
            Event.organizer_id == organizer_id,
            Event.status != "deleted",
        )
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


# ─── Misc admin filters ───────────────────────────────────────────────────────
# These are admin-only endpoints so no status filter is applied —
# admins can query events of any status.

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