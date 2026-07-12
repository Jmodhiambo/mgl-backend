#!/usr/bin/env python3
"""All user email templates for MGLTickets."""

from typing import Dict
from app.emails.templates.email_template_base import EmailTemplate


class VerificationEmailTemplate(EmailTemplate):

    def __init__(self):
        super().__init__(
            id="user.verification",
            name="Email Verification",
            category="user",
            description="Sent to new users to verify their email address",
            required_variables=["name", "verification_url"],
            template_file="user/verification_email.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return "Verify Your MGLTickets Account"


class PasswordResetEmailTemplate(EmailTemplate):

    def __init__(self):
        super().__init__(
            id="user.password_reset",
            name="Password Reset",
            category="user",
            description="Sent when a user requests a password reset",
            required_variables=["name", "reset_url"],
            template_file="user/password_reset.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return "Reset Your MGLTickets Password"


class AccountReactivationEmailTemplate(EmailTemplate):

    def __init__(self):
        super().__init__(
            id="user.account_reactivation",
            name="Account Reactivation",
            category="user",
            description="Sent when a user account is reactivated",
            required_variables=["name", "login_url"],
            template_file="user/account_reactivation.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return "Your MGLTickets Account Has Been Reactivated"