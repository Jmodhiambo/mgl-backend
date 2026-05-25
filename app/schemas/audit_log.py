#!/usr/bin/env python3
"""Pydantic schemas for AuditLog.

Place at:  app/schemas/audit_log.py
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, model_validator


# ─── Read ─────────────────────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    """Returned to the frontend for a single audit-log entry."""

    id: int
    admin_id: Optional[int] = None
    admin_name: str

    action: str
    target_type: str
    target_id: Optional[int] = None

    details: Optional[dict[str, Any]] = None
    """Deserialized from the TEXT column — stored as JSON string in the DB."""

    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def deserialize_details(cls, data: Any) -> Any:
        """Convert the raw TEXT `details` column to a dict if it arrives as a string."""
        if hasattr(data, "__dict__"):
            # SQLAlchemy model instance
            raw = getattr(data, "details", None)
            if isinstance(raw, str):
                try:
                    object.__setattr__(data, "details", json.loads(raw))
                except (json.JSONDecodeError, TypeError):
                    object.__setattr__(data, "details", {})
        elif isinstance(data, dict):
            raw = data.get("details")
            if isinstance(raw, str):
                try:
                    data["details"] = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    data["details"] = {}
        return data


# ─── Write (internal — services call this, never exposed directly) ────────────

class AuditLogCreate(BaseModel):
    """Used internally by any admin service that mutates data."""

    admin_id: Optional[int] = None
    admin_name: str
    action: str
    target_type: str
    target_id: Optional[int] = None
    details: Optional[dict[str, Any]] = None


# ─── List response (optional envelope) ───────────────────────────────────────

class AuditLogListResponse(BaseModel):
    total: int
    items: list[AuditLogOut]