#!/usr/bin/env python3
"""Event services for MGLTickets."""

import asyncio
from datetime import datetime
from fastapi import HTTPException, status
import app.db.repositories.event_repo as event_repo
import app.db.repositories.booking_repo as booking_repo
import app.db.repositories.ticket_instance_repo as ti_repo
import app.db.repositories.ticket_type_repo as tt_repo
import app.db.repositories.settings_repo as settings_repo

from app.schemas.event import EventStats, EventDetails
from app.schemas.event import EventCreateWithFlyer, EventUpdate

from app.core.logging_config import logger


# ─────────────────────────────────────────────────────────────────────────────
# CREATION
# ─────────────────────────────────────────────────────────────────────────────

async def create_event_service(event_data: EventCreateWithFlyer):
    """
    Create a new event and return AdminEventOut.

    Commission injection:
      If commission_rate was not explicitly set on event_data (i.e. it still
      holds the schema default of 7.0), we fetch the current platform default
      from PlatformSettings and override it. This ensures the rate locked onto
      the event always reflects the platform default at creation time, without
      requiring the router to know about platform settings.
    """
    logger.info(f"Creating event: {event_data.title!r}")

    # Fetch live platform commission rate and lock it onto this event
    try:
        platform_settings = await settings_repo.get_platform_settings_repo()
        if platform_settings is not None:
            event_data = event_data.model_copy(update={
                "commission_rate":   float(platform_settings.platform_fee_percent),
                "commission_source": "platform_default",
            })
            logger.info(
                f"Commission rate locked at {event_data.commission_rate}% "
                f"(from platform settings)"
            )
    except Exception as exc:
        # Non-fatal — fall back to schema default (7.0 %)
        logger.warning(f"Could not fetch platform settings for commission; using default. {exc}")

    base = await event_repo.create_event_repo(event_data)
    logger.info(f"Created event with ID: {base.id} — re-fetching as AdminEventOut")
    full = await event_repo.get_event_by_id_admin_repo(base.id)
    if not full:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Event created but could not be retrieved.",
        )
    return full


# ─────────────────────────────────────────────────────────────────────────────
# BASIC CRUD
# ─────────────────────────────────────────────────────────────────────────────

