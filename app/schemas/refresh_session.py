#!/usr/bin/env python3
"""Schemas for RefreshSession model in MGLTickets."""

from datetime import datetime
from app.schemas.base import BaseModelEAT
from typing import Optional

class RefreshSessionOut(BaseModelEAT):
    session_id: str
    user_id: int
    refresh_token_hash: str
    expires_at: datetime

    class Config:
        from_attributes = True


class RefreshSessionCreate(BaseModelEAT):
    session_id: str
    user_id: int
    refresh_token_hash: str
    expires_at: datetime

    class Config:
        from_attributes = True


class RefreshSessionUpdate(BaseModelEAT):
    session_id: Optional[str]
    refresh_token_hash: Optional[str]
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True