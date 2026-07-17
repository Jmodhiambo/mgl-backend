#!/usr/bin/env python3
# app/api/organizer/organizer_emails.py
"""API routes for Organizer Emails."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from app.schemas.user import UserOut
from app.schemas.organizer_emails import (
    SendEmailRequest,
    SendEmailResponse,
    EmailHistoryResponse,
    EmailStatsResponse,
    EmailDetailWithRecipients,
)
from app.services import organizer_emails_services as email_services
from app.core.security import require_organizer, require_admin
from app.core.logging_config import logger

router = APIRouter()


# ── Organizer endpoints ───────────────────────────────────────────────────────

@router.post(
    "/organizers/me/emails/send",
    response_model=SendEmailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send bulk email to attendees",
)
async def send_bulk_email(
    data: SendEmailRequest,
    organizer: UserOut = Depends(require_organizer),
):
    """
    Send email to one or multiple booking recipients.

    template_used options: reminder, update, thank_you, cancellation,
    venue_change, time_change, custom.

    Named templates resolve subject automatically. Custom requires
    subject and custom_message. Templates that need extra context
    (e.g. update_message, old_venue/new_venue) must include those
    keys in extra_variables.
    """
    logger.info(
        f"Organizer {organizer.id} sending '{data.template_used}' "
        f"to {len(data.booking_ids)} booking(s)"
    )
    return await email_services.send_bulk_email_service(organizer.id, data)


@router.get(
    "/organizers/me/emails/stats",
    response_model=EmailStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get email statistics",
)
async def get_email_stats(
    organizer: UserOut = Depends(require_organizer),
):
    """Aggregate email stats for the current organizer."""
    logger.info(f"Organizer {organizer.id} fetching email stats")
    return await email_services.get_email_stats_service(organizer.id)


@router.get(
    "/organizers/me/emails",
    response_model=EmailHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get email history",
)
async def get_email_history(
    event_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    organizer: UserOut = Depends(require_organizer),
):
    """Paginated email history for the current organizer."""
    logger.info(f"Organizer {organizer.id} fetching email history")
    return await email_services.get_email_history_service(
        organizer_id=organizer.id,
        event_id=event_id,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/organizers/me/emails/{email_id}",
    response_model=EmailDetailWithRecipients,
    status_code=status.HTTP_200_OK,
    summary="Get email details",
)
async def get_email_details(
    email_id: int,
    organizer: UserOut = Depends(require_organizer),
):
    """Full email detail with per-recipient rows."""
    logger.info(f"Organizer {organizer.id} fetching details for email {email_id}")
    return await email_services.get_email_details_service(organizer.id, email_id)


@router.delete(
    "/organizers/me/emails/{email_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete email",
)
async def delete_email(
    email_id: int,
    organizer: UserOut = Depends(require_organizer),
):
    """Permanently delete an email and all its recipient records."""
    logger.info(f"Organizer {organizer.id} deleting email {email_id}")
    await email_services.delete_email_service(organizer.id, email_id)


# ── Admin endpoints ───────────────────────────────────────────────────────────

@router.get(
    "/admin/emails",
    response_model=EmailHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all emails (Admin)",
)
async def get_all_emails_admin(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    admin: UserOut = Depends(require_admin),
):
    """All emails across all organizers — admin only."""
    logger.info(f"Admin {admin.id} fetching all emails")
    return await email_services.get_all_emails_admin_service(limit=limit, offset=offset)


@router.get(
    "/admin/emails/stats",
    status_code=status.HTTP_200_OK,
    summary="Get overall email statistics (Admin)",
)
async def get_all_email_stats_admin(
    admin: UserOut = Depends(require_admin),
):
    """Platform-wide email statistics — admin only."""
    logger.info(f"Admin {admin.id} fetching overall email stats")
    return await email_services.get_all_email_stats_admin_service()


@router.get(
    "/admin/emails/{email_id}",
    response_model=EmailDetailWithRecipients,
    status_code=status.HTTP_200_OK,
    summary="Get email details (Admin)",
)
async def get_email_details_admin(
    email_id: int,
    admin: UserOut = Depends(require_admin),
):
    """View any email regardless of organizer — admin only."""
    logger.info(f"Admin {admin.id} fetching details for email {email_id}")
    return await email_services.get_email_details_admin_service(email_id)


# ── Template info endpoints ───────────────────────────────────────────────────

@router.get(
    "/email-templates",
    status_code=status.HTTP_200_OK,
    summary="Get available email templates",
)
async def get_email_templates():
    """List all registered organizer email templates from the template registry."""
    from app.emails.templates.template_registry import TemplateRegistry
    registry = TemplateRegistry()
    return registry.list(category="organizer")


@router.get(
    "/email-templates/variables",
    status_code=status.HTTP_200_OK,
    summary="Get template variables",
)
async def get_template_variables():
    """
    All variables available for use in email templates.
    Base variables are resolved from booking data automatically.
    Extra variables must be supplied in extra_variables on the send request.
    """
    return {
        "base_variables": [
            "customer_name", "order_id", "event_title", "ticket_type",
            "quantity", "venue", "event_date", "organizer_name", "total_price",
        ],
        "extra_variables": {
            "update":       ["update_message"],
            "cancellation": ["cancellation_reason", "total_price"],
            "venue_change": ["old_venue", "new_venue"],
            "time_change":  ["old_date_time", "new_date_time"],
        },
    }