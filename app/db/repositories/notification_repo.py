#!/usr/bin/env python3
"""Async repository for Notification model operations.

Mirrors the structure of user_repo.py:
  • Every function opens its own session via get_async_session().
  • Returns validated Pydantic schemas, never raw ORM objects.
  • No business logic here – only raw DB reads / writes.
"""

from sqlalchemy import select, func, update, and_
from datetime import datetime, timezone
from typing import Optional

from app.db.models.notification import Notification
from app.db.session import get_async_session
from app.schemas.notification import NotificationOut


# ─── Create ───────────────────────────────────────────────────────────────────

async def create_notification_repo(
    title: str,
    message: str,
    category: str,
    priority: str = "medium",
    recipient_id: Optional[int] = None,
    recipient_role: str = "admin",
    source_type: Optional[str] = None,
    source_id: Optional[int] = None,
    action_url: Optional[str] = None,
    expires_at: Optional[datetime] = None,
) -> NotificationOut:
    """Insert a single notification row and return it."""
    async with get_async_session() as session:
        notif = Notification(
            title=title,
            message=message,
            category=category,
            priority=priority,
            recipient_id=recipient_id,
            recipient_role=recipient_role,
            source_type=source_type,
            source_id=source_id,
            action_url=action_url,
            expires_at=expires_at,
        )
        session.add(notif)
        await session.commit()
        await session.refresh(notif)
        return NotificationOut.model_validate(notif)


async def bulk_create_notifications_repo(
    notifications: list[dict],
) -> list[NotificationOut]:
    """Insert multiple notifications in one transaction.

    Each dict in *notifications* must contain the same keys accepted by
    create_notification_repo (minus the async overhead of N round-trips).
    """
    async with get_async_session() as session:
        rows = [Notification(**data) for data in notifications]
        session.add_all(rows)
        await session.commit()
        for row in rows:
            await session.refresh(row)
        return [NotificationOut.model_validate(row) for row in rows]


# ─── Read ─────────────────────────────────────────────────────────────────────

async def get_notification_by_id_repo(
    notification_id: int,
) -> Optional[NotificationOut]:
    """Fetch a single notification by PK."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notif = result.scalar_one_or_none()
        return NotificationOut.model_validate(notif) if notif else None


async def list_notifications_for_admin_repo(
    limit: int = 50,
    offset: int = 0,
) -> list[NotificationOut]:
    """All notifications destined for the admin role, newest first."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Notification)
            .where(Notification.recipient_role == "admin")
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = result.scalars().all()
        return [NotificationOut.model_validate(r) for r in rows]


async def list_notifications_for_user_repo(
    user_id: int,
    limit: int = 50,
    offset: int = 0,
) -> list[NotificationOut]:
    """Notifications for a specific user, newest first."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Notification)
            .where(Notification.recipient_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = result.scalars().all()
        return [NotificationOut.model_validate(r) for r in rows]


async def list_unread_for_admin_repo() -> list[NotificationOut]:
    """Unread admin notifications only."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Notification).where(
                and_(
                    Notification.recipient_role == "admin",
                    Notification.is_read == False,  # noqa: E712
                )
            ).order_by(Notification.created_at.desc())
        )
        rows = result.scalars().all()
        return [NotificationOut.model_validate(r) for r in rows]


async def list_by_category_repo(
    category: str,
    recipient_role: str = "admin",
) -> list[NotificationOut]:
    """Filter by category for a given role."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Notification).where(
                and_(
                    Notification.category == category,
                    Notification.recipient_role == recipient_role,
                )
            ).order_by(Notification.created_at.desc())
        )
        rows = result.scalars().all()
        return [NotificationOut.model_validate(r) for r in rows]


async def list_by_priority_repo(
    priority: str,
    recipient_role: str = "admin",
) -> list[NotificationOut]:
    """Filter by priority ('high' | 'medium' | 'low') for a given role."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Notification).where(
                and_(
                    Notification.priority == priority,
                    Notification.recipient_role == recipient_role,
                )
            ).order_by(Notification.created_at.desc())
        )
        rows = result.scalars().all()
        return [NotificationOut.model_validate(r) for r in rows]


# ─── Count ────────────────────────────────────────────────────────────────────

async def count_unread_for_admin_repo() -> int:
    """Total unread admin notifications."""
    async with get_async_session() as session:
        result = await session.execute(
            select(func.count())
            .select_from(Notification)
            .where(
                and_(
                    Notification.recipient_role == "admin",
                    Notification.is_read == False,  # noqa: E712
                )
            )
        )
        return result.scalar_one()


async def count_unread_for_user_repo(user_id: int) -> int:
    """Total unread notifications for a specific user."""
    async with get_async_session() as session:
        result = await session.execute(
            select(func.count())
            .select_from(Notification)
            .where(
                and_(
                    Notification.recipient_id == user_id,
                    Notification.is_read == False,  # noqa: E712
                )
            )
        )
        return result.scalar_one()


# ─── Update (mark read / unread) ──────────────────────────────────────────────

async def mark_notification_read_repo(notification_id: int) -> Optional[NotificationOut]:
    """Mark a single notification as read."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notif = result.scalar_one_or_none()
        if notif:
            notif.is_read = True
            notif.updated_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(notif)
            return NotificationOut.model_validate(notif)
        return None


async def mark_all_read_for_admin_repo() -> int:
    """Mark ALL admin notifications as read. Returns count of rows updated."""
    async with get_async_session() as session:
        result = await session.execute(
            update(Notification)
            .where(
                and_(
                    Notification.recipient_role == "admin",
                    Notification.is_read == False,  # noqa: E712
                )
            )
            .values(is_read=True, updated_at=datetime.now(timezone.utc))
        )
        await session.commit()
        return result.rowcount


async def mark_all_read_for_user_repo(user_id: int) -> int:
    """Mark all of a user's notifications as read. Returns row count."""
    async with get_async_session() as session:
        result = await session.execute(
            update(Notification)
            .where(
                and_(
                    Notification.recipient_id == user_id,
                    Notification.is_read == False,  # noqa: E712
                )
            )
            .values(is_read=True, updated_at=datetime.now(timezone.utc))
        )
        await session.commit()
        return result.rowcount


# ─── Delete ───────────────────────────────────────────────────────────────────

async def delete_notification_repo(notification_id: int) -> bool:
    """Hard-delete a single notification. Returns True if it existed."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notif = result.scalar_one_or_none()
        if notif:
            await session.delete(notif)
            await session.commit()
            return True
        return False


async def delete_read_notifications_for_admin_repo() -> int:
    """Delete all read admin notifications (used by 'Clear read' button).
    Returns count of deleted rows."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Notification).where(
                and_(
                    Notification.recipient_role == "admin",
                    Notification.is_read == True,  # noqa: E712
                )
            )
        )
        rows = result.scalars().all()
        count = len(rows)
        for row in rows:
            await session.delete(row)
        await session.commit()
        return count


async def delete_expired_notifications_repo() -> int:
    """Prune all rows past their expires_at timestamp.
    Intended to be called by a scheduled cleanup job.
    Returns count of deleted rows.
    """
    now = datetime.now(timezone.utc)
    async with get_async_session() as session:
        result = await session.execute(
            select(Notification).where(
                and_(
                    Notification.expires_at.isnot(None),
                    Notification.expires_at < now,
                )
            )
        )
        rows = result.scalars().all()
        count = len(rows)
        for row in rows:
            await session.delete(row)
        await session.commit()
        return count