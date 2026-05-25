#!/usr/bin/env python3
"""Notification services for MGLTickets.

Two kinds of functions live here:

1. CRUD services  – called directly by the notification router/endpoints.
   These are the functions the frontend talks to via the API.

2. Trigger helpers  – thin, fire-and-forget wrappers meant to be registered
   as BackgroundTasks in OTHER domain routers (events, bookings, payments,
   users, messages).  Each trigger function is named notify_<what_happened>
   and builds the correct title / message / category / priority before
   delegating to create_notification_repo.

   Usage pattern (copy into the relevant router):
   ───────────────────────────────────────────────
   # in event_admin.py (or whichever domain router)
   from fastapi import BackgroundTasks
   from app.services.notification_services import notify_event_submitted
   ...
   @router.post("/admin/events", response_model=EventOut)
   async def create_event(
       payload: EventCreate,
       background_tasks: BackgroundTasks,
       user=Depends(require_admin),
   ):
       event = await event_services.create_event_service(payload)
       background_tasks.add_task(
           notify_event_submitted,
           event.id,
           event.title,
           event.organizer_name,
       )
       return event

   Using BackgroundTasks means the notification is written AFTER the response
   is sent, so it never adds latency to the caller.  Errors are swallowed
   inside each trigger so a notification failure never affects the main flow.

Structure mirrors user_services.py exactly.
"""

from typing import Optional
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status

from app.core.logging_config import logger
import app.db.repositories.notification_repo as notification_repo
from app.schemas.notification import NotificationOut


# ═══════════════════════════════════════════════════════════════════════════════
# 1.  CRUD SERVICES  (called by the notification router)
# ═══════════════════════════════════════════════════════════════════════════════

async def list_admin_notifications_service(
    limit: int = 50,
    offset: int = 0,
) -> list[NotificationOut]:
    """Return paginated notifications for the admin panel."""
    logger.info("Listing admin notifications...")
    return await notification_repo.list_notifications_for_admin_repo(limit, offset)


async def list_user_notifications_service(
    user_id: int,
    limit: int = 50,
    offset: int = 0,
) -> list[NotificationOut]:
    """Return paginated notifications for a specific user."""
    logger.info(f"Listing notifications for user ID: {user_id}")
    return await notification_repo.list_notifications_for_user_repo(user_id, limit, offset)


async def list_unread_admin_notifications_service() -> list[NotificationOut]:
    """Return all unread admin notifications."""
    logger.info("Listing unread admin notifications...")
    return await notification_repo.list_unread_for_admin_repo()


async def count_unread_admin_notifications_service() -> int:
    """Return count of unread admin notifications (used by header badge)."""
    return await notification_repo.count_unread_for_admin_repo()


async def count_unread_user_notifications_service(user_id: int) -> int:
    """Return count of unread notifications for a specific user."""
    return await notification_repo.count_unread_for_user_repo(user_id)


async def get_notification_service(notification_id: int) -> NotificationOut:
    """Fetch a single notification by ID."""
    logger.info(f"Fetching notification ID: {notification_id}")
    notif = await notification_repo.get_notification_by_id_repo(notification_id)
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )
    return notif


async def mark_notification_read_service(notification_id: int) -> NotificationOut:
    """Mark a single notification as read."""
    logger.info(f"Marking notification {notification_id} as read.")
    notif = await notification_repo.mark_notification_read_repo(notification_id)
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )
    return notif


async def mark_all_admin_read_service() -> dict:
    """Mark all admin notifications as read."""
    logger.info("Marking all admin notifications as read.")
    count = await notification_repo.mark_all_read_for_admin_repo()
    return {"updated": count, "message": f"{count} notification(s) marked as read."}


async def mark_all_user_read_service(user_id: int) -> dict:
    """Mark all notifications for a user as read."""
    logger.info(f"Marking all notifications read for user ID: {user_id}")
    count = await notification_repo.mark_all_read_for_user_repo(user_id)
    return {"updated": count, "message": f"{count} notification(s) marked as read."}


async def dismiss_notification_service(notification_id: int) -> bool:
    """Hard-delete a notification (the 'X' dismiss button)."""
    logger.info(f"Dismissing notification ID: {notification_id}")
    deleted = await notification_repo.delete_notification_repo(notification_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )
    return True


