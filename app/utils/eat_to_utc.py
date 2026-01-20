#!usr/bin/env python3
"""Convert East Africa Time (EAT) to UTC."""

from datetime import datetime, timezone
from typing import Optional

def convert_eat_to_utc(eat_time: Optional[datetime]) -> Optional[datetime]:
    """Convert EAT to UTC for internal comparisons since my Pydantic models converts time to EAT."""
    if eat_time:
        return eat_time.replace(tzinfo=timezone.utc)
    return None