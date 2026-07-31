#!/usr/bin/env python3
# app/services/organizer_emails_services.py
"""
Service layer for organizer bulk email operations.

Architecture:
  - Every organizer bulk-send template (the six named templates, plus
    'custom') renders through EmailManager's single branded wrapper —
    organizer/branded_message.html — via send_branded_message(). Subject
    and body are the organizer's own text; only the header colour/subtitle
    are looked up from the template's branding metadata.
  - Selecting a template_used only affects: (1) which header colour/subtitle
    is used, and (2) which extra_variables are required. It no longer locks
    the organizer into fixed copy — subject/body are always caller-supplied
    and are still personalised per recipient (see _substitute_tokens below).
  - organizer_emails + organizer_email_recipients tables track history.
  - Bulk sends are rate-limited to 10/sec to respect Resend API limits.
  - Each recipient email fires as a background task via _bg_email().
"""

import asyncio
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional

from fastapi import HTTPException, status

from app.core.config import FRONTEND_URL
from app.core.logging_config import logger
from app.emails.email_manager import email_manager
from app.emails.templates.template_registry import TemplateRegistry
from app.schemas.organizer_emails import (
    SendEmailRequest,
    SendEmailResponse,
    PreviewEmailRequest,
    PreviewEmailResponse,
    EmailHistoryResponse,
    EmailStatsResponse,
    EmailDetailWithRecipients,
    OrganizerEmailOut,
    OrganizerEmailRecipientOut,
)
import app.db.repositories.booking_repo as booking_repo
import app.db.repositories.organizer_emails_repo as email_repo
import app.db.repositories.organizer_email_recipients_repo as recipient_repo


_registry = TemplateRegistry()


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


def _format_eat(dt: datetime) -> str:
    """
    Render a UTC-stored datetime in Africa/Nairobi (EAT) for actual email
    content. booking_repo.get_enriched_bookings_by_ids_repo returns the raw
    UTC datetime — this is the one place that converts it for display,
    keeping the repo layer free of formatting concerns (same separation
    used in payment_services.py, event_services.py, and user_services.py).
    dt is assumed to be timezone-aware.
    """
    return dt.astimezone(ZoneInfo("Africa/Nairobi")).strftime("%d %b %Y at %H:%M EAT")


# ── Token substitution ────────────────────────────────────────────────────────

# Mirrors the frontend's fillTokens() in BookingsView.tsx exactly — same
# {{key}} syntax, same "leave unmatched tokens as-is" behaviour — so a
# personalised send never silently diverges from what the live preview
# showed for an unfilled token.
_TOKEN_RE = re.compile(r"\{\{(\w+)\}\}")


def _substitute_tokens(text: str, variables: dict) -> str:
    def _replace(match: "re.Match[str]") -> str:
        key = match.group(1)
        return str(variables[key]) if key in variables else match.group(0)
    return _TOKEN_RE.sub(_replace, text)


# ── Template validation / branding ────────────────────────────────────────────

_VALID_TEMPLATES = {
    "reminder", "update", "thank_you", "cancellation",
    "venue_change", "time_change", "custom",
}

# Extra variables each named template requires beyond the base booking set.
# Still enforced even though subject/body are free text — an organizer can
# reference {{cancellation_reason}} in their message, but they still have to
# have actually filled it in.
_EXTRA_REQUIRED: dict[str, list[str]] = {
    "reminder":     [],
    "update":       ["update_message"],
    "thank_you":    [],
    "cancellation": ["cancellation_reason", "total_price"],
    "venue_change": ["old_venue", "new_venue"],
    "time_change":  ["old_date_time", "new_date_time"],
    "custom":       [],
}

# 'custom' has no registered EmailTemplate (it isn't a fixed template at
# all), so its branding lives here rather than in the registry.
_CUSTOM_BRANDING = {"header_class": "blue", "header_subtitle": "Message From Your Organizer"}


def _get_branding(template_used: str) -> dict:
    """Resolve {header_class, header_subtitle} for a template_used value."""
    if template_used == "custom":
        return _CUSTOM_BRANDING

    template = _registry.get(f"organizer.{template_used}")
    if not template:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown template_used '{template_used}'.",
        )
    return {"header_class": template.header_class, "header_subtitle": template.header_subtitle}


# ── Send ──────────────────────────────────────────────────────────────────────

