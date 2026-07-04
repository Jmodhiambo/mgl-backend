#!/usr/bin/env python3
"""Async repository for TicketInstance model operations."""

from typing import Optional, List
from datetime import datetime, timezone

from sqlalchemy import select, update

from app.db.session import get_async_session
from app.db.models.ticket_instance import TicketInstance
from app.schemas.ticket_instance import (
    TicketInstanceOut,
    TicketInstanceCreate,
    TicketInstanceUpdate,
)


# ── Helper ────────────────────────────────────────────────────────────────────

def _build_out(ti: TicketInstance) -> TicketInstanceOut:
    """Build TicketInstanceOut from an ORM row.
    qr_payload is computed here from the row's own event_id — no join needed
    now that event_id is a first-class column on ticket_instances."""
    from app.core.ticket_signing import build_ticket_qr_payload

    return TicketInstanceOut(
        id=ti.id,
        booking_id=ti.booking_id,
        event_id=ti.event_id,
        ticket_type_id=ti.ticket_type_id,
        user_id=ti.user_id,
        code=ti.code,
        qr_payload=build_ticket_qr_payload(ti.code, ti.id, ti.event_id),
        status=ti.status,
        price=ti.price,
        issued_to=ti.issued_to,
        created_at=ti.created_at,
        updated_at=ti.updated_at,
        used_at=ti.used_at,
    )


# ── CRUD ──────────────────────────────────────────────────────────────────────

async def create_ticket_instance_repo(
    ticket_instance_create: TicketInstanceCreate,
) -> TicketInstanceOut:
    """Create a new TicketInstance and return it with its computed qr_payload.

    Flushes first to get the auto-assigned id (needed for qr_payload
    signing), then commits. The qr_payload is NOT stored — it is
    recomputed on every read by _build_out(), keeping schema migrations
    out of this feature entirely.
    """
    async with get_async_session() as session:
        ti = TicketInstance(
            booking_id=ticket_instance_create.booking_id,
            event_id=ticket_instance_create.event_id,
            ticket_type_id=ticket_instance_create.ticket_type_id,
            user_id=ticket_instance_create.user_id,
            price=ticket_instance_create.price,
            code=ticket_instance_create.code,
            status=ticket_instance_create.status or "issued",
            issued_to=ticket_instance_create.issued_to,
        )
        session.add(ti)
        await session.flush()    # assigns ti.id
        await session.refresh(ti)
        await session.commit()
        await session.refresh(ti)
        return _build_out(ti)


async def get_ticket_instance_by_id_repo(
    ticket_instance_id: int,
) -> Optional[TicketInstanceOut]:
    """Retrieve a TicketInstance by its ID."""
    async with get_async_session() as session:
        ti = await session.get(TicketInstance, ticket_instance_id)
        if not ti:
            return None
        return _build_out(ti)


async def update_ticket_instance_repo(
    ticket_instance_id: int,
    ticket_instance_update: TicketInstanceUpdate,
) -> Optional[TicketInstanceOut]:
    """Update an existing TicketInstance."""
    async with get_async_session() as session:
        ti = await session.get(TicketInstance, ticket_instance_id)
        if not ti:
            return None

        for field, value in ticket_instance_update.model_dump(exclude_unset=True).items():
            setattr(ti, field, value)

        session.add(ti)
        await session.commit()
        await session.refresh(ti)
        return _build_out(ti)


async def delete_ticket_instance_repo(ticket_instance_id: int) -> bool:
    """Delete a TicketInstance by its ID."""
    async with get_async_session() as session:
        ti = await session.get(TicketInstance, ticket_instance_id)
        if not ti:
            return False
        await session.delete(ti)
        await session.commit()
        return True


async def list_ticket_instances_repo() -> List[TicketInstanceOut]:
    """List all TicketInstances (admin use)."""
    async with get_async_session() as session:
        result = await session.execute(select(TicketInstance))
        return [_build_out(ti) for ti in result.scalars().all()]


async def list_ticket_instances_in_date_range_repo(
    start_date: str,
    end_date: str,
) -> List[TicketInstanceOut]:
    """List TicketInstances created within a date range."""
    async with get_async_session() as session:
        result = await session.execute(
            select(TicketInstance).where(
                TicketInstance.created_at >= start_date,
                TicketInstance.created_at <= end_date,
            )
        )
        return [_build_out(ti) for ti in result.scalars().all()]


async def get_ticket_instances_by_user_repo(
    user_id: int,
) -> List[TicketInstanceOut]:
    """List TicketInstances for a specific user (plain, no event enrichment)."""
    async with get_async_session() as session:
        result = await session.execute(
            select(TicketInstance).where(TicketInstance.user_id == user_id)
        )
        return [_build_out(ti) for ti in result.scalars().all()]


async def get_ticket_instances_by_status_repo(
    status: str,
) -> List[TicketInstanceOut]:
    """List TicketInstances filtered by status."""
    async with get_async_session() as session:
        result = await session.execute(
            select(TicketInstance).where(TicketInstance.status == status)
        )
        return [_build_out(ti) for ti in result.scalars().all()]


