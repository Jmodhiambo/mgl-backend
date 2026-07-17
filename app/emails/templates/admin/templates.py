#!/usr/bin/env python3
# app/emails/templates/admin/templates.py
"""All admin email templates for MGLTickets."""

from typing import Dict
from app.emails.templates.email_template_base import EmailTemplate


class ContactNotificationTemplate(EmailTemplate):

    def __init__(self):
        super().__init__(
            id="admin.contact_notification",
            name="Contact Form Notification",
            category="admin",
            description="Internal alert sent to support when a contact message is submitted",
            required_variables=[
                "reference_id", "sender_name", "sender_email",
                "category", "subject", "message", "source",
                "priority", "admin_url",
            ],
            template_file="admin/contact_notification.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        priority_tag = "[URGENT] " if variables.get("priority") == "high" else ""
        return f"{priority_tag}New Contact Message – {variables['reference_id']}: {variables['subject']}"