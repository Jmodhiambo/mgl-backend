#!/usr/bin/env python3
"""Event services for MGLTickets."""

import app.db.repositories.event_repo as event_repo
from app.schemas.event import EventCreateWithFlyer, EventUpdate
from datetime import datetime
from app.core.logging_config import logger

async def create_event_service(event_data: EventCreateWithFlyer) -> dict:
    """Create a new event."""
    logger.info(f"Creating event: {event_data}")
    event = event_repo.create_event_repo(event_data)
    logger.info(f"Created event with ID: {event.id}")
    return event

async def update_event_service(event_id: int, event_data: EventUpdate) -> dict:
    """Update an event by its ID."""
    logger.info(f"Updating event with ID: {event_id}")
    event = event_repo.update_event_repo(event_id, event_data)
    logger.info(f"Updated event with ID: {event.id}")
    return event

async def get_approved_events_service() -> list[dict]:
    """Retrieve all approved events."""
    logger.info("Retrieving approved events")
    return event_repo.get_approved_events_repo()

async def get_unapproved_events_service() -> list[dict]:
    """Retrieve all unapproved events."""
    logger.info("Retrieving unapproved events")
    return event_repo.get_unapproved_events_repo()

async def get_all_events_service() -> list[dict]:
    """Retrieve all events."""
    logger.info("Retrieving all events")
    return event_repo.get_all_events_repo()

async def get_event_by_id_service(event_id: int) -> dict:
    """Retrieve an event by its ID."""
    logger.info(f"Retrieving event with ID: {event_id}")
    return event_repo.get_event_by_id_repo(event_id)

async def approve_event_service(event_id: int) -> dict:
    """Approve an event."""
    logger.info(f"Approving event with ID: {event_id}")
    return event_repo.approve_event_repo(event_id)

async def reject_event_service(event_id: int) -> dict:
    """Reject an event."""
    logger.info(f"Rejecting event with ID: {event_id}")
    return event_repo.reject_event_repo(event_id)

async def delete_event_service(event_id: int) -> None:
    """Delete an event."""
    logger.info(f"Deleting event with ID: {event_id}")
    return event_repo.delete_event_repo(event_id)

async def update_event_status_service(event_id: int, status: str) -> dict:
    """Update the status of an event."""
    logger.info(f"Updating status of event with ID: {event_id} to {status.upper()}")
    return event_repo.update_event_status_repo(event_id, status)

async def get_events_by_organizer_service(organizer_id: int) -> list[dict]:
    """Retrieve events by organizer ID."""
    logger.info(f"Retrieving events for organizer with ID: {organizer_id}")
    return event_repo.get_events_by_organizer_repo(organizer_id)

async def get_events_in_date_range_service(start_date: datetime, end_date: datetime) -> list[dict]:
    """Retrieve events within a specific date range."""
    logger.info(f"Retrieving events from {start_date} to {end_date}")
    return event_repo.get_events_in_date_range_repo(start_date, end_date)

async def search_events_by_title_service(title: str) -> list[dict]:
    """Search events by title."""
    logger.info(f"Searching events by title: {title}")
    return event_repo.search_events_by_title_repo(title)

async def count_events_by_organizer_service(organizer_id: int) -> int:
    """Count events by organizer ID."""
    logger.info(f"Counting events for organizer with ID: {organizer_id}")
    return event_repo.count_events_by_organizer_repo(organizer_id)

async def count_events_service() -> int:
    """Count total number of events."""
    logger.info("Counting total number of events")
    return event_repo.count_events_repo()

async def get_latest_events_service(limit: int = 5) -> list[dict]:
    """Get the latest added events."""
    logger.info(f"Retrieving the latest {limit} events")
    return event_repo.get_latest_events_repo(limit)

async def get_events_by_status_service(status: str) -> list[dict]:
    """Get events by their status."""
    logger.info(f"Retrieving events with status: {status.upper()}")
    return event_repo.get_events_by_status_repo(status)

async def get_events_with_bookings_service() -> list[dict]:
    """Get all events that have bookings."""
    logger.info("Retrieving events with bookings")
    return event_repo.get_events_with_bookings_repo()

async def get_events_without_bookings_service() -> list[dict]:
    """Get all events that do not have bookings."""
    logger.info("Retrieving events without bookings")
    return event_repo.get_events_without_bookings_repo()

async def search_events_by_venue_service(venue: str) -> list[dict]:
    """Search events by venue."""
    logger.info(f"Searching events by venue: {venue.upper()}")
    return event_repo.search_events_by_venue_repo(venue)

async def get_events_created_after_service(date: datetime) -> list[dict]:
    """Get events created after a specific date."""
    logger.info(f"Retrieving events created after {date}")
    return event_repo.get_events_created_after_repo(date)

async def get_events_created_before_service(date: datetime) -> list[dict]:
    """Get events created before a specific date."""
    logger.info(f"Retrieving events created before {date}")
    return event_repo.get_events_created_before_repo(date)

async def get_events_updated_after_service(date: datetime) -> list[dict]:
    """Get events updated after a specific date."""
    logger.info(f"Retrieving events updated after {date}")
    return event_repo.get_events_updated_after_repo(date)

async def get_events_updated_before_service(date: datetime) -> list[dict]:
    """Get events updated before a specific date."""
    logger.info(f"Retrieving events updated before {date}")
    return event_repo.get_events_updated_before_repo(date)

async def get_events_sorted_by_start_time_service(ascending: bool = True) -> list[dict]:
    """Get events sorted by start time."""
    logger.info("Retrieving events sorted by start time")
    return event_repo.get_events_sorted_by_start_time_repo(ascending)

async def get_events_sorted_by_end_time_service(ascending: bool = True) -> list[dict]:
    """Get events sorted by end time."""
    logger.info("Retrieving events sorted by end time")
    return event_repo.get_events_sorted_by_end_time_repo(ascending)

async def get_events_by_country_service(country: str) -> list[dict]:
    """Get events by country."""
    logger.info(f"Retrieving events in {country.upper()}")
    return event_repo.get_events_by_country_repo(country)