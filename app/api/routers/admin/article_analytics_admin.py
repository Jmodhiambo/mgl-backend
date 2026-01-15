#!/usr/bin/env python3
"""Admin Article Analytics routes."""

from fastapi import APIRouter, Depends, status
from typing import Optional
from app.schemas.article_analytics import ArticleViewOut, ArticleFeedbackOut, ArticleSearchQueryOut, ArticleSearchClickOut, SearchAnalytics, PopularSearchTerm
import app.services.article_analytics_services as aa_services
from app.core.security import require_admin

router = APIRouter()


@router.get("/admin/analytics/articles/{article_slug}/stats", response_model=Optional[dict[str, str]], status_code=status.HTTP_200_OK)
async def get_article_stats(article_slug: str, user=Depends(require_admin)) -> Optional[dict[str, str]]:
    """Get article stats."""
    return await aa_services.get_article_stats_service(article_slug)


@router.get("/admin/analytics/articles/top", response_model=list[ArticleViewOut], status_code=status.HTTP_200_OK)
async def get_top_articles(limit: int = 10, days: int = 30, user=Depends(require_admin)) -> list[ArticleViewOut]:
    """Get the most viewed articles based on search queries in the last X days."""
    return await aa_services.get_top_articles_service(limit, days)


@router.get("/admin/analytics/articles/needing-improvement", response_model=list[ArticleFeedbackOut], status_code=status.HTTP_200_OK)
async def get_articles_needing_improvement(threshold: float = 0.50, user=Depends(require_admin)) -> list[ArticleFeedbackOut]:
    """Get the most viewed articles based on search queries in the last X days."""
    return await aa_services.get_articles_needing_improvement_service(threshold)


@router.get("/admin/analytics/search-queries", response_model=list[ArticleSearchQueryOut], status_code=status.HTTP_200_OK)
async def get_search_queries(limit: int = 10, days: int = 30, user=Depends(require_admin)) -> list[ArticleSearchQueryOut]:
    """Get the most popular search queries in the last X days."""
    return await aa_services.get_search_queries_service(limit, days)


@router.get("/admin/analytics/search-terms", response_model=list[PopularSearchTerm], status_code=status.HTTP_200_OK)
async def get_popular_search_terms(limit: int = 10, days: int = 30, user=Depends(require_admin)) -> list[PopularSearchTerm]:
    """Get the most popular search queries in the last X days."""
    return await aa_services.get_popular_search_terms_service(limit, days)


@router.get("/admin/analytics/search-clicks", response_model=list[ArticleSearchClickOut], status_code=status.HTTP_200_OK)
async def get_search_clicks(days: int = 30, user=Depends(require_admin)) -> list[ArticleSearchClickOut]:
    """Get the most popular search queries in the last X days."""
    return await aa_services.search_analytics_service(days)