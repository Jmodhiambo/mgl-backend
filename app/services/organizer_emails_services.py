#!/usr/bin/env python3
"""Services for OrganizerEmails operations."""

from typing import List, Optional
from fastapi import HTTPException, status
from datetime import datetime, timezone
from app.core.logging_config import logger
from app.services.user_services import get_user_by_id_service
from app.services.booking_services import get_bookings_by_ids_service
from app.db.repositories import organizer_emails_repo as email_repo
from app.db.repositories import organizer_email_recipients_repo as recipient_repo
from app.emails.email_manager import email_manager
from app.emails.templates.organizer.custom_email import send_custom_email
from app.schemas.organizer_emails import (
    SendEmailRequest,
    SendEmailResponse,
    OrganizerEmailOut,
    OrganizerEmailDetail,
    EmailDetailWithRecipients,
    EmailHistoryResponse,
    EmailStatsResponse,
    OrganizerEmailRecipientOut
)


async def send_bulk_email_service(
    organizer_id: int,
    data: SendEmailRequest
) -> SendEmailResponse:
    """
    Send bulk email to multiple bookings using email templates.
    
    Args:
        organizer_id: ID of the organizer sending the email
        data: Email data including booking IDs, subject, and message
    
    Returns:
        SendEmailResponse with email ID and send statistics
    """
    logger.info(f"Organizer {organizer_id} sending bulk email to {len(data.booking_ids)} bookings")
    
    # Validation
    if not data.booking_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No booking IDs provided"
        )
    
    if not data.subject or len(data.subject.strip()) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject must be at least 3 characters"
        )
    
    if not data.message or len(data.message.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message must be at least 10 characters"
        )
    
    # Validate template_used
    valid_templates = ['reminder', 'update', 'thank_you', 'cancellation', 'venue_change', 'time_change', 'custom']
    if data.template_used not in valid_templates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid template. Must be one of: {', '.join(valid_templates)}"
        )
    
    # Fetch booking details from database
    bookings = await get_bookings_by_ids_service(data.booking_ids)
    
    if not bookings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No valid bookings found"
        )
    
    # Get organizer details (for email variables)
    organizer = await get_user_by_id_service(organizer_id)
    
    # Determine recipient type
    recipient_type = 'single' if len(bookings) == 1 else 'bulk'
    recipient_count = len(bookings)
    recipient_emails = [b['customer_email'] for b in bookings]
    
    # Create email record
    email_record = await email_repo.create_organizer_email_repo(
        organizer_id=organizer_id,
        event_id=data.event_id,
        recipient_type=recipient_type,
        recipient_count=recipient_count,
        subject=data.subject,
        message=data.message,
        template_used=data.template_used,
        booking_ids=data.booking_ids,
        recipient_emails=recipient_emails
    )
    
    # Map template_used to template_id
    template_id = f'organizer.{data.template_used}'
    
    # Create recipient records and send emails
    success_count = 0
    failed_count = 0
    
    for booking in bookings:
        # Create recipient record
        recipient = await recipient_repo.create_email_recipient_repo(
            email_id=email_record.id,
            booking_id=booking['id'],
            recipient_name=booking['customer_name'],
            recipient_email=booking['customer_email']
        )
        
        try:
            # Prepare email variables
            email_variables = {
                'customer_name': booking['customer_name'],
                'event_title': booking['event_title'],
                'ticket_type': booking['ticket_type'],
                'quantity': str(booking['quantity']),
                'booking_id': str(booking['id']),
                'venue': booking.get('venue', 'TBA'),
                'event_date': booking.get('event_date', 'TBA'),
                'organizer_name': organizer['name'],
                'organization_name': organizer.get('organization_name', 'MGLTickets')
            }
            
            # Add template-specific variables
            if data.template_used == 'update':
                email_variables['update_message'] = data.message
            elif data.template_used == 'cancellation':
                email_variables['cancellation_reason'] = data.message
                email_variables['total_price'] = str(booking.get('total_price', 0))
            elif data.template_used == 'venue_change':
                email_variables['old_venue'] = booking.get('old_venue', 'Previous venue')
                email_variables['new_venue'] = booking.get('venue', 'New venue')
                email_variables['venue_address'] = booking.get('venue_address', 'Address TBA')
            elif data.template_used == 'time_change':
                email_variables['old_date_time'] = booking.get('old_date_time', 'Previous date/time')
                email_variables['new_date_time'] = booking.get('event_date', 'New date/time')
            
            # For custom template, we use the subject and message directly
            if data.template_used == 'custom':
                # Send custom email without template
                success = await send_custom_email(
                    to=booking['customer_email'],
                    subject=data.subject,
                    body=data.message,
                    organizer_name=organizer['name']
                )
            else:
                # Send email using template
                success = await email_manager.send_from_template(
                    template_id=template_id,
                    to_email=booking['customer_email'],
                    variables=email_variables,
                    from_email='no_reply'
                )
            
            if success:
                # Update recipient status
                await recipient_repo.update_recipient_status_repo(
                    recipient_id=recipient.id,
                    status='sent',
                    sent_at=datetime.now(timezone.utc)
                )
                success_count += 1
                logger.info(f"Email sent successfully to {booking['customer_email']}")
            else:
                raise Exception("Email send failed")
            
        except Exception as e:
            # Update recipient with error
            await recipient_repo.update_recipient_status_repo(
                recipient_id=recipient.id,
                status='failed',
                error_message=str(e)
            )
            failed_count += 1
            logger.error(f"Failed to send email to {booking['customer_email']}: {str(e)}")
    
    # Update email record with final status
    final_status = 'sent' if failed_count == 0 else ('partially_sent' if success_count > 0 else 'failed')
    await email_repo.update_organizer_email_status_repo(
        email_id=email_record.id,
        status=final_status,
        success_count=success_count,
        failed_count=failed_count,
        sent_at=datetime.now(timezone.utc)
    )
    
    logger.info(f"Bulk email completed. Success: {success_count}, Failed: {failed_count}")
    
    return SendEmailResponse(
        email_id=email_record.id,
        recipient_count=recipient_count,
        status=final_status,
        success_count=success_count,
        failed_count=failed_count,
        message=f"Email sent to {success_count} recipient(s)" if failed_count == 0 
                else f"Email sent to {success_count} recipient(s), {failed_count} failed"
    )


