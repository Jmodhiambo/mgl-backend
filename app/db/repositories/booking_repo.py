#!/usr/bin/env python3
"""Async repository for Booking model operations."""

from datetime import datetime
from typing import Optional
from sqlalchemy import select, func
from app.db.session import get_async_session
from app.db.models.booking import Booking
from app.schemas.booking import BookingOut, BookingCreate, BookingUpdate


async def create_booking_repo(booking_data: BookingCreate) -> BookingOut:
    """Create a new booking in the database."""
    async with get_async_session() as session:
        new_booking = Booking(
            user_id=booking_data.user_id,
            ticket_type_id=booking_data.ticket_type_id,
            quantity=booking_data.quantity,
            total_price=booking_data.total_price,
            status="pending"
        )
        session.add(new_booking)
        await session.commit()
        await session.refresh(new_booking)
        return BookingOut.model_validate(new_booking)


async def get_booking_by_id_repo(booking_id: int) -> Optional[BookingOut]:
    """Retrieve a booking by its ID."""
    async with get_async_session() as session:
        booking = await session.get(Booking, booking_id)
        return BookingOut.model_validate(booking) if booking else None


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
    """Count total bookings for a user."""
    async with get_async_session() as session:
        result = await session.execute(
            select(func.count()).select_from(Booking).where(Booking.user_id == user_id)
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
    """List all bookings for a specific event."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Booking).where(Booking.event_id == event_id)
        )
        bookings = result.scalars().all()
        return [BookingOut.model_validate(booking) for booking in bookings]

async def list_bookings_repo() -> list[BookingOut]:
    """List all bookings."""
    async with get_async_session() as session:
        result = await session.execute(select(Booking))
        bookings = result.scalars().all()
        return [BookingOut.model_validate(booking) for booking in bookings]


async def list_bookings_by_user_repo(user_id: int) -> list[BookingOut]:
    """List all bookings for a specific user."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Booking).where(Booking.user_id == user_id)
        )
        bookings = result.scalars().all()
        return [BookingOut.model_validate(booking) for booking in bookings]


async def list_all_bookings_by_status_repo(status: str) -> list[BookingOut]:
    """List all bookings matching a specific status."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Booking).where(Booking.status == status)
        )
        bookings = result.scalars().all()
        return [BookingOut.model_validate(booking) for booking in bookings]


async def list_bookings_status_by_user_repo(user_id: int, status: str) -> list[BookingOut]:
    """List all bookings with a specific status for a user."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Booking).where(
                Booking.user_id == user_id,
                Booking.status == status
            )
        )
        bookings = result.scalars().all()
        return [BookingOut.model_validate(booking) for booking in bookings]


async def list_bookings_by_ticket_type_and_status_repo(ticket_type_id: int, status: str) -> list[BookingOut]:
    """List bookings for a ticket type with a given status."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Booking).where(
                Booking.ticket_type_id == ticket_type_id,
                Booking.status == status
            )
        )
        bookings = result.scalars().all()
        return [BookingOut.model_validate(booking) for booking in bookings]
    
async def list_bookings_for_an_event_by_ticket_type_repo(event_id: int, ticket_type_id: int) -> list[BookingOut]:
    """List bookings for a specific event and ticket type."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Booking).where(
                Booking.event_id == event_id,
                Booking.ticket_type_id == ticket_type_id
            )
        )
        bookings = result.scalars().all()
        return [BookingOut.model_validate(booking) for booking in bookings]
    
async def list_all_bookings_for_an_event_repo(event_id: int) -> list[BookingOut]:
    """List all bookings for a specific event."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Booking).where(Booking.event_id == event_id)
        )
        bookings = result.scalars().all()
        return [BookingOut.model_validate(booking) for booking in bookings]

async def list_recent_bookings_by_event_repo(event_id: int, limit: int = 5) -> list[BookingOut]:
    """List the most recent bookings for a specific event."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Booking).where(Booking.event_id == event_id).order_by(Booking.created_at.desc()).limit(limit)
        )
        bookings = result.scalars().all()
        return [BookingOut.model_validate(booking) for booking in bookings]