async def clear_read_admin_notifications_service() -> dict:
    """Delete all read admin notifications ('Clear read' button)."""
    logger.info("Clearing read admin notifications.")
    count = await notification_repo.delete_read_notifications_for_admin_repo()
    return {"deleted": count, "message": f"{count} read notification(s) cleared."}


async def cleanup_expired_notifications_service() -> dict:
    """Prune expired notifications. Call from a scheduled job."""
    logger.info("Running expired notification cleanup...")
    count = await notification_repo.delete_expired_notifications_repo()
    logger.info(f"Expired notification cleanup: {count} rows deleted.")
    return {"deleted": count}


async def list_by_category_service(
    category: str,
    recipient_role: str = "admin",
) -> list[NotificationOut]:
    """Filter notifications by category for a role."""
    valid = {"event", "user", "payment", "message", "system"}
    if category not in valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category. Must be one of: {', '.join(valid)}",
        )
    return await notification_repo.list_by_category_repo(category, recipient_role)


# ═══════════════════════════════════════════════════════════════════════════════
# 2.  TRIGGER HELPERS  (registered as BackgroundTasks in domain routers)
#
#     Convention:
#       • Function name  →  notify_<past_tense_event>
#       • Returns NotificationOut so the caller can log/trace if needed.
#       • Never raises – errors are logged but swallowed so a notification
#         failure never breaks the main operation.
#       • Always add via background_tasks.add_task(...) at the router level,
#         never awaited directly inside a service function.
# ═══════════════════════════════════════════════════════════════════════════════

def _expiry(days: int = 30) -> datetime:
    """Standard 30-day notification lifetime."""
    return datetime.now(timezone.utc) + timedelta(days=days)


# ── Events ────────────────────────────────────────────────────────────────────

async def notify_event_submitted(
    event_id: int,
    event_title: str,
    event_slug: str,
    organizer_name: str,
    admin_name: Optional[str] = None,
) -> Optional[NotificationOut]:
    """Register as a BackgroundTask in the event creation router endpoint.

    Example:
        # in event_admin.py
        from app.services.notification_services import notify_event_submitted
        ...
        @router.post("/admin/events", response_model=EventOut)
        async def create_event(payload: EventCreate, background_tasks: BackgroundTasks, ...):
            event = await event_services.create_event_service(payload)
            background_tasks.add_task(notify_event_submitted, event.id, event.title, event.slug, organizer.name, admin.name)
            return event
    """
    if admin_name:
        log_info = f"[notify] event submitted: {event_id} by {organizer_name}, created by admin {admin_name}"
        message_info = f'"{event_title}" submitted by {organizer_name} (created by admin {admin_name}) needs review.'
    else:
        log_info = f"[notify] event submitted: {event_id} by {organizer_name}"
        message_info = f'"{event_title}" submitted by {organizer_name} needs review.'
    try:
        logger.info(log_info)
        return await notification_repo.create_notification_repo(
            title="New event pending approval",
            message=message_info,
            category="event",
            priority="high",
            recipient_role="admin",
            source_type="event",
            source_id=event_id,
            action_url=f"/events/{event_slug}",
            expires_at=_expiry(),
        )
    except Exception as exc:
        logger.error(f"[notify] notify_event_submitted failed: {exc}")
        return None


async def notify_event_approved(
    event_id: int,
    event_title: str,
    event_slug: str,
    admin_name: str,
    organizer_id: int,
) -> Optional[NotificationOut]:
    """Register as a BackgroundTask in the event approval router endpoint.

    Example:
        # in event_admin.py
        from app.services.notification_services import notify_event_approved
        ...
        @router.patch("/admin/events/{event_id}/approve", response_model=EventOut)
        async def approve_event(event_id: int, background_tasks: BackgroundTasks, ...):
            event = await event_services.approve_event_service(event_id)
            background_tasks.add_task(notify_event_approved, event.id, event.title, event.slug, user.name, event.organizer_id)
            return event
    """
    try:
        logger.info(f"[notify] event approved: {event_title} (ID: {event_id}) by admin {admin_name}")
        return await notification_repo.create_notification_repo(
            title="Event approved",
            message=f'"{event_title}" has been approved by admin {admin_name} and is now live.',
            category="event",
            priority="medium",
            recipient_id=organizer_id,
            recipient_role="organizer" if organizer_id else "admin",
            source_type="event",
            source_id=event_id,
            action_url=f"/events/{event_slug}",
            expires_at=_expiry(),
        )
    except Exception as exc:
        logger.error(f"[notify] notify_event_approved failed: {exc}")
        return None


