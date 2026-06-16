#!/usr/bin/env python3
"""Schemas for analytics endpoint in MGLTickets."""

from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class DashboardStatsOut(BaseModel):
    """Schema for outputting dashboard statistics."""
    total_users: int
    total_organizers: int
    total_admins: int
    total_events: int
    total_bookings: int
    total_revenue: int
    active_events: int
    pending_approvals: int
    open_messages: int
    new_users_this_week: int
    revenue_this_month: int

    class Config:
        from_attributes = True