async def list_recent_bookings_repo(limit: int = 10) -> list[BookingOut]:
    """List the most recent bookings."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Booking).order_by(Booking.created_at.desc()).limit(limit)
        )
        bookings = result.scalars().all()
        return [BookingOut.model_validate(booking) for booking in bookings]


async def list_bookings_in_date_range_repo(start_date: datetime, end_date: datetime) -> list[BookingOut]:
    """List all bookings within a date range."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Booking).where(
                Booking.created_at >= start_date,
                Booking.created_at <= end_date
            )
        )
        bookings = result.scalars().all()
        return [BookingOut.model_validate(booking) for booking in bookings]
    

async def count_bookings_by_event_repo(event_id: int) -> int:
    """Count total bookings for an event."""
    async with get_async_session() as session:
        result = await session.execute(
            select(func.count())
            .select_from(Booking)
            .where(Booking.event_id == event_id)
        )
        return result.scalar_one()
    

async def count_tickets_sold_by_event_id_repo(event_id: int) -> int:
    """Count total tickets sold for an event."""
    async with get_async_session() as session:
        result = await session.execute(
            select(func.sum(Booking.quantity))
            .select_from(Booking)
            .where(Booking.event_id == event_id)
            .where(Booking.status == 'confirmed')
        )
        total = result.scalar_one_or_none()
        return total if total else 0
    

async def get_total_revenue_by_event_id_repo(event_id: int) -> float:
    """Get total revenue for an event."""
    async with get_async_session() as session:
        result = await session.execute(
            select(func.sum(Booking.total_price))
            .select_from(Booking)
            .where(Booking.event_id == event_id)
            .where(Booking.status == 'confirmed')
        )
        total = result.scalar_one_or_none()
        return total if total else 0


async def count_bookings_by_organizer_repo(organizer_id: int) -> int:
    """Count total bookings for all events by an organizer."""
    from app.db.models.event import Event
    
    async with get_async_session() as session:
        result = await session.execute(
            select(func.count())
            .select_from(Booking)
            .join(Event, Booking.event_id == Event.id)
            .where(Event.organizer_id == organizer_id)
        )
        return result.scalar_one()


async def count_tickets_sold_by_organizer_repo(organizer_id: int) -> int:
    """Count total tickets sold across all events by an organizer."""
    from app.db.models.event import Event
    
    async with get_async_session() as session:
        result = await session.execute(
            select(func.sum(Booking.quantity))
            .select_from(Booking)
            .join(Event, Booking.event_id == Event.id)
            .where(Event.organizer_id == organizer_id)
            .where(Booking.status == 'confirmed')
        )
        total = result.scalar_one_or_none()
        return total if total else 0


async def calculate_revenue_by_organizer_repo(organizer_id: int) -> int:
    """Calculate total revenue from confirmed bookings for an organizer."""
    from app.db.models.event import Event
    
    async with get_async_session() as session:
        result = await session.execute(
            select(func.sum(Booking.total_price))
            .select_from(Booking)
            .join(Event, Booking.event_id == Event.id)
            .where(Event.organizer_id == organizer_id)
            .where(Booking.status == 'confirmed')
        )
        revenue = result.scalar_one_or_none()
        return revenue if revenue else 0


async def get_recent_bookings_by_organizer_repo(organizer_id: int, limit: int = 10) -> list:
    """Get recent bookings across all organizer's events."""
    from app.db.models.event import Event
    from app.db.models.user import User
    from app.db.models.ticket_type import TicketType
    
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
            booking_dict = {
                'id': booking.id,
                'user_id': booking.user_id,
                'ticket_type_id': booking.ticket_type_id,
                'customer_name': user_name,
                'customer_email': user_email,
                'event_title': event_title,
                'ticket_type_name': ticket_name,
                'quantity': booking.quantity,
                'total_price': booking.total_price,
                'status': booking.status,
                'created_at': booking.created_at,
                'updated_at': booking.updated_at
            }
            bookings.append(booking_dict)
        
        return bookings