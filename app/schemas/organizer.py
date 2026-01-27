#!/usr/bin/env python3
"""Schemas for User-Organizer model in MGLTickets."""

from datetime import datetime
from pydantic import EmailStr
from typing import Optional
from app.schemas.base import BaseModelEAT


class DashboardStats(BaseModelEAT):
    """Schema for the organizer's dashboard stats."""
    total_events: int
    total_bookings: int
    total_revenue: float
    active_events: int
    upcoming_events: int
    completed_events: int
    monthly_growth: float
    tickets_sold: int

    class Config:
        from_attributes = True


class RecentBooking(BaseModelEAT):
    """Schema for the organizer's recent bookings."""
    id: int
    event_title: str
    customer_name: str
    quantity: int
    total_price: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class TopEvent(BaseModelEAT):
    """Schema for the organizer's top events."""
    id: int
    title: str
    bookings: int
    revenue: float
    tickets_sold: int

    class Config:
        from_attributes = True