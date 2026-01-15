#!/usr/bin/env python3
"""Async repository for ArticleAnalytics model operations."""

from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy import Integer, select, func, distinct
from app.db.session import get_async_session
from app.db.models.article_analytics import ArticleView, ArticleFeedback, ArticleSearchQuery, ArticleEngagement, ArticleSearchClick
from app.schemas.article_analytics import ArticleViewOut, ArticleFeedbackOut, ArticleSearchQueryOut, PopularSearchTerm, SearchAnalytics

async def create_article_view_repo(
        article_slug: str,
        user_id: Optional[int],
        session_id: str,
        referrer: str,
        device_type: str,
        user_agent: str,
        screen_width: int,
        screen_height: int,
        client_ip: str
    ) -> ArticleView:
    """Track an article view."""
    async with get_async_session() as session:
        article_view = ArticleView(
            article_slug=article_slug,
            user_id=user_id,
            session_id=session_id,
            referrer=referrer,
            device_type=device_type,
            user_agent=user_agent,
            screen_width=screen_width,
            screen_height=screen_height,
            client_ip=client_ip
        )
        session.add(article_view)
        await session.commit()
        await session.refresh(article_view)
        return ArticleViewOut.model_validate(article_view)
    
async def create_article_engagement_repo(
        article_slug: str, 
        user_id: Optional[int],
        session_id: str,
        time_spent_seconds: Optional[int],
        scroll_depth_percent: Optional[int]
) -> ArticleView:
    """Track an article engagement."""
    async with get_async_session() as session:
        article_view = ArticleView(
            article_slug=article_slug,
            user_id=user_id,
            session_id=session_id,
            time_spent_seconds=time_spent_seconds,
            scroll_depth_percent=scroll_depth_percent
        )
        session.add(article_view)
        await session.commit()
        await session.refresh(article_view)
        return ArticleViewOut.model_validate(article_view)
    
async def create_article_feedback_repo(article_slug: str, is_helpful: bool, user_id: Optional[int]) -> ArticleFeedback:
    """Submit article feedback."""
    async with get_async_session() as session:
        article_feedback = ArticleFeedback(
            article_slug=article_slug,
            is_helpful=is_helpful,
            user_id=user_id
        )
        session.add(article_feedback)
        await session.commit()
        await session.refresh(article_feedback)
        return ArticleFeedbackOut.model_validate(article_feedback)
    
async def create_article_search_query_repo(query: str, clicked_article_slug: str, results_count: int, user_id: int = None) -> ArticleSearchQuery:
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


