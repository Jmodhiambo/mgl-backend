#!/usr/bin/env python3
# app/services/organizer_emails_services.py
"""
Service layer for organizer bulk email operations.

Architecture:
  - Sending goes through email_manager (Resend).
  - organizer_emails + organizer_email_recipients tables track history.
  - Bulk sends are rate-limited to 10/sec to respect Resend API limits.
  - Each recipient email fires as a background task via _bg_email().
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status

from app.core.config import FRONTEND_URL
from app.core.logging_config import logger
from app.emails.email_manager import email_manager
from app.schemas.organizer_emails import (
    SendEmailRequest,
    SendEmailResponse,
    EmailHistoryResponse,
    EmailStatsResponse,
    EmailDetailWithRecipients,
    OrganizerEmailOut,
    OrganizerEmailRecipientOut,
    EmailTemplateStats,
)
import app.db.repositories.booking_repo as booking_repo
import app.db.repositories.organizer_emails_repo as email_repo
import app.db.repositories.organizer_email_recipients_repo as recipient_repo


# ── Background helper ─────────────────────────────────────────────────────────

def _bg_email(coro) -> None:
    """
    Schedule an email coroutine as a background task.
    Falls back to direct run if no running event loop exists (tests, CLI).
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        asyncio.run(coro)


# ── Template mapping ──────────────────────────────────────────────────────────

# Maps frontend template_used value to the registered email_manager template ID.
_TEMPLATE_ID_MAP = {
    "reminder":     "organizer.reminder",
    "update":       "organizer.update",
    "thank_you":    "organizer.thank_you",
    "cancellation": "organizer.cancellation",
    "venue_change": "organizer.venue_change",
    "time_change":  "organizer.time_change",
    "custom":       None,   # handled via email_manager.send_custom
}

# Extra variables each named template requires beyond the base booking set.
_EXTRA_REQUIRED: dict[str, list[str]] = {
    "reminder":     [],
    "update":       ["update_message"],
    "thank_you":    [],
    "cancellation": ["cancellation_reason", "total_price"],
    "venue_change": ["old_venue", "new_venue"],
    "time_change":  ["old_date_time", "new_date_time"],
    "custom":       [],
}


# ── Send ──────────────────────────────────────────────────────────────────────

