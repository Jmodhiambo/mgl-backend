#!/usr/bin/env python3
"""Service layer for Article Analytics operations."""

from typing import Optional
import app.db.repositories.article_analytics_repo as article_analytics_repo
from app.schemas.article_analytics import ArticleViewCreate, ArticleEngagementCreate, ArticleSearchClickCreate
from app.core.logging_config import logger


async def create_article_view_service(user_id: Optional[int], client_ip: Optional[str], article_data: ArticleViewCreate) -> dict:
    """Track an article view."""
    logger.info(f"Tracking article view for {article_data.article_slug}")
    await article_analytics_repo.create_article_view_repo(
        article_slug=article_data.article_slug,
        user_id=user_id,
        session_id=article_data.session_id,
        referrer=article_data.referrer,
        device_type=article_data.device_type,
        user_agent=article_data.user_agent,
        screen_width=article_data.screen_width,
        screen_height=article_data.screen_height,
        client_ip=client_ip
    )
    return {"message": "Article view tracked successfully."}


async def create_article_engagement_service(user_id: Optional[int], article_data: ArticleEngagementCreate) -> dict:
    """Track an article engagement."""
    logger.info(f"Tracking article engagement for {article_data.article_slug}")
    await article_analytics_repo.create_article_engagement_repo(
        article_slug=article_data.article_slug,
        user_id=user_id,
        session_id=article_data.session_id,
        time_spent_seconds=article_data.time_spent_seconds,
        scroll_depth_percent=article_data.scroll_depth_percent
    )
    return {"message": "Article engagement tracked successfully."}


async def create_article_feedback_service(
        article_slug: str,
        is_helpful: bool,
        user_id: Optional[int] = None
    ) -> dict:
    """Submit article feedback."""
    logger.info(f"Submitting article feedback for {article_slug}")
    await article_analytics_repo.create_article_feedback_repo(
        article_slug,
        is_helpful,
        user_id
    )
    return {"message": "Article feedback submitted successfully."}


async def create_article_search_query_service(
        query: str,
        results_count: int,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_id: Optional[int] = None,
):
    """Submit an article search query. Returns the created row (frontend
    needs the generated `id` back so it can attribute a later click to
    this search)."""
    logger.info(f"Submitting article search query for {query!r}")
    return await article_analytics_repo.create_article_search_query_repo(
        query=query,
        results_count=results_count,
        session_id=session_id,
        ip_address=ip_address,
        user_id=user_id,
    )


async def create_article_search_click_service(user_id: Optional[int], article_data: ArticleSearchClickCreate) -> int:
    """Submit article search click. And return search query id."""
    logger.info(f"Submitting article search click for {article_data.clicked_article_slug} and {article_data.search_query_id}")
    return await article_analytics_repo.create_article_search_click_repo(
        search_query_id=article_data.search_query_id,
        clicked_article_slug=article_data.clicked_article_slug,
        clicked_article_title=article_data.clicked_article_title,
        result_position=article_data.result_position,
        time_to_click_seconds=article_data.time_to_click_seconds,
        user_id=user_id
    )


async def get_article_stats_service(article_slug: str):
    """Get article stats."""
    logger.info(f"Getting article stats for {article_slug}")
    return await article_analytics_repo.get_article_stats_repo(article_slug)


async def get_top_articles_service(limit: int = 10, days: int = 30):
    """Get the most viewed articles in the last X days."""
    logger.info(f"Getting top articles for {days} days")
    return await article_analytics_repo.get_top_articles_repo(limit, days)


async def get_articles_needing_improvement_service(threshold: float = 0.50):
    """Get articles whose feedback helpfulness rate is below `threshold`."""
    logger.info(f"Getting articles needing improvement")
    return await article_analytics_repo.get_articles_needing_improvement_repo(threshold)


async def get_search_queries_service(limit: int = 10, days: int = 30):
    """Get the most recent search queries in the last X days."""
    logger.info(f"Getting search queries for {days} days")
    return await article_analytics_repo.get_search_queries_repo(limit, days)


async def get_search_clicks_service(days: int = 30, limit: int = 50):
    """Get recent search-result clicks."""
    logger.info(f"Getting search clicks for {days} days")
    return await article_analytics_repo.get_search_clicks_repo(days, limit)


async def get_popular_search_terms_service(limit: int = 10, days: int = 30):
    """Get the most popular distinct search terms in the last X days."""
    logger.info(f"Getting popular search terms for {days} days")
    return await article_analytics_repo.get_popular_search_terms_repo(limit, days)


async def search_analytics_service(days: int = 30):
    """Get aggregated search analytics (totals, CTR, top terms/articles)."""
    logger.info(f"Getting search analytics for {days} days")
    return await article_analytics_repo.search_analytics_repo(days)


async def get_articles_overview_service(days: int = 30):
    """Get the sitewide Help Center summary for the dashboard's top cards."""
    logger.info(f"Getting articles overview for {days} days")
    return await article_analytics_repo.get_articles_overview_repo(days)