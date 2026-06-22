#!/usr/bin/env python3
"""Service layer for Organizer related analytics."""

from app.core.logging_config import logger
import app.db.repositories.organizer_analytics_repo as oa_repo
from app.schemas.organizer import DashboardStats, OrganizerOrderOut


async def get_dashboard_stats_service(organizer_id: int) -> DashboardStats:
    """Aggregated KPI stats for the organizer dashboard."""
    logger.info("Fetching organizer dashboard stats")
    return await oa_repo.get_organizer_dashboard_stats_repo(organizer_id)


async def list_orders_by_organizer_service(organizer_id: int) -> list[OrganizerOrderOut]:
    """All orders (with nested booking line items) for events owned by organizer_id, newest first.

    Used by GET /organizers/me/orders (BookingsView — Orders tab) in the event_organizer.py.
    """
    logger.info(f"Listing orders for organizer {organizer_id}")
    return await oa_repo.list_orders_by_organizer_repo(organizer_id)


async def get_recent_orders_by_organizer_service(organizer_id: int, limit: int = 10) -> list[OrganizerOrderOut]:
    """Most recent N orders for the organizer's events.

    Used by the dashboard recent-activity widget.
    Called in the event_organizer.py.
    """
    logger.info(f"Listing recent orders for organizer {organizer_id}", extra={"extra": {"limit": limit}})
    return await oa_repo.get_recent_orders_by_organizer_repo(organizer_id, limit)