async def get_email_history_service(
    organizer_id: int,
    event_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> EmailHistoryResponse:
    """
    Get email history for an organizer.
    
    Args:
        organizer_id: ID of the organizer
        event_id: Optional event ID to filter by
        status: Optional status to filter by
        limit: Maximum number of results
        offset: Offset for pagination
    
    Returns:
        EmailHistoryResponse with list of emails and pagination info
    """
    logger.info(f"Fetching email history for organizer {organizer_id}")
    
    emails, total = await email_repo.get_organizer_emails_by_organizer_repo(
        organizer_id=organizer_id,
        event_id=event_id,
        status=status,
        limit=limit,
        offset=offset
    )
    
    return EmailHistoryResponse(
        emails=emails,
        total=total,
        limit=limit,
        offset=offset
    )


async def get_email_details_service(
    organizer_id: int,
    email_id: int
) -> EmailDetailWithRecipients:
    """
    Get detailed information about a specific email.
    
    Args:
        organizer_id: ID of the organizer
        email_id: ID of the email
    
    Returns:
        EmailDetailWithRecipients with full email and recipient details
    """
    logger.info(f"Fetching email details for email {email_id}")
    
    email = await email_repo.get_organizer_email_with_recipients_repo(email_id)
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    
    # Verify ownership
    if email.organizer_id != organizer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this email"
        )
    
    return email


async def get_email_stats_service(organizer_id: int) -> EmailStatsResponse:
    """
    Get email statistics for an organizer.
    
    Args:
        organizer_id: ID of the organizer
    
    Returns:
        EmailStatsResponse with comprehensive statistics
    """
    logger.info(f"Fetching email stats for organizer {organizer_id}")
    
    stats = await email_repo.get_email_stats_repo(organizer_id)
    
    return EmailStatsResponse(
        total_sent=stats['total_sent'],
        total_recipients=stats['total_recipients'],
        success_rate=stats['success_rate'],
        emails_this_month=stats['emails_this_month'],
        recipients_this_month=stats['recipients_this_month'],
        by_template=stats['by_template'],
        by_status=stats['by_status']
    )


async def delete_email_service(organizer_id: int, email_id: int) -> bool:
    """
    Delete an email (organizer can only delete their own emails).
    
    Args:
        organizer_id: ID of the organizer
        email_id: ID of the email to delete
    
    Returns:
        True if deleted successfully
    """
    logger.info(f"Deleting email {email_id} for organizer {organizer_id}")
    
    # Verify ownership
    email = await email_repo.get_organizer_email_by_id_repo(email_id)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    
    if email.organizer_id != organizer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this email"
        )
    
    # Delete recipients first (cascade should handle this, but being explicit)
    await recipient_repo.delete_recipients_by_email_id_repo(email_id)
    
    # Delete email
    deleted = await email_repo.delete_organizer_email_repo(email_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete email"
        )
    
    return True


# ==================== Admin Services ====================

async def get_all_emails_admin_service(
    limit: int = 50,
    offset: int = 0
) -> EmailHistoryResponse:
    """
    Get all emails across all organizers (admin only).
    
    Args:
        limit: Maximum number of results
        offset: Offset for pagination
    
    Returns:
        EmailHistoryResponse with all emails
    """
    logger.info("Admin fetching all emails")
    
    emails, total = await email_repo.get_all_organizer_emails_repo(
        limit=limit,
        offset=offset
    )
    
    return EmailHistoryResponse(
        emails=emails,
        total=total,
        limit=limit,
        offset=offset
    )


async def get_all_email_stats_admin_service() -> dict:
    """
    Get overall email statistics (admin only).
    
    Returns:
        Dictionary with overall statistics
    """
    logger.info("Admin fetching overall email stats")
    
    return await email_repo.get_all_email_stats_repo()


async def get_email_details_admin_service(email_id: int) -> EmailDetailWithRecipients:
    """
    Get email details (admin can view any email).
    
    Args:
        email_id: ID of the email
    
    Returns:
        EmailDetailWithRecipients with full details
    """
    logger.info(f"Admin fetching email details for email {email_id}")
    
    email = await email_repo.get_organizer_email_with_recipients_repo(email_id)
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    
    return email


# ==================== Helper Functions ====================


async def _get_mock_bookings(booking_ids: List[int]) -> List[dict]:
    """
    Mock function to get booking data.
    Replace this with actual database query.
    
    Args:
        booking_ids: List of booking IDs
    
    Returns:
        List of booking dictionaries
    """
    # TODO: Replace with actual database query
    # from app.db.repositories import booking_repo
    # return await booking_repo.get_bookings_by_ids(booking_ids)
    
    # Mock data
    return [
        {
            'id': bid,
            'customer_name': f'Customer {bid}',
            'customer_email': f'customer{bid}@example.com',
            'event_title': 'Sample Event',
            'ticket_type': 'VIP Pass',
            'quantity': 2,
            'venue': 'Central Park',
            'event_date': 'July 15, 2025 at 7:00 PM',
            'total_price': 5000,
            'organizer_name': 'Event Organizer'
        }
        for bid in booking_ids
    ]