async def notify_event_rejected(
    event_id: int,
    event_title: str,
    event_slug: str,
    admin_name: str,
    organizer_id: int,
    reason: str = "",
) -> Optional[NotificationOut]:
    """Register as a BackgroundTask in the event rejection router endpoint.

    Example:
        # in event_admin.py
        from app.services.notification_services import notify_event_rejected
        ...
        @router.patch("/admin/events/{event_id}/reject", response_model=EventOut)
        async def reject_event(event_id: int, reason: str, background_tasks: BackgroundTasks, ...):
            event = await event_services.reject_event_service(event_id)
            background_tasks.add_task(notify_event_rejected, event.id, event.title, event.slug, admin_name, event.organizer_id, reason)
            return event
    """
    try:
        detail = f" Reason: {reason}" if reason else ""
        logger.info(f"[notify] event rejected: {event_title} (ID: {event_id}) by admin {admin_name}")
        return await notification_repo.create_notification_repo(
            title="Event rejected",
            message=f'"{event_title}" was not approved by admin: {admin_name}.{detail}',
            category="event",
            priority="high",
            recipient_id=organizer_id,
            recipient_role="organizer" if organizer_id else "admin",
            source_type="event",
            source_id=event_id,
            action_url=f"/events/{event_slug}",
            expires_at=_expiry(),
        )
    except Exception as exc:
        logger.error(f"[notify] notify_event_rejected failed: {exc}")
        return None


async def notify_event_sold_out(
    event_id: int,
    event_title: str,
    event_slug: str,
    ticket_type_name: str,
) -> Optional[NotificationOut]:
    """Register as a BackgroundTask in the booking creation router endpoint,
    triggered when a ticket type reaches full capacity.

    Example:
        # in booking_admin.py
        from app.services.notification_services import notify_event_sold_out
        ...
        @router.post("/admin/bookings", response_model=BookingOut)
        async def create_booking(payload: BookingCreate, background_tasks: BackgroundTasks, ...):
            booking = await booking_services.create_booking_service(payload)
            if booking.ticket_type_is_sold_out:
                background_tasks.add_task(notify_event_sold_out, event_id, event.title, ticket_type.name)
            return booking
    """
    try:
        logger.info(f"[notify] event sold out: {event_id}")
        return await notification_repo.create_notification_repo(
            title="Ticket type sold out",
            message=f'"{ticket_type_name}" tickets for "{event_title}" are fully sold out.',
            category="event",
            priority="low",
            recipient_role="admin",
            source_type="event",
            source_id=event_id,
            action_url="/events",
            expires_at=_expiry(),
        )
    except Exception as exc:
        logger.error(f"[notify] notify_event_sold_out failed: {exc}")
        return None


async def notify_event_cancelled(
    event_id: int,
    event_title: str,
    role: str,
    name: str,
) -> Optional[NotificationOut]:
    """Register as a BackgroundTask in the event cancellation router endpoint.

    Example:
        # in event_admin.py
        from app.services.notification_services import notify_event_cancelled
        ...
        @router.patch("/admin/events/{event_id}/cancel", response_model=EventOut)
        async def cancel_event(event_id: int, background_tasks: BackgroundTasks, ...):
            event = await event_services.cancel_event_service(event_id)
            background_tasks.add_task(notify_event_cancelled, event.id, event.title, role, name)
            return event
    """
    try:
        if role == "admin":
            logger.info(f"[notify] event cancelled: {event_id} by admin: {name}")
            message_info = f'"{event_title}" has been cancelled by admin: {name}.'
        else:
            logger.info(f"[notify] event cancelled: {event_id} by organizer: {name}")
            message_info = f'"{event_title}" has been cancelled by organizer: {name}.'

        return await notification_repo.create_notification_repo(
            title="Event cancelled",
            message=message_info,
            category="event",
            priority="high",
            recipient_role="admin",
            source_type="event",
            source_id=event_id,
            action_url="/events",
            expires_at=_expiry(),
        )
    except Exception as exc:
        logger.error(f"[notify] notify_event_cancelled failed: {exc}")
        return None


# ── Users ─────────────────────────────────────────────────────────────────────

