#!/usr/bin/env python3
"""Repository for CoOrganizer model operations."""

from typing import Optional
from sqlalchemy import select, delete, update, func
from sqlalchemy.orm import joinedload
from app.db.session import get_async_session
from app.db.models.co_organizer import CoOrganizer
from app.db.models.event import Event
from app.db.models.booking import Booking
from app.schemas.co_organizer import CoOrganizerOut, CoOrganizerWithUserAndEvent, CoOrganizerWithEvent
from app.schemas.event import OrganizerEventOut
from app.db.repositories.event_repo import _organizer_row_to_schema


_UNRESOLVED_BOOKINGS_COUNT = (
    select(func.count(Booking.id))
    .where(Booking.event_id == Event.id)
    .where(Booking.status.notin_(["cancelled", "refunded"]))
    .correlate(Event)
    .scalar_subquery()
    .label("unresolved_bookings_count")
)

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
    limit: Optional[int] = None,
    offset: int = 0,
) -> tuple[list[CoOrganizerWithUserAndEvent], int]:
    """
    Return enriched co-organizer rows via a single JOIN across
    CoOrganizer → User and CoOrganizer → Event, plus the total matching
    row count (ignoring limit/offset) so callers can build pagination.

    Calling conventions:
      • organizer_id only  → all co-organizers across that organizer's events
      • organizer_id + event_id → co-organizers for one event, ownership-scoped
      • event_id only      → admin mode: co-organizers for any event, no ownership filter

    The ownership boundary for organizer calls is enforced here by filtering on
    organizer_id; admin callers omit it and rely on require_admin at the router.

    limit/offset:
      • limit=None (the default) returns every matching row, unpaginated —
        this is what the admin caller uses today, so its behaviour is
        unchanged by this signature.
      • Passing an explicit limit applies LIMIT/OFFSET to the row query only;
        the count query always reflects the full matching set regardless of
        limit/offset, so `total` is stable across pages.

    Returns (items, total). Ordered newest-first (created_at desc, id desc
    as a tiebreaker) so pagination is stable even when multiple rows share
    a created_at timestamp.

    The schema is built inside the session context so the eagerly-loaded
    related objects are still accessible after execute().
    """
    async with get_async_session() as session:
        filters = []
        if organizer_id is not None:
            filters.append(CoOrganizer.organizer_id == organizer_id)
        if event_id is not None:
            filters.append(CoOrganizer.event_id == event_id)

        count_stmt = select(func.count(CoOrganizer.id))
        for f in filters:
            count_stmt = count_stmt.where(f)
        total = (await session.execute(count_stmt)).scalar_one()

        stmt = select(CoOrganizer).options(
            joinedload(CoOrganizer.user),
            joinedload(CoOrganizer.event),
        )
        for f in filters:
            stmt = stmt.where(f)
        stmt = stmt.order_by(CoOrganizer.created_at.desc(), CoOrganizer.id.desc())
        if limit is not None:
            stmt = stmt.limit(limit).offset(offset)

        result = await session.execute(stmt)
        rows = result.scalars().unique().all()
        items = [
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
        return items, total


async def get_user_co_organizing_events_with_details_repo(
    user_id: int,
) -> list[CoOrganizerWithEvent]:
    """
    Return all events a user is co-organizing, each bundled with the
    co-organizer relationship metadata AND the same aggregated booking/
    revenue stats organizers see for their own events (total_bookings,
    total_revenue, commission breakdown, etc.).

    Previously this joinedload'd CoOrganizer.event and validated it as a
    bare EventOut, which doesn't carry any stats fields at all — that's
    why My Events had nothing to show on co-organizing cards. The stats
    aggregation below is intentionally identical to
    get_events_by_organizer_with_stats_repo in event_repo.py (same join
    shape, same _organizer_row_to_schema mapper reused directly) so a
    co-organizer's numbers can never drift from what the actual organizer
    sees for the same event — one source of truth for the stats math
    instead of two similar-but-separate queries.

    Two queries rather than one: the CoOrganizer rows give the
    relationship metadata (invited_by, create_co_organizer, created_at),
    and a separate aggregated query keyed by event_id gives the stats.
    Folding CoOrganizer into that GROUP BY would work but blurs "co-organizer
    relationship query" with "event stats query" into one fragile
    statement — keeping them apart means the stats query stays a
    byte-for-byte match with the organizer's own.

    Orphaned records (event deleted but co-organizer row still exists) are
    silently skipped.
    """
    async with get_async_session() as session:
        co_rows = (
            await session.execute(
                select(CoOrganizer).where(CoOrganizer.user_id == user_id)
            )
        ).scalars().all()

        if not co_rows:
            return []

        event_ids = [row.event_id for row in co_rows]

        stats_stmt = (
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
            .where(Event.id.in_(event_ids))
            .group_by(Event.id)
        )
        stats_rows = (await session.execute(stats_stmt)).all()
        events_by_id: dict[int, OrganizerEventOut] = {
            row[0].id: _organizer_row_to_schema(row) for row in stats_rows
        }

        output: list[CoOrganizerWithEvent] = []
        for row in co_rows:
            event = events_by_id.get(row.event_id)
            if event is None:
                continue  # event deleted, skip orphan
            output.append(
                CoOrganizerWithEvent(
                    co_organizer_id=row.id,
                    invited_by=row.invited_by,
                    create_co_organizer=row.create_co_organizer,
                    created_at=row.created_at,
                    event=event,
                )
            )
        return output