async def send_bulk_email_service(
    organizer_id: int,
    data: SendEmailRequest,
) -> SendEmailResponse:
    """
    Resolve each booking to an attendee, build per-recipient variables,
    and fire emails in background at a rate-limited pace.

    Flow:
      1. Validate template_used and extra_variables presence.
      2. Fetch enriched booking rows (customer_email, order_id, etc.).
      3. Create an OrganizerEmails log row (status=pending).
      4. For each recipient: build variables, schedule email, create
         OrganizerEmailRecipients row (status=pending).
      5. Update log row to sent / partially_sent / failed.
    """
    template_used = data.template_used.lower()

    if template_used not in _TEMPLATE_ID_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown template_used '{template_used}'. "
                   f"Valid options: {', '.join(_TEMPLATE_ID_MAP.keys())}",
        )

    # Validate extra_variables
    required_extras = _EXTRA_REQUIRED.get(template_used, [])
    extra = data.extra_variables or {}
    missing = [k for k in required_extras if k not in extra]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template '{template_used}' requires extra_variables: "
                   f"{', '.join(missing)}",
        )

    if template_used == "custom":
        if not data.custom_message:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="custom_message is required for template_used 'custom'.")
        if not data.subject:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="subject is required for template_used 'custom'.")

    # Fetch enriched bookings
    bookings = await booking_repo.get_enriched_bookings_by_ids_repo(data.booking_ids)
    if not bookings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No bookings found for the provided booking_ids.")

    total = len(bookings)
    recipient_emails = [b.customer_email for b in bookings if b.customer_email]
    event_id = bookings[0].event_id if bookings else None
    subject = data.subject or _resolve_subject(template_used, bookings[0], extra)

    # Create email log row
    email_log = await email_repo.create_organizer_email_repo(
        organizer_id=organizer_id,
        event_id=event_id,
        recipient_type="single" if total == 1 else "bulk",
        recipient_count=total,
        subject=subject,
        message=data.custom_message or "",
        template_used=template_used,
        booking_ids=data.booking_ids,
        recipient_emails=recipient_emails,
    )

    sent = 0
    failed = 0

    for i, booking in enumerate(bookings):
        # Rate-limit — 10 emails/sec
        if i > 0 and i % 10 == 0:
            await asyncio.sleep(1)

        if not booking.customer_email:
            logger.warning(f"Booking {booking.id} has no customer email — skipping")
            failed += 1
            continue

        # Create recipient row
        recipient = await recipient_repo.create_email_recipient_repo(
            email_id=email_log.id,
            booking_id=booking.id,
            recipient_name=booking.customer_name or "Valued Customer",
            recipient_email=booking.customer_email,
        )

        try:
            if template_used == "custom":
                _bg_email(_send_custom_and_update(
                    recipient_id=recipient.id,
                    to_email=booking.customer_email,
                    subject=subject,
                    body=data.custom_message,
                    organizer_name=booking.organizer_name or "Your Organizer",
                ))
            else:
                base_vars = _build_base_variables(booking, extra)
                _bg_email(_send_template_and_update(
                    recipient_id=recipient.id,
                    template_id=_TEMPLATE_ID_MAP[template_used],
                    to_email=booking.customer_email,
                    variables=base_vars,
                ))
            sent += 1

        except Exception as exc:
            logger.error(f"Failed to queue email for booking {booking.id}: {exc}")
            await recipient_repo.update_recipient_status_repo(
                recipient_id=recipient.id,
                status="failed",
                error_message=str(exc),
            )
            failed += 1

    # Resolve final status
    if failed == 0:
        final_status = "sent"
    elif sent == 0:
        final_status = "failed"
    else:
        final_status = "partially_sent"

    await email_repo.update_organizer_email_status_repo(
        email_id=email_log.id,
        status=final_status,
        success_count=sent,
        failed_count=failed,
        sent_at=datetime.now(timezone.utc),
    )

    logger.info(
        f"Bulk email '{template_used}' by organizer {organizer_id}: "
        f"{sent}/{total} queued, {failed} failed."
    )

    return SendEmailResponse(
        total_recipients=total,
        queued=sent,
        failed=failed,
        email_id=email_log.id,
        message=f"{sent} email(s) queued successfully."
        + (f" {failed} failed." if failed else ""),
    )


# ── Per-recipient coroutines ──────────────────────────────────────────────────

async def _send_template_and_update(
    recipient_id: int,
    template_id: str,
    to_email: str,
    variables: dict,
) -> None:
    """Send a named template then update the recipient row."""
    try:
        await email_manager.send_from_template(
            template_id=template_id,
            to_email=to_email,
            variables=variables,
        )
        await recipient_repo.update_recipient_status_repo(
            recipient_id=recipient_id,
            status="sent",
            sent_at=datetime.now(timezone.utc),
        )
    except Exception as exc:
        logger.error(f"Failed to send template email to {to_email}: {exc}")
        await recipient_repo.update_recipient_status_repo(
            recipient_id=recipient_id,
            status="failed",
            error_message=str(exc),
        )


async def _send_custom_and_update(
    recipient_id: int,
    to_email: str,
    subject: str,
    body: str,
    organizer_name: str,
) -> None:
    """Send a custom freeform email then update the recipient row."""
    try:
        await email_manager.send_custom(
            to_email=to_email,
            subject=subject,
            body=body,
            organizer_name=organizer_name,
        )
        await recipient_repo.update_recipient_status_repo(
            recipient_id=recipient_id,
            status="sent",
            sent_at=datetime.now(timezone.utc),
        )
    except Exception as exc:
        logger.error(f"Failed to send custom email to {to_email}: {exc}")
        await recipient_repo.update_recipient_status_repo(
            recipient_id=recipient_id,
            status="failed",
            error_message=str(exc),
        )


