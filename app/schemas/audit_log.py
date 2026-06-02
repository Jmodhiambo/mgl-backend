#!/usr/bin/env python3
"""Pydantic schemas for AuditLog.

Place at:  app/schemas/audit_log.py

FIX: The model_validator no longer tries to json.loads() the details field.
PostgreSQL's JSON column already returns a Python dict via SQLAlchemy — calling
json.loads() on a dict raised a TypeError and corrupted the details payload.
The validator now only handles the legacy SQLite TEXT case as a fallback.
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

    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def deserialize_details(cls, data: Any) -> Any:
        """Normalise the details field.

        PostgreSQL JSON column → SQLAlchemy returns a dict already.
        Legacy SQLite TEXT column → arrives as a JSON string, needs parsing.
        Anything else (None, already a dict) → pass through untouched.
        """
        def _parse(raw: Any) -> Any:
            if raw is None or isinstance(raw, dict):
                return raw          # already correct — do nothing
            if isinstance(raw, str):
                try:
                    return json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    return {}
            return raw              # unexpected type — leave for Pydantic to handle

        if hasattr(data, "__dict__"):
            # SQLAlchemy ORM instance
            raw = getattr(data, "details", None)
            parsed = _parse(raw)
            if parsed is not raw:
                object.__setattr__(data, "details", parsed)
        elif isinstance(data, dict):
            data["details"] = _parse(data.get("details"))

        return data
    
    class Config:
        from_attributes = True


# ─── Write (internal — services call this, never exposed directly) ────────────

class AuditLogCreate(BaseModel):
    """Used internally by any admin service that mutates data."""

    admin_id: Optional[int] = None
    admin_name: str
    action: str
    target_type: str
    target_id: Optional[int] = None
    details: Optional[dict[str, Any]] = None

    class Config:
        from_attributes = True


# ─── List response ────────────────────────────────────────────────────────────

class AuditLogListResponse(BaseModel):
    total: int
    items: list[AuditLogOut]

    class Config:
        from_attributes = True