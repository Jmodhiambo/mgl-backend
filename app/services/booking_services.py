#!/usr/bin/env python3
"""Booking services for MGLTickets."""

from datetime import datetime

from app.core.logging_config import logger
import app.db.repositories.booking_repo as booking_repo
from app.schemas.booking import BookingCreate, BookingUpdate
from typing import Optional

async def create_booking_service(booking_data: BookingCreate) -> dict:
    """Service to create a new booking."""
    logger.info("Creating a new booking")
    booking = await booking_repo.create_booking_repo(booking_data)
    logger.info(f"Created booking with ID: {booking.id}")
    return booking

async def get_booking_by_id_service(booking_id: int) -> Optional[dict]:
    """Service to retrieve a booking by its ID."""
    logger.info("Retrieving booking by ID", extra={"extra": {"booking_id": booking_id}})
    booking = await booking_repo.get_booking_by_id_repo(booking_id)
    if booking:
        logger.info(f"Retrieved booking: {booking}")
    else:
        logger.warning(f"Booking with ID {booking_id} not found")
    return booking

async def update_booking_service(booking_id: int, booking_data: BookingUpdate) -> Optional[dict]:
    """Service to update an existing booking."""
    logger.info("Updating booking", extra={"extra": {"booking_id": booking_id}})
    booking = await booking_repo.update_booking_repo(booking_id, booking_data)
    if booking:
        logger.info(f"Updated booking: {booking}")
    else:
        logger.warning(f"Booking with ID {booking_id} not found for update")
    return booking

async def update_booking_status_service(booking_id: int, status: str) -> None:
    """Service to update the status of an existing booking."""
    logger.info("Updating booking status", extra={"extra": {"booking_id": booking_id}})
    await booking_repo.update_booking_status_repo(booking_id, status)

    # Retrieve the updated booking for logging
    booking = await booking_repo.get_booking_by_id_repo(booking_id)
    if booking.status == status:
        logger.info(f"Updated booking status: {booking}")
    else:
        logger.warning(f"Status update for booking ID {booking_id} failed")
        raise ValueError("Booking update failed for booking with ID {booking_id}")
    
async def get_total_bookings_by_user_service(user_id: int) -> int:
    """Service to get the total number of bookings for a specific user."""
    logger.info("Getting total bookings for user", extra={"extra": {"user_id": user_id}})
    total = await booking_repo.get_total_bookings_by_user_repo(user_id)
    logger.info(f"Total bookings for user {user_id}: {total}")
    return total

async def delete_booking_service(booking_id: int) -> bool:
    """Service to delete a booking."""
    logger.info("Deleting booking", extra={"extra": {"booking_id": booking_id}})
    booking = await booking_repo.delete_booking_repo(booking_id)
    if booking:
        logger.info(f"Deleted booking with ID: {booking_id}")
    else:
        logger.warning(f"Booking with ID {booking_id} not found for deletion")
    return booking

async def list_bookings_by_event_id_service(event_id: int) -> list[dict]:
    """Service to list all bookings for a specific event."""
    logger.info("Listing bookings by event", extra={"extra": {"event_id": event_id}})
    return await booking_repo.list_bookings_by_event_id_repo(event_id)

async def list_bookings_service() -> list[dict]:
    """Service to list all bookings."""
    logger.info("Listing all bookings")
    booking = await booking_repo.list_bookings_repo()
    return booking

async def list_bookings_by_user_service(user_id: int) -> list[dict]:
    """Service to list all bookings for a specific user."""
    logger.info("Listing bookings for user", extra={"extra": {"user_id": user_id}})
    return await booking_repo.list_bookings_by_user_repo(user_id)

async def list_bookings_by_status_service(status: str) -> list[dict]:
    """Service to list all bookings with a specific status."""
    logger.info("Listing bookings by status", extra={"extra": {"status": status}})
    return await booking_repo.list_all_bookings_by_status_repo(status)

async def list_bookings_status_by_user_service(user_id: int, status: str) -> list[dict]:
    """Service to list all bookings for a specific user with a specific status."""
    logger.info("Listing bookings by user and status", extra={"extra": {"user_id": user_id, "status": status}})
    return await booking_repo.list_bookings_status_by_user_repo(user_id, status)

async def list_bookings_by_ticket_type_and_status_service(ticket_type_id: int, status: str) -> list[dict]:
    """Service to list all bookings for a specific ticket type."""
    logger.info("Listing bookings by ticket type", extra={"extra": {"ticket_type_id": ticket_type_id}})
    return await booking_repo.list_bookings_by_ticket_type_and_status_repo(ticket_type_id, status)

async def list_bookings_for_an_event_by_ticket_type_service(event_id: int, ticket_type_id: int) -> list[dict]:
    """Service to list all bookings for a specific event and ticket type."""
    logger.info("Listing bookings by event and ticket type", extra={"extra": {"event_id": event_id, "ticket_type_id": ticket_type_id}})
    return await booking_repo.list_bookings_for_an_event_by_ticket_type_repo(event_id, ticket_type_id)

async def list_all_bookings_for_an_event_service(event_id: int) -> list[dict]:
    """Service to list all bookings for a specific event."""
    logger.info("Listing all bookings for an event", extra={"extra": {"event_id": event_id}})
    return await booking_repo.list_all_bookings_for_an_event_repo(event_id)

async def  list_recent_bookings_by_event_service(event_id: int, limit: int = 10) -> list[dict]:
    """Service to list the most recent bookings for a specific event."""
    logger.info("Listing recent bookings by event", extra={"extra": {"event_id": event_id, "limit": limit}})
    return await booking_repo.list_recent_bookings_by_event_repo(event_id, limit)

async def list_recent_bookings_service(limit: int = 10) -> list[dict]:
    """Service to list recent bookings."""
    logger.info("Listing recent bookings", extra={"extra": {"limit": limit}})
    return await booking_repo.list_recent_bookings_repo(limit)

async def list_bookings_in_date_range_service(start_date: datetime, end_date: datetime) -> list[dict]:
    """Service to list bookings within a specific date range."""
    logger.info("Listing bookings in date range", extra={"extra": {"start_date": start_date, "end_date": end_date}})
    return await booking_repo.list_bookings_in_date_range_repo(start_date, end_date)

async def get_recent_bookings_by_organizer_service(organizer_id: int, limit: int = 10) -> list[dict]:
    """Service to list the most recent bookings for a specific organizer."""
    logger.info("Listing recent bookings by organizer", extra={"extra": {"organizer_id": organizer_id, "limit": limit}})
    return await booking_repo.get_recent_bookings_by_organizer_repo(organizer_id, limit)