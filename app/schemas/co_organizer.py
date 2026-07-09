#!/usr/bin/env python3
"""Schemas for Co-Organizer model in MGLTickets."""

from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from app.schemas.event import OrganizerEventOut


class CoOrganizerOut(BaseModel):
    """Raw co-organizer record — relationship metadata only (no user/event fields).
    Used internally and by the create/update endpoints where the caller already
    knows the context."""
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


class CoOrganizerCreate(BaseModel):
    """Co-Organizer schema for API requests."""
    user_id: int
    organizer_id: int
    event_id: int

    class Config:
        from_attributes = True


class CoOrganizerUpdate(BaseModel):
    """Co-Organizer schema for update requests."""
    create_co_organizer: bool

    class Config:
        from_attributes = True


class CoOrganizerWithUserAndEvent(BaseModel):
    """
    Enriched co-organizer response for list endpoints.

    Bundles the co-organizer relationship metadata, the invited user's public
    fields, and the event title into a single flat object — so the frontend
    gets everything it needs for the co-organizers table in one call with no
    extra round-trips.

    `id` is the co_organizers row PK (used by DELETE endpoints).
    `user_id` is the invited user's users.id (kept separate so the UI can
    link to the user profile without confusion).
    """
    # ── Co-organizer relationship ─────────────────────────────────────────
    id: int                       # co_organizers.id — pass to DELETE
    event_id: int
    event_title: str
    invited_by: int
    create_co_organizer: bool
    created_at: datetime

    # ── Invited user (flattened, not nested) ──────────────────────────────
    user_id: int
    name: str
    email: str
    phone_number: Optional[str] = None
    role: str

    class Config:
        from_attributes = True


class CoOrganizerWithEvent(BaseModel):
    """
    Enriched co-organizer response that bundles the full event alongside the
    co-organizer relationship metadata. Used by the MyEvents page so the
    frontend gets everything it needs in a single call instead of N+1 requests.

    The `create_co_organizer` flag tells the frontend whether this co-organizer
    may in turn invite other co-organizers (delegated invite privilege).

    `event` is OrganizerEventOut, not the bare public EventOut — co-organizers
    see the same aggregated booking/revenue stats and commission breakdown an
    organizer sees for their own events. Previously this was EventOut, which
    doesn't carry total_bookings/total_revenue at all, so My Events silently
    had nothing to show on co-organizing cards.
    """
    # ── Co-organizer relationship ──────────────────────────────────────────
    co_organizer_id:      int
    invited_by:           int
    create_co_organizer:  bool
    created_at:            datetime   # maps to CoOrganizer.created_at

    # ── Full event, with stats ──────────────────────────────────────────────
    event: OrganizerEventOut

    class Config:
        from_attributes = True


# Rebuild after all forward references are resolved
CoOrganizerWithEvent.model_rebuild()