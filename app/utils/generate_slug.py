#!/usr/bin/env python3
"""Slug generator for MGLTickets."""

from slugify import slugify
from typing import Optional
from app.services.event_services import get_event_by_slug_service

"""
Generate a URL-safe slug form event title.
Example:
"The Lion King Drama Festival!" → "the-lion-king-drama-festival"
"""


def generate_slug(title: str, counter: Optional[int] = None) -> str:
    """Generate slug - no database calls, just string manipulation."""
    slug = slugify(title, max_length=200) or "event"

    if counter and counter > 1:
        slug = f"{slug}-{counter}"

    return slug


async def generate_unique_slug(title: str, max_attempts: int = 100) -> str:
    """Generate a unique slug for an event."""
    base_slug = generate_slug(title)

    # Return base slug if it is unique
    if not await get_event_by_slug_service(base_slug):
        return base_slug

    # Generate a unique slug by appending a counter
    for counter in range(2, max_attempts + 2):
        unique_slug = generate_slug(title, counter)
        if not await get_event_by_slug_service(unique_slug):
            return unique_slug
        
    raise ValueError(f"Could not generate a unique slug after {max_attempts} attempts.")