async def notify_user_registered(
    user_id: int,
    user_name: str,
    user_email: str,
) -> Optional[NotificationOut]:
    """Register as a BackgroundTask in the user registration router endpoint.

    Example:
        # in user_admin.py (or auth_router.py)
        from app.services.notification_services import notify_user_registered
        ...
        @router.post("/auth/register", response_model=UserOut)
        async def register_user(payload: UserCreate, background_tasks: BackgroundTasks):
            user = await user_services.register_user_service(...)
            background_tasks.add_task(notify_user_registered, user.id, user.name, user.email)
            return user
    """
    try:
        logger.info(f"[notify] user registered with ID: {user_id}")
        return await notification_repo.create_notification_repo(
            title="New user registered",
            message=f"{user_name} ({user_email}) just created an account.",
            category="user",
            priority="low",
            recipient_role="admin",
            source_type="user",
            source_id=user_id,
            action_url="/users",
            expires_at=_expiry(),
        )
    except Exception as exc:
        logger.error(f"[notify] notify_user_registered failed: {exc}")
        return None


async def notify_user_flagged(
    user_id: int,
    user_name: str,
    reason: str = "Suspicious activity detected.",
) -> Optional[NotificationOut]:
    """Register as a BackgroundTask in whichever router endpoint detects
    suspicious user behaviour (e.g. failed login threshold, fraud check).

    Example:
        # in auth_router.py
        from app.services.notification_services import notify_user_flagged
        ...
        @router.post("/auth/login")
        async def login(payload: LoginForm, background_tasks: BackgroundTasks):
            result = await auth_services.login_service(payload)
            if result.suspicious:
                background_tasks.add_task(notify_user_flagged, user.id, user.name, "Multiple failed login attempts")
            return result
    """
    try:
        logger.info(f"[notify] user flagged: {user_id}")
        return await notification_repo.create_notification_repo(
            title="User account flagged",
            message=f"{user_name}'s account was flagged. {reason}",
            category="user",
            priority="high",
            recipient_role="admin",
            source_type="user",
            source_id=user_id,
            action_url="/users",
            expires_at=_expiry(),
        )
    except Exception as exc:
        logger.error(f"[notify] notify_user_flagged failed: {exc}")
        return None


async def notify_organizer_registered(
    user_id: int,
    user_name: str,
) -> Optional[NotificationOut]:
    """Register as a BackgroundTask in the role promotion router endpoint,
    specifically when a user is promoted to organizer.

    Example:
        # in user_admin.py
        from app.services.notification_services import notify_organizer_registered
        ...
        @router.patch("/admin/users/{user_id}/role/user-to-organizer", response_model=UserOut)
        async def promote_to_organizer(user_id: int, background_tasks: BackgroundTasks, ...):
            user = await user_services.update_user_role_service(user_id, "organizer")
            background_tasks.add_task(notify_organizer_registered, user.id, user.name)
            return user
    """
    try:
        logger.info(f"[notify] new organizer: {user_id}")
        return await notification_repo.create_notification_repo(
            title="New organizer registration",
            message=f"{user_name} has completed their organizer profile setup.",
            category="user",
            priority="medium",
            recipient_role="admin",
            source_type="user",
            source_id=user_id,
            action_url="/users",
            expires_at=_expiry(),
        )
    except Exception as exc:
        logger.error(f"[notify] notify_organizer_registered failed: {exc}")
        return None


# ── Payments & Bookings ───────────────────────────────────────────────────────

async def notify_booking_confirmed(
    booking_id: int,
    user_id: int,
    user_name: str,
    event_title: str,
    quantity: int,
    total_price: float,
) -> Optional[NotificationOut]:
    """Register as a BackgroundTask in the booking creation router endpoint.
    Directed at the USER only — admin is not notified for every purchase
    as that would be too noisy at scale.

    Example:
        # in booking_router.py (user-facing, not admin)
        from app.services.notification_services import notify_booking_confirmed
        ...
        @router.post("/bookings", response_model=BookingOut)
        async def create_booking(payload: BookingCreate, background_tasks: BackgroundTasks, user=Depends(require_user)):
            booking = await booking_services.create_booking_service(payload)
            background_tasks.add_task(
                notify_booking_confirmed,
                booking.id, user.id, user.name, event.title, booking.quantity, booking.total_price,
            )
            return booking
    """
    try:
        logger.info(f"[notify] booking confirmed: {booking_id} for user {user_id}")
        return await notification_repo.create_notification_repo(
            title="Booking confirmed",
            message=(
                f"Your booking of {quantity} ticket(s) for \"{event_title}\" "
                f"is confirmed. Total paid: KES {total_price:,.0f}."
            ),
            category="payment",
            priority="medium",
            recipient_id=user_id,
            recipient_role="user",
            source_type="booking",
            source_id=booking_id,
            action_url=f"/bookings/{booking_id}",
            expires_at=_expiry(),
        )
    except Exception as exc:
        logger.error(f"[notify] notify_booking_confirmed failed: {exc}")
        return None


