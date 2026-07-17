#!/usr/bin/env python3
# app/db/repositories/booking_repo.py
"""Async repository for Booking model operations."""

from datetime import datetime
from typing import Optional
from sqlalchemy import select, func
from app.db.session import get_async_session
from app.db.models.booking import Booking
from app.db.models.ticket_type import TicketType
from app.schemas.booking import BookingOut, BookingUpdate

# NOTE: Bookings are no longer created directly via this repo.
# order_repo.create_order_repo() creates Order + Booking rows together in
# one transaction (one Booking per ticket type line item). This keeps
# pricing validation, availability checks, and atomicity in one place.
# BookingCreate/create_booking_repo were removed — see order_repo.py.


async def get_booking_by_id_repo(booking_id: int) -> Optional[BookingOut]:
    """Retrieve a booking by its ID."""
    async with get_async_session() as session:
        booking = await session.get(Booking, booking_id)
        return BookingOut.model_validate(booking) if booking else None


async def get_bookings_by_ids_repo(ids: list[int]) -> list[BookingOut]:
    """Retrieve a list of bookings by their IDs."""
    async with get_async_session() as session:
        result = await session.execute(select(Booking).where(Booking.id.in_(ids)))
        bookings = result.scalars().all()
        return [BookingOut.model_validate(booking) for booking in bookings]


async def get_enriched_bookings_by_ids_repo(ids: list[int]) -> list:
    """
    Fetch enriched booking rows for a list of booking IDs.
    Joins User, Event, TicketType, and Order to resolve display fields.
    Includes order_id so the email service can reference the parent order.
    Used by organizer_emails_services.send_bulk_email_service.
    """
    from app.db.models.event import Event
    from app.db.models.user import User
    from app.db.models.order import Order

    async with get_async_session() as session:
        result = await session.execute(
            select(
                Booking,
                User.name.label("customer_name"),
                User.email.label("customer_email"),
                Event.title.label("event_title"),
                TicketType.name.label("ticket_type_name"),
                Event.venue,
                Event.start_time,
                Order.id.label("order_id"),
            )
            .join(User, Booking.user_id == User.id)
            .join(Event, Booking.event_id == Event.id)
            .join(TicketType, Booking.ticket_type_id == TicketType.id)
            .join(Order, Booking.order_id == Order.id)
            .where(Booking.id.in_(ids))
            .order_by(Booking.id)
        )

        rows = result.all()
        bookings = []
        for row in rows:
            booking = row[0]
            bookings.append(type('EnrichedBooking', (), {
                'id':               booking.id,
                'order_id':         row.order_id,
                'user_id':          booking.user_id,
                'event_id':         booking.event_id,
                'ticket_type_id':   booking.ticket_type_id,
                'customer_name':    row.customer_name,
                'customer_email':   row.customer_email,
                'event_title':      row.event_title,
                'ticket_type_name': row.ticket_type_name,
                'venue':            row.venue,
                'event_date':       row.start_time.strftime('%d %b %Y at %H:%M') if row.start_time else None,
                'quantity':         booking.quantity,
                'total_price':      booking.total_price,
                'status':           booking.status,
                'organizer_name':   None,  # not on Booking — caller passes organizer name separately
            })())
        return bookings


async def update_booking_repo(booking_id: int, booking_data: BookingUpdate) -> Optional[BookingOut]:
    """Update an existing booking."""
    async with get_async_session() as session:
        booking = await session.get(Booking, booking_id)
        if not booking:
            return None
        booking.quantity = booking_data.quantity
        booking.status = booking_data.status
        booking.total_price = booking_data.total_price
        await session.commit()
        await session.refresh(booking)
        return BookingOut.model_validate(booking)


async def update_booking_status_repo(booking_id: int, status: str) -> None:
    """Update only the status of a booking."""
    async with get_async_session() as session:
        booking = await session.get(Booking, booking_id)
        if not booking:
            return None
        booking.status = status
        await session.commit()


