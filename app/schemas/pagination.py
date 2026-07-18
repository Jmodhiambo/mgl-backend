#!/usr/bin/env python3
"""Shared pagination schema for MGLTickets.

Any list endpoint that supports limit/offset pagination should return
PaginatedResponse[YourItemSchema] rather than a bare list — this keeps the
envelope shape (items / total / limit / offset / has_more) identical across
every paginated endpoint in the app instead of each page inventing its own.
"""

from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated list envelope.

    items:    the page of results, in the same order the query returned them
    total:    total number of matching rows across all pages (not just this page)
    limit:    the page size that was requested
    offset:   the offset that was requested
    has_more: True if offset + len(items) < total — lets the frontend know
              whether to render a "load more" / "next page" control
    """
    items: list[T]
    total: int
    limit: int
    offset: int
    has_more: bool