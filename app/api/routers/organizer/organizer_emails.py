#!/usr/bin/env python3
"""API routes for Organizer Emails."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from app.schemas.user import UserOut
from app.schemas.organizer_emails import (
    SendEmailRequest,
    SendEmailResponse,
    EmailHistoryResponse,
    EmailStatsResponse,
    EmailDetailWithRecipients
)
from app.services import organizer_emails_services as email_services
from app.core.security import require_organizer, require_admin
from app.core.logging_config import logger

router = APIRouter()


# ==================== Organizer Endpoints ====================

@router.post(
    "/organizers/me/emails/send",
    response_model=SendEmailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send bulk email to attendees",
    description="Send email to one or multiple booking recipients. Supports templates and custom messages."
)
async def send_bulk_email(
    data: SendEmailRequest,
    organizer: UserOut = Depends(require_organizer)
):
    """
    Send email to attendees.
    
    **Use cases:**
    - Event reminders (24 hours before)
    - Last-minute changes (venue, time)
    - Post-event thank you messages
    - Special announcements
    - Weather alerts
    
    **Template options:**
    - `reminder`: Event reminder template
    - `update`: Event update template
    - `thank_you`: Thank you template
    - `cancellation`: Event cancellation
    - `venue_change`: Venue change notification
    - `time_change`: Time change notification
    - `custom`: Custom message
    """
    logger.info(f"Organizer {organizer.id} sending bulk email to {len(data.booking_ids)} bookings")
    return await email_services.send_bulk_email_service(organizer.id, data)


@router.get(
    "/organizers/me/emails",
    response_model=EmailHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get email history",
    description="Retrieve email sending history with optional filters"
)
async def get_email_history(
    event_id: Optional[int] = Query(None, description="Filter by event ID"),
    status: Optional[str] = Query(None, description="Filter by status (pending, sent, failed, partially_sent)"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    organizer: UserOut = Depends(require_organizer)
):
    """
    Get email history for the current organizer.
    
    **Filters:**
    - `event_id`: Show emails for a specific event
    - `status`: Filter by email status
    - `limit`: Results per page (1-100)
    - `offset`: Pagination offset
    
    **Returns:** Paginated list of emails with metadata
    """
    logger.info(f"Organizer {organizer.id} fetching email history")
    return await email_services.get_email_history_service(
        organizer_id=organizer.id,
        event_id=event_id,
        status=status,
        limit=limit,
        offset=offset
    )


@router.get(
    "/organizers/me/emails/{email_id}",
    response_model=EmailDetailWithRecipients,
    status_code=status.HTTP_200_OK,
    summary="Get email details",
    description="Get detailed information about a specific email including all recipients"
)
async def get_email_details(
    email_id: int,
    organizer: UserOut = Depends(require_organizer)
):
    """
    Get detailed email information.
    
    **Includes:**
    - Email content and metadata
    - List of all recipients
    - Individual recipient status
    - Send/open/click statistics
    
    **Returns:** Complete email details with recipient information
    """
    logger.info(f"Organizer {organizer.id} fetching details for email {email_id}")
    return await email_services.get_email_details_service(organizer.id, email_id)


@router.get(
    "/organizers/me/emails/stats",
    response_model=EmailStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get email statistics",
    description="Get comprehensive email statistics for the organizer"
)
async def get_email_stats(
    organizer: UserOut = Depends(require_organizer)
):
    """
    Get email statistics.
    
    **Includes:**
    - Total emails sent
    - Total recipients
    - Success rate
    - This month's activity
    - Breakdown by template
    - Breakdown by status
    
    **Returns:** Comprehensive email statistics
    """
    logger.info(f"Organizer {organizer.id} fetching email stats")
    return await email_services.get_email_stats_service(organizer.id)


@router.delete(
    "/organizers/me/emails/{email_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete email",
    description="Delete an email and all associated recipient records"
)
async def delete_email(
    email_id: int,
    organizer: UserOut = Depends(require_organizer)
):
    """
    Delete an email.
    
    **Warning:** This will permanently delete:
    - The email record
    - All recipient records
    - Send statistics
    
    This action cannot be undone.
    
    **Returns:** 204 No Content on success
    """
    logger.info(f"Organizer {organizer.id} deleting email {email_id}")
    await email_services.delete_email_service(organizer.id, email_id)
    return {"message": "Email deleted successfully"}


# ==================== Admin Endpoints ====================

@router.get(
    "/admin/emails",
    response_model=EmailHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all emails (Admin)",
    description="Admin endpoint to view all emails across all organizers"
)
async def get_all_emails_admin(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    admin: UserOut = Depends(require_admin)
):
    """
    Get all emails (admin only).
    
    **Admin access:** View emails from all organizers
    
    **Returns:** Paginated list of all emails
    """
    logger.info(f"Admin {admin.id} fetching all emails")
    return await email_services.get_all_emails_admin_service(limit=limit, offset=offset)


@router.get(
    "/admin/emails/stats",
    status_code=status.HTTP_200_OK,
    summary="Get overall email statistics (Admin)",
    description="Admin endpoint to view overall email statistics"
)
async def get_all_email_stats_admin(
    admin: UserOut = Depends(require_admin)
):
    """
    Get overall email statistics (admin only).
    
    **Includes:**
    - Total emails across all organizers
    - Total recipients
    - Breakdown by status
    
    **Returns:** Platform-wide email statistics
    """
    logger.info(f"Admin {admin.id} fetching overall email stats")
    return await email_services.get_all_email_stats_admin_service()


@router.get(
    "/admin/emails/{email_id}",
    response_model=EmailDetailWithRecipients,
    status_code=status.HTTP_200_OK,
    summary="Get email details (Admin)",
    description="Admin endpoint to view any email details"
)
async def get_email_details_admin(
    email_id: int,
    admin: UserOut = Depends(require_admin)
):
    """
    Get email details (admin can view any email).
    
    **Admin access:** View details of any email regardless of organizer
    
    **Returns:** Complete email details with recipient information
    """
    logger.info(f"Admin {admin.id} fetching details for email {email_id}")
    return await email_services.get_email_details_admin_service(email_id)


# ==================== Email Templates Endpoint ====================

@router.get(
    "/email-templates",
    status_code=status.HTTP_200_OK,
    summary="Get available email templates",
    description="Get list of available email templates with their content"
)
async def get_email_templates():
    """
    Get available email templates.
    
    **Available templates:**
    - `reminder`: Event reminder
    - `update`: Event update
    - `thank_you`: Thank you message
    - `cancellation`: Event cancellation
    - `venue_change`: Venue change notification
    - `time_change`: Time change notification
    - `custom`: Blank template
    
    **Returns:** Dictionary of templates with subjects and bodies
    """
    from app.utils.email_templates import get_email_templates
    return get_email_templates()


@router.get(
    "/email-templates/variables",
    status_code=status.HTTP_200_OK,
    summary="Get template variables",
    description="Get list of available variables for email templates"
)
async def get_template_variables():
    """
    Get available template variables.
    
    **Usage:** Use these variables in custom templates with {variable_name} syntax
    
    **Example:** "Dear {customer_name}, your booking #{booking_id} is confirmed!"
    
    **Returns:** List of available variable names
    """
    from app.utils.email_templates import get_template_variables
    return {"variables": get_template_variables()}