async def send_bulk_email_service(
    organizer_id: int,
    organizer_name: str,
    data: SendEmailRequest,
) -> SendEmailResponse:
    """
    Resolve each booking to an attendee, personalise the organizer's subject
    and body per recipient, and fire emails in background at a rate-limited
    pace.

    Flow:
      1. Validate template_used and extra_variables presence.
      2. Fetch enriched booking rows (customer_email, order_id, etc.).
      3. Create an OrganizerEmails log row (status=pending).
      4. For each recipient: substitute {{tokens}} in subject/body using
         that booking's own data, schedule the branded send, create an
         OrganizerEmailRecipients row (status=pending).
      5. Update log row to sent / partially_sent / failed.
    """
    template_used = data.template_used.lower()

    if template_used not in _VALID_TEMPLATES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown template_used '{template_used}'. "
                   f"Valid options: {', '.join(sorted(_VALID_TEMPLATES))}",
        )

    if not data.subject:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="subject is required.")
    if not data.body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="body is required.")

    # Validate extra_variables
    required_extras = _EXTRA_REQUIRED.get(template_used, [])
    extra = data.extra_variables or {}
    missing = [k for k in required_extras if not extra.get(k)]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template '{template_used}' requires extra_variables: "
                   f"{', '.join(missing)}",
        )

    branding = _get_branding(template_used)

    # Fetch enriched bookings — scoped to this organizer's own events.
    bookings = await booking_repo.get_enriched_bookings_by_ids_repo(
        data.booking_ids, organizer_id=organizer_id,
    )
    if not bookings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No bookings found for the provided booking_ids.")

    # If any requested id didn't come back, it either doesn't exist or
    # belongs to another organizer's event — either way, reject the whole
    # request rather than silently emailing a subset. Deliberately not
    # distinguishing "doesn't exist" from "not yours" in the message.
    returned_ids = {b.id for b in bookings}
    missing_ids = set(data.booking_ids) - returned_ids
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking(s) not found: {sorted(missing_ids)}",
        )

    total = len(bookings)
    recipient_emails = [b.customer_email for b in bookings if b.customer_email]
    event_id = bookings[0].event_id if bookings else None

    # Create email log row — message now always holds the organizer's own
    # body text, not just the old 'custom'-only special case.
    email_log = await email_repo.create_organizer_email_repo(
        organizer_id=organizer_id,
        event_id=event_id,
        recipient_type="single" if total == 1 else "bulk",
        recipient_count=total,
        subject=data.subject,
        message=data.body,
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
            variables = _build_base_variables(organizer_name, booking, extra)
            personalized_subject = _substitute_tokens(data.subject, variables)
            personalized_body = _substitute_tokens(data.body, variables)

            _bg_email(_send_branded_and_update(
                recipient_id=recipient.id,
                to_email=booking.customer_email,
                subject=personalized_subject,
                body=personalized_body,
                header_class=branding["header_class"],
                header_subtitle=branding["header_subtitle"],
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


# ── Preview ───────────────────────────────────────────────────────────────────

async def preview_email_service(
    organizer_id: int,
    organizer_name: str,
    data: PreviewEmailRequest,
) -> PreviewEmailResponse:
    """
    Render exactly what send_bulk_email_service would dispatch for one
    representative booking — same branding lookup, same token substitution,
    same EmailManager render path — without creating any log/recipient rows
    or sending anything.

    Scoped to the calling organizer's own events — a booking_id belonging
    to another organizer reads as a plain 404, same as if it didn't exist.
    """
    template_used = data.template_used.lower()

    if template_used not in _VALID_TEMPLATES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown template_used '{template_used}'. "
                   f"Valid options: {', '.join(sorted(_VALID_TEMPLATES))}",
        )

    branding = _get_branding(template_used)

    bookings = await booking_repo.get_enriched_bookings_by_ids_repo(
        [data.booking_id], organizer_id=organizer_id,
    )
    if not bookings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")
    booking = bookings[0]

    extra = data.extra_variables or {}
    variables = _build_base_variables(organizer_name, booking, extra)

    subject = _substitute_tokens(data.subject, variables)
    body = _substitute_tokens(data.body, variables)

    html = email_manager.render_branded_message(
        subject=subject,
        body=body,
        header_class=branding["header_class"],
        header_subtitle=branding["header_subtitle"],
    )

    return PreviewEmailResponse(subject=subject, html=html)


# ── Per-recipient coroutine ───────────────────────────────────────────────────

async def _send_branded_and_update(
    recipient_id: int,
    to_email: str,
    subject: str,
    body: str,
    header_class: str,
    header_subtitle: str,
) -> None:
    """Send a branded free-text email then update the recipient row."""
    try:
        await email_manager.send_branded_message(
            to_email=to_email,
            subject=subject,
            body=body,
            header_class=header_class,
            header_subtitle=header_subtitle,
        )
        await recipient_repo.update_recipient_status_repo(
            recipient_id=recipient_id,
            status="sent",
            sent_at=datetime.now(timezone.utc),
        )
    except Exception as exc:
        logger.error(f"Failed to send email to {to_email}: {exc}")
        await recipient_repo.update_recipient_status_repo(
            recipient_id=recipient_id,
            status="failed",
            error_message=str(exc),
        )


# ── Variable builder ──────────────────────────────────────────────────────────

def _build_base_variables(organizer_name: str, booking, extra: dict) -> dict:
    """Build the per-recipient {{token}} substitution dict from an enriched booking row."""
    base = {
        "customer_name":  booking.customer_name or "Valued Customer",
        "order_id":       str(booking.order_id or booking.id),
        "event_title":    booking.event_title or "your event",
        "ticket_type":    booking.ticket_type_name or "General",
        "quantity":       str(booking.quantity),
        "venue":          booking.venue or "TBA",
        "event_date":     _format_eat(booking.event_date) if booking.event_date else "TBA",
        "organizer_name": organizer_name or "Your Organizer",
        "total_price":    f"{booking.total_price:,.0f}" if booking.total_price else "0",
    }
    base.update(extra)
    return base


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