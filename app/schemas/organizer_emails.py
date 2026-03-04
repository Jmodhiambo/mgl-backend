#!/usr/bin/env python3
"""Schemas for OrganizerEmails model in MGLTickets."""

from datetime import datetime
from pydantic import EmailStr, Field, field_validator
from typing import Optional, List, Literal
from app.schemas.base import BaseModelEAT


# ==================== OrganizerEmails Schemas ====================

class OrganizerEmailCreate(BaseModelEAT):
    """Schema for creating a new organizer email."""
    event_id: Optional[int] = None
    booking_ids: List[int] = Field(..., min_length=1, description="List of booking IDs to send email to")
    subject: str = Field(..., min_length=3, max_length=500, description="Email subject")
    message: str = Field(..., min_length=10, description="Email message body")
    template_used: Literal[
        'reminder', 
        'update', 
        'thank_you', 
        'cancellation', 
        'venue_change', 
        'time_change', 
        'custom'
    ] = Field(
        default='custom',
        description="Email template to use"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "event_id": 1,
                "booking_ids": [1, 2, 3],
                "subject": "Reminder: Event Tomorrow!",
                "message": "Don't forget about the event tomorrow at 7 PM!",
                "template_used": "reminder"
            }
        }


class OrganizerEmailOut(BaseModelEAT):
    """Schema for outputting organizer email data."""
    id: int
    organizer_id: int
    event_id: Optional[int] = None
    recipient_type: str = Field(..., description="Type: single, bulk, or all")
    recipient_count: int = Field(..., description="Number of recipients")
    subject: str
    message: str
    template_used: str = Field(..., description="Template used: reminder, update, thank_you, etc.")
    status: str = Field(..., description="Status: pending, sent, failed, partially_sent, cancelled")
    sent_at: Optional[datetime] = None
    failed_count: int = Field(default=0, description="Number of failed deliveries")
    success_count: int = Field(default=0, description="Number of successful deliveries")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrganizerEmailDetail(OrganizerEmailOut):
    """Schema for detailed organizer email with recipients."""
    recipient_emails: Optional[List[str]] = None
    booking_ids: Optional[List[int]] = None

    class Config:
        from_attributes = True


class SendEmailRequest(BaseModelEAT):
    """Schema for sending email request."""
    event_id: Optional[int] = Field(None, description="Event ID (optional)")
    booking_ids: List[int] = Field(..., min_length=1, description="List of booking IDs to send email to")
    subject: str = Field(..., min_length=3, max_length=500, description="Email subject")
    message: str = Field(..., min_length=10, description="Email message body")
    template_used: Literal[
        'reminder', 
        'update', 
        'thank_you', 
        'cancellation', 
        'venue_change', 
        'time_change', 
        'custom'
    ] = Field(
        default='custom',
        description="Email template: reminder, update, thank_you, cancellation, venue_change, time_change, or custom"
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "event_id": 1,
                "booking_ids": [101, 102, 103],
                "subject": "Important Event Update",
                "message": "We have an important update about your event...",
                "template_used": "update"
            }
        }


class SendEmailResponse(BaseModelEAT):
    """Schema for send email response."""
    email_id: int = Field(..., description="ID of the created email record")
    recipient_count: int = Field(..., description="Total number of recipients")
    status: str = Field(..., description="Overall status: sent, failed, or partially_sent")
    success_count: int = Field(..., description="Number of successfully sent emails")
    failed_count: int = Field(..., description="Number of failed emails")
    message: str = Field(..., description="Human-readable status message")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "email_id": 123,
                "recipient_count": 50,
                "status": "sent",
                "success_count": 50,
                "failed_count": 0,
                "message": "Email sent to 50 recipient(s)"
            }
        }


class EmailHistoryQuery(BaseModelEAT):
    """Schema for email history query parameters."""
    event_id: Optional[int] = None
    status: Optional[str] = None
    limit: int = 50
    offset: int = 0

    class Config:
        from_attributes = True


class EmailHistoryResponse(BaseModelEAT):
    """Schema for email history response."""
    emails: List[OrganizerEmailOut]
    total: int
    limit: int
    offset: int

    class Config:
        from_attributes = True


class EmailStatsResponse(BaseModelEAT):
    """Schema for email statistics response."""
    total_sent: int = Field(..., description="Total number of emails sent")
    total_recipients: int = Field(..., description="Total number of recipients")
    success_rate: float = Field(..., ge=0, le=100, description="Success rate percentage")
    emails_this_month: int = Field(..., description="Emails sent this month")
    recipients_this_month: int = Field(..., description="Recipients this month")
    by_template: dict = Field(..., description="Email count by template type")
    by_status: dict = Field(..., description="Email count by status")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "total_sent": 150,
                "total_recipients": 450,
                "success_rate": 98.5,
                "emails_this_month": 25,
                "recipients_this_month": 80,
                "by_template": {
                    "reminder": 60,
                    "update": 40,
                    "thank_you": 30,
                    "custom": 20
                },
                "by_status": {
                    "sent": 145,
                    "failed": 3,
                    "partially_sent": 2
                }
            }
        }


class TemplateInfoResponse(BaseModelEAT):
    """Schema for template information."""
    id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template display name")
    category: str = Field(..., description="Template category (user/organizer/admin)")
    description: str = Field(..., description="Template description")
    required_variables: List[str] = Field(..., description="Required variables for this template")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "organizer.reminder",
                "name": "Event Reminder",
                "category": "organizer",
                "description": "Reminder email sent to attendees before the event",
                "required_variables": [
                    "customer_name",
                    "event_title",
                    "ticket_type",
                    "quantity",
                    "booking_id",
                    "venue",
                    "event_date",
                    "organizer_name"
                ]
            }
        }


class TemplateListResponse(BaseModelEAT):
    """Schema for list of available templates."""
    templates: dict = Field(..., description="Dictionary of available templates")
    
    class Config:
        from_attributes = True


# ==================== OrganizerEmailRecipients Schemas ====================

class OrganizerEmailRecipientCreate(BaseModelEAT):
    """Schema for creating an email recipient."""
    email_id: int
    booking_id: int
    recipient_name: str
    recipient_email: EmailStr

    class Config:
        from_attributes = True


class OrganizerEmailRecipientOut(BaseModelEAT):
    """Schema for outputting email recipient data."""
    id: int
    email_id: int
    booking_id: int
    recipient_name: str
    recipient_email: str
    status: str = Field(..., description="Status: pending, sent, failed, or bounced")
    sent_at: Optional[datetime] = None
    opened_at: Optional[datetime] = Field(None, description="When email was opened (if tracking enabled)")
    clicked_at: Optional[datetime] = Field(None, description="When link was clicked (if tracking enabled)")
    error_message: Optional[str] = Field(None, description="Error message if sending failed")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrganizerEmailRecipientUpdate(BaseModelEAT):
    """Schema for updating email recipient status."""
    status: Optional[Literal['pending', 'sent', 'failed', 'bounced']] = None
    sent_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class EmailDetailWithRecipients(OrganizerEmailDetail):
    """Schema for email with full recipient details."""
    recipients: List[OrganizerEmailRecipientOut]

    class Config:
        from_attributes = True