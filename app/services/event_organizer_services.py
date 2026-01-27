#!/usr/bin/env python 3
"""Services for Event Organizer model in MGLTickets."""

import asyncio
from fastapi import HTTPException, status

import app.db.repositories.event_repo as event_repo
import app.db.repositories.booking_repo as booking_repo
import app.db.repositories.ticket_instance_repo as ti_repo
import app.db.repositories.ticket_type_repo as tt_repo

from app.schemas.event import EventStats, EventDetails

from app.core.logging_config import logger


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