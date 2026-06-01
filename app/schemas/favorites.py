#!/usr/bin/env python3
"""Schemas for Favorite model in MGLTickets."""

from datetime import datetime
from app.schemas.base import BaseModelEAT
from app.schemas.event import EventOut


class FavoriteOut(BaseModelEAT):
    """
    Bare favorite record — contains only IDs and timestamps.
    Used internally and for create/delete responses.
    """
    id: int
    user_id: int
    event_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FavoriteWithEventOut(BaseModelEAT):
    """
    Favorite record with the full event object embedded.
    Returned by GET /users/me/favorites so the frontend gets
    everything it needs in one call without a second fetch.
    """
    id: int
    user_id: int
    event_id: int
    created_at: datetime
    event: EventOut  # embedded via SQLAlchemy relationship

    class Config:
        from_attributes = True


class FavoriteCreate(BaseModelEAT):
    """Payload for creating a favorite. user_id comes from the auth token."""
    event_id: int

    class Config:
        from_attributes = True


# Rebuild after EventOut is defined
FavoriteWithEventOut.model_rebuild()