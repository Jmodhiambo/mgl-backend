#!/usr/bin/env python3
# app/emails/email_manager.py
"""Centralised email manager for MGLTickets."""

import os
from datetime import datetime
from typing import Dict, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from premailer import transform

from app.emails.base import BaseEmailService
from app.emails.templates.template_registry import TemplateRegistry
from app.core.config import EMAIL_DEV_MODE
from app.core.logging_config import logger


# Absolute path to the templates directory so Jinja2 can locate .html files
# regardless of where the process is launched from.
_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


class EmailManager:
    """
    Renders Jinja2 email templates, inlines CSS via premailer, and dispatches
    through the configured EmailService.

    In dev mode (EMAIL_DEV_MODE=true) emails are never sent — the rendered
    HTML is logged instead, so you can inspect output without Resend credentials
    or burning send quota.
    """

    def __init__(self, service: Optional[BaseEmailService] = None):
        if service is None:
            from app.emails.email_service import EmailService
            service = EmailService()

        self._service = service
        self._registry = TemplateRegistry()
        self._jinja = Environment(
            loader=FileSystemLoader(_TEMPLATES_DIR),
            autoescape=select_autoescape(["html"]),
        )
        logger.info("EmailManager initialised")

    async def send_from_template(
        self,
        template_id: str,
        to_email: str,
        variables: Dict,
        from_email: str = "no_reply",
    ) -> bool:
        """
        Render a registered template and send the email.

        Args:
            template_id: Registered template ID (e.g. 'user.verification')
            to_email: Recipient address
            variables: Template variables — must satisfy the template's
                       required_variables list
            from_email: Sender identifier ('no_reply', 'support', 'billing', etc.)

        Returns:
            True on success, False on failure (non-raising; logs the error)

        Raises:
            ValueError: If the template is unknown or required variables are missing
        """
        # ── 1. Look up template ──────────────────────────────────────────
        template = self._registry.get(template_id)
        if not template:
            raise ValueError(f"Unknown email template: '{template_id}'")

        # ── 2. Validate variables ────────────────────────────────────────
        is_valid, missing = template.validate_variables(variables)
        if not is_valid:
            raise ValueError(
                f"Template '{template_id}' is missing required variables: "
                f"{', '.join(missing)}"
            )

        # ── 3. Render subject ────────────────────────────────────────────
        subject = template.get_subject(variables)

        # ── 4. Render HTML via Jinja2 ────────────────────────────────────
        jinja_template = self._jinja.get_template(template.template_file)
        raw_html = jinja_template.render(year=datetime.now().year, **variables)

        # ── 5. Inline CSS with premailer ─────────────────────────────────
        # premailer converts <style> blocks to inline style attributes so
        # email clients that strip <head> styles (Outlook, Gmail web) still
        # render the design correctly.
        html = transform(raw_html)

        # ── 6. Send (or log in dev mode) ─────────────────────────────────
        if EMAIL_DEV_MODE:
            logger.info(
                f"[DEV MODE] Would send '{template_id}' to {to_email}\n"
                f"Subject: {subject}\n"
                f"HTML length: {len(html)} chars"
            )
            return True

        try:
            await self._service.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html,
                from_email=from_email,
            )
            logger.info(f"Email '{template_id}' sent to {to_email}")
            return True
        except Exception as e:
            logger.error(
                f"Failed to send email '{template_id}' to {to_email}: {e}"
            )
            return False

    async def send_custom(
        self,
        to_email: str,
        subject: str,
        body: str,
        organizer_name: str,
        from_email: str = "no_reply",
    ) -> bool:
        """
        Send a freeform custom email (no registered template).

        Used by organizers to send ad-hoc messages to attendees.

        Args:
            to_email: Recipient address
            subject: Email subject
            body: Plain-text body — rendered inside a simple HTML wrapper
            organizer_name: Displayed as the sender name in the email body
            from_email: Sender identifier
        """
        jinja_template = self._jinja.get_template("organizer/custom_email.html")
        raw_html = jinja_template.render(
            year=datetime.now().year,
            organizer_name=organizer_name,
            body=body,
        )
        html = transform(raw_html)

        if EMAIL_DEV_MODE:
            logger.info(
                f"[DEV MODE] Would send custom email to {to_email}\n"
                f"Subject: {subject}\n"
                f"HTML length: {len(html)} chars"
            )
            return True

        try:
            await self._service.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html,
                from_email=from_email,
            )
            logger.info(f"Custom email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send custom email to {to_email}: {e}")
            return False

    # ── Introspection helpers ─────────────────────────────────────────── #

    def list_templates(self, category: Optional[str] = None) -> Dict:
        return self._registry.list(category)

    def get_template_info(self, template_id: str) -> Optional[Dict]:
        template = self._registry.get(template_id)
        return template.get_metadata() if template else None


# Module-level singleton — import this everywhere
email_manager = EmailManager()