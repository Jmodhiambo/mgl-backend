#!/usr/bin/env python3
"""Schemas for Favorite model in MGLTickets."""

from datetime import datetime
from app.schemas.base import BaseModelEAT


class FavoriteOut(BaseModelEAT):
    id: int
    user_id: int
    event_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FavoriteCreate(BaseModelEAT):
    user_id: int
    event_id: int

    class Config:
        from_attributes = True