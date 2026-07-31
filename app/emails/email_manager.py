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

    Two render/send paths exist:
      - send_from_template(): fixed, per-template HTML files. Used for
        user/admin account emails (verification, password reset, event
        approval, etc.) whose content is not caller-editable.
      - send_branded_message() / render_branded_message(): the generic
        organizer wrapper (organizer/branded_message.html). Subject and
        body are fully caller-supplied free text; only the header colour
        and subtitle come from a template's branding metadata. Every
        organizer bulk-send template (named or custom) goes through this
        path so that a preview call and the real send are byte-for-byte
        identical given the same inputs.

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

    # ------------------------------------------------------------------ #
    # Shared render / dispatch helpers                                    #
    # ------------------------------------------------------------------ #

    def _render(self, template_file: str, context: Dict) -> str:
        """
        Render a Jinja2 template file and inline its CSS via premailer.

        disable_validation=True: cssutils (which premailer uses to parse
        CSS) only validates against CSS 2.1, so it flags — and can drop —
        modern-but-valid declarations like linear-gradient() backgrounds,
        vendor prefixes, and word-break/overflow-wrap. Disabling
        validation stops it from rejecting those as "invalid".
        """
        jinja_template = self._jinja.get_template(template_file)
        raw_html = jinja_template.render(year=datetime.now().year, **context)
        return transform(raw_html, disable_validation=True)

    async def _dispatch(
        self,
        to_email: str,
        subject: str,
        html: str,
        from_email: str,
        log_label: str,
    ) -> bool:
        """Send (or log, in dev mode) a fully-rendered email."""
        if EMAIL_DEV_MODE:
            logger.info(
                f"[DEV MODE] Would send '{log_label}' to {to_email}\n"
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
            logger.info(f"Email '{log_label}' sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email '{log_label}' to {to_email}: {e}")
            return False

    # ------------------------------------------------------------------ #
    # Fixed templates (user/admin account emails, organizer system emails) #
    # ------------------------------------------------------------------ #

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

        # ── 4. Render HTML + inline CSS ──────────────────────────────────
        html = self._render(template.template_file, variables)

        # ── 5. Send (or log in dev mode) ─────────────────────────────────
        return await self._dispatch(to_email, subject, html, from_email, template_id)

    # ------------------------------------------------------------------ #
    # Branded free-text messages (organizer bulk sends)                   #
    # ------------------------------------------------------------------ #

    def render_branded_message(
        self,
        subject: str,
        body: str,
        header_class: str,
        header_subtitle: str,
    ) -> str:
        """
        Render the generic branded wrapper around free-text subject/body.

        This is the single render path shared by preview and send for every
        organizer bulk-email template. Given the same subject/body/branding
        inputs, this returns exactly the HTML send_branded_message() would
        dispatch — a preview is never a lookalike, it's the real output.
        """
        return self._render(
            "organizer/branded_message.html",
            {
                "subject": subject,
                "body": body,
                "header_class": header_class,
                "header_subtitle": header_subtitle,
            },
        )

    async def send_branded_message(
        self,
        to_email: str,
        subject: str,
        body: str,
        header_class: str,
        header_subtitle: str,
        from_email: str = "no_reply",
    ) -> bool:
        """Render and send a branded free-text organizer email."""
        html = self.render_branded_message(subject, body, header_class, header_subtitle)
        return await self._dispatch(to_email, subject, html, from_email, "organizer.branded_message")

    # ── Introspection helpers ─────────────────────────────────────────── #

    def list_templates(self, category: Optional[str] = None) -> Dict:
        return self._registry.list(category)

    def get_template_info(self, template_id: str) -> Optional[Dict]:
        template = self._registry.get(template_id)
        return template.get_metadata() if template else None


# Module-level singleton — import this everywhere
email_manager = EmailManager()