async def get_ticket_instance_by_seat_number_repo(
    seat_number: str,
) -> Optional[TicketInstanceOut]:
    """Retrieve a TicketInstance by seat number."""
    async with get_async_session() as session:
        result = await session.execute(
            select(TicketInstance).where(TicketInstance.seat_number == seat_number)
        )
        ti = result.scalars().first()
        return _build_out(ti) if ti else None


# ── Enriched query for MyTickets.tsx ─────────────────────────────────────────

async def get_ticket_instances_by_user_enriched_repo(user_id: int) -> list:
    """
    List ticket instances for a user with event and ticket type display context.
    Returns the enriched shape MyTickets.tsx and Dashboard expect.

    Now that event_id lives directly on TicketInstance, the only join
    needed is Event (for title/venue/start_time) and TicketType (for name).
    The booking join is gone — one less table in the query.
    """
    from app.db.models.event import Event
    from app.db.models.ticket_type import TicketType
    from app.core.ticket_signing import build_ticket_qr_payload

    async with get_async_session() as session:
        result = await session.execute(
            select(
                TicketInstance,
                Event.title,
                Event.venue,
                Event.start_time,
                TicketType.name,
            )
            .join(Event, TicketInstance.event_id == Event.id)
            .join(TicketType, TicketInstance.ticket_type_id == TicketType.id)
            .where(TicketInstance.user_id == user_id)
            .order_by(TicketInstance.created_at.desc())
        )
        instances = []
        for ti, event_title, venue, start_time, ticket_type_name in result:
            instances.append({
                'id': ti.id,
                'booking_id': ti.booking_id,
                'event_id': ti.event_id,
                'ticket_type_id': ti.ticket_type_id,
                'user_id': ti.user_id,
                'code': ti.code,
                'qr_payload': build_ticket_qr_payload(ti.code, ti.id, ti.event_id),
                'status': ti.status,
                'price': ti.price,
                'issued_to': ti.issued_to,
                'created_at': ti.created_at,
                'updated_at': ti.updated_at,
                'used_at': ti.used_at,
                'event_title': event_title,
                'venue': venue,
                'event_date': start_time.isoformat() if start_time else None,
                'ticket_type_name': ticket_type_name,
            })
        return instances


# ── Atomic check-in ───────────────────────────────────────────────────────────

async def check_in_ticket_instance_repo(
    ticket_instance_id: int,
    code: str,
) -> dict:
    """
    Attempt to check in (mark 'used') a single ticket instance atomically.

    The WHERE clause includes status == 'issued' so the database enforces
    the double-scan constraint: only one concurrent UPDATE can match — the
    second sees 0 rows affected and is rejected. No separate SELECT precedes
    the UPDATE (a read-then-write would have a race window).

    `code` is checked alongside `id` as depth-in-defence: a leaked numeric
    id can't be replayed without the matching code.

    Now that event_id is on TicketInstance directly, the context join only
    needs Event and TicketType — no Booking join for event resolution.
    """
    from app.db.models.event import Event
    from app.db.models.ticket_type import TicketType

    async with get_async_session() as session:
        # Atomic conditional update — the entire double-scan defence
        result = await session.execute(
            update(TicketInstance)
            .where(
                TicketInstance.id == ticket_instance_id,
                TicketInstance.code == code,
                TicketInstance.status == "issued",
            )
            .values(status="used", used_at=datetime.now(timezone.utc))
            .returning(TicketInstance)
        )
        updated = result.scalar_one_or_none()
        await session.commit()

        if updated is not None:
            ctx = await _fetch_checkin_context(session, updated)
            return {
                "outcome": "accepted",
                "ticket_instance_id": updated.id,
                "code": updated.code,
                **ctx,
                "holder_name": updated.issued_to,
                "first_used_at": None,
            }

        # 0 rows affected — find out why
        existing = await session.scalar(
            select(TicketInstance).where(
                TicketInstance.id == ticket_instance_id,
                TicketInstance.code == code,
            )
        )

        if existing is None:
            return {
                "outcome": "not_found",
                "ticket_instance_id": None,
                "code": None,
                "event_id": None,
                "event_title": None,
                "ticket_type_name": None,
                "holder_name": None,
                "first_used_at": None,
            }

        ctx = await _fetch_checkin_context(session, existing)
        outcome = "already_used" if existing.status == "used" else "cancelled"
        return {
            "outcome": outcome,
            "ticket_instance_id": existing.id,
            "code": existing.code,
            **ctx,
            "holder_name": existing.issued_to,
            "first_used_at": existing.used_at,
        }


async def _fetch_checkin_context(session, ti: TicketInstance) -> dict:
    """Resolve event and ticket type display info for a check-in result.
    Uses ti.event_id directly — no booking join required."""
    from app.db.models.event import Event
    from app.db.models.ticket_type import TicketType

    row = await session.execute(
        select(Event.id, Event.title, TicketType.name)
        .where(Event.id == ti.event_id)
        .join(TicketType, TicketType.id == ti.ticket_type_id)
    )
    ctx = row.one_or_none()
    if ctx is None:
        return {"event_id": ti.event_id, "event_title": None, "ticket_type_name": None}
    event_id, event_title, ticket_type_name = ctx
    return {
        "event_id": event_id,
        "event_title": event_title,
        "ticket_type_name": ticket_type_name,
    }