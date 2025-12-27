#!/usr/bin/env python3
"""Base schemas for converting UTC to EAT."""

from pydantic import BaseModel, field_serializer
from datetime import datetime, timezone

# Define East Africa Timezone
import pytz
EAT = pytz.timezone("Africa/Nairobi")

class BaseModelEAT(BaseModel):
    """
    Base model that keeps all internal datetimes in UTC
    but converts them to EAT only when serializing responses.
    """

    class Config:
        from_attributes = True

    @field_serializer
    def serialize_to_eat(self, value, info):
        """Convert datetime fields to EAT only for API responses."""
        if isinstance(value, datetime):
            # Ensure the datetime is aware in UTC
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            # Convert to EAT
            return value.astimezone(EAT).isoformat()
        return value