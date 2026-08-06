#!/usr/bin/env python3
"""Async repository for ArticleAnalytics model operations."""

from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy import Integer, Float, select, func, distinct
from app.db.session import get_async_session
from app.db.models.article_analytics import ArticleView, ArticleFeedback, ArticleSearchQuery, ArticleEngagement, ArticleSearchClick
from app.schemas.article_analytics import (
    ArticleViewOut, ArticleEngagementOut, ArticleFeedbackOut, ArticleSearchQueryOut,
    ArticleSearchClickOut, PopularSearchTerm, SearchAnalytics,
    ArticleStatsOut, CountBucket, ViewsOverTimeEntry,
    TopArticleOut, ArticleImprovementCandidate, ArticlesOverviewOut,
)


async def create_article_view_repo(
        article_slug: str,
        user_id: Optional[int],
        session_id: str,
        referrer: Optional[str],
        device_type: Optional[str],
        user_agent: Optional[str],
        screen_width: Optional[int],
        screen_height: Optional[int],
        client_ip: Optional[str]
    ) -> ArticleViewOut:
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
            client_ip=client_ip,
        )
        session.add(article_view)
        await session.commit()
        await session.refresh(article_view)
        return ArticleViewOut.model_validate(article_view)


async def create_article_engagement_repo(
        article_slug: str,
        user_id: Optional[int],
        session_id: Optional[str],
        time_spent_seconds: int,
        scroll_depth_percent: int,
) -> ArticleEngagementOut:
    """Track an article engagement.
    FIXED — this used to construct an ArticleView(...) with engagement-only
    fields, which doesn't exist on that model and would 500 the same way
    the article-view endpoint did."""
    async with get_async_session() as session:
        article_engagement = ArticleEngagement(
            article_slug=article_slug,
            user_id=user_id,
            session_id=session_id,
            time_spent_seconds=time_spent_seconds,
            scroll_depth_percent=scroll_depth_percent,
        )
        session.add(article_engagement)
        await session.commit()
        await session.refresh(article_engagement)
        return ArticleEngagementOut.model_validate(article_engagement)


async def create_article_feedback_repo(article_slug: str, is_helpful: bool, user_id: Optional[int]) -> ArticleFeedbackOut:
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


async def create_article_search_query_repo(
        query: str,
        results_count: int,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_id: Optional[int] = None,
) -> ArticleSearchQueryOut:
    """Submit article search query.
    FIXED — this used to pass clicked_article_slug into ArticleSearchQuery(...),
    a column that only exists on ArticleSearchClick, and silently dropped
    results_count/session_id even though the model (and the frontend payload)
    both carry them."""
    async with get_async_session() as session:
        article_search_query = ArticleSearchQuery(
            query=query,
            user_id=user_id,
            results_count=results_count,
            session_id=session_id,
            ip_address=ip_address,
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
    ) -> int:
    """Record an article search click. Returns the search_query_id."""
    async with get_async_session() as session:
        article_search_click = ArticleSearchClick(
            search_query_id=search_query_id,
            clicked_article_slug=clicked_article_slug,
            clicked_article_title=clicked_article_title,
            result_position=result_position,
            time_to_click_seconds=time_to_click_seconds,
        )
        session.add(article_search_click)
        await session.commit()
        await session.refresh(article_search_click)
        return article_search_click.search_query_id   # Only need to send query id to the frontend


