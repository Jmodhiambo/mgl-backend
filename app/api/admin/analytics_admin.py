#!/usr/bin/env python3
"""Admin analytics routes."""

from fastapi import APIRouter, Depends, Query
import app.services.admin_analytics_services as analytics_services
from app.core.security import require_admin

router = APIRouter()


@router.get("/admin/analytics/dashboard")
async def get_dashboard_stats(user=Depends(require_admin)):
    """
    Aggregated KPI stats for the admin dashboard stat cards.
    Returns: DashboardStats shape expected by the frontend.
    """
    return await analytics_services.get_dashboard_stats_service()


@router.get("/admin/analytics/revenue")
async def get_revenue_chart(
    months: int = Query(default=7, ge=1, le=24),
    user=Depends(require_admin),
):
    """
    Monthly revenue totals (completed payments) for the last N months.
    Returns: [{label: 'Jan', value: 120000}, ...]
    """
    return await analytics_services.get_revenue_chart_service(months)


@router.get("/admin/analytics/user-growth")
async def get_user_growth_chart(
    months: int = Query(default=6, ge=1, le=24),
    user=Depends(require_admin),
):
    """
    New user registrations per month for the last N months.
    Returns: [{label: 'Jan', value: 42}, ...]
    """
    return await analytics_services.get_user_growth_chart_service(months)


@router.get("/admin/analytics/events-by-category")
async def get_events_by_category(user=Depends(require_admin)):
    """
    Approved event count grouped by category, sorted by count desc.
    Returns: [{label: 'Music', value: 12}, ...]
    """
    return await analytics_services.get_events_by_category_service()


@router.get("/admin/analytics/booking-statuses")
async def get_booking_statuses(user=Depends(require_admin)):
    """
    Booking count grouped by status.
    Returns: [{label: 'Confirmed', value: 340}, ...]
    """
    return await analytics_services.get_booking_statuses_service()


@router.get("/admin/analytics/activity-feed")
async def get_activity_feed(
    limit: int = Query(default=20, ge=1, le=100),
    user=Depends(require_admin),
):
    """
    Platform-wide recent activity feed derived from audit logs.
    Returns: [{id, message, icon, time, action}, ...]
    """
    return await analytics_services.get_activity_feed_service(limit)