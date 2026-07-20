#!/usr/bin/env python3
"""Service layer for Organizer related analytics."""

from datetime import datetime
from typing import Optional

from app.core.logging_config import logger
import app.db.repositories.organizer_analytics_repo as oa_repo
from app.schemas.organizer import DashboardStats, OrganizerOrderOut
from app.schemas.pagination import PaginatedResponse


async def get_dashboard_stats_service(organizer_id: int) -> DashboardStats:
    """Aggregated KPI stats for the organizer dashboard."""
    logger.info("Fetching organizer dashboard stats")
    return await oa_repo.get_organizer_dashboard_stats_repo(organizer_id)


async def list_orders_by_organizer_service(
    organizer_id: int,
    event_id: Optional[int] = None,
    limit: int = 20,
    offset: int = 0,
    search: Optional[str] = None,
    order_status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> PaginatedResponse[OrganizerOrderOut]:
    """All orders (with nested booking line items) for events owned by
    organizer_id, newest first, paginated and filterable server-side —
    optionally scoped to a single event_id (used by the event-specific
    BookingsView Orders tab).

    Used by GET /organizers/me/orders (BookingsView — Orders tab).
    """
    logger.info(
        f"Listing orders for organizer {organizer_id} "
        f"(event_id={event_id}, limit={limit}, offset={offset}, "
        f"search={search}, order_status={order_status})"
    )
    items, total = await oa_repo.list_orders_by_organizer_repo(
        organizer_id,
        event_id=event_id,
        limit=limit,
        offset=offset,
        search=search,
        order_status=order_status,
        start_date=start_date,
        end_date=end_date,
    )
    return PaginatedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(items)) < total,
    )


async def get_recent_orders_by_organizer_service(organizer_id: int, limit: int = 10) -> list[OrganizerOrderOut]:
    """Most recent N orders for the organizer's events.

    Used by the dashboard recent-activity widget. Not paginated — unrelated
    to the Orders tab pagination above, out of scope for this change.
    """
    logger.info(f"Listing recent orders for organizer {organizer_id}", extra={"extra": {"limit": limit}})
    return await oa_repo.get_recent_orders_by_organizer_repo(organizer_id, limit)