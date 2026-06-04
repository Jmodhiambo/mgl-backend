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


# ─────────────────────────────────────────────────────────────────────────────
# CREATION
# ─────────────────────────────────────────────────────────────────────────────

async def create_event_service(event_data: EventCreateWithFlyer):
    """
    Create a new event and return AdminEventOut.

    Why AdminEventOut?
    - create_event_repo returns bare EventOut missing city, country, category,
      is_approved, is_active, total_bookings, total_revenue, organizer_name.
    - Both admin and organizer routers call this service, so we return the
      richest common type: AdminEventOut (superset of OrganizerEventOut).
    - FastAPI serialises only the fields declared on the router's response_model,
      so organizer callers never see organizer_name even though it is present.
    - For a brand-new event total_bookings/total_revenue are 0 — correct.
    """
    logger.info(f"Creating event: {event_data.title!r}")
    base = await event_repo.create_event_repo(event_data)
    logger.info(f"Created event with ID: {base.id} — re-fetching as AdminEventOut")
    full = await event_repo.get_event_by_id_admin_repo(base.id)
    if not full:
        # Should never happen — we just inserted the row
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Event created but could not be retrieved.",
        )
    return full


# ─────────────────────────────────────────────────────────────────────────────
# BASIC CRUD
# ─────────────────────────────────────────────────────────────────────────────