async def notify_booking_cancelled(
    booking_id: int,
    user_id: int,
    user_name: str,
    event_title: str,
) -> Optional[NotificationOut]:
    """Register as a BackgroundTask in the booking cancellation router endpoint.
    Fires TWO notifications — one to the admin (for visibility) and one to
    the user (so they know their cancellation was processed).  Both are added
    as separate background tasks from the same router endpoint.

    Example:
        # in booking_admin.py
        from app.services.notification_services import notify_booking_cancelled
        ...
        @router.patch("/admin/bookings/{booking_id}/cancel", response_model=BookingOut)
        async def cancel_booking(booking_id: int, background_tasks: BackgroundTasks, ...):
            booking = await booking_services.cancel_booking_service(booking_id)
            # notify admin
            background_tasks.add_task(
                notify_booking_cancelled,
                booking.id, user.id, user.name, event.title,
            )
            return booking

    Note:
        The function sends one notification row per call.  Call it twice from
        the router if you want both admin and user notified:
            background_tasks.add_task(notify_booking_cancelled, ..., notify_admin=True)
            background_tasks.add_task(notify_booking_cancelled, ..., notify_admin=False)
        Or simply call the function once per recipient as shown — each call is
        cheap and runs in the background.
    """
    try:
        logger.info(f"[notify] booking cancelled: {booking_id}")

        # ── Admin notification ────────────────────────────────────────────────
        await notification_repo.create_notification_repo(
            title="Booking cancelled",
            message=f"{user_name} cancelled their booking for \"{event_title}\" (Booking #{booking_id}).",
            category="payment",
            priority="medium",
            recipient_role="admin",
            source_type="booking",
            source_id=booking_id,
            action_url="/bookings",
            expires_at=_expiry(),
        )

        # ── User notification ─────────────────────────────────────────────────
        return await notification_repo.create_notification_repo(
            title="Booking cancelled",
            message=f"Your booking for \"{event_title}\" has been cancelled. If a refund applies, it will be processed shortly.",
            category="payment",
            priority="medium",
            recipient_id=user_id,
            recipient_role="user",
            source_type="booking",
            source_id=booking_id,
            action_url=f"/bookings/{booking_id}",
            expires_at=_expiry(),
        )
    except Exception as exc:
        logger.error(f"[notify] notify_booking_cancelled failed: {exc}")
        return None


async def notify_payment_dispute(
    payment_id: int,
    user_name: str,
    amount: float,
    transaction_ref: str,
) -> Optional[NotificationOut]:
    """Register as a BackgroundTask in the payment dispute router endpoint.

    Example:
        # in payment_admin.py
        from app.services.notification_services import notify_payment_dispute
        ...
        @router.post("/admin/payments/{payment_id}/dispute", response_model=PaymentOut)
        async def open_dispute(payment_id: int, background_tasks: BackgroundTasks, ...):
            payment = await payment_services.open_dispute_service(payment_id)
            background_tasks.add_task(notify_payment_dispute, payment.id, user.name, payment.amount, payment.transaction_ref)
            return payment
    """
    try:
        logger.info(f"[notify] payment dispute: {payment_id}")
        return await notification_repo.create_notification_repo(
            title="Payment dispute opened",
            message=f"{user_name} raised a dispute for KES {amount:,.0f} — Ref: {transaction_ref}.",
            category="payment",
            priority="high",
            recipient_role="admin",
            source_type="payment",
            source_id=payment_id,
            action_url="/payments",
            expires_at=_expiry(),
        )
    except Exception as exc:
        logger.error(f"[notify] notify_payment_dispute failed: {exc}")
        return None


