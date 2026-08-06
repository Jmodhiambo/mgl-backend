#!/usr/bin/env python3
"""Schemas for Article Analytics model in MGLTickets."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class AnalyticsAck(BaseModel):
    """Generic acknowledgement for fire-and-forget tracking endpoints
    (view/engagement/feedback). These endpoints don't need to echo the
    full DB row back — the frontend just needs a 2xx."""
    message: str


class CountBucket(BaseModel):
    """Generic (label, count) bucket — used for device/referrer/user-agent
    breakdowns in ArticleStatsOut."""
    label: Optional[str] = None
    count: int

    class Config:
        from_attributes = True


class ViewsOverTimeEntry(BaseModel):
    viewed_at: datetime
    count: int

    class Config:
        from_attributes = True


class ArticleStatsOut(BaseModel):
    """Full stats breakdown for a single article (admin drill-down)."""
    total_views: int
    unique_sessions: int
    average_time_spent: Optional[float] = None
    average_scroll_depth: Optional[float] = None
    max_time_spent: Optional[int] = None
    max_scroll_depth: Optional[int] = None
    device_breakdown: list[CountBucket] = []
    top_referrers: list[CountBucket] = []
    top_user_agents: list[CountBucket] = []
    views_over_time: list[ViewsOverTimeEntry] = []
    total_feedback: int
    helpful_count: int
    not_help_count: int

    class Config:
        from_attributes = True


class TopArticleOut(BaseModel):
    """A single row in the 'top viewed articles' admin dashboard list."""
    article_slug: str
    view_count: int
    unique_sessions: int

    class Config:
        from_attributes = True


class ArticleImprovementCandidate(BaseModel):
    """An article whose feedback helpfulness rate is below the admin's threshold."""
    article_slug: str
    total_feedback: int
    helpful_count: int
    helpful_rate: float

    class Config:
        from_attributes = True


class ArticlesOverviewOut(BaseModel):
    """Sitewide Help Center summary — the top cards on the admin dashboard."""
    total_views: int
    total_unique_sessions: int
    total_searches: int
    total_feedback: int
    helpful_rate: Optional[float] = None
    avg_engagement_seconds: Optional[float] = None
    articles_needing_improvement: int

    class Config:
        from_attributes = True


class ArticleViewOut(BaseModel):
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
    client_ip: Optional[str] = None
    viewed_at: datetime

    class Config:
        from_attributes = True


class ArticleViewCreate(BaseModel):
    """Schema for Article View model in MGLTickets."""
    article_slug: str
    session_id: str
    referrer: Optional[str] = None
    device_type: Optional[str] = None
    user_agent: Optional[str] = None
    screen_width: Optional[int] = None
    screen_height: Optional[int] = None

    class Config:
        from_attributes = True


class ArticleEngagementOut(BaseModel):
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


class ArticleEngagementCreate(BaseModel):
    """Schema for Article Engagement model in MGLTickets."""
    article_slug: str
    session_id: str
    time_spent_seconds: int
    scroll_depth_percent: int

    class Config:
        from_attributes = True


class ArticleFeedbackOut(BaseModel):
    """Schema for Article Feedback model in MGLTickets."""
    id: int
    article_slug: str
    user_id: Optional[int]
    is_helpful: bool
    feedback_text: Optional[str] = None
    created_at: datetime
    user_intent: Optional[str] = None

    class Config:
        from_attributes = True


class ArticleFeedbackCreate(BaseModel):
    """Schema for Article Feedback model in MGLTickets."""
    article_slug: str
    feedback: str

    class Config:
        from_attributes = True


class ArticleSearchQueryOut(BaseModel):
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


class ArticleSearchQueryCreate(BaseModel):
    """Schema for creating an article search query record."""

    query: str = Field(..., min_length=1, max_length=500, description="Search query text")
    results_count: int = Field(..., ge=0, description="Number of results returned")
    session_id: Optional[str] = Field(None, max_length=255, description="Session ID for anonymous users")

    class Config:
        from_attributes = True


class ArticleSearchClickCreate(BaseModel):
    """Schema for creating an article search click record."""

    search_query_id: int = Field(..., description="ID of the search query")
    clicked_article_slug: str = Field(..., min_length=1, max_length=255, description="Slug of clicked article")
    clicked_article_title: Optional[str] = Field(None, max_length=500, description="Title of clicked article")
    result_position: Optional[int] = Field(None, ge=1, description="Position in search results (1-indexed)")
    time_to_click_seconds: Optional[int] = Field(None, ge=0, description="Seconds between search and click")

    @field_validator('result_position')
    def validate_position(cls, v):
        if v is not None and v < 1:
            raise ValueError('Result position must be at least 1')
        return v

    class Config:
        from_attributes = True


class ArticleSearchClickOut(BaseModel):
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


class SearchAnalytics(BaseModel):
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


class PopularSearchTerm(BaseModel):
    """Popular search term with metadata."""

    query: str
    search_count: int
    avg_results: float
    click_through_rate: float
    most_clicked_article: Optional[str]

    class Config:
        from_attributes = True