async def get_total_bookings_by_user_repo(user_id: int) -> int:
    """
    Count confirmed bookings for a user.

    Filtered to status == "confirmed" — cancelled and refunded bookings
    are no longer active bookings from the user's point of view, so they
    shouldn't inflate a "total bookings" figure. This matches the same
    convention applied to count_bookings_by_event_repo and
    count_bookings_by_organizer_repo below: "total_bookings" means
    confirmed bookings everywhere in this codebase now, consistently.
    Cancellation/refund counts, if ever needed as their own stat, should
    be a separately-named function — not folded into this one.
    """
    async with get_async_session() as session:
        result = await session.execute(
            select(func.count())
            .select_from(Booking)
            .where(Booking.user_id == user_id, Booking.status == "confirmed")
        )
        return result.scalar_one()


async def delete_booking_repo(booking_id: int) -> bool:
    """Delete a booking."""
    async with get_async_session() as session:
        booking = await session.get(Booking, booking_id)
        if not booking:
            return False
        await session.delete(booking)
        await session.commit()
        return True


async def list_bookings_by_event_id_repo(event_id: int) -> list[BookingOut]:
    async with get_async_session() as session:
        result = await session.execute(
            select(Booking).where(Booking.event_id == event_id)
        )
        return [BookingOut.model_validate(b) for b in result.scalars().all()]


async def list_bookings_repo() -> list[BookingOut]:
    async with get_async_session() as session:
        result = await session.execute(select(Booking))
        return [BookingOut.model_validate(b) for b in result.scalars().all()]


async def list_bookings_by_user_repo(user_id: int) -> list[BookingOut]:
    async with get_async_session() as session:
        result = await session.execute(
            select(Booking).where(Booking.user_id == user_id)
        )
        return [BookingOut.model_validate(b) for b in result.scalars().all()]


async def list_all_bookings_by_status_repo(status: str) -> list[BookingOut]:
    async with get_async_session() as session:
        result = await session.execute(
            select(Booking).where(Booking.status == status)
        )
        return [BookingOut.model_validate(b) for b in result.scalars().all()]


async def list_bookings_status_by_user_repo(user_id: int, status: str) -> list[BookingOut]:
    async with get_async_session() as session:
        result = await session.execute(
            select(Booking).where(Booking.user_id == user_id, Booking.status == status)
        )
        return [BookingOut.model_validate(b) for b in result.scalars().all()]


async def list_bookings_by_ticket_type_and_status_repo(ticket_type_id: int, status: str) -> list[BookingOut]:
    async with get_async_session() as session:
        result = await session.execute(
            select(Booking).where(
                Booking.ticket_type_id == ticket_type_id, Booking.status == status
            )
        )
        return [BookingOut.model_validate(b) for b in result.scalars().all()]


async def list_bookings_for_an_event_by_ticket_type_repo(event_id: int, ticket_type_id: int) -> list[BookingOut]:
    async with get_async_session() as session:
        result = await session.execute(
            select(Booking).where(
                Booking.event_id == event_id, Booking.ticket_type_id == ticket_type_id
            )
        )
        return [BookingOut.model_validate(b) for b in result.scalars().all()]


async def list_all_bookings_for_an_event_repo(event_id: int) -> list[BookingOut]:
    async with get_async_session() as session:
        result = await session.execute(
            select(Booking).where(Booking.event_id == event_id)
        )
        return [BookingOut.model_validate(b) for b in result.scalars().all()]


async def list_recent_bookings_by_event_repo(event_id: int, limit: int = 5) -> list[BookingOut]:
    async with get_async_session() as session:
        result = await session.execute(
            select(Booking)
            .where(Booking.event_id == event_id)
            .order_by(Booking.created_at.desc())
            .limit(limit)
        )
        return [BookingOut.model_validate(b) for b in result.scalars().all()]


async def list_recent_bookings_repo(limit: int = 10) -> list[BookingOut]:
    async with get_async_session() as session:
        result = await session.execute(
            select(Booking).order_by(Booking.created_at.desc()).limit(limit)
        )
        return [BookingOut.model_validate(b) for b in result.scalars().all()]


async def list_bookings_in_date_range_repo(start_date: datetime, end_date: datetime) -> list[BookingOut]:
    async with get_async_session() as session:
        result = await session.execute(
            select(Booking).where(
                Booking.created_at >= start_date, Booking.created_at <= end_date
            )
        )
        return [BookingOut.model_validate(b) for b in result.scalars().all()]


