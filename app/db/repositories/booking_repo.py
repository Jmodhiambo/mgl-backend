#!/usr/bin/env python3
"""Repository for Booking model operations."""

from datetime import datetime
from app.db.session import get_session
from typing import Optional
from app.db.models.booking import Booking
from app.schemas.booking import BookingOut, BookingCreate, BookingUpdate

def create_booking_repo(booking_data: BookingCreate) -> BookingOut:
    """Create a new booking in the database."""
    with get_session() as session:
        new_booking = Booking(
            user_id=booking_data.user_id,
            ticket_type_id=booking_data.ticket_type_id,
            quantity=booking_data.quantity,
            total_price=booking_data.total_price,
            status="pending"
        )
        session.add(new_booking)
        session.commit()
        session.refresh(new_booking)
        return BookingOut.model_validate(new_booking)

def get_booking_by_id_repo(booking_id: int) -> Optional[BookingOut]:
    """Retrieve a booking by its ID."""
    with get_session() as session:
        booking = session.get(Booking, booking_id)
        return BookingOut.model_validate(booking) if booking else None
    
def update_booking_repo(booking_id: int, booking_data: BookingUpdate) -> Optional[BookingOut]:
    """Update an existing booking in the database."""
    with get_session() as session:
        booking = session.get(Booking, booking_id)
        if not booking:
            return None
        booking.quantity = booking_data.quantity
        booking.status = booking_data.status
        booking.total_price = booking_data.total_price
        session.commit()
        session.refresh(booking)
        return BookingOut.model_validate(booking)
    
def update_booking_status_repo(booking_id: int, status: str) -> Optional[BookingOut]:
    """Update the status of an existing booking in the database."""
    with get_session() as session:
        booking = session.get(Booking, booking_id)
        if not booking:
            return None
        booking.status = status
        session.commit()
        session.refresh(booking)
        return BookingOut.model_validate(booking)
    
def delete_booking_repo(booking_id: int) -> bool:
    """Delete a booking from the database."""
    with get_session() as session:
        booking = session.get(Booking, booking_id)
        if not booking:
            return False
        session.delete(booking)
        session.commit()
        return True
    
def list_bookings_repo() -> list[BookingOut]:
    """List all bookings in the database."""
    with get_session() as session:
        bookings = session.query(Booking).all()
        return [BookingOut.model_validate(booking) for booking in bookings]
    
def list_bookings_by_user_repo(user_id: int) -> list[BookingOut]:
    """List all bookings for a specific user."""
    with get_session() as session:
        bookings = session.query(Booking).filter(Booking.user_id == user_id).all()
        return [BookingOut.model_validate(booking) for booking in bookings]
    
def list_all_bookings_by_status_repo(status: str) -> list[BookingOut]:
    """List all bookings with a specific status in the database."""
    with get_session() as session:
        bookings = session.query(Booking).filter(Booking.status == status).all()
        return [BookingOut.model_validate(booking) for booking in bookings]
    
def list_bookings_status_by_user_repo(user_id: int, status: str) -> list[BookingOut]:
    """List all bookings with a specific status for a specific user."""
    with get_session() as session:
        bookings = session.query(Booking).filter(Booking.user_id == user_id, Booking.status == status).all()
        return [BookingOut.model_validate(booking) for booking in bookings]
    
def list_bookings_by_ticket_type_and_status_repo(ticket_type_id: int, status: str) -> list[BookingOut]:
    """List all bookings with a specific status for a specific ticket type."""
    with get_session() as session:
        bookings = session.query(Booking).filter(Booking.ticket_type_id == ticket_type_id, Booking.status == status).all()
        return [BookingOut.model_validate(booking) for booking in bookings]
    
def list_recent_bookings_repo(limit: int = 10) -> list[BookingOut]:
    """List the most recent bookings in the database."""
    with get_session() as session:
        bookings = session.query(Booking).order_by(Booking.created_at.desc()).limit(limit).all()
        return [BookingOut.model_validate(booking) for booking in bookings]
    
def list_bookings_in_date_range_repo(start_date: datetime, end_date: datetime) -> list[BookingOut]:
    """List all bookings within a specific date range."""
    with get_session() as session:
        bookings = session.query(Booking).filter(Booking.created_at >= start_date, Booking.created_at <= end_date).all()
        return [BookingOut.model_validate(booking) for booking in bookings]