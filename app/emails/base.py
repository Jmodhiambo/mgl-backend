#!/usr/bin/env python3
"""Base email service ABC for MGLTickets."""

from abc import ABC, abstractmethod


class BaseEmailService(ABC):
    """
    Abstract base class for all email service implementations.

    To swap providers, create a new class that inherits from this,
    implement send_email, and pass it into EmailManager.
    """

    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: str = "no_reply",
    ) -> None:
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_content: Rendered HTML email body
            from_email: Sender identifier ('no_reply', 'support', 'billing',
                        'press', 'partnership')

        Raises:
            Exception: If sending fails
        """
        pass