async def get_event_by_id_service(event_id: int):
    event = await event_repo.get_event_by_id_repo(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


async def get_event_by_slug_service(slug: str):
    return await event_repo.get_event_by_slug_repo(slug)


async def get_event_by_id_admin_service(event_id: int):
    event = await event_repo.get_event_by_id_admin_repo(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


async def get_event_by_slug_admin_service(slug: str):
    event = await event_repo.get_event_by_slug_repo(slug)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return await event_repo.get_event_by_id_admin_repo(event.id)


async def get_events_by_organizer_admin_service(organizer_id: int):
    return await event_repo.get_events_by_organizer_admin_repo(organizer_id)


async def update_event_service(event_id: int, event_data: EventUpdate):
    updated = await event_repo.update_event_repo(event_id, event_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Event not found")
    return await event_repo.get_event_by_id_organizer_repo(updated.id)


async def delete_event_service(event_id: int):
    return await event_repo.delete_event_repo(event_id)


async def update_event_status_service(event_id: int, new_status: str):
    """Update event status (upcoming, ongoing, completed, canceled & deleted)."""
    statuses = ["upcoming", "ongoing", "completed", "cancelled", "deleted"]
    if new_status not in statuses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status.")
    
    event = await event_repo.get_event_by_id_repo(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found."
        )
    if event.status == "deleted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event has already been deleted.",
        )
    return await event_repo.update_event_status_repo(event_id, new_status)


# ─────────────────────────────────────────────────────────────────────────────
# APPROVAL
# ─────────────────────────────────────────────────────────────────────────────

async def approve_event_service(event_id: int):
    return await event_repo.approve_event_repo(event_id)


async def reject_event_service(event_id: int):
    return await event_repo.reject_event_repo(event_id)


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN LIST QUERIES
# ─────────────────────────────────────────────────────────────────────────────

async def get_approved_events_service():
    return await event_repo.get_approved_events_admin_repo()


async def get_unapproved_events_service():
    return await event_repo.get_unapproved_events_admin_repo()


async def get_all_events_service():
    return await event_repo.get_all_events_admin_repo()


# ─────────────────────────────────────────────────────────────────────────────
# ORGANIZER LIST QUERIES
# ─────────────────────────────────────────────────────────────────────────────

async def get_events_by_organizer_service(organizer_id: int):
    return await event_repo.get_events_by_organizer_with_stats_repo(organizer_id)


# ─────────────────────────────────────────────────────────────────────────────
# COUNTS
# ─────────────────────────────────────────────────────────────────────────────

async def count_events_by_organizer_service(organizer_id: int) -> int:
    return await event_repo.count_events_by_organizer_repo(organizer_id)


async def count_events_service() -> int:
    return await event_repo.count_events_repo()


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC / SEARCH QUERIES
# ─────────────────────────────────────────────────────────────────────────────

async def get_latest_events_service(limit: int = 5):
    return await event_repo.get_latest_events_repo(limit)


async def get_events_by_status_service(new_status: str):
    return await event_repo.get_events_by_status_repo(new_status)


async def search_events_by_title_service(title: str):
    return await event_repo.search_events_by_title_repo(title)


async def search_events_by_venue_service(venue: str):
    return await event_repo.search_events_by_venue_repo(venue)


async def get_events_by_country_service(country: str):
    return await event_repo.get_events_by_country_repo(country)


async def get_events_in_date_range_service(start_date: datetime, end_date: datetime):
    return await event_repo.get_events_in_date_range_repo(start_date, end_date)


async def get_events_sorted_by_start_time_service(ascending: bool = True):
    return await event_repo.get_events_sorted_by_start_time_repo(ascending)


async def get_events_sorted_by_end_time_service(ascending: bool = True):
    return await event_repo.get_events_sorted_by_end_time_repo(ascending)


async def get_events_created_after_service(date: datetime):
    return await event_repo.get_events_created_after_repo(date)


async def get_events_created_before_service(date: datetime):
    return await event_repo.get_events_created_before_repo(date)


async def get_events_updated_after_service(date: datetime):
    return await event_repo.get_events_updated_after_repo(date)


async def get_events_updated_before_service(date: datetime):
    return await event_repo.get_events_updated_before_repo(date)


# ─────────────────────────────────────────────────────────────────────────────
# ORGANIZER DETAIL / STATS
# ─────────────────────────────────────────────────────────────────────────────

async def get_event_stats_service(event_id: int) -> EventStats:
    """
    Get aggregated stats for a single event, including commission breakdown.
    The commission_rate is read from the event's own field.
    """
    logger.info(f"Getting event stats for event_id={event_id}")
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

        # Fetch the event to get its locked commission_rate
        event = await event_repo.get_event_by_id_organizer_repo(event_id)
        commission_rate = float(event.commission_rate) if event else 7.0
        platform_cut    = round(total_revenue * commission_rate / 100, 2)
        organizer_net   = round(total_revenue - platform_cut, 2)

        return EventStats(
            total_bookings=total_bookings,
            total_revenue=total_revenue,
            tickets_sold=tickets_sold,
            tickets_remaining=tickets_remaining,
            commission_rate=commission_rate,
            platform_cut=platform_cut,
            organizer_net=organizer_net,
        )
    except Exception as e:
        logger.error(f"Error fetching event stats for event_id={event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching event stats",
        )


async def get_event_recent_bookings_service(event_id: int, limit: int = 5):
    return await booking_repo.list_recent_bookings_by_event_repo(event_id, limit)


async def get_event_details_service(event_id: int) -> EventDetails:
    """Full EventDetails bundle by event ID."""
    event = await event_repo.get_event_by_id_organizer_repo(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return await _build_event_details(event)


async def get_event_details_by_slug_service(slug: str) -> EventDetails:
    """
    Full EventDetails bundle looked up by slug.
    Used by GET /organizers/me/events/by-slug/{slug}/details — the preferred
    endpoint for the organizer portal since slugs are URL-safe and human-readable.
    """
    event = await event_repo.get_event_by_slug_organizer_repo(slug)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return await _build_event_details(event)


async def _build_event_details(event) -> EventDetails:
    """Shared helper — assembles EventDetails from a pre-fetched OrganizerEventOut."""
    try:
        event_stats, ticket_types, recent_bookings = await asyncio.gather(
            get_event_stats_service(event.id),
            tt_repo.list_ticket_types_by_event_id_repo(event.id),
            get_event_recent_bookings_service(event.id),
        )
        return EventDetails(
            event=event,
            stats=event_stats,
            ticket_types=ticket_types,
            recent_bookings=recent_bookings,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building EventDetails for event_id={event.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching event details",
        )


async def get_top_events_by_organizer_service(organizer_id: int, limit: int = 5):
    return await event_repo.get_top_events_by_organizer_repo(organizer_id, limit)