async def count_bookings_by_event_repo(event_id: int) -> int:
    """
    Count confirmed bookings for an event.

    Filtered to status == "confirmed" — cancelled and refunded bookings
    are no longer active bookings, so they shouldn't inflate this figure.
    Backs EventStats.total_bookings, which now means the same thing as
    OrganizerEventOut.total_bookings / AdminEventOut.total_bookings
    (event_repo.py's joined queries, already confirmed-only via their
    Booking outerjoin condition) — the two used to disagree before this
    change; they're now consistent everywhere "total_bookings" appears.

    If a cancellation/refund count is ever needed as its own organizer-
    facing stat, that should be a new, separately-named function — not
    folded back into this one.
    """
    async with get_async_session() as session:
        result = await session.execute(
            select(func.count())
            .select_from(Booking)
            .where(Booking.event_id == event_id, Booking.status == "confirmed")
        )
        return result.scalar_one()


async def count_unresolved_bookings_by_event_repo(event_id: int) -> int:
    """
    Count this event's bookings that still represent live, unresolved
    financial obligation — i.e. status NOT in ('cancelled', 'refunded').
    This includes 'pending' bookings (payment in flight, no Daraja
    callback yet), which is the key difference from
    count_bookings_by_event_repo above: that function is confirmed-only,
    so it would never catch a pending booking — but a pending booking
    absolutely should still block an event from being hard-deleted, since
    money may be about to change hands.

    Backs the event-deletion guard (event_services.
    update_event_status_service / confirm_event_deletion_ready_service),
    where the question is "is there still money at stake right now" — a
    cancelled booking never had money change hands, and a refunded
    booking has already had it returned, so neither should block a
    delete or keep an event stuck in pending_deletion.

    Current Booking.status values: pending, confirmed, cancelled,
    refunded (mirrors Order.status by design — see booking.py).
    """
    async with get_async_session() as session:
        result = await session.execute(
            select(func.count())
            .select_from(Booking)
            .where(Booking.event_id == event_id)
            .where(Booking.status.notin_(["cancelled", "refunded"]))
        )
        return result.scalar_one()


async def count_tickets_sold_by_event_id_repo(event_id: int) -> int:
    async with get_async_session() as session:
        result = await session.execute(
            select(func.sum(Booking.quantity))
            .select_from(Booking)
            .where(Booking.event_id == event_id, Booking.status == "confirmed")
        )
        total = result.scalar_one_or_none()
        return total if total else 0


async def get_total_revenue_by_event_id_repo(event_id: int) -> float:
    async with get_async_session() as session:
        result = await session.execute(
            select(func.sum(Booking.total_price))
            .select_from(Booking)
            .where(Booking.event_id == event_id, Booking.status == "confirmed")
        )
        total = result.scalar_one_or_none()
        return total if total else 0


async def count_bookings_by_organizer_repo(organizer_id: int) -> int:
    """
    Count confirmed bookings across all of an organizer's events.

    Filtered to status == "confirmed" — matches count_bookings_by_event_repo
    and get_total_bookings_by_user_repo above, and now also matches its own
    sibling count_tickets_sold_by_organizer_repo immediately below, which
    already had this filter. This function was the inconsistent one before
    this change (unfiltered, while its neighbour was confirmed-only) —
    now all three "total" counts in this module mean the same thing.
    """
    from app.db.models.event import Event
    async with get_async_session() as session:
        result = await session.execute(
            select(func.count())
            .select_from(Booking)
            .join(Event, Booking.event_id == Event.id)
            .where(Event.organizer_id == organizer_id, Booking.status == "confirmed")
        )
        return result.scalar_one()


async def count_tickets_sold_by_organizer_repo(organizer_id: int) -> int:
    from app.db.models.event import Event
    async with get_async_session() as session:
        result = await session.execute(
            select(func.sum(Booking.quantity))
            .select_from(Booking)
            .join(Event, Booking.event_id == Event.id)
            .where(Event.organizer_id == organizer_id, Booking.status == "confirmed")
        )
        total = result.scalar_one_or_none()
        return total if total else 0


