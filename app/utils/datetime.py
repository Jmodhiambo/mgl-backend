#! /usr/bin/env python3
"""Converts UTC to EAT (East Africa Time)"""

from datetime import datetime
import pytz

def to_eat(dt: datetime) -> datetime:
    """Convert a UTC datetime to East Africa Time (EAT)."""
    if dt is None:
        return None

    eat = pytz.timezone("Africa/Nairobi")

    # If dt does not have timezone info, assume it's UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.utc)

    return dt.astimezone(eat)