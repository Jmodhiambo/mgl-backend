#!/usr/bin/env python3
"""Async repository for ArticleAnalytics model operations."""

from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, Integer
from app.db.session import get_async_session
from app.db.models.article_analytics import ArticleView, ArticleFeedback, ArticleSearchQuery
from app.schemas.article_analytics import ArticleViewOut, ArticleFeedbackOut, ArticleSearchQueryOut

async def track_article_view_repo(
        article_slug: str,
        user_id: int = None,
        session_id: str = None,
        referrer: str = None,
        device_type: str = None,
        time_spent_seconds: int = None,
        scroll_depth_percent: int = None
    ) -> ArticleView:
    """Track an article view."""
    async with get_async_session() as session:
        article_view = ArticleView(
            article_slug=article_slug,
            user_id=user_id,
            session_id=session_id,
            referrer=referrer,
            device_type=device_type,
            time_spent_seconds=time_spent_seconds,
            scroll_depth_percent=scroll_depth_percent,
        )
        session.add(article_view)
        await session.commit()
        await session.refresh(article_view)
        return ArticleViewOut.model_validate(article_view)
    
async def submit_article_feedback_repo(article_slug: str, user_id: int, feedback_type: str, feedback_text: str) -> ArticleFeedback:
    """Submit article feedback."""
    async with get_async_session() as session:
        article_feedback = ArticleFeedback(
            article_slug=article_slug,
            user_id=user_id,
            feedback_type=feedback_type,
            feedback_text=feedback_text,
        )
        session.add(article_feedback)
        await session.commit()
        await session.refresh(article_feedback)
        return ArticleFeedbackOut.model_validate(article_feedback)
    
async def submit_article_search_query_repo(query: str, clicked_article_slug: str, results_count: int, user_id: int = None) -> ArticleSearchQuery:
    """Submit article search query."""
    async with get_async_session() as session:
        article_search_query = ArticleSearchQuery(
            query=query,
            user_id=user_id,
            clicked_article_slug=clicked_article_slug,
            results_count=results_count
        )
        session.add(article_search_query)
        await session.commit()
        await session.refresh(article_search_query)
        return ArticleSearchQueryOut.model_validate(article_search_query)
    
async def get_article_stats_repo(article_slug: str) -> Optional[dict[str, str]]:
    """Get article stats."""
    async with get_async_session() as session:
        total_views = await session.execute(
            select(func.count(ArticleView.id)).where(ArticleView.article_slug == article_slug)
        )
        total_feedback = await session.execute(
            select(func.count(ArticleFeedback.id)).where(ArticleFeedback.article_slug == article_slug)
        )
        helpful_count = await session.execute(
            select(func.count(ArticleFeedback.id)).where(ArticleFeedback.article_slug == article_slug).where(ArticleFeedback.is_helpful == True)
        )
        not_help_count = await session.execute(
            select(func.count(ArticleFeedback.id)).where(ArticleFeedback.article_slug == article_slug).where(ArticleFeedback.is_helpful == False)
        )
        return {
            "article_slug": article_slug,
            "total_views": total_views.scalar_one(),
            "total_feedback": total_feedback.scalar_one(),
            "helpful_count": helpful_count.scalar_one(),
            "not_help_count": not_help_count.scalar_one(),
            "helpful_percentage": (helpful_count.scalar_one() / total_feedback.scalar_one() * 100) if total_feedback.scalar_one() > 0 else 0
        }
    
async def get_top_articles_repo(limit: int = 10, days: int = 30) -> list[ArticleViewOut]:
    """Get the most viewed articles based on search queries in the last X days."""
    async with get_async_session() as session:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        top_articles = await session.execute(
            select(ArticleView)
            .where(ArticleView.viewed_at >= since)
            .group_by(ArticleView.article_slug)
            .order_by(func.count(ArticleView.id).desc())
            .limit(limit)
        )
        return [ArticleViewOut.model_validate(article) for article in top_articles.scalars().all()]

async def get_articles_needing_improvement_repo(threshold: float = 0.50) -> list[ArticleFeedbackOut]:
    """Find articles with low helpfulness rates."""
    async with get_async_session() as session:
        result = await session.execute(
            select(
                ArticleFeedback.article_slug,
                func.count(ArticleFeedback.id).label('total_feedback'),
                func.sum(func.cast(ArticleFeedback.is_helpful, Integer)).label('helpful_count')
            )
            .group_by(ArticleFeedback.article_slug)
            .having(
                func.sum(func.cast(ArticleFeedback.is_helpful, Integer)) / func.count(ArticleFeedback.id) < threshold
            )
        )
        return [ArticleFeedbackOut.model_validate(article) for article in result.scalars().all()]
    
async def get_search_queries_repo(limit: int = 10, days: int = 30) -> list[ArticleSearchQueryOut]:
    """Get the most popular search queries in the last X days."""
    async with get_async_session() as session:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        top_queries = await session.execute(
            select(ArticleSearchQuery)
            .where(ArticleSearchQuery.created_at >= since)
            .group_by(ArticleSearchQuery.query)
            .order_by(func.count(ArticleSearchQuery.id).desc())
            .limit(limit)
        )
        return [ArticleSearchQueryOut.model_validate(query) for query in top_queries.scalars().all()]