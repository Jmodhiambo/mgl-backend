#!/usr/bin/env python3
# app/emails/templates/user/templates.py
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
            description="Sent when a deactivated user account is reactivated",
            required_variables=["name", "login_url"],
            template_file="user/account_reactivation.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return "Your MGLTickets Account Has Been Reactivated"


class AccountDeactivatedEmailTemplate(EmailTemplate):

    def __init__(self):
        super().__init__(
            id="user.account_deactivated",
            name="Account Deactivated",
            category="user",
            description="Sent when a user account is deactivated",
            required_variables=["name"],
            template_file="user/account_deactivated.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return "Your MGLTickets Account Has Been Deactivated"


class PasswordChangedEmailTemplate(EmailTemplate):

    def __init__(self):
        super().__init__(
            id="user.password_changed",
            name="Password Changed",
            category="user",
            description="Security notification sent after a successful password change",
            required_variables=["name", "email", "changed_at", "login_url"],
            template_file="user/password_changed.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return "Your MGLTickets Password Has Been Changed"


class OrderConfirmedEmailTemplate(EmailTemplate):

    def __init__(self):
        super().__init__(
            id="user.order_confirmed",
            name="Order Confirmed",
            category="user",
            description="E-ticket delivery email sent after a successful order (paid or free)",
            required_variables=[
                "name", "order_id", "event_title", "venue",
                "event_date", "total_price", "payment_method",
                "tickets_url",
            ],
            template_file="user/order_confirmed.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"Order Confirmed – Your Tickets for {variables['event_title']}"


class PaymentFailedEmailTemplate(EmailTemplate):

    def __init__(self):
        super().__init__(
            id="user.payment_failed",
            name="Payment Failed",
            category="user",
            description="Sent when an M-Pesa payment fails",
            required_variables=[
                "name", "order_id", "event_title",
                "amount", "failure_reason", "retry_url",
            ],
            template_file="user/payment_failed.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"Payment Failed – {variables['event_title']}"


class ContactConfirmationEmailTemplate(EmailTemplate):

    def __init__(self):
        super().__init__(
            id="user.contact_confirmation",
            name="Contact Form Confirmation",
            category="user",
            description="Confirmation sent to a user after they submit a contact message",
            required_variables=[
                "name", "email", "reference_id", "category", "subject",
            ],
            template_file="user/contact_confirmation.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"We Received Your Message – Ref: {variables['reference_id']}"
    
class CheckInConfirmedEmailTemplate(EmailTemplate):
 
    def __init__(self):
        super().__init__(
            id="user.check_in_confirmed",
            name="Check-In Confirmed",
            category="user",
            description="Sent to the ticket holder immediately after a successful event check-in",
            required_variables=[
                "name", "event_title", "ticket_type_name", "code", "checked_in_at",
            ],
            template_file="user/check_in_confirmed.html",
        )
 
    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"You're Checked In – {variables['event_title']}"