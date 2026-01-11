#!/usr/bin/env python3
"""Articles Analytics model for MGLTickets."""

from sqlalchemy import ForeignKey, Integer, DateTime, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from app.db.session import Base
from typing import Optional

class ArticleView(Base):
    """Database Article Views model for MGLTickets."""

    __tablename__ = "article_views"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    article_slug: Mapped[str] = mapped_column(String(255), nullable=False)  # Referencces static article
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True) # Null if not logged in
    viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    session_id: Mapped[str] = mapped_column(String(255), nullable=False)  # Unique session ID
    referrer: Mapped[str] = mapped_column(String(255), nullable=True)     # Where they came from
    device_type: Mapped[str] = mapped_column(String(50), nullable=True)   # Desktop, Mobile, Tablet

    # Time spent on article
    time_spent_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    scroll_depth_percent: Mapped[int] = mapped_column(Integer, nullable=True)

    def __repr__(self):
        return f"<ArticleView id={self.id} article_slug={self.article_slug} user_id={self.user_id} viewed_at={self.viewed_at}>"
    

class ArticleFeedback(Base):
    """Database Article Feedback model for MGLTickets."""

    __tablename__ = "article_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    article_slug: Mapped[str] = mapped_column(String(255), index=True, nullable=False)  # Referencces static article
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True) # Null if not logged in
    is_helpful: Mapped[bool] = mapped_column(Boolean, nullable=False)  # True or False
    feedback_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=False)  # Optional detailed feedback
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc))

    # Optional: What was the user trying to do?
    user_intent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    def __repr__(self):
        return f"<ArticleFeedback id={self.id} article_slug={self.article_slug} user_id={self.user_id} is_helpful={self.is_helpful} created_at={self.created_at}>"
    

class ArticleSearchQuery(Base):
    """Database Article Search Query model for MGLTickets."""

    __tablename__ = "article_search_queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    query: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    results_count: Mapped[int] = mapped_column(Integer, nullable=False)
    clicked_article_slug: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.now(timezone.utc))


    def __repr__(self):
        return f"<ArticleSearchQuery id={self.id} query={self.query} user_id={self.user_id} results_count={self.results_count} clicked_article_slug={self.clicked_article_slug} created_at={self.created_at}>"