async def notify_refund_processed(
    booking_id: int,
    user_name: str,
    amount: float,
    event_title: str,
) -> Optional[NotificationOut]:
    """Register as a BackgroundTask in the refund router endpoint.

    Example:
        # in booking_admin.py or payment_admin.py
        from app.services.notification_services import notify_refund_processed
        ...
        @router.patch("/admin/bookings/{booking_id}/refund", response_model=BookingOut)
        async def refund_booking(booking_id: int, background_tasks: BackgroundTasks, ...):
            booking = await booking_services.refund_booking_service(booking_id)
            background_tasks.add_task(notify_refund_processed, booking.id, user.name, payment.amount, event.title)
            return booking
    """
    try:
        logger.info(f"[notify] refund processed: booking {booking_id}")
        return await notification_repo.create_notification_repo(
            title="Refund processed",
            message=f"Refund of KES {amount:,.0f} to {user_name} for {event_title} completed.",
            category="payment",
            priority="medium",
            recipient_role="admin",
            source_type="booking",
            source_id=booking_id,
            action_url="/payments",
            expires_at=_expiry(),
        )
    except Exception as exc:
        logger.error(f"[notify] notify_refund_processed failed: {exc}")
        return None


async def notify_revenue_milestone(
    milestone_amount: float,
    period_label: str,
    percent_above_target: float,
) -> Optional[NotificationOut]:
    """Register as a BackgroundTask in a scheduled analytics router endpoint
    or a cron-triggered admin route that checks revenue thresholds.

    Example:
        # in analytics_admin.py
        from app.services.notification_services import notify_revenue_milestone
        ...
        @router.post("/admin/analytics/check-milestones")
        async def check_milestones(background_tasks: BackgroundTasks, ...):
            result = await analytics_services.check_revenue_milestones_service()
            if result.milestone_crossed:
                background_tasks.add_task(notify_revenue_milestone, 400_000, "this month", 6.0)
            return result
    """
    try:
        logger.info(f"[notify] revenue milestone: KES {milestone_amount:,.0f}")
        return await notification_repo.create_notification_repo(
            title="Revenue milestone reached",
            message=(
                f"Revenue crossed KES {milestone_amount:,.0f} {period_label} — "
                f"{percent_above_target:.0f}% above target."
            ),
            category="payment",
            priority="medium",
            recipient_role="admin",
            source_type="system",
            action_url="/analytics",
            expires_at=_expiry(),
        )
    except Exception as exc:
        logger.error(f"[notify] notify_revenue_milestone failed: {exc}")
        return None


async def notify_payment_failure(
    payment_id: int,
    user_name: str,
    amount: float,
) -> Optional[NotificationOut]:
    """Register as a BackgroundTask in the payment processing router endpoint,
    triggered when a payment fails to go through.

    Example:
        # in payment_admin.py
        from app.services.notification_services import notify_payment_failure
        ...
        @router.post("/payments/initiate", response_model=PaymentOut)
        async def initiate_payment(payload: PaymentCreate, background_tasks: BackgroundTasks, ...):
            payment = await payment_services.initiate_payment_service(payload)
            if payment.status == "failed":
                background_tasks.add_task(notify_payment_failure, payment.id, user.name, payment.amount)
            return payment
    """
    try:
        logger.info(f"[notify] payment failure: {payment_id}")
        return await notification_repo.create_notification_repo(
            title="Payment failure detected",
            message=f"Payment of KES {amount:,.0f} by {user_name} failed to process.",
            category="payment",
            priority="high",
            recipient_role="admin",
            source_type="payment",
            source_id=payment_id,
            action_url="/payments",
            expires_at=_expiry(),
        )
    except Exception as exc:
        logger.error(f"[notify] notify_payment_failure failed: {exc}")
        return None


# ── Contact Messages ──────────────────────────────────────────────────────────

