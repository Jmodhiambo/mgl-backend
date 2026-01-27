#!/usr/bin/env python3
"""
Organizer statistics service function.

"""

from app.schemas.organizer import DashboardStats
from app.core.logging_config import logger
# Import the repository functions you created
import app.db.repositories.event_repo as event_repo
import app.db.repositories.booking_repo as booking_repo


import asyncio

async def get_organizer_stats_service(organizer_id: int) -> DashboardStats:
    """
    Optimized version that fetches all stats in parallel.
    
    Args:
        organizer_id: The ID of the organizer
        
    Returns:
        DashboardStats: Object containing all dashboard statistics
    """
    logger.info(f"Fetching dashboard stats (optimized) for organizer ID: {organizer_id}")
    
    try:
        # Fetch all stats in parallel using asyncio.gather()
        (
            total_events,
            active_events,
            upcoming_events,
            completed_events,
            total_bookings,
            tickets_sold,
            total_revenue,
            current_month_events,
            last_month_events
        ) = await asyncio.gather(
            event_repo.count_events_by_organizer_repo(organizer_id),
            event_repo.count_active_events_by_organizer_repo(organizer_id),
            event_repo.count_upcoming_events_by_organizer_repo(organizer_id),
            event_repo.count_completed_events_by_organizer_repo(organizer_id),
            booking_repo.count_bookings_by_organizer_repo(organizer_id),
            booking_repo.count_tickets_sold_by_organizer_repo(organizer_id),
            booking_repo.calculate_revenue_by_organizer_repo(organizer_id),
            event_repo.count_events_created_this_month_repo(organizer_id),
            event_repo.count_events_created_last_month_repo(organizer_id)
        )
        
        # Calculate monthly growth
        if last_month_events > 0:
            monthly_growth = ((current_month_events - last_month_events) / last_month_events) * 100
        elif current_month_events > 0:
            monthly_growth = 100.0
        else:
            monthly_growth = 0.0
        
        monthly_growth = round(monthly_growth, 1)
        
        stats = DashboardStats(
            total_events=total_events,
            total_bookings=total_bookings,
            total_revenue=total_revenue,
            active_events=active_events,
            upcoming_events=upcoming_events,
            completed_events=completed_events,
            monthly_growth=monthly_growth,
            tickets_sold=tickets_sold
        )
        
        logger.info(f"Successfully fetched stats (optimized) for organizer ID: {organizer_id}")
        return stats
        
    except Exception as e:
        logger.error(f"Error fetching organizer stats for ID {organizer_id}: {str(e)}")
        raise