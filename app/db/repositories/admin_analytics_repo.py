#!/usr/bin/env python3
"""Repository layer for admin analytics queries.

All queries are read-only aggregations — no writes here.
Place at: app/db/repositories/admin_analytics_repo.py
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from sqlalchemy import func, select, and_

from app.db.models.audit_log import AuditLog
from app.db.models.booking import Booking
from app.db.models.contact_messages import ContactMessage
from app.db.models.event import Event
from app.db.models.payment import Payment
from app.db.models.user import User
from app.db.session import get_async_session


# ─── Bucket helper ────────────────────────────────────────────────────────────

def _month_buckets(months: int) -> list[datetime]:
    """
    Return the first day of each of the last N months, oldest first.

    Uses proper month arithmetic instead of timedelta(days=28) which drifts
    badly over long ranges and can produce duplicate or missing month labels.
    """
    now = datetime.now(timezone.utc)
    buckets: list[datetime] = []
    for i in range(months - 1, -1, -1):
        month = now.month - i
        year  = now.year
        while month <= 0:
            month += 12
            year  -= 1
        buckets.append(datetime(year, month, 1, tzinfo=timezone.utc))
    return buckets


# ─── Dashboard Stats ──────────────────────────────────────────────────────────

async def get_dashboard_stats_repo() -> dict:
    """
    Single-session aggregation for the admin dashboard KPI cards.
    """
    async with get_async_session() as session:
        now         = datetime.now(timezone.utc)
        week_ago    = now - timedelta(days=7)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # User counts
        total_users = await session.scalar(
            select(func.count()).select_from(User).where(User.role == "user")
        ) or 0

        total_organizers = await session.scalar(
            select(func.count()).select_from(User).where(User.role == "organizer")
        ) or 0

        total_admins = await session.scalar(
            select(func.count()).select_from(User).where(User.role == "admin")
        ) or 0

        new_users_this_week = await session.scalar(
            select(func.count()).select_from(User).where(
                User.created_at >= week_ago
            )
        ) or 0

        # Event counts
        total_events = await session.scalar(
            select(func.count()).select_from(Event).where(
                Event.is_approved.is_(True)
            )
        ) or 0

        active_events = await session.scalar(
            select(func.count()).select_from(Event).where(
                and_(
                    Event.is_approved.is_(True),
                    Event.start_time <= now,
                    Event.end_time   >= now,
                )
            )
        ) or 0

        pending_approvals = await session.scalar(
            select(func.count()).select_from(Event).where(
                Event.is_approved.is_(False)
            )
        ) or 0

        # Booking count
        total_bookings = await session.scalar(
            select(func.count()).select_from(Booking)
        ) or 0

        # Revenue — completed payments only
        total_revenue = await session.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0))
            .select_from(Payment)
            .where(Payment.status == "completed")
        ) or 0

        revenue_this_month = await session.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0))
            .select_from(Payment)
            .where(
                and_(
                    Payment.status   == "completed",
                    Payment.created_at >= month_start,
                )
            )
        ) or 0

        # Open contact messages
        open_messages = await session.scalar(
            select(func.count()).select_from(ContactMessage).where(
                ContactMessage.status.in_(["new", "pending"])
            )
        ) or 0

        return {
            "total_users":         total_users,
            "total_organizers":    total_organizers,
            "total_admins":        total_admins,
            "total_events":        total_events,
            "total_bookings":      total_bookings,
            "total_revenue":       float(total_revenue),
            "active_events":       active_events,
            "pending_approvals":   pending_approvals,
            "open_messages":       open_messages,
            "new_users_this_week": new_users_this_week,
            "revenue_this_month":  float(revenue_this_month),
        }


# ─── Revenue Chart ────────────────────────────────────────────────────────────

async def get_revenue_chart_repo(months: int = 7) -> list[dict]:
    """
    Monthly revenue totals (completed payments) for the last N months.
    Returns [{label: 'Jan', value: 120000.0}, ...] oldest-first.

    Fix: replaced text("date_trunc(...) AS month") with
    func.date_trunc(...).label("month") so SQLAlchemy exposes the column
    as r.month on the result row instead of raising AttributeError.
    """
    async with get_async_session() as session:
        buckets   = _month_buckets(months)
        month_col = func.date_trunc("month", Payment.created_at).label("month")

        result = await session.execute(
            select(
                month_col,
                func.coalesce(func.sum(Payment.amount), 0).label("total"),
            )
            .where(
                and_(
                    Payment.status     == "completed",
                    Payment.created_at >= buckets[0],
                )
            )
            .group_by(month_col)
            .order_by(month_col)
        )

        # Key by abbreviated month name; last write wins for same-label months
        # (not possible with proper bucket arithmetic, but safe either way)
        rows = {r.month.strftime("%b"): float(r.total) for r in result}

        # Fill zeros for months that had no completed payments
        return [
            {"label": b.strftime("%b"), "value": rows.get(b.strftime("%b"), 0.0)}
            for b in buckets
        ]


# ─── User Growth Chart ────────────────────────────────────────────────────────

async def get_user_growth_chart_repo(months: int = 6) -> list[dict]:
    """
    New user registrations per month for the last N months.
    Returns [{label: 'Jan', value: 42}, ...] oldest-first.

    Fix: same text() → func.date_trunc().label() fix as revenue chart,
    plus replaced drifting timedelta(days=28) bucket logic with
    _month_buckets() which uses proper calendar month arithmetic.
    """
    async with get_async_session() as session:
        buckets   = _month_buckets(months)
        month_col = func.date_trunc("month", User.created_at).label("month")

        result = await session.execute(
            select(
                month_col,
                func.count(User.id).label("total"),
            )
            .where(User.created_at >= buckets[0])
            .group_by(month_col)
            .order_by(month_col)
        )

        rows = {r.month.strftime("%b"): r.total for r in result}

        return [
            {"label": b.strftime("%b"), "value": rows.get(b.strftime("%b"), 0)}
            for b in buckets
        ]


# ─── Events by Category ───────────────────────────────────────────────────────

async def get_events_by_category_repo() -> list[dict]:
    """
    Count of approved events grouped by category, sorted by count desc.
    Returns [{label: 'Music', value: 12}, ...]
    """
    async with get_async_session() as session:
        result = await session.execute(
            select(
                Event.category.label("category"),
                func.count(Event.id).label("total"),
            )
            .where(Event.is_approved.is_(True))
            .group_by(Event.category)
            .order_by(func.count(Event.id).desc())
        )
        return [{"label": r.category, "value": r.total} for r in result]


# ─── Booking Status Distribution ─────────────────────────────────────────────

async def get_booking_statuses_repo() -> list[dict]:
    """
    Count of bookings grouped by status.
    Returns [{label: 'Confirmed', value: 340}, ...]
    """
    async with get_async_session() as session:
        result = await session.execute(
            select(
                Booking.status.label("status"),
                func.count(Booking.id).label("total"),
            )
            .group_by(Booking.status)
            .order_by(func.count(Booking.id).desc())
        )
        return [
            {"label": r.status.capitalize(), "value": r.total}
            for r in result
        ]


# ─── Platform-wide Activity Feed ─────────────────────────────────────────────

async def get_activity_feed_repo(limit: int = 20) -> list[dict]:
    """
    Recent platform-wide admin audit log entries, enriched for display.
    Returns the latest N entries ordered newest-first.
    """
    async with get_async_session() as session:
        result = await session.execute(
            select(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        rows = result.scalars().all()

        icon_map: dict[str, str] = {
            "user_deactivated":      "user",
            "user_activated":        "user",
            "user_role_changed":     "user",
            "user_verified":         "user",
            "user_deleted":          "user",
            "user_created":          "user",
            "event_approved":        "check",
            "event_rejected":        "calendar",
            "event_deleted":         "calendar",
            "create_event":          "calendar",
            "booking_refunded":      "money",
            "booking_deleted":       "ticket",
            "update_booking":        "ticket",
            "update_booking_status": "ticket",
            "message_marked_spam":   "message",
            "message_closed":        "message",
            "message_responded":     "message",
            "session_revoked":       "user",
            "settings_updated":      "check",
        }

        def _human_message(row: AuditLog) -> str:
            details = row.details or {}
            name    = row.admin_name
            action  = row.action

            templates: dict[str, object] = {
                "user_deactivated":      lambda d: f"{name} deactivated user #{row.target_id}",
                "user_activated":        lambda d: f"{name} activated user #{row.target_id}",
                "user_role_changed":     lambda d: f"{name} changed role of user #{row.target_id} to {d.get('new_role', '?')}",
                "user_verified":         lambda d: f"{name} verified user #{row.target_id}",
                "user_deleted":          lambda d: f"{name} deleted user #{row.target_id}",
                "event_approved":        lambda d: f"{name} approved '{d.get('approved_event', 'event')}'",
                "event_rejected":        lambda d: f"{name} rejected '{d.get('rejected_event', 'event')}'",
                "event_deleted":         lambda d: f"{name} deleted event #{row.target_id}",
                "create_event":          lambda d: f"{name} created event '{d.get('event_title', '')}'",
                "booking_refunded":      lambda d: f"{name} refunded booking #{row.target_id}",
                "update_booking_status": lambda d: f"{name} updated booking #{row.target_id} to '{d.get('updated_status', '')}'",
                "message_marked_spam":   lambda d: f"{name} marked message #{row.target_id} as spam",
                "message_closed":        lambda d: f"{name} closed message #{row.target_id}",
                "message_responded":     lambda d: f"{name} responded to message #{row.target_id}",
                "session_revoked":       lambda d: f"{name} revoked a session",
                "settings_updated":      lambda d: f"{name} updated platform settings",
            }

            fn = templates.get(action)
            return fn(details) if fn else f"{name} performed {action}"  # type: ignore[operator]

        return [
            {
                "id":      row.id,
                "message": _human_message(row),
                "icon":    icon_map.get(row.action, "check"),
                "time":    row.created_at.isoformat(),
                "action":  row.action,
            }
            for row in rows
        ]