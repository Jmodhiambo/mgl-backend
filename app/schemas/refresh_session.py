#!/usr/bin/env python3
"""Schemas for RefreshSession model in MGLTickets."""

from datetime import datetime
from app.schemas.base import BaseModelEAT
from typing import Optional

class RefreshSessionOut(BaseModelEAT):
    """Schema for outputting RefreshSession data."""
    session_id: str
    user_id: int
    refresh_token_hash: str
    expires_at: datetime
    last_used_at: datetime
    revoked_at: Optional[datetime]
    replaced_by_sid: Optional[str]
    device_info: Optional[str]
    ip_address: Optional[str]
    location: Optional[str]

    class Config:
        from_attributes = True


class RefreshSessionCreate(BaseModelEAT):
    """For creating a new RefreshSession."""
    session_id: str
    user_id: int
    refresh_token_hash: str
    expires_at: datetime
    device_info: Optional[str]
    ip_address: Optional[str]
    location: Optional[str]

    class Config:
        from_attributes = True


class RefreshSessionUpdate(BaseModelEAT):
    """For updating a RefreshSession, e.g. to mark it as revoked."""
    session_id: Optional[str]
    refresh_token_hash: Optional[str]
    expires_at: Optional[datetime]
    device_info: Optional[str]
    ip_address: Optional[str]
    location: Optional[str]

    class Config:
        from_attributes = True

# ─── Response models ──────────────────────────────────────────────────────────

class RevokeAllOtherSessionsRequest(BaseModelEAT):
    """The caller's own session_id (from their JWT 'sid' claim).
    This one will be kept; all others are revoked."""
    current_session_id: str

    class Config:
        from_attributes = True


class RevokeAllOtherSessionsResponse(BaseModelEAT):
    revoked_count: int
    message: str

    class Config:
        from_attributes = True

class RevokeSessionRequest(BaseModelEAT):
    """Optional body for single-session revoke endpoints.
 
    All three routers (admin, user, organizer) accept this body on
    DELETE /*/sessions/{session_id}.  The reason field is stored in
    revoke_reason on the RefreshSession row for audit purposes.
    """
    reason: str = "user_revoked"

    class Config:
        from_attributes = True