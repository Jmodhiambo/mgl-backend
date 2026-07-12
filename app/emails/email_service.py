#!/usr/bin/env python3
"""Concrete email service implementation for MGLTickets (currently Resend)."""

import resend
from typing import Dict

from app.emails.base import BaseEmailService
from app.core.config import (
    EMAIL_API_KEY,
    EMAIL_FROM_NO_REPLY,
    EMAIL_FROM_SUPPORT,
    EMAIL_FROM_BILLING,
    EMAIL_FROM_PRESS,
    EMAIL_FROM_PARTNERSHIP,
    EMAIL_FROM_NAME,
)
from app.core.logging_config import logger


# Maps sender identifiers to configured email addresses
_SENDER_MAP: Dict[str, str] = {
    "no_reply": EMAIL_FROM_NO_REPLY,
    "support": EMAIL_FROM_SUPPORT,
    "billing": EMAIL_FROM_BILLING,
    "press": EMAIL_FROM_PRESS,
    "partnership": EMAIL_FROM_PARTNERSHIP,
}


def _resolve_sender(sender: str) -> str:
    """
    Resolve a sender identifier to a formatted 'Name <email>' string.

    Falls back to support address for unknown identifiers.
    """
    address = _SENDER_MAP.get(sender, EMAIL_FROM_SUPPORT)
    return f"{EMAIL_FROM_NAME} <{address}>"


class EmailService(BaseEmailService):
    """
    Email service powered by Resend.

    To switch providers, replace the body of send_email with the new
    provider's SDK call — the interface and all call sites stay the same.
    """

    def __init__(self) -> None:
        # SecretStr must be unwrapped here — passing the object directly
        # would send its string representation, not the actual key value.
        resend.api_key = EMAIL_API_KEY.get_secret_value()
        logger.info("Email service initialised (Resend)")

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: str = "no_reply",
    ) -> None:
        """
        Send an email via Resend.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_content: Rendered HTML body
            from_email: Sender identifier ('no_reply', 'support', 'billing',
                        'press', 'partnership')

        Raises:
            Exception: If the Resend API returns an error
        """
        from_address = _resolve_sender(from_email)

        try:
            params: resend.Emails.SendParams = {
                "from": from_address,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            }
            response = resend.Emails.send(params)
            logger.info(
                f"Email sent to {to_email} "
                f"(id={response.get('id', 'unknown')})"
            )
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            raise