#!/usr/bin/env python3
"""Schemas for Article Analytics model in MGLTickets."""

from datetime import datetime
from app.schemas.base import BaseModelEAT
from typing import Optional

class ArticleViewOut(BaseModelEAT):
    """Schema for Article View model in MGLTickets."""
    id: int
    article_slug: str
    user_id: int = None
    viewed_at: datetime
    session_id: str = None
    referrer: Optional[str] = None
    device_type: Optional[str] = None
    time_spent_seconds: Optional[int] = None
    scroll_depth_percent: Optional[int] = None

    class Config:
        from_attributes = True

class ArticleFeedbackOut(BaseModelEAT):
    """Schema for Article Feedback model in MGLTickets."""
    id: int
    article_slug: str
    user_id: int = None
    is_helpful: bool
    feedback_text: Optional[str] = None
    created_at: datetime
    user_intent: Optional[str] = None

    class Config:
        from_attributes = True


class ArticleSearchQueryOut(BaseModelEAT):
    """Schema for Article Search Query model in MGLTickets."""
    id: int
    query: str
    user_id: int = None
    results_count: int
    clicked_article_slug: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True