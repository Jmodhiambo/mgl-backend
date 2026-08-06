#!/usr/bin/env python3
"""Admin Article Analytics routes — powers the Help Center analytics dashboard."""

from fastapi import APIRouter, Depends, status
from typing import Optional
from app.schemas.article_analytics import (
    ArticleStatsOut, TopArticleOut, ArticleImprovementCandidate,
    ArticleSearchQueryOut, ArticleSearchClickOut, PopularSearchTerm,
    SearchAnalytics, ArticlesOverviewOut,
)
import app.services.article_analytics_services as aa_services
from app.core.security import require_admin

router = APIRouter()


@router.get("/admin/analytics/articles/overview", response_model=ArticlesOverviewOut, status_code=status.HTTP_200_OK)
async def get_articles_overview(days: int = 30, user=Depends(require_admin)) -> ArticlesOverviewOut:
    """Sitewide Help Center summary for the dashboard's top cards."""
    return await aa_services.get_articles_overview_service(days)


@router.get("/admin/analytics/articles/{article_slug}/stats", response_model=Optional[ArticleStatsOut], status_code=status.HTTP_200_OK)
async def get_article_stats(article_slug: str, user=Depends(require_admin)) -> Optional[ArticleStatsOut]:
    """Full stats breakdown for a single article (drill-down view)."""
    return await aa_services.get_article_stats_service(article_slug)


@router.get("/admin/analytics/articles/top", response_model=list[TopArticleOut], status_code=status.HTTP_200_OK)
async def get_top_articles(limit: int = 10, days: int = 30, user=Depends(require_admin)) -> list[TopArticleOut]:
    """Most viewed articles in the last X days, ranked by view count."""
    return await aa_services.get_top_articles_service(limit, days)


@router.get("/admin/analytics/articles/needing-improvement", response_model=list[ArticleImprovementCandidate], status_code=status.HTTP_200_OK)
async def get_articles_needing_improvement(threshold: float = 0.50, user=Depends(require_admin)) -> list[ArticleImprovementCandidate]:
    """Articles whose feedback helpfulness rate is below `threshold`."""
    return await aa_services.get_articles_needing_improvement_service(threshold)


@router.get("/admin/analytics/search-queries", response_model=list[ArticleSearchQueryOut], status_code=status.HTTP_200_OK)
async def get_search_queries(limit: int = 10, days: int = 30, user=Depends(require_admin)) -> list[ArticleSearchQueryOut]:
    """Most recent Help Center search queries (activity log)."""
    return await aa_services.get_search_queries_service(limit, days)


@router.get("/admin/analytics/search-terms", response_model=list[PopularSearchTerm], status_code=status.HTTP_200_OK)
async def get_popular_search_terms(limit: int = 10, days: int = 30, user=Depends(require_admin)) -> list[PopularSearchTerm]:
    """Most popular distinct search terms, with click-through rate and top resulting article."""
    return await aa_services.get_popular_search_terms_service(limit, days)


@router.get("/admin/analytics/search-clicks", response_model=list[ArticleSearchClickOut], status_code=status.HTTP_200_OK)
async def get_search_clicks(days: int = 30, limit: int = 50, user=Depends(require_admin)) -> list[ArticleSearchClickOut]:
    """Most recent search-result clicks (activity log)."""
    return await aa_services.get_search_clicks_service(days, limit)


@router.get("/admin/analytics/search-summary", response_model=SearchAnalytics, status_code=status.HTTP_200_OK)
async def get_search_summary(days: int = 30, user=Depends(require_admin)) -> SearchAnalytics:
    """Aggregated search analytics — totals, click-through rate, top terms/articles."""
    return await aa_services.search_analytics_service(days)