async def get_article_stats_repo(article_slug: str) -> Optional[ArticleStatsOut]:
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
            select(func.avg(ArticleEngagement.time_spent_seconds)).where(ArticleEngagement.article_slug == article_slug)
        )
        average_scroll_depth = await session.execute(
            select(func.avg(ArticleEngagement.scroll_depth_percent)).where(ArticleEngagement.article_slug == article_slug)
        )
        max_time_spent = await session.execute(
            select(func.max(ArticleEngagement.time_spent_seconds)).where(ArticleEngagement.article_slug == article_slug)
        )
        max_scroll_depth = await session.execute(
            select(func.max(ArticleEngagement.scroll_depth_percent)).where(ArticleEngagement.article_slug == article_slug)
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

        # Views over time, bucketed by day. FIXED — this used to group by
        # the raw viewed_at timestamp (down to the microsecond), so every
        # row was its own bucket of 1 and the result was never actually
        # aggregated into anything chart-able.
        views_over_time = await session.execute(
            select(func.date_trunc('day', ArticleView.viewed_at), func.count(ArticleView.id))
            .where(ArticleView.article_slug == article_slug)
            .group_by(func.date_trunc('day', ArticleView.viewed_at))
            .order_by(func.date_trunc('day', ArticleView.viewed_at).desc())
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
        return ArticleStatsOut(
            total_views=total_views.scalars().one(),
            unique_sessions=unique_sessions.scalars().one(),
            average_time_spent=average_time_spent.scalars().one(),
            average_scroll_depth=average_scroll_depth.scalars().one(),
            max_time_spent=max_time_spent.scalars().one(),
            max_scroll_depth=max_scroll_depth.scalars().one(),
            device_breakdown=[CountBucket(label=label, count=count) for label, count in device_breakdown.all()],
            top_referrers=[CountBucket(label=label, count=count) for label, count in top_referrers.all()],
            top_user_agents=[CountBucket(label=label, count=count) for label, count in top_user_agents.all()],
            views_over_time=[ViewsOverTimeEntry(viewed_at=viewed_at, count=count) for viewed_at, count in views_over_time.all()],
            total_feedback=total_feedback.scalars().one(),
            helpful_count=helpful_count.scalars().one(),
            not_help_count=not_help_count.scalars().one(),
        )


async def get_top_articles_repo(limit: int = 10, days: int = 30) -> list[TopArticleOut]:
    """Get the most viewed articles in the last X days, ranked by view count.

    FIXED — this used to `select(ArticleView)` (every column) while grouping
    only by `article_slug`. Postgres rejects that (every selected column
    must be aggregated or in the GROUP BY), so this would 500 the moment
    it was ever called. 'Top articles' is inherently an aggregate — slug +
    counts — not a single representative ArticleView row, so the return
    shape changed from ArticleViewOut to TopArticleOut.
    """
    async with get_async_session() as session:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        result = await session.execute(
            select(
                ArticleView.article_slug,
                func.count(ArticleView.id).label('view_count'),
                func.count(distinct(ArticleView.session_id)).label('unique_sessions'),
            )
            .where(ArticleView.viewed_at >= since)
            .group_by(ArticleView.article_slug)
            .order_by(func.count(ArticleView.id).desc())
            .limit(limit)
        )
        return [
            TopArticleOut(article_slug=slug, view_count=view_count, unique_sessions=unique_sessions)
            for slug, view_count, unique_sessions in result.all()
        ]


async def get_articles_needing_improvement_repo(threshold: float = 0.50) -> list[ArticleImprovementCandidate]:
    """Find articles with a helpfulness rate below `threshold`.

    FIXED — two bugs here previously:
    1. The query selected (article_slug, total_feedback, helpful_count) —
       three columns — then called `.scalars().all()`, which only takes the
       *first* column. Every row would just be a bare slug string, and
       ArticleFeedbackOut.model_validate(a_string) would blow up (that
       schema needs id/user_id/is_helpful/created_at, none of which exist
       on a string).
    2. `func.sum(...) / func.count(...)` on two integer columns does
       integer division in Postgres — e.g. 2 helpful out of 3 total
       truncates to 0, which is always < any threshold, so articles with a
       genuinely good helpfulness rate could get flagged as needing
       improvement. Cast to Float before dividing.
    """
    async with get_async_session() as session:
        helpful_count_expr = func.sum(func.cast(ArticleFeedback.is_helpful, Integer))
        total_count_expr = func.count(ArticleFeedback.id)

        result = await session.execute(
            select(
                ArticleFeedback.article_slug,
                total_count_expr.label('total_feedback'),
                helpful_count_expr.label('helpful_count'),
            )
            .group_by(ArticleFeedback.article_slug)
            .having(
                func.cast(helpful_count_expr, Float) / total_count_expr < threshold
            )
        )
        return [
            ArticleImprovementCandidate(
                article_slug=article_slug,
                total_feedback=total_feedback,
                helpful_count=helpful_count,
                helpful_rate=(helpful_count / total_feedback) if total_feedback else 0.0,
            )
            for article_slug, total_feedback, helpful_count in result.all()
        ]


async def get_search_queries_repo(limit: int = 10, days: int = 30) -> list[ArticleSearchQueryOut]:
    """List the most recent search queries in the last X days (activity log).

    FIXED — same invalid-GROUP-BY bug as get_top_articles_repo: selected
    the full ArticleSearchQuery entity but grouped only by `query` text.
    'Most popular distinct search terms' is what get_popular_search_terms_repo
    already does properly; this one is the recency-ordered raw log instead,
    which is what ArticleSearchQueryOut (individual rows, not aggregates)
    actually represents.
    """
    async with get_async_session() as session:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        result = await session.execute(
            select(ArticleSearchQuery)
            .where(ArticleSearchQuery.created_at >= since)
            .order_by(ArticleSearchQuery.created_at.desc())
            .limit(limit)
        )
        return [ArticleSearchQueryOut.model_validate(q) for q in result.scalars().all()]


async def get_search_clicks_repo(days: int = 30, limit: int = 50) -> list[ArticleSearchClickOut]:
    """List recent search-result clicks (activity log)."""
    async with get_async_session() as session:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        result = await session.execute(
            select(ArticleSearchClick)
            .where(ArticleSearchClick.created_at >= since)
            .order_by(ArticleSearchClick.created_at.desc())
            .limit(limit)
        )
        return [ArticleSearchClickOut.model_validate(c) for c in result.scalars().all()]


async def get_popular_search_terms_repo(limit: int = 10, days: int = 30) -> list[PopularSearchTerm]:
    """Get the most popular distinct search terms in the last X days, each
    with its click-through rate and most-clicked resulting article.

    FIXED — every sub-query here grouped by query text and limited to N
    rows, but then called `.scalars().one()`, which raises
    MultipleResultsFound for any limit > 1 (and the function's return type
    was a single PopularSearchTerm despite the name promising a ranked
    list). Clicks and searches are only linked via search_query_id, not
    query text directly, so per-term CTR needs a join back through
    ArticleSearchQuery — done per term below.
    """
    async with get_async_session() as session:
        since = datetime.now(timezone.utc) - timedelta(days=days)

        base_result = await session.execute(
            select(
                ArticleSearchQuery.query,
                func.count(ArticleSearchQuery.id).label('search_count'),
                func.avg(ArticleSearchQuery.results_count).label('avg_results'),
            )
            .where(ArticleSearchQuery.created_at >= since)
            .group_by(ArticleSearchQuery.query)
            .order_by(func.count(ArticleSearchQuery.id).desc())
            .limit(limit)
        )

        terms: list[PopularSearchTerm] = []
        for query_text, search_count, avg_results in base_result.all():
            clicks_result = await session.execute(
                select(func.count(ArticleSearchClick.id))
                .join(ArticleSearchQuery, ArticleSearchClick.search_query_id == ArticleSearchQuery.id)
                .where(ArticleSearchQuery.query == query_text)
                .where(ArticleSearchQuery.created_at >= since)
            )
            click_count = clicks_result.scalars().one()

            most_clicked_result = await session.execute(
                select(ArticleSearchClick.clicked_article_slug, func.count(ArticleSearchClick.id))
                .join(ArticleSearchQuery, ArticleSearchClick.search_query_id == ArticleSearchQuery.id)
                .where(ArticleSearchQuery.query == query_text)
                .where(ArticleSearchQuery.created_at >= since)
                .group_by(ArticleSearchClick.clicked_article_slug)
                .order_by(func.count(ArticleSearchClick.id).desc())
                .limit(1)
            )
            most_clicked_row = most_clicked_result.first()

            terms.append(PopularSearchTerm(
                query=query_text,
                search_count=search_count,
                avg_results=float(avg_results) if avg_results is not None else 0.0,
                click_through_rate=(click_count / search_count) if search_count else 0.0,
                most_clicked_article=most_clicked_row[0] if most_clicked_row else None,
            ))
        return terms


async def search_analytics_repo(days: int = 30) -> SearchAnalytics:
    """Get search analytics."""
    async with get_async_session() as session:
        since = datetime.now(timezone.utc) - timedelta(days=days)

        total_searches_result = await session.execute(
            select(func.count(ArticleSearchQuery.id)).where(ArticleSearchQuery.created_at >= since)
        )
        total_searches = total_searches_result.scalars().one()

        total_clicks_result = await session.execute(
            select(func.count(ArticleSearchClick.id)).where(ArticleSearchClick.created_at >= since)
        )
        total_clicks = total_clicks_result.scalars().one()

        # FIXED — this used to be a copy-paste of avg_results_per_search
        # (avg of results_count), not a click-through rate at all.
        click_through_rate = (total_clicks / total_searches) if total_searches else 0.0

        avg_results_per_search = await session.execute(
            select(func.coalesce(func.avg(ArticleSearchQuery.results_count), 0.0))
            .where(ArticleSearchQuery.created_at >= since)
        )

        # FIXED — this used to be avg(created_at - created_at), always zero.
        # time_to_click_seconds is already stored on the row; average that directly.
        avg_time_to_click = await session.execute(
            select(func.avg(ArticleSearchClick.time_to_click_seconds)).where(ArticleSearchClick.created_at >= since)
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

        # FIXED — the old query put an aggregate (func.count(...)) directly
        # in a WHERE clause with no join between the two tables, which is
        # invalid SQL and would fail at execution. A LEFT OUTER JOIN +
        # IS NULL correctly finds searches with zero matching clicks.
        searches_with_no_clicks_result = await session.execute(
            select(func.count(ArticleSearchQuery.id))
            .outerjoin(ArticleSearchClick, ArticleSearchClick.search_query_id == ArticleSearchQuery.id)
            .where(ArticleSearchQuery.created_at >= since)
            .where(ArticleSearchClick.id.is_(None))
        )

        return SearchAnalytics(
            total_searches=total_searches,
            total_clicks=total_clicks,
            click_through_rate=click_through_rate,
            avg_results_per_search=avg_results_per_search.scalars().one(),
            avg_time_to_click=avg_time_to_click.scalars().one(),
            most_searched_terms=[tuple(row) for row in most_searched_terms.all()],
            most_clicked_articles=[tuple(row) for row in most_clicked_articles.all()],
            searches_with_no_clicks=searches_with_no_clicks_result.scalars().one()
        )


async def get_articles_overview_repo(days: int = 30) -> ArticlesOverviewOut:
    """Sitewide Help Center summary for the admin dashboard's top cards —
    total views/searches/feedback and how many articles are currently
    flagged as needing improvement, all scoped to the last `days` days
    (article-needing-improvement is all-time, since a rolling window on a
    low-volume feedback signal would be noisy)."""
    async with get_async_session() as session:
        since = datetime.now(timezone.utc) - timedelta(days=days)

        total_views_result = await session.execute(
            select(func.count(ArticleView.id)).where(ArticleView.viewed_at >= since)
        )
        total_unique_sessions_result = await session.execute(
            select(func.count(distinct(ArticleView.session_id))).where(ArticleView.viewed_at >= since)
        )
        total_searches_result = await session.execute(
            select(func.count(ArticleSearchQuery.id)).where(ArticleSearchQuery.created_at >= since)
        )
        total_feedback_result = await session.execute(
            select(func.count(ArticleFeedback.id)).where(ArticleFeedback.created_at >= since)
        )
        helpful_count_result = await session.execute(
            select(func.count(ArticleFeedback.id))
            .where(ArticleFeedback.created_at >= since)
            .where(ArticleFeedback.is_helpful == True)
        )
        avg_engagement_result = await session.execute(
            select(func.avg(ArticleEngagement.time_spent_seconds)).where(ArticleEngagement.engaged_at >= since)
        )

        total_feedback = total_feedback_result.scalars().one()
        helpful_count = helpful_count_result.scalars().one()

    # Separate session (own connection) — reuses the already-fixed repo function.
    improvement_candidates = await get_articles_needing_improvement_repo(threshold=0.50)

    return ArticlesOverviewOut(
        total_views=total_views_result.scalars().one(),
        total_unique_sessions=total_unique_sessions_result.scalars().one(),
        total_searches=total_searches_result.scalars().one(),
        total_feedback=total_feedback,
        helpful_rate=(helpful_count / total_feedback) if total_feedback else None,
        avg_engagement_seconds=avg_engagement_result.scalars().one(),
        articles_needing_improvement=len(improvement_candidates),
    )