# ── Variable builders ─────────────────────────────────────────────────────────

def _build_base_variables(booking, extra: dict) -> dict:
    """Build the template variable dict from an enriched booking row."""
    base = {
        "customer_name":  booking.customer_name or "Valued Customer",
        "order_id":       str(booking.order_id or booking.id),
        "event_title":    booking.event_title or "your event",
        "ticket_type":    booking.ticket_type_name or "General",
        "quantity":       str(booking.quantity),
        "venue":          booking.venue or "TBA",
        "event_date":     booking.event_date or "TBA",
        "organizer_name": booking.organizer_name or "Your Organizer",
        "total_price":    f"{booking.total_price:,.0f}" if booking.total_price else "0",
    }
    base.update(extra)
    return base


def _resolve_subject(template_used: str, booking, extra: dict) -> str:
    """Generate a subject line for the log row when none is provided."""
    titles = {
        "reminder":     f"Reminder: {booking.event_title} is Coming Up!",
        "update":       f"Important Update: {booking.event_title}",
        "thank_you":    f"Thank You for Attending {booking.event_title}!",
        "cancellation": f"Important: {booking.event_title} Has Been Cancelled",
        "venue_change": f"Venue Change: {booking.event_title}",
        "time_change":  f"Time Change: {booking.event_title}",
        "custom":       "Message from your organizer",
    }
    return titles.get(template_used, "Message from MGLTickets")


# ── History ───────────────────────────────────────────────────────────────────

async def get_email_history_service(
    organizer_id: int,
    event_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> EmailHistoryResponse:
    logger.info(f"Fetching email history for organizer {organizer_id}")
    emails, total = await email_repo.get_organizer_emails_by_organizer_repo(
        organizer_id=organizer_id,
        event_id=event_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return EmailHistoryResponse(
        total=total,
        limit=limit,
        offset=offset,
        emails=emails,
    )


async def get_email_details_service(
    organizer_id: int, email_id: int
) -> EmailDetailWithRecipients:
    logger.info(f"Fetching email {email_id} for organizer {organizer_id}")
    detail = await email_repo.get_organizer_email_with_recipients_repo(email_id)
    if not detail or detail.organizer_id != organizer_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found.")
    return detail


async def get_email_details_admin_service(email_id: int) -> EmailDetailWithRecipients:
    logger.info(f"Admin fetching email {email_id}")
    detail = await email_repo.get_organizer_email_with_recipients_repo(email_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found.")
    return detail


# ── Stats ─────────────────────────────────────────────────────────────────────

async def get_email_stats_service(organizer_id: int) -> EmailStatsResponse:
    logger.info(f"Fetching email stats for organizer {organizer_id}")
    raw = await email_repo.get_email_stats_repo(organizer_id=organizer_id)
    return EmailStatsResponse(
        total_sent=raw["total_sent"],
        total_recipients=raw["total_recipients"],
        success_rate=raw["success_rate"],
        emails_this_month=raw["emails_this_month"],
        recipients_this_month=raw["recipients_this_month"],
        by_template=raw["by_template"],
        by_status=raw["by_status"],
    )


async def get_all_emails_admin_service(
    limit: int = 50, offset: int = 0
) -> EmailHistoryResponse:
    logger.info("Admin fetching all emails")
    emails, total = await email_repo.get_all_organizer_emails_repo(limit=limit, offset=offset)
    return EmailHistoryResponse(total=total, limit=limit, offset=offset, emails=emails)


async def get_all_email_stats_admin_service() -> dict:
    logger.info("Admin fetching overall email stats")
    return await email_repo.get_all_email_stats_repo()


# ── Delete ────────────────────────────────────────────────────────────────────

async def delete_email_service(organizer_id: int, email_id: int) -> None:
    logger.info(f"Organizer {organizer_id} deleting email {email_id}")
    email = await email_repo.get_organizer_email_by_id_repo(email_id)
    if not email or email.organizer_id != organizer_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found.")
    await email_repo.delete_organizer_email_repo(email_id)