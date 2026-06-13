#!/usr/bin/env python3
"""Service layer for admin analytics."""

from __future__ import annotations

from app.core.logging_config import logger
import app.db.repositories.admin_analytics_repo as repo


async def get_dashboard_stats_service() -> dict:
    """Aggregated KPI stats for the admin dashboard."""
    logger.info("Fetching admin dashboard stats")
    return await repo.get_dashboard_stats_repo()


async def get_revenue_chart_service(months: int = 7) -> list[dict]:
    """Monthly revenue totals for the last N months."""
    logger.info(f"Fetching revenue chart data ({months} months)")
    return await repo.get_revenue_chart_repo(months)


async def get_user_growth_chart_service(months: int = 6) -> list[dict]:
    """Monthly new user registrations for the last N months."""
    logger.info(f"Fetching user growth chart data ({months} months)")
    return await repo.get_user_growth_chart_repo(months)


async def get_events_by_category_service() -> list[dict]:
    """Approved event count grouped by category."""
    logger.info("Fetching events by category")
    return await repo.get_events_by_category_repo()


async def get_booking_statuses_service() -> list[dict]:
    """Booking count grouped by status."""
    logger.info("Fetching booking status distribution")
    return await repo.get_booking_statuses_repo()


async def get_activity_feed_service(limit: int = 20) -> list[dict]:
    """Platform-wide recent activity feed from audit logs."""
    logger.info(f"Fetching activity feed (limit={limit})")
    return await repo.get_activity_feed_repo(limit)