async def get_event_by_id_service(event_id: int):
    """Retrieve a public EventOut by ID."""
    logger.info(f"Retrieving event with ID: {event_id}")
    event = await event_repo.get_event_by_id_repo(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


async def get_event_by_slug_service(slug: str):
    """Retrieve a public EventOut by slug."""
    logger.info(f"Retrieving event with slug: {slug}")
    return await event_repo.get_event_by_slug_repo(slug)

async def get_event_by_id_admin_service(event_id: int):
    """Retrieve a single event as AdminEventOut (with organizer name + stats)."""
    logger.info(f"Retrieving admin event with ID: {event_id}")
    event = await event_repo.get_event_by_id_admin_repo(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


async def get_event_by_slug_admin_service(slug: str):
    """Retrieve a single event by slug as AdminEventOut."""
    logger.info(f"Retrieving admin event with slug: {slug}")
    event = await event_repo.get_event_by_slug_repo(slug)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    # Re-fetch via admin repo to get organizer name + stats
    return await event_repo.get_event_by_id_admin_repo(event.id)


async def get_events_by_organizer_admin_service(organizer_id: int):
    """Retrieve events for a specific organizer as AdminEventOut list."""
    logger.info(f"Retrieving admin events for organizer ID: {organizer_id}")
    return await event_repo.get_events_by_organizer_admin_repo(organizer_id)


async def update_event_service(event_id: int, event_data: EventUpdate):
    """
    Update an event and return OrganizerEventOut.
    update_event_repo returns bare EventOut — re-fetch via the organizer
    repo so the response includes stats and approval fields.
    """
    logger.info(f"Updating event with ID: {event_id}")
    updated = await event_repo.update_event_repo(event_id, event_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Event not found")
    logger.info(f"Updated event with ID: {updated.id} — re-fetching as OrganizerEventOut")
    return await event_repo.get_event_by_id_organizer_repo(updated.id)


async def delete_event_service(event_id: int):
    """Delete an event."""
    logger.info(f"Deleting event with ID: {event_id}")
    return await event_repo.delete_event_repo(event_id)


async def update_event_status_service(event_id: int, new_status: str):
    """Update the status of an event."""
    logger.info(f"Updating status of event ID {event_id} to {new_status.upper()}")
    return await event_repo.update_event_status_repo(event_id, new_status)


# ─────────────────────────────────────────────────────────────────────────────
# APPROVAL
# ─────────────────────────────────────────────────────────────────────────────

async def approve_event_service(event_id: int):
    """Approve an event."""
    logger.info(f"Approving event with ID: {event_id}")
    return await event_repo.approve_event_repo(event_id)


async def reject_event_service(event_id: int):
    """Reject an event."""
    logger.info(f"Rejecting event with ID: {event_id}")
    return await event_repo.reject_event_repo(event_id)


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN LIST QUERIES  (return AdminEventOut / plain EventOut)
# ─────────────────────────────────────────────────────────────────────────────

async def get_approved_events_service():
    """Retrieve all approved events."""
    logger.info("Retrieving approved events")
    return await event_repo.get_approved_events_admin_repo()


async def get_unapproved_events_service():
    """Retrieve all unapproved events."""
    logger.info("Retrieving unapproved events")
    return await event_repo.get_unapproved_events_admin_repo()


async def get_all_events_service():
    """Retrieve all events (approved + unapproved) with admin join data."""
    logger.info("Retrieving all events")
    return await event_repo.get_all_events_admin_repo()


# ─────────────────────────────────────────────────────────────────────────────
# ORGANIZER LIST QUERIES  (return OrganizerEventOut with stats)
# ─────────────────────────────────────────────────────────────────────────────

async def get_events_by_organizer_service(organizer_id: int):
    """
    Retrieve events for an organizer with booking/revenue stats.

    Previously called get_events_by_organizer_repo which returns plain
    EventOut objects — missing the stat and approval fields required by
    OrganizerEventOut, causing a 500 ResponseValidationError on the list page.

    Now calls get_events_by_organizer_with_stats_repo which runs the proper
    aggregation JOIN and returns OrganizerEventOut.
    """
    logger.info(f"Retrieving events for organizer with ID: {organizer_id}")
    return await event_repo.get_events_by_organizer_with_stats_repo(organizer_id)


# ─────────────────────────────────────────────────────────────────────────────
# COUNTS
# ─────────────────────────────────────────────────────────────────────────────

async def count_events_by_organizer_service(organizer_id: int) -> int:
    """Count events by organizer ID."""
    logger.info(f"Counting events for organizer with ID: {organizer_id}")
    return await event_repo.count_events_by_organizer_repo(organizer_id)


async def count_events_service() -> int:
    """Count total number of approved events."""
    logger.info("Counting total number of events")
    return await event_repo.count_events_repo()


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC / SEARCH QUERIES
# ─────────────────────────────────────────────────────────────────────────────

async def get_latest_events_service(limit: int = 5):
    """Get the latest approved events."""
    logger.info(f"Retrieving the latest {limit} events")
    return await event_repo.get_latest_events_repo(limit)


async def get_events_by_status_service(new_status: str):
    """Get events by their status."""
    logger.info(f"Retrieving events with status: {new_status.upper()}")
    return await event_repo.get_events_by_status_repo(new_status)


async def get_events_with_bookings_service():
    """Get all events that have bookings."""
    logger.info("Retrieving events with bookings")
    return await event_repo.get_events_with_bookings_repo()


async def get_events_without_bookings_service():
    """Get all events that do not have bookings."""
    logger.info("Retrieving events without bookings")
    return await event_repo.get_events_without_bookings_repo()


async def search_events_by_title_service(title: str):
    """Search events by title."""
    logger.info(f"Searching events by title: {title}")
    return await event_repo.search_events_by_title_repo(title)


async def search_events_by_venue_service(venue: str):
    """Search events by venue."""
    logger.info(f"Searching events by venue: {venue.upper()}")
    return await event_repo.search_events_by_venue_repo(venue)


async def get_events_by_country_service(country: str):
    """Get events by country."""
    logger.info(f"Retrieving events in {country.upper()}")
    return await event_repo.get_events_by_country_repo(country)


async def get_events_in_date_range_service(start_date: datetime, end_date: datetime):
    """Retrieve events within a specific date range."""
    logger.info(f"Retrieving events from {start_date} to {end_date}")
    return await event_repo.get_events_in_date_range_repo(start_date, end_date)


async def get_events_sorted_by_start_time_service(ascending: bool = True):
    """Get events sorted by start time."""
    logger.info("Retrieving events sorted by start time")
    return await event_repo.get_events_sorted_by_start_time_repo(ascending)


async def get_events_sorted_by_end_time_service(ascending: bool = True):
    """Get events sorted by end time."""
    logger.info("Retrieving events sorted by end time")
    return await event_repo.get_events_sorted_by_end_time_repo(ascending)


async def get_events_created_after_service(date: datetime):
    """Get events created after a specific date."""
    logger.info(f"Retrieving events created after {date}")
    return await event_repo.get_events_created_after_repo(date)


async def get_events_created_before_service(date: datetime):
    """Get events created before a specific date."""
    logger.info(f"Retrieving events created before {date}")
    return await event_repo.get_events_created_before_repo(date)


async def get_events_updated_after_service(date: datetime):
    """Get events updated after a specific date."""
    logger.info(f"Retrieving events updated after {date}")
    return await event_repo.get_events_updated_after_repo(date)


async def get_events_updated_before_service(date: datetime):
    """Get events updated before a specific date."""
    logger.info(f"Retrieving events updated before {date}")
    return await event_repo.get_events_updated_before_repo(date)


# ─────────────────────────────────────────────────────────────────────────────
# ORGANIZER DETAIL / STATS
# ─────────────────────────────────────────────────────────────────────────────

async def get_event_stats_service(event_id: int) -> EventStats:
    """Get aggregated stats for a single event."""
    logger.info("Getting event stats", extra={"extra": {"event_id": event_id}})
    try:
        (
            total_bookings,
            total_revenue,
            tickets_sold,
            total_available,
            total_sold,
        ) = await asyncio.gather(
            booking_repo.count_bookings_by_event_repo(event_id),
            booking_repo.get_total_revenue_by_event_id_repo(event_id),
            booking_repo.count_tickets_sold_by_event_id_repo(event_id),
            tt_repo.count_available_tickets_by_event_repo(event_id),
            tt_repo.count_tickets_sold_by_event_id_repo(event_id),
        )
        tickets_remaining = total_available - total_sold
        stats = EventStats(
            total_bookings=total_bookings,
            total_revenue=total_revenue,
            tickets_sold=tickets_sold,
            tickets_remaining=tickets_remaining,
        )
        logger.info("Event stats fetched", extra={"extra": {"event_id": event_id}})
        return stats
    except Exception as e:
        logger.error("Error fetching event stats", extra={"extra": {"event_id": event_id, "error": str(e)}})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching event stats",
        )


async def get_event_recent_bookings_service(event_id: int, limit: int = 5):
    """List the most recent bookings for a specific event."""
    logger.info("Listing recent bookings by event", extra={"extra": {"event_id": event_id, "limit": limit}})
    return await booking_repo.list_recent_bookings_by_event_repo(event_id, limit)


async def get_event_details_service(event_id: int) -> EventDetails:
    """
    Return the full EventDetails bundle: event info, stats, ticket types,
    and the 5 most recent bookings.

    The event field inside EventDetails is typed as OrganizerEventOut, so we
    fetch it via get_event_by_id_organizer_repo (which does the aggregation
    JOIN) rather than get_event_by_id_repo (which returns bare EventOut).
    """
    event = await event_repo.get_event_by_id_organizer_repo(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    try:
        (event_stats, ticket_types, recent_bookings) = await asyncio.gather(
            get_event_stats_service(event_id),
            tt_repo.list_ticket_types_by_event_id_repo(event_id),
            get_event_recent_bookings_service(event_id),
        )
        details = EventDetails(
            event=event,
            stats=event_stats,
            ticket_types=ticket_types,
            recent_bookings=recent_bookings,
        )
        logger.info("Event details fetched", extra={"extra": {"event_id": event_id}})
        return details
    except Exception as e:
        logger.error("Error fetching event details", extra={"extra": {"event_id": event_id, "error": str(e)}})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching event details",
        )


async def get_top_events_by_organizer_service(organizer_id: int, limit: int = 5):
    """Get the top events for an organizer by revenue."""
    logger.info("Getting top events by organizer", extra={"extra": {"organizer_id": organizer_id, "limit": limit}})
    return await event_repo.get_top_events_by_organizer_repo(organizer_id, limit)