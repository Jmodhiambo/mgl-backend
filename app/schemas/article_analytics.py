#!/usr/bin/env python3
"""Schemas for Article Analytics model in MGLTickets."""

from datetime import datetime
from app.schemas.base import BaseModelEAT
from typing import Optional
from pydantic import Field, validator

class ArticleViewOut(BaseModelEAT):
    """Schema for Article View model in MGLTickets."""
    id: int
    article_slug: str
    user_id: Optional[int]
    session_id: str
    referrer: Optional[str]
    device_type: Optional[str]
    user_agent: Optional[str] 
    screen_width: Optional[int]
    screen_height: Optional[int] 
    viewed_at: datetime

    class Config:
        from_attributes = True


class ArticleViewCreate(BaseModelEAT):
    """Schema for Article View model in MGLTickets."""
    article_slug: str
    session_id: str
    referrer: Optional[str]
    device_type: Optional[str]
    user_agent: Optional[str]
    screen_width: Optional[int]
    screen_height: Optional[int]

    class Config:
        from_attributes = True


class ArticleEngagementOut(BaseModelEAT):
    """Schema for Article Engagement model in MGLTickets."""
    id: int
    article_slug: str
    user_id: Optional[int]
    session_id: str
    time_spent_seconds: int
    scroll_depth_percent: int
    engaged_at: datetime

    class Config:
        from_attributes = True


class ArticleEngagementCreate(BaseModelEAT):
    """Schema for Article Engagement model in MGLTickets."""
    article_slug: str
    session_id: str
    time_spent_seconds: int
    scroll_depth_percent: int

    class Config:
        from_attributes = True


class ArticleFeedbackOut(BaseModelEAT):
    """Schema for Article Feedback model in MGLTickets."""
    id: int
    article_slug: str
    user_id: Optional[int]
    is_helpful: bool
    feedback_text: Optional[str]
    created_at: datetime
    user_intent: Optional[str]

    class Config:
        from_attributes = True


class ArticleFeedbackCreate(BaseModelEAT):
    """Schema for Article Feedback model in MGLTickets."""
    article_slug: str
    feedback: str

    class Config:
        from_attributes = True


class ArticleSearchQueryOut(BaseModelEAT):
    """Schema for outputting article search query data."""
    
    id: int
    query: str
    results_count: int
    user_id: Optional[int]
    session_id: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ArticleSearchQueryCreate(BaseModelEAT):
    """Schema for creating an article search query record."""
    
    query: str = Field(..., min_length=1, max_length=500, description="Search query text")
    results_count: int = Field(..., ge=0, description="Number of results returned")
    session_id: Optional[str] = Field(None, max_length=255, description="Session ID for anonymous users")
    
    class Config:
        from_attributes = True


class ArticleSearchClickCreate(BaseModelEAT):
    """Schema for creating an article search click record."""
    
    search_query_id: int = Field(..., description="ID of the search query")
    clicked_article_slug: str = Field(..., min_length=1, max_length=255, description="Slug of clicked article")
    clicked_article_title: Optional[str] = Field(None, max_length=500, description="Title of clicked article")
    result_position: Optional[int] = Field(None, ge=1, description="Position in search results (1-indexed)")
    time_to_click_seconds: Optional[int] = Field(None, ge=0, description="Seconds between search and click")
    
    @validator('result_position')
    def validate_position(cls, v):
        if v is not None and v < 1:
            raise ValueError('Result position must be at least 1')
        return v
    
    class Config:
        from_attributes = True


class ArticleSearchClickOut(BaseModelEAT):
    """Schema for outputting article search click data."""
    
    id: int
    search_query_id: int
    clicked_article_slug: str
    clicked_article_title: Optional[str]
    result_position: Optional[int]
    time_to_click_seconds: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class SearchAnalytics(BaseModelEAT):
    """Aggregated search analytics."""
    
    total_searches: int
    total_clicks: int
    click_through_rate: float
    avg_results_per_search: float
    avg_time_to_click: Optional[float]
    most_searched_terms: list[tuple[str, int]]  # (query, count)
    most_clicked_articles: list[tuple[str, int]]  # (slug, count)
    searches_with_no_clicks: int
    
    class Config:
        from_attributes = True


class PopularSearchTerm(BaseModelEAT):
    """Popular search term with metadata."""
    
    query: str
    search_count: int
    avg_results: float
    click_through_rate: float
    most_clicked_article: Optional[str]
    
    class Config:
        from_attributes = True