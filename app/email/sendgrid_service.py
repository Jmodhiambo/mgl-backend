#!/usr/bin/env python3
"""SendGrid email service for MGLTickets."""

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from typing import Dict, Optional

from app.email.base import EmailService
from app.core.config import (
    SENDGRID_API_KEY,
    SENDGRID_NO_REPLY_EMAIL,
    SENDGRID_SUPPORT_EMAIL,
    SENDGRID_BILLING_EMAIL,
    SENDGRID_PRESS_EMAIL,
    SENDGRID_PARTNERSHIP_EMAIL,
    SENDGRID_FROM_NAME
)

def email_sender(sender):
    if sender == "no_reply":
        return SENDGRID_NO_REPLY_EMAIL
    elif sender == "support":
        return SENDGRID_SUPPORT_EMAIL
    elif sender == "billing":
        return SENDGRID_BILLING_EMAIL
    elif sender == "press":
        return SENDGRID_PRESS_EMAIL
    elif sender == "partnership":
        return SENDGRID_PARTNERSHIP_EMAIL
    else:
        return SENDGRID_SUPPORT_EMAIL

class SendGridEmailService(EmailService):
    def __init__(self) -> None:
        self.client = SendGridAPIClient(api_key=SENDGRID_API_KEY)

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        template_data: Optional[Dict] = None
    ) -> None:
        message = Mail(
            from_email=email_sender(template_data.get("from_email")),
            from_name=SENDGRID_FROM_NAME,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )

        self.client.send(message)
