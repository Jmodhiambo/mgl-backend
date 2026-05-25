#!/usr/bin/env python3
"""Admin Article Analytics routes."""

from fastapi import Request, APIRouter, Depends, status
from app.schemas.article_analytics import (
    ArticleViewOut, ArticleEngagementOut, ArticleFeedbackOut, ArticleSearchQueryOut,
    ArticleViewCreate, ArticleEngagementCreate, ArticleSearchClickCreate
)
import app.services.article_analytics_services as aa_services
from app.core.security import get_current_user_optional

router = APIRouter()


@router.post("/analytics/article-view", response_model=ArticleViewOut, status_code=status.HTTP_201_CREATED)
async def create_article_view(request: Request, article_data: ArticleViewCreate, user=Depends(get_current_user_optional)):
    """
    Track when someone views an article.
    """
    try:
        # Get client IP address
        client_ip = request.client.host if request.client else None

        # Get user ID if authenticated else None
        user_id = user.id if user else None

        await aa_services.create_article_view_service(
            user_id = user_id,
            client_ip = client_ip,
            article_data = article_data
        )
        
        return {"message": "Article view tracked successfully."}
    except Exception as e:
        return {"error": str(e)}



@router.post("/analytics/article-engagement", response_model=ArticleEngagementOut, status_code=status.HTTP_201_CREATED)
async def create_article_engagement(article_data: ArticleEngagementCreate, user=Depends(get_current_user_optional)):
    """
    Track when someone engages with an article.
    """
    try:
        await aa_services.create_article_engagement_service(
            user_id = user.id if user else None,
            article_data = article_data
        )
        
        return {"message": "Article engagement tracked successfully."}
    except Exception as e:    
        return {"error": str(e)}


@router.post("/analytics/article-feedback", response_model=ArticleFeedbackOut, status_code=status.HTTP_201_CREATED)
async def create_article_feedback(
    article_slug: str,
    feedback: str,
    user=Depends(get_current_user_optional)
):
    """
    Submit article feedback.
    """
    try:
        is_helpful = True if feedback == "helpful" else False

        await aa_services.create_article_feedback_service(
            article_slug = article_slug,
            is_helpful = is_helpful,
            user_id = user.id if user else None
        )
        
        return {"message": "Article feedback submitted successfully."}
    except Exception as e:
        return {"error": str(e)}


@router.post("/analytics/article-search", response_model=ArticleSearchQueryOut, status_code=status.HTTP_201_CREATED)
async def create_article_search_query(
    query: str,
    user=Depends(get_current_user_optional)
):
    """
    Submit article search query.
    """
    return await aa_services.create_article_search_query_service(
        query = query,
        user_id = user.id if user else None
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
        user_id = user.id if user else None,
        article_data = article_data
    )