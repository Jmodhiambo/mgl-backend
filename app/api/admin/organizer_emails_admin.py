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
    "/admin/email-templates",
    status_code=status.HTTP_200_OK,
    summary="Get All Email Templates (Admin)",
    description="View all available email templates in the system"
)
async def get_all_templates_admin(
    admin: UserOut = Depends(require_admin)
):
    """
    Get all email templates (admin only).
    
    **Admin Access:** View all email templates across categories.
    
    **Includes:**
    - User templates
    - Organizer templates
    - Admin templates (if any)
    - Template metadata and required variables
    
    **Returns:**
    - Complete list of all templates
    
    **Use Cases:**
    - Template management
    - Content review
    - Template documentation
    """
    from app.emails.email_manager import email_manager
    
    logger.info(f"Admin {admin.id} fetching all email templates")
    return email_manager.list_templates()
 
 
@router.get(
    "/admin/email-templates/{template_id}",
    status_code=status.HTTP_200_OK,
    summary="Get Template Details (Admin)",
    description="View detailed information about a specific template"
)
async def get_template_details_admin(
    template_id: str,
    admin: UserOut = Depends(require_admin)
):
    """
    Get specific template details (admin only).
    
    **Admin Access:** View full template information.
    
    **Includes:**
    - Template ID and name
    - Category
    - Description
    - Required variables
    - Template content preview
    
    **Returns:**
    - Complete template metadata
    
    **Use Cases:**
    - Template inspection
    - Content review
    - Variable documentation
    """
    from app.emails.email_manager import email_manager
    
    logger.info(f"Admin {admin.id} fetching template {template_id}")
    template_info = email_manager.get_template_info(template_id)
    
    if not template_info:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template '{template_id}' not found"
        )
    
    return template_info