async def calculate_revenue_by_organizer_repo(organizer_id: int) -> int:
    from app.db.models.event import Event
    async with get_async_session() as session:
        result = await session.execute(
            select(func.sum(Booking.total_price))
            .select_from(Booking)
            .join(Event, Booking.event_id == Event.id)
            .where(Event.organizer_id == organizer_id, Booking.status == "confirmed")
        )
        revenue = result.scalar_one_or_none()
        return revenue if revenue else 0


async def get_recent_bookings_by_organizer_repo(organizer_id: int, limit: int = 10) -> list:
    from app.db.models.event import Event
    from app.db.models.user import User

    async with get_async_session() as session:
        result = await session.execute(
            select(Booking, User.name, User.email, Event.title, TicketType.name)
            .join(Event, Booking.event_id == Event.id)
            .join(User, Booking.user_id == User.id)
            .join(TicketType, Booking.ticket_type_id == TicketType.id)
            .where(Event.organizer_id == organizer_id)
            .order_by(Booking.created_at.desc())
            .limit(limit)
        )

        bookings = []
        for booking, user_name, user_email, event_title, ticket_name in result:
            bookings.append({
                "id": booking.id,
                "user_id": booking.user_id,
                "order_id": booking.order_id,
                "event_id": booking.event_id,
                "ticket_type_id": booking.ticket_type_id,
                "customer_name": user_name,
                "customer_email": user_email,
                "event_title": event_title,
                "ticket_type_name": ticket_name,
                "quantity": booking.quantity,
                "total_price": booking.total_price,
                "status": booking.status,
                "created_at": booking.created_at,
                "updated_at": booking.updated_at,
            })
        return bookings


async def list_bookings_enriched_repo() -> list:
    """List all bookings with joined user, event, and ticket type data.
    Used by GET /admin/bookings to return AdminBooking-shaped rows."""
    from app.db.models.event import Event
    from app.db.models.user import User

    async with get_async_session() as session:
        result = await session.execute(
            select(Booking, User.name, User.email, Event.title,
                   TicketType.name, Event.venue, Event.start_time)
            .join(User, Booking.user_id == User.id)
            .join(Event, Booking.event_id == Event.id)
            .join(TicketType, Booking.ticket_type_id == TicketType.id)
            .order_by(Booking.created_at.desc())
        )
        bookings = []
        for booking, user_name, user_email, event_title, ticket_name, venue, start_time in result:
            bookings.append({
                'id': booking.id,
                'order_id': booking.order_id,
                'user_id': booking.user_id,
                'event_id': booking.event_id,
                'ticket_type_id': booking.ticket_type_id,
                'customer_name': user_name,
                'customer_email': user_email,
                'event_title': event_title,
                'ticket_type_name': ticket_name,
                'venue': venue,
                'event_date': start_time.isoformat() if start_time else None,
                'quantity': booking.quantity,
                'total_price': booking.total_price,
                'status': booking.status,
                'created_at': booking.created_at,
                'updated_at': booking.updated_at,
            })
        return bookings


async def list_event_bookings_enriched_repo(event_id: int) -> list:
    """List all bookings for an event with joined user and ticket type data.
    Used by organizer event booking endpoints."""
    from app.db.models.event import Event
    from app.db.models.user import User

    async with get_async_session() as session:
        result = await session.execute(
            select(Booking, User.name, User.email, Event.title,
                   TicketType.name, Event.venue, Event.start_time)
            .join(User, Booking.user_id == User.id)
            .join(Event, Booking.event_id == Event.id)
            .join(TicketType, Booking.ticket_type_id == TicketType.id)
            .where(Booking.event_id == event_id)
            .order_by(Booking.created_at.desc())
        )
        bookings = []
        for booking, user_name, user_email, event_title, ticket_name, venue, start_time in result:
            bookings.append({
                'id': booking.id,
                'order_id': booking.order_id,
                'user_id': booking.user_id,
                'event_id': booking.event_id,
                'ticket_type_id': booking.ticket_type_id,
                'customer_name': user_name,
                'customer_email': user_email,
                'event_title': event_title,
                'ticket_type_name': ticket_name,
                'venue': venue,
                'event_date': start_time.isoformat() if start_time else None,
                'quantity': booking.quantity,
                'total_price': booking.total_price,
                'status': booking.status,
                'created_at': booking.created_at,
                'updated_at': booking.updated_at,
            })
        return bookings