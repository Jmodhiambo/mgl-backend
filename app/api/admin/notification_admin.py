#!/usr/bin/env python3
"""Admin notification routes for MGLTickets.

Mirrors the structure of user_admin.py exactly:
  • All routes live under /admin/notifications
  • Auth is gated by require_admin (temporarily commented out on dev routes)
  • Returns Pydantic schemas, never raw ORM objects

Frontend ↔ backend mapping
──────────────────────────
  GET  /admin/notifications              → full list (paginated)
  GET  /admin/notifications/unread       → unread only
  GET  /admin/notifications/count/unread → badge count
  GET  /admin/notifications/category/{category} → filter by category
  GET  /admin/notifications/{id}         → single item
  PATCH /admin/notifications/{id}/read   → mark one read
  PATCH /admin/notifications/read-all    → mark all read
  DELETE /admin/notifications/{id}       → dismiss one
  DELETE /admin/notifications/clear-read → clear all read (bulk)
  POST  /admin/notifications/cleanup     → prune expired rows (cron / manual)
"""

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from app.schemas.notification import NotificationOut
from app.core.security import require_admin
import app.services.notification_services as notification_services

from app.services.audit_log_services import log_admin_action_service

router = APIRouter()


# ─── List & Filter ────────────────────────────────────────────────────────────

@router.get("/admin/notifications", response_model=list[NotificationOut])
async def list_admin_notifications(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user=Depends(require_admin),
):
    """
    Return paginated admin notifications, newest first.
    Used to populate the full Notifications page.
    """
    return await notification_services.list_admin_notifications_service(limit, offset)


@router.get("/admin/notifications/unread", response_model=list[NotificationOut])
async def list_unread_admin_notifications(
    user=Depends(require_admin),
):
    """
    Return only unread admin notifications.
    Useful for the 'Unread only' toggle on the frontend.
    """
    return await notification_services.list_unread_admin_notifications_service()


@router.get("/admin/notifications/count/unread", response_model=int)
async def count_unread_admin_notifications(
    user=Depends(require_admin),
):
    """
    Return the count of unread admin notifications.
    Used to drive the red badge in the Header / sidebar.
    """
    return await notification_services.count_unread_admin_notifications_service()


@router.get("/admin/notifications/category/{category}", response_model=list[NotificationOut])
async def list_notifications_by_category(
    category: str,
    user=Depends(require_admin),
):
    """
    Filter admin notifications by category.
    category: 'event' | 'user' | 'payment' | 'message' | 'system'
    """
    return await notification_services.list_by_category_service(category, "admin")


@router.get("/admin/notifications/{notification_id}", response_model=NotificationOut)
async def get_notification(
    notification_id: int,
    user=Depends(require_admin),
):
    """
    Fetch a single notification by ID.
    """
    return await notification_services.get_notification_service(notification_id)


# ─── Mark Read ────────────────────────────────────────────────────────────────

@router.patch("/admin/notifications/{notification_id}/read", response_model=NotificationOut)
async def mark_notification_read(
    notification_id: int,
    background_tasks: BackgroundTasks,
    user=Depends(require_admin),
):
    """
    Mark a single notification as read.
    Called when the user clicks 'Mark read' or 'View →' on a notification.
    """
    notification = await notification_services.mark_notification_read_service(notification_id)

    if notification is not None:
        # Create admin log entry for marking notification read
        background_tasks.add_task(
            log_admin_action_service,
            admin_id=user.id,
            admin_name=user.name,
            action="mark_notification_read",
            target_type="notification",
            target_id=notification_id,
            details={"notification_id": notification_id, "status": "read"},
        )
    return notification


@router.patch("/admin/notifications/read-all", response_model=dict)
async def mark_all_admin_notifications_read(
    background_tasks: BackgroundTasks,
    user=Depends(require_admin),
):
    """
    Mark ALL admin notifications as read.
    Called by the 'Mark all read' button.
    Returns: { updated: int, message: str }
    """
    notification = await notification_services.mark_all_admin_read_service()

    if notification is not None:
        # Create admin log entry for all notifications read
        background_tasks.add_task(
            log_admin_action_service,
            admin_id=user.id,
            admin_name=user.name,
            action="mark_all_notifications_read",
            target_type="notification",
            target_id=None,
            details={"updated": notification["updated"], "status": "all_read"},
        )
    return notification


# ─── Dismiss / Delete ─────────────────────────────────────────────────────────

@router.delete("/admin/notifications/{notification_id}", response_model=bool)
async def dismiss_notification(
    notification_id: int,
    background_tasks: BackgroundTasks,
    user=Depends(require_admin),
):
    """
    Hard-delete a single notification (the 'X' dismiss button).
    Returns True on success.
    """
    notification = await notification_services.dismiss_notification_service(notification_id)

    if notification is not None:
        # Create admin log entry for notification dismissal
        background_tasks.add_task(
            log_admin_action_service,
            admin_id=user.id,
            admin_name=user.name,
            action="dismiss_notification",
            target_type="notification",
            target_id=notification_id,
            details={"notification_id": notification_id, "status": "dismissed"},
        )

    return notification


@router.delete("/admin/notifications/clear-read", response_model=dict)
async def clear_read_notifications(
    background_tasks: BackgroundTasks,
    user=Depends(require_admin),
):
    """
    Delete all read admin notifications.
    Called by the 'Clear read' button.
    Returns: { deleted: int, message: str }
    """
    res = await notification_services.clear_read_admin_notifications_service()

    if res is not None:
        # Create admin log entry for clearing read notifications
        background_tasks.add_task(
            log_admin_action_service,
            admin_id=user.id,
            admin_name=user.name,
            action="clear_read_notifications",
            target_type="notification",
            target_id=None,
            details={"deleted": res["deleted"], "status": "cleared"},
        )

    return res


# ─── Maintenance ──────────────────────────────────────────────────────────────

@router.post("/admin/notifications/cleanup", response_model=dict)
async def cleanup_expired_notifications(
    background_tasks: BackgroundTasks,
    user=Depends(require_admin),
):
    """
    Prune all notifications that have passed their expires_at timestamp.
    Intended to be called by a scheduled job (e.g. APScheduler / cron)
    or manually from the Settings page.
    Returns: { deleted: int }
    """
    res = await notification_services.cleanup_expired_notifications_service()

    if res is not None:
        background_tasks.add_task(
            log_admin_action_service,
            admin_id=user.id,
            admin_name=user.name,
            action="cleanup_expired_notifications",
            target_type="notification",
            target_id=None,
            details={"deleted": res["deleted"], "status": "cleaned"},
        )

    return res