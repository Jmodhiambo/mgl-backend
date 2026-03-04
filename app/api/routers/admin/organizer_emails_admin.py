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