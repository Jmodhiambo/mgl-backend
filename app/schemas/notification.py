#!/usr/bin/env python3
"""Pydantic schemas for the Notification model.

Mirrors the pattern used in app/schemas/user.py:
  • NotificationOut  – returned by every endpoint (full public shape).
  • NotificationCreate – used internally by service trigger helpers
    (not directly exposed as a request body, but available if needed).
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class NotificationCreate(BaseModel):
    """Internal schema for creating a notification programmatically."""

    title: str
    message: str
    category: str
    priority: str = "medium"
    recipient_id: Optional[int] = None
    recipient_role: str = "admin"
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    action_url: Optional[str] = None
    expires_at: Optional[datetime] = None


class NotificationOut(BaseModel):
    """Public-facing schema returned by all notification endpoints.
    Matches the Notification interface expected by the React frontend.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    message: str
    category: str       # 'event' | 'user' | 'payment' | 'message' | 'system'
    priority: str       # 'high' | 'medium' | 'low'
    is_read: bool
    recipient_id: Optional[int] = None
    recipient_role: str
    source_type: Optional[str] = None
    source_id: Optional[int] = None
    action_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None