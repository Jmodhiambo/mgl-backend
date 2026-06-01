#!/usr/bin/env python3
"""Event services for MGLTickets."""

import asyncio
from datetime import datetime
from fastapi import HTTPException, status
import app.db.repositories.event_repo as event_repo
import app.db.repositories.booking_repo as booking_repo
import app.db.repositories.ticket_instance_repo as ti_repo
import app.db.repositories.ticket_type_repo as tt_repo

from app.schemas.event import EventStats, EventDetails
from app.schemas.event import EventCreateWithFlyer, EventUpdate

from app.core.logging_config import logger

async def create_event_service(event_data: EventCreateWithFlyer) -> dict:
    """Create a new event."""
    logger.info(f"Creating event: {event_data}")
    event = await event_repo.create_event_repo(event_data)
    logger.info(f"Created event with ID: {event.id}")
    return event

async def get_event_by_id_service(event_id: int) -> dict:
    """Retrieve an event by its ID."""
    logger.info(f"Retrieving event with ID: {event_id}")
    event = await event_repo.get_event_by_id_repo(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

async def get_event_by_slug_service(slug: str) -> dict:
    """Retrieve an event by its slug."""
    logger.info(f"Retrieving event with slug: {slug}")
    return await event_repo.get_event_by_slug_repo(slug)

async def update_event_service(event_id: int, event_data: EventUpdate) -> dict:
    """Update an event by its ID."""
    logger.info(f"Updating event with ID: {event_id}")
    event = await event_repo.update_event_repo(event_id, event_data)
    logger.info(f"Updated event with ID: {event.id}")
    return event

async def get_approved_events_service() -> list[dict]:
    """Retrieve all approved events."""
    logger.info("Retrieving approved events")
    return await event_repo.get_approved_events_repo()

async def get_unapproved_events_service() -> list[dict]:
    """Retrieve all unapproved events."""
    logger.info("Retrieving unapproved events")
    return await event_repo.get_unapproved_events_repo()

async def get_all_events_service() -> list[dict]:
    """Retrieve all events."""
    logger.info("Retrieving all events")
    return await event_repo.get_all_events_repo()

async def approve_event_service(event_id: int) -> dict:
    """Approve an event."""
    logger.info(f"Approving event with ID: {event_id}")
    return await event_repo.approve_event_repo(event_id)

async def reject_event_service(event_id: int) -> dict:
    """Reject an event."""
    logger.info(f"Rejecting event with ID: {event_id}")
    return await event_repo.reject_event_repo(event_id)

async def delete_event_service(event_id: int) -> None:
    """Delete an event."""
    logger.info(f"Deleting event with ID: {event_id}")
    return await event_repo.delete_event_repo(event_id)

async def update_event_status_service(event_id: int, status: str) -> dict:
    """Update the status of an event."""
    logger.info(f"Updating status of event with ID: {event_id} to {status.upper()}")
    return await event_repo.update_event_status_repo(event_id, status)

async def get_events_by_organizer_service(organizer_id: int) -> list[dict]:
    """Retrieve events by organizer ID."""
    logger.info(f"Retrieving events for organizer with ID: {organizer_id}")
    return await event_repo.get_events_by_organizer_repo(organizer_id)

async def get_events_in_date_range_service(start_date: datetime, end_date: datetime) -> list[dict]:
    """Retrieve events within a specific date range."""
    logger.info(f"Retrieving events from {start_date} to {end_date}")
    return await event_repo.get_events_in_date_range_repo(start_date, end_date)

async def search_events_by_title_service(title: str) -> list[dict]:
    """Search events by title."""
    logger.info(f"Searching events by title: {title}")
    return await event_repo.search_events_by_title_repo(title)

async def count_events_by_organizer_service(organizer_id: int) -> int:
    """Count events by organizer ID."""
    logger.info(f"Counting events for organizer with ID: {organizer_id}")
    return await event_repo.count_events_by_organizer_repo(organizer_id)

async def count_events_service() -> int:
    """Count total number of events."""
    logger.info("Counting total number of events")
    return await event_repo.count_events_repo()

async def get_latest_events_service(limit: int = 5) -> list[dict]:
    """Get the latest added events."""
    logger.info(f"Retrieving the latest {limit} events")
    return await event_repo.get_latest_events_repo(limit)

async def get_events_by_status_service(status: str) -> list[dict]:
    """Get events by their status."""
    logger.info(f"Retrieving events with status: {status.upper()}")
    return await event_repo.get_events_by_status_repo(status)

async def get_events_with_bookings_service() -> list[dict]:
    """Get all events that have bookings."""
    logger.info("Retrieving events with bookings")
    return await event_repo.get_events_with_bookings_repo()

async def get_events_without_bookings_service() -> list[dict]:
    """Get all events that do not have bookings."""
    logger.info("Retrieving events without bookings")
    return await event_repo.get_events_without_bookings_repo()

async def search_events_by_venue_service(venue: str) -> list[dict]:
    """Search events by venue."""
    logger.info(f"Searching events by venue: {venue.upper()}")
    return await event_repo.search_events_by_venue_repo(venue)

async def get_events_created_after_service(date: datetime) -> list[dict]:
    """Get events created after a specific date."""
    logger.info(f"Retrieving events created after {date}")
    return await event_repo.get_events_created_after_repo(date)

async def get_events_created_before_service(date: datetime) -> list[dict]:
    """Get events created before a specific date."""
    logger.info(f"Retrieving events created before {date}")
    return await event_repo.get_events_created_before_repo(date)

async def get_events_updated_after_service(date: datetime) -> list[dict]:
    """Get events updated after a specific date."""
    logger.info(f"Retrieving events updated after {date}")
    return await event_repo.get_events_updated_after_repo(date)

async def get_events_updated_before_service(date: datetime) -> list[dict]:
    """Get events updated before a specific date."""
    logger.info(f"Retrieving events updated before {date}")
    return await event_repo.get_events_updated_before_repo(date)

async def get_events_sorted_by_start_time_service(ascending: bool = True) -> list[dict]:
    """Get events sorted by start time."""
    logger.info("Retrieving events sorted by start time")
    return await event_repo.get_events_sorted_by_start_time_repo(ascending)

async def get_events_sorted_by_end_time_service(ascending: bool = True) -> list[dict]:
    """Get events sorted by end time."""
    logger.info("Retrieving events sorted by end time")
    return await event_repo.get_events_sorted_by_end_time_repo(ascending)

async def get_events_by_country_service(country: str) -> list[dict]:
    """Get events by country."""
    logger.info(f"Retrieving events in {country.upper()}")
    return await event_repo.get_events_by_country_repo(country)

"""Orgnanizer-specific services for MGLTickets."""
async def get_event_stats_service(event_id: int) -> EventStats:
    """Get event stats for a given event"""
    logger.info("Getting event stats", extra={"extra": {"event_id": event_id}})

    try:
        # Fetch all stats in parallel using asyncio.gather()
        (
            total_bookings,
            total_revenue,
            tickets_sold,
            total_available,
            total_sold
        ) = await asyncio.gather(
            booking_repo.count_bookings_by_event_repo(event_id),
            booking_repo.get_total_revenue_by_event_id_repo(event_id),
            booking_repo.count_tickets_sold_by_event_id_repo(event_id),
            tt_repo.count_available_tickets_by_event_repo(event_id),
            tt_repo.count_tickets_sold_by_event_id_repo(event_id)
        )

        tickets_remaining = total_available - total_sold

        stats = EventStats(
            total_bookings=total_bookings,
            total_revenue=total_revenue,
            tickets_sold=tickets_sold,
            tickets_remaining=tickets_remaining
        )

        logger.info(f"Event stats fetched", extra={"extra": {"event_id": event_id, "stats": stats}})
        return stats

    except Exception as e:
        logger.error(f"Error fetching event stats", extra={"extra": {"event_id": event_id, "error": str(e)}})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching event stats")


async def get_event_recent_bookings_service(event_id: int, limit: int = 5) -> list[dict]:
    """Service to list the most recent bookings for a specific event."""
    logger.info("Listing recent bookings by event", extra={"extra": {"event_id": event_id, "limit": limit}})
    return await booking_repo.list_recent_bookings_by_event_repo(event_id, limit)


async def get_event_details_service(event_id: int) -> EventDetails:
    """Get everything related to the event. Including event, stats. ticket types, recent bookings."""
    event = await event_repo.get_event_by_id_repo(event_id)

    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    
    try:
        # Fetch all details in parallel using asyncio.gather()
        (
            event_stats,
            ticket_types,
            recent_bookings
        ) = await asyncio.gather(
            get_event_stats_service(event_id),
            tt_repo.list_ticket_types_by_event_id_repo(event_id),
            get_event_recent_bookings_service(event_id)
        )

        details = EventDetails(
            event=event,
            stats=event_stats,
            ticket_types=ticket_types,
            recent_bookings=recent_bookings
        )

        logger.info(f"Event details fetched", extra={"extra": {"event_id": event_id, "details": details}})
        return details

    except Exception as e:
        logger.error(f"Error fetching event details", extra={"extra": {"event_id": event_id, "error": str(e)}})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching event details")
    

async def get_top_events_by_organizer_service(organizer_id: int, limit: int = 5) -> list[dict]:
    """Service to get the top events for an organizer by revenue."""
    logger.info("Getting top events by organizer", extra={"extra": {"organizer_id": organizer_id, "limit": limit}})
    return await event_repo.get_top_events_by_organizer_repo(organizer_id, limit)