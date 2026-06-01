#!/usr/bin/env python3
"""Schemas for Co-Organizer model in MGLTickets."""

from datetime import datetime
from typing import Optional
from app.schemas.base import BaseModelEAT
from app.schemas.event import EventOut


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
        from_attributes = True


class CoOrganizerCreate(BaseModelEAT):
    """Co-Organizer schema for API requests."""
    user_id: int
    organizer_id: int
    event_id: int

    class Config:
        from_attributes = True


class CoOrganizerUpdate(BaseModelEAT):
    """Co-Organizer schema for update requests."""
    create_co_organizer: bool

    class Config:
        from_attributes = True


class CoOrganizerWithEvent(BaseModelEAT):
    """
    Enriched co-organizer response that bundles the full event alongside the
    co-organizer relationship metadata.  Used by the MyEvents page so the
    frontend gets everything it needs in a single call instead of N+1 requests.

    The `create_co_organizer` flag tells the frontend whether this co-organizer
    may in turn invite other co-organizers (delegated invite privilege).
    """
    # ── Co-organizer relationship ──────────────────────────────────────────
    co_organizer_id:      int
    invited_by:           int
    create_co_organizer:  bool
    created_at:            datetime   # maps to CoOrganizer.created_at

    # ── Full event ─────────────────────────────────────────────────────────
    event: EventOut

    class Config:
        from_attributes = True


# Rebuild after all forward references are resolved
CoOrganizerWithEvent.model_rebuild()