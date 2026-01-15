#!/usr/bin/env python3
"""Articles Analytics model for MGLTickets."""

from sqlalchemy import ForeignKey, Integer, DateTime, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from app.db.session import Base
from typing import Optional

class ArticleView(Base):
    """Database Article Views model for MGLTickets."""

    __tablename__ = "article_views"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    article_slug: Mapped[str] = mapped_column(String(255), nullable=False)  # Referencces static article
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True) # Null if not logged in
    session_id: Mapped[str] = mapped_column(String(255), nullable=False)  # Unique session ID
    referrer: Mapped[str] = mapped_column(String(255), nullable=True)     # Where they came from
    device_type: Mapped[str] = mapped_column(String(50), nullable=True)   # Desktop, Mobile, Tablet
    user_agent: Mapped[str] = mapped_column(String(255), nullable=True)   # User agent
    screen_width: Mapped[int] = mapped_column(Integer, nullable=True)     # Screen width
    screen_height: Mapped[int] = mapped_column(Integer, nullable=True)    # Screen height
    viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc))


    def __repr__(self):
        return f"<ArticleView id={self.id} article_slug={self.article_slug} user_id={self.user_id} viewed_at={self.viewed_at}>"
    

class ArticleEngagement(Base):
    """Database Article Engagement model for MGLTickets."""

    __tablename__ = "article_engagements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    article_slug: Mapped[str] = mapped_column(String(255), nullable=False)  # Referencces static article
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True) # Null if not logged in
    session_id: Mapped[str] = mapped_column(String(255), nullable=True)  # Unique session ID
    time_spent_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    scroll_depth_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    engaged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    def __repr__(self):
        return f"<ArticleEngagement id={self.id} article_slug={self.article_slug} user_id={self.user_id} engaged_at={self.engaged_at}>"
    

class ArticleFeedback(Base):
    """Database Article Feedback model for MGLTickets."""

    __tablename__ = "article_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    article_slug: Mapped[str] = mapped_column(String(255), index=True, nullable=False)  # Referencces static article
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True) # Null if not logged in
    is_helpful: Mapped[bool] = mapped_column(Boolean, nullable=False)  # True or False
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    def __repr__(self):
        return f"<ArticleFeedback id={self.id} article_slug={self.article_slug} user_id={self.user_id} is_helpful={self.is_helpful} created_at={self.created_at}>"
    

class ArticleSearchQuery(Base):
    """Tracks help article search queries."""

    __tablename__ = "article_search_queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    query: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    results_count: Mapped[int] = mapped_column(Integer, nullable=False)
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    # Relationships
    clicks: Mapped[list["ArticleSearchClick"]] = relationship("ArticleSearchClick", back_populates="search_query")

    
    def __repr__(self):
        return f"<ArticleSearchQuery id={self.id} query={self.query} user_id={self.user_id} results_count={self.results_count} created_at={self.created_at}>"
    

class ArticleSearchClick(Base):
    """Tracks which articles users click from search results."""

    __tablename__ = "article_search_clicks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    search_query_id: Mapped[int] = mapped_column(Integer, ForeignKey("article_search_queries.id"), nullable=False)
    clicked_article_slug: Mapped[str] = mapped_column(String(255), nullable=True)  # Referencces static article
    clicked_article_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Position in search results (1-indexed)
    result_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timing
    time_to_click_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    # Relationships
    search_query: Mapped["ArticleSearchQuery"] = relationship("ArticleSearchQuery", back_populates="clicks")

    def __repr__(self):
        return f"<ArticleSearchClick id={self.id} query_id={self.search_query_id} article_slug={self.article_slug} created_at={self.created_at}>"