async def create_article_search_click_repo(
        search_query_id: int,
        clicked_article_slug: str,
        clicked_article_title: Optional[str] = None,
        result_position: Optional[int] = None,
        time_to_click_seconds: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> dict[str, str]:
    """Submit article search query."""
    async with get_async_session() as session:
        article_search_click = ArticleSearchClick(
            search_query_id=search_query_id,
            clicked_article_slug=clicked_article_slug,
            clicked_article_title=clicked_article_title,
            result_position=result_position,
            time_to_click_seconds=time_to_click_seconds,
            user_id=user_id
        )
        session.add(article_search_click)
        await session.commit()
        await session.refresh(article_search_click)
        return article_search_click.search_query_id   # Only need to send query id to the frontend
    
 
async def get_article_stats_repo(article_slug: str) -> Optional[dict[str, str]]:
    """Get article stats."""
    async with get_async_session() as session:

        # Total views
        total_views = await session.execute(
            select(func.count(ArticleView.id)).where(ArticleView.article_slug == article_slug)
        )

        # Unique sessions
        unique_sessions = await session.execute(
            select(func.count(distinct(ArticleView.session_id))).where(ArticleView.article_slug == article_slug)
        )

        # Average engagement metrics
        average_time_spent = await session.execute(
            select(func.avg(ArticleEngagement.time_spent_seconds)).where(ArticleView.article_slug == article_slug)
        )
        average_scroll_depth = await session.execute(
            select(func.avg(ArticleEngagement.scroll_depth_percent)).where(ArticleView.article_slug == article_slug)
        )
        max_time_spent = await session.execute(
            select(func.max(ArticleEngagement.time_spent_seconds)).where(ArticleView.article_slug == article_slug)
        )
        max_scroll_depth = await session.execute(
            select(func.max(ArticleEngagement.scroll_depth_percent)).where(ArticleView.article_slug == article_slug)
        )

        # Device breakdown
        device_breakdown = await session.execute(
            select(ArticleView.device_type, func.count(ArticleView.id)).where(ArticleView.article_slug == article_slug).group_by(ArticleView.device_type)
        )

        # Top referrers
        top_referrers = await session.execute(
            select(ArticleView.referrer, func.count(ArticleView.id)).where(ArticleView.article_slug == article_slug).group_by(ArticleView.referrer).order_by(func.count(ArticleView.id).desc())
        )

        # Top user agents
        top_user_agents = await session.execute(
            select(ArticleView.user_agent, func.count(ArticleView.id)).where(ArticleView.article_slug == article_slug).group_by(ArticleView.user_agent).order_by(func.count(ArticleView.id).desc())
        )

        # Views over time (last 30 days)
        views_over_time = await session.execute(
            select(ArticleView.viewed_at, func.count(ArticleView.id)).where(ArticleView.article_slug == article_slug).group_by(ArticleView.created_at).order_by(ArticleView.created_at.desc())
        )

        # Feedback stats
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
            "total_views": total_views.scalars().one(),
            "unique_sessions": unique_sessions.scalars().one(),
            "average_time_spent": average_time_spent.scalars().one(),
            "average_scroll_depth": average_scroll_depth.scalars().one(),
            "max_time_spent": max_time_spent.scalars().one(),
            "max_scroll_depth": max_scroll_depth.scalars().one(),
            "device_breakdown": device_breakdown.all(),
            "top_referrers": top_referrers.all(),
            "top_user_agents": top_user_agents.all(),
            "views_over_time": views_over_time.all(),
            "total_feedback": total_feedback.scalars().one(),
            "helpful_count": helpful_count.scalars().one(),
            "not_help_count": not_help_count.scalars().one(),
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
    

async def get_popular_search_terms_repo(limit: int = 10, days: int = 30) -> PopularSearchTerm:
    """Get the most popular search term in the last X days."""
    async with get_async_session() as session:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        
        # The query
        query = await session.execute(
            select(ArticleSearchQuery.query)
            .where(ArticleSearchQuery.created_at >= since)
            .group_by(ArticleSearchQuery.query)
            .order_by(func.count(ArticleSearchQuery.id).desc())
            .limit(limit)
        )

        # Search count
        search_count = await session.execute(
            select(func.count(ArticleSearchQuery.id))
            .where(ArticleSearchQuery.created_at >= since)
            .group_by(ArticleSearchQuery.query)
            .order_by(func.count(ArticleSearchQuery.id).desc())
            .limit(limit)
        )

        # Average results
        average_results = await session.execute(
            select(func.avg(ArticleSearchQuery.results_count))
            .where(ArticleSearchQuery.created_at >= since)
            .group_by(ArticleSearchQuery.query)
            .order_by(func.count(ArticleSearchQuery.id).desc())
            .limit(limit)
        )

        # Click through rate
        click_through_rate = await session.execute(
            select(func.avg(ArticleSearchQuery.results_count))
            .where(ArticleSearchQuery.created_at >= since)
            .group_by(ArticleSearchQuery.query)
            .order_by(func.count(ArticleSearchQuery.id).desc())
            .limit(limit)
        )

        # Most clicked article
        most_clicked_article = await session.execute(
            select(ArticleSearchClick.clicked_article_slug)
            .where(ArticleSearchClick.created_at >= since)
            .group_by(ArticleSearchClick.search_query_id)
            .order_by(func.count(ArticleSearchClick.id).desc())
            .limit(limit)
        )

        return PopularSearchTerm(
            query=query.scalars().one(),
            search_count=search_count.scalars().one(),
            avg_results=average_results.scalars().one(),
            click_through_rate=click_through_rate.scalars().one(),
            most_clicked_article=most_clicked_article.scalars().one()
        )
    

async def search_analytics_repo(days: int = 30) -> SearchAnalytics:
    """Get search analytics."""
    async with get_async_session() as session:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        total_searches = await session.execute(
            select(func.count(ArticleSearchQuery.id)).where(ArticleSearchQuery.created_at >= since)
        )
        total_clicks = await session.execute(
            select(func.count(ArticleSearchClick.id)).where(ArticleSearchClick.created_at >= since)
        )
        click_through_rate = await session.execute(
            select(func.avg(ArticleSearchQuery.results_count)).where(ArticleSearchQuery.created_at >= since)
        )
        avg_results_per_search = await session.execute(
            select(func.avg(ArticleSearchQuery.results_count)).where(ArticleSearchQuery.created_at >= since)
        )
        avg_time_to_click = await session.execute(
            select(func.avg(ArticleSearchClick.created_at - ArticleSearchClick.created_at)).where(ArticleSearchClick.created_at >= since)
        )
        most_searched_terms = await session.execute(
            select(ArticleSearchQuery.query, func.count(ArticleSearchQuery.id))
            .where(ArticleSearchQuery.created_at >= since)
            .group_by(ArticleSearchQuery.query)
            .order_by(func.count(ArticleSearchQuery.id).desc())
            .limit(5)
        )
        most_clicked_articles = await session.execute(
            select(ArticleSearchClick.clicked_article_slug, func.count(ArticleSearchClick.id))
            .where(ArticleSearchClick.created_at >= since)
            .group_by(ArticleSearchClick.clicked_article_slug)
            .order_by(func.count(ArticleSearchClick.id).desc())
            .limit(5)
        )
        searches_with_no_clicks = await session.execute(
            select(func.count(ArticleSearchQuery.id))
            .where(ArticleSearchQuery.created_at >= since)
            .where(func.count(ArticleSearchClick.id) == 0)
        )

        return SearchAnalytics(
            total_searches=total_searches.scalars().one(),
            total_clicks=total_clicks.scalars().one(),
            click_through_rate=click_through_rate.scalars().one(),
            avg_results_per_search=avg_results_per_search.scalars().one(),
            avg_time_to_click=avg_time_to_click.scalars().one(),
            most_searched_terms=most_searched_terms.all(),
            most_clicked_articles=most_clicked_articles.all(),
            searches_with_no_clicks=searches_with_no_clicks.scalars().one()
        )