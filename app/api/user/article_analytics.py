#!/usr/bin/env python3
"""User Article Analytics routes."""

from fastapi import Request, APIRouter, Depends, status
from app.schemas.article_analytics import (
    ArticleViewOut, ArticleEngagementOut, ArticleFeedbackOut, ArticleSearchQueryOut,
    ArticleViewCreate, ArticleEngagementCreate, ArticleFeedbackCreate,
    ArticleSearchQueryCreate, ArticleSearchClickCreate,
    AnalyticsAck,
)
import app.services.article_analytics_services as aa_services
from app.core.security import get_current_user_optional

router = APIRouter()


def _client_ip(request: Request) -> str | None:
    """Same pattern as the login endpoint — prefer X-Real-IP (set by Nginx),
    fall back to the raw connection address."""
    return request.headers.get("x-real-ip") or (request.client.host if request.client else None)


@router.post("/analytics/article-view", response_model=AnalyticsAck, status_code=status.HTTP_201_CREATED)
async def create_article_view(request: Request, article_data: ArticleViewCreate, user=Depends(get_current_user_optional)):
    """
    Track when someone views an article.

    NOTE: previously this caught every exception and returned {"error": ...},
    which then failed response_model validation against ArticleViewOut and
    produced a confusing 500 that hid the real error. Letting the exception
    propagate now gives a clean traceback of the actual failure, and the
    response_model (AnalyticsAck) matches what's actually returned.
    """
    client_ip = _client_ip(request)
    user_id = user.id if user else None

    return await aa_services.create_article_view_service(
        user_id=user_id,
        client_ip=client_ip,
        article_data=article_data
    )


@router.post("/analytics/article-engagement", response_model=AnalyticsAck, status_code=status.HTTP_201_CREATED)
async def create_article_engagement(article_data: ArticleEngagementCreate, user=Depends(get_current_user_optional)):
    """
    Track when someone engages with an article.
    """
    return await aa_services.create_article_engagement_service(
        user_id=user.id if user else None,
        article_data=article_data
    )


@router.post("/analytics/article-feedback", response_model=AnalyticsAck, status_code=status.HTTP_201_CREATED)
async def create_article_feedback(
    article_data: ArticleFeedbackCreate,
    user=Depends(get_current_user_optional)
):
    """
    Submit article feedback.

    FIXED — this used to take article_slug/feedback as bare (query-string)
    params, but ArticleFeedback.tsx posts a JSON body. The body was being
    silently ignored and the request would 422 on the missing required
    query params. Now reads the body via ArticleFeedbackCreate, matching
    every other analytics endpoint.
    """
    is_helpful = article_data.feedback == "helpful"

    return await aa_services.create_article_feedback_service(
        article_slug=article_data.article_slug,
        is_helpful=is_helpful,
        user_id=user.id if user else None
    )


@router.post("/analytics/article-search", response_model=ArticleSearchQueryOut, status_code=status.HTTP_201_CREATED)
async def create_article_search_query(
    request: Request,
    article_data: ArticleSearchQueryCreate,
    user=Depends(get_current_user_optional)
):
    """
    Submit article search query.

    FIXED — this used to take `query: str` as a bare parameter, which
    FastAPI treats as a query-string param (?query=...), not a JSON body.
    HelpCenterPage.tsx posts a JSON body with query/results_count/session_id,
    so results_count and session_id were being silently dropped before.
    """
    return await aa_services.create_article_search_query_service(
        query=article_data.query,
        results_count=article_data.results_count,
        session_id=article_data.session_id,
        ip_address=_client_ip(request),
        user_id=user.id if user else None,
    )


@router.post("/analytics/article-search-click", response_model=int, status_code=status.HTTP_201_CREATED)
async def create_article_search_click(
    article_data: ArticleSearchClickCreate,
    user=Depends(get_current_user_optional)
):
    """
    Submit article search click.
    """
    return await aa_services.create_article_search_click_service(
        user_id=user.id if user else None,
        article_data=article_data
    )