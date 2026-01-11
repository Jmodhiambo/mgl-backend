#!/usr/bin/env python3
"""Admin Article Analytics routes."""

from fastapi import APIRouter, Depends, status
from app.schemas.article_analytics import ArticleViewOut, ArticleFeedbackOut, ArticleSearchQueryOut
import app.services.article_analytics_services as aa_services
from app.core.security import require_user

router = APIRouter()


@router.post("/analytics/article-views", response_model=ArticleViewOut, status_code=status.HTTP_201_CREATED)
async def track_article_view(
    article_slug: str,
    session_id: str = None, 
    referrer: str = None,
    device_type: str = None,
    time_spent_seconds: int = None, 
    scroll_depth_percent: int = None,
    user=Depends(require_user)
):
    """
    Track when someone views an article.
    """
    return await aa_services.track_article_view_service(
        article_slug = article_slug,
        user_id = user.id,
        session_id = session_id,
        referrer = referrer,
        device_type = device_type,
        time_spent_seconds = time_spent_seconds,
        scroll_depth_percent = scroll_depth_percent
    )


@router.post("/analytics/article-feedback", response_model=ArticleFeedbackOut, status_code=status.HTTP_201_CREATED)
async def submit_article_feedback(
    article_slug: str,
    is_helpful: bool,
    feedback_text: str,
    user_intent: str,
    user=Depends(require_user)
):
    """
    Submit article feedback.
    """
    return await aa_services.submit_article_feedback_service(
        article_slug = article_slug,
        user_id = user.id,
        is_helpful = is_helpful,
        feedback_text = feedback_text,
        user_intent = user_intent
    )


@router.post("/analytics/article-search", response_model=ArticleSearchQueryOut, status_code=status.HTTP_201_CREATED)
async def submit_article_search(
    query: str,
    user=Depends(require_user)
):
    """
    Submit article search query.
    """
    return await aa_services.submit_article_search_query_service(
        query = query,
        user_id = user.id
    )