#!/usr/bin/env python3
"""Schemas for Co-Organizer model in MGLTickets."""

from datetime import datetime
from app.schemas.base import BaseModelEAT


class CoOrganizerOut(BaseModelEAT):
    """Co-Organizer schema for API responses."""
    id: int
    user_id: int
    organizer_id: int
    event_id: int
    invited_by: int
    create_co_organizer: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class CoOrganizerCreate(BaseModelEAT):
    """Co-Organizer schema for API requests."""
    user_id: int
    organizer_id: int
    event_id: int

    class Config:
        orm_mode = True


class CoOrganizerUpdate(BaseModelEAT):
    """Co-Organizer schema for API requests."""
    create_corganizer: bool

    class Config:
        orm_mode = True