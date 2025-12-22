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

async def list_recent_bookings_by_event_repo(event_id: int, limit: int = 10) -> list[BookingOut]:
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