async def notify_new_contact_message(
    message_id: int,
    sender_name: str,
    email: str,
    subject: str,
    message: str,
    category: str = "general",
) -> Optional[NotificationOut]:
    """Register as a BackgroundTask in the contact message creation router endpoint.

    Example:
        # in contact_admin.py
        from app.services.notification_services import notify_new_contact_message
        ...
        @router.post("/contact", response_model=ContactMessageOut)
        async def create_contact_message(payload: ContactMessageCreate, background_tasks: BackgroundTasks):
            msg = await contact_services.create_message_service(payload)
            background_tasks.add_task(notify_new_contact_message, msg.id, msg.name, msg.email, msg.subject, msg.message, msg.category)
            return msg
    """
    try:
        logger.info(f"[notify] new contact message: {message_id}. The message is from {sender_name} with email {email} and subject '{subject}'.")
        priority = "high" if category in ("payment", "booking") else "medium"
        return await notification_repo.create_notification_repo(
            title="New contact message",
            message=f'{sender_name} sent a message: "{message}".',
            category="message",
            priority=priority,
            recipient_role="admin",
            source_type="message",
            source_id=message_id,
            action_url="/messages",
            expires_at=_expiry(),
        )
    except Exception as exc:
        logger.error(f"[notify] notify_new_contact_message failed: {exc}")
        return None


async def notify_message_spam_flagged(
    message_id: int,
    reference_id: str,
) -> Optional[NotificationOut]:
    """Register as a BackgroundTask in the spam-marking router endpoint.

    Example:
        # in contact_admin.py
        from app.services.notification_services import notify_message_spam_flagged
        ...
        @router.patch("/admin/contact/{message_id}/spam", response_model=ContactMessageOut)
        async def mark_spam(message_id: int, background_tasks: BackgroundTasks, ...):
            msg = await contact_services.mark_message_as_spam_service(message_id)
            background_tasks.add_task(notify_message_spam_flagged, msg.id, msg.reference_id)
            return msg
    """
    try:
        logger.info(f"[notify] message spam flagged: {message_id}")
        return await notification_repo.create_notification_repo(
            title="Spam message auto-flagged",
            message=f"System auto-marked {reference_id} as spam based on content filters.",
            category="system",
            priority="low",
            recipient_role="admin",
            source_type="message",
            source_id=message_id,
            action_url="/messages",
            expires_at=_expiry(),
        )
    except Exception as exc:
        logger.error(f"[notify] notify_message_spam_flagged failed: {exc}")
        return None


# ── System ────────────────────────────────────────────────────────────────────

async def notify_session_cleanup_complete(deleted_count: int) -> Optional[NotificationOut]:
    """Register as a BackgroundTask in the session cleanup router endpoint.

    Example:
        # in auth_admin.py
        from app.services.notification_services import notify_session_cleanup_complete
        ...
        @router.post("/admin/auth/cleanup-sessions")
        async def cleanup_sessions(hours: int = 24, background_tasks: BackgroundTasks = None, ...):
            result = await ref_session_services.cleanup_expired_and_revoked_sessions_service(hours)
            background_tasks.add_task(notify_session_cleanup_complete, result["deleted"])
            return result
    """
    try:
        logger.info(f"[notify] session cleanup: {deleted_count} sessions removed.")
        return await notification_repo.create_notification_repo(
            title="Session cleanup completed",
            message=f"{deleted_count} stale sessions were purged from the database.",
            category="system",
            priority="low",
            recipient_role="admin",
            source_type="system",
            expires_at=_expiry(days=7),  # system notices expire sooner
        )
    except Exception as exc:
        logger.error(f"[notify] notify_session_cleanup_complete failed: {exc}")
        return None


async def notify_bulk_user_registrations(
    new_user_count: int,
    period_label: str = "this week",
) -> Optional[NotificationOut]:
    """Register as a BackgroundTask in a scheduled analytics router endpoint
    or a cron-triggered admin route that runs weekly registration summaries.

    Example:
        # in analytics_admin.py
        from app.services.notification_services import notify_bulk_user_registrations
        ...
        @router.post("/admin/analytics/weekly-summary")
        async def weekly_summary(background_tasks: BackgroundTasks, ...):
            summary = await analytics_services.get_weekly_summary_service()
            background_tasks.add_task(notify_bulk_user_registrations, summary.new_users, "this week")
            return summary
    """
    try:
        logger.info(f"[notify] bulk registrations: {new_user_count}")
        return await notification_repo.create_notification_repo(
            title="New bulk user registrations",
            message=f"{new_user_count} new users joined {period_label}.",
            category="user",
            priority="low",
            recipient_role="admin",
            source_type="system",
            action_url="/users",
            expires_at=_expiry(),
        )
    except Exception as exc:
        logger.error(f"[notify] notify_bulk_user_registrations failed: {exc}")
        return None