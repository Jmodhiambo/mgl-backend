#!/usr/bin/env python3
"""SendGrid email service for MGLTickets."""

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from typing import Dict, Optional

from app.emails.base import EmailService
from app.core.config import (
    SENDGRID_API_KEY,
    SENDGRID_NO_REPLY_EMAIL,
    SENDGRID_SUPPORT_EMAIL,
    SENDGRID_BILLING_EMAIL,
    SENDGRID_PRESS_EMAIL,
    SENDGRID_PARTNERSHIP_EMAIL,
    SENDGRID_FROM_NAME
)
from app.core.logging_config import logger


def get_sender_email(sender: str) -> str:
    """
    Get sender email based on sender type.
    
    Args:
        sender: Sender type ('no_reply', 'support', 'billing', 'press', 'partnership')
    
    Returns:
        Email address for the sender type
    """
    sender_map = {
        "no_reply": SENDGRID_NO_REPLY_EMAIL,
        "support": SENDGRID_SUPPORT_EMAIL,
        "billing": SENDGRID_BILLING_EMAIL,
        "press": SENDGRID_PRESS_EMAIL,
        "partnership": SENDGRID_PARTNERSHIP_EMAIL
    }
    return sender_map.get(sender, SENDGRID_SUPPORT_EMAIL)


class SendGridEmailService(EmailService):
    """SendGrid email service implementation."""
    
    def __init__(self) -> None:
        """Initialize SendGrid client."""
        self.client = SendGridAPIClient(api_key=SENDGRID_API_KEY)
        logger.info("SendGrid email service initialized")

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        template_data: Optional[Dict] = None
    ) -> None:
        """
        Send email using SendGrid.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            template_data: Additional template data (contains 'from_email' key)
        
        Raises:
            Exception: If email sending fails
        """
        # Determine sender
        from_email_type = 'no_reply'
        if template_data and 'from_email' in template_data:
            from_email_type = template_data['from_email']
        
        from_email = get_sender_email(from_email_type)
        
        # If SendGrid is not configured, just log
        if not self.client:
            logger.info(f"[SENDGRID NOT CONFIGURED] Would send email:")
            logger.info(f"  From: {from_email} ({SENDGRID_FROM_NAME})")
            logger.info(f"  To: {to_email}")
            logger.info(f"  Subject: {subject}")
            logger.info(f"  Content length: {len(html_content)} characters")
            return
        
        try:
            # Create email message
            message = Mail(
                from_email=(from_email, SENDGRID_FROM_NAME),
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            # Send email
            response = self.client.send(message)
            
            # Check response
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email} (Status: {response.status_code})")
            else:
                logger.error(f"SendGrid returned status {response.status_code}: {response.body}")
                raise Exception(f"SendGrid error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            raise