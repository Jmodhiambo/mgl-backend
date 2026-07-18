#!/usr/bin/env python3
# app/emails/templates/template_registry.py
"""Template registry — single source of truth for all email templates."""

from typing import Dict, List, Optional

from app.emails.templates.email_template_base import EmailTemplate
from app.core.logging_config import logger


class TemplateRegistry:
    """Holds all registered email templates, keyed by their ID."""

    def __init__(self):
        self._templates: Dict[str, EmailTemplate] = {}
        self._register_all()
        logger.info(
            f"Template registry initialised with {len(self._templates)} templates"
        )

    def _register_all(self) -> None:
        """Import and register every template class."""

        # ── User templates ─────────────────────────────────────────────────
        from app.emails.templates.user.templates import (
            VerificationEmailTemplate,
            PasswordResetEmailTemplate,
            AccountReactivationEmailTemplate,
            AccountDeactivatedEmailTemplate,
            PasswordChangedEmailTemplate,
            OrderConfirmedEmailTemplate,
            PaymentFailedEmailTemplate,
            ContactConfirmationEmailTemplate,
            CheckInConfirmedEmailTemplate,
        )

        # ── Organizer templates ────────────────────────────────────────────
        from app.emails.templates.organizer.templates import (
            BookingReminderTemplate,
            EventUpdateTemplate,
            ThankYouTemplate,
            EventCancellationTemplate,
            VenueChangeTemplate,
            TimeChangeTemplate,
            CoOrganizerInvitationTemplate,
            CoOrganizerInvitationNewUserTemplate,
            EventCreatedTemplate,
            EventApprovedTemplate,
            EventRejectedTemplate,
            EventPendingDeletionTemplate,
            EventDeletionConfirmedTemplate,
            TicketTypeSuspendedTemplate,
            TicketTypeUnsuspendedTemplate,
        )

        # ── Admin templates ────────────────────────────────────────────────
        from app.emails.templates.admin.templates import (
            ContactNotificationTemplate,
        )

        for template in [
            # User
            VerificationEmailTemplate(),
            PasswordResetEmailTemplate(),
            AccountReactivationEmailTemplate(),
            AccountDeactivatedEmailTemplate(),
            PasswordChangedEmailTemplate(),
            OrderConfirmedEmailTemplate(),
            PaymentFailedEmailTemplate(),
            ContactConfirmationEmailTemplate(),
            CheckInConfirmedEmailTemplate(),
            # Organizer
            BookingReminderTemplate(),
            EventUpdateTemplate(),
            ThankYouTemplate(),
            EventCancellationTemplate(),
            VenueChangeTemplate(),
            TimeChangeTemplate(),
            CoOrganizerInvitationTemplate(),
            CoOrganizerInvitationNewUserTemplate(),
            EventCreatedTemplate(),
            EventApprovedTemplate(),
            EventRejectedTemplate(),
            EventPendingDeletionTemplate(),
            EventDeletionConfirmedTemplate(),
            TicketTypeSuspendedTemplate(),
            TicketTypeUnsuspendedTemplate(),
            # Admin
            ContactNotificationTemplate(),
        ]:
            self._register(template)

    def _register(self, template: EmailTemplate) -> None:
        self._templates[template.id] = template
        logger.debug(f"Registered email template: {template.id}")

    def get(self, template_id: str) -> Optional[EmailTemplate]:
        return self._templates.get(template_id)

    def list(self, category: Optional[str] = None) -> Dict[str, dict]:
        templates = self._templates.values()
        if category:
            templates = (t for t in templates if t.category == category)
        return {t.id: t.get_metadata() for t in templates}

    def ids(self, category: Optional[str] = None) -> List[str]:
        if category:
            return [tid for tid, t in self._templates.items() if t.category == category]
        return list(self._templates.keys())