#!/usr/bin/env python3
"""Service layer for Article Analytics operations."""

from typing import Optional
import app.db.repositories.article_analytics_repo as article_analytics_repo
from app.schemas.article_analytics import ArticleViewCreate, ArticleEngagementCreate, ArticleSearchClickCreate
from app.core.logging_config import logger


async def create_article_view_service(user_id: Optional[int], client_ip: Optional[str], article_data: ArticleViewCreate) -> dict[str, str] | None:
    """Track an article view."""
    logger.info(f"Tracking article view for {article_data.article_slug}")
    return await article_analytics_repo.create_article_view_repo(
        article_slug = article_data.article_slug,
        user_id = user_id,
        session_id = article_data.session_id,
        referrer = article_data.referrer,
        device_type = article_data.device_type,
        user_agent = article_data.user_agent,
        screen_width = article_data.screen_width,
        screen_height = article_data.screen_height,
        client_ip = client_ip
    )


async def create_article_engagement_service(user_id: Optional[int], article_data: ArticleEngagementCreate) -> dict[str, str] | None:
    """Track an article engagement."""
    logger.info(f"Tracking article engagement for {article_data.article_slug}")
    return await article_analytics_repo.create_article_engagement_repo(
        article_slug = article_data.article_slug,
        user_id = user_id,
        session_id = article_data.session_id,
        time_spent_seconds = article_data.time_spent_seconds,
        scroll_depth_percent = article_data.scroll_depth_percent
    )

async def create_article_feedback_service(
        article_slug: str,
        is_helpful: bool,
        user_id: Optional[int] = None
    ) -> dict[str, str] | None:
    """Submit article feedback."""
    logger.info(f"Submitting article feedback for {article_slug}")
    return await article_analytics_repo.create_article_feedback_repo(
        article_slug,
        is_helpful,
        user_id
    )


async def create_article_search_query_service(query: str, clicked_article_slug: Optional[str] = None, results_count: int = 0, user_id: int = None) -> dict[str, str] | None:
    """Submit article search query."""
    logger.info(f"Submitting article search query for {query}")
    return await article_analytics_repo.create_article_search_query_repo(query, clicked_article_slug, results_count, user_id)


async def create_article_search_click_service(user_id: Optional[int], article_data: ArticleSearchClickCreate ) -> int:
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


async def get_article_stats_service(article_slug: str) -> dict[str, str] | None:
    """Get article stats."""
    logger.info(f"Getting article stats for {article_slug}")
    return await article_analytics_repo.get_article_stats_repo(article_slug)


async def get_top_articles_service(limit: int = 10, days: int = 30) -> list[dict[str, str]] | None:
    """Get the most viewed articles based on search queries in the last X days."""
    logger.info(f"Getting top articles for {days} days")
    return await article_analytics_repo.get_top_articles_repo(limit, days)


async def get_articles_needing_improvement_service(threshold: float = 0.50) -> list[dict[str, str]] | None:
    """Get the most viewed articles based on search queries in the last X days."""
    logger.info(f"Getting articles needing improvement")
    return await article_analytics_repo.get_articles_needing_improvement_repo(threshold)


async def get_search_queries_service(limit: int = 10, days: int = 30) -> list[dict[str, str]] | None:
    """Get the most popular search queries in the last X days."""
    logger.info(f"Getting search queries for {days} days")
    return await article_analytics_repo.get_search_queries_repo(limit, days)


async def get_popular_search_terms_service(limit: int = 10, days: int = 30) -> Optional[dict[str, str]]:
    """Get the most popular search queries in the last X days."""
    logger.info(f"Getting popular search term for {days} days")
    return await article_analytics_repo.get_popular_search_terms_repo(limit, days)


async def search_analytics_service(days: int = 30) -> Optional[dict[str, str]]:
    """Get the most popular search queries in the last X days."""
    logger.info(f"Getting search analytics for {days} days")
    return await article_analytics_repo.search_analytics_repo(days)