#!/usr/bin/env python3
"""Service layer for Article Analytics operations."""

from typing import Optional
import app.db.repositories.article_analytics_repo as article_analytics_repo
from app.core.logging_config import logger


async def track_article_view_service(
        article_slug: str,
        user_id: int = None,
        session_id: str = None,
        referrer: str = None,
        device_type: str = None,
        time_spent_seconds: int = None,
        scroll_depth_percent: int = None
    ) -> dict[str, str] | None:
    """Track an article view."""
    logger.info(f"Tracking article view for {article_slug}")
    return await article_analytics_repo.track_article_view_repo(article_slug, user_id, session_id, referrer, device_type, time_spent_seconds, scroll_depth_percent)


async def submit_article_feedback_service(
        article_slug: str,
        is_helpful: bool,
        feedback_text: str,
        user_intent: str,
        user_id: int = None
    ) -> dict[str, str] | None:
    """Submit article feedback."""
    logger.info(f"Submitting article feedback for {article_slug}")
    return await article_analytics_repo.submit_article_feedback_repo(
        article_slug,
        user_id,
        is_helpful,
        feedback_text,
        user_intent
    )


async def submit_article_search_query_service(query: str, clicked_article_slug: str = None, results_count: int = None, user_id: int = None) -> dict[str, str] | None:
    """Submit article search query."""
    logger.info(f"Submitting article search query for {query}")
    return await article_analytics_repo.submit_article_search_query_repo(query, clicked_article_slug, results_count, user_id)


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