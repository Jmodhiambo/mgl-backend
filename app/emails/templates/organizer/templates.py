#!/usr/bin/env python3
# app/emails/templates/organizer/templates.py
"""All organizer email templates for MGLTickets."""

from typing import Dict
from app.emails.templates.email_template_base import EmailTemplate


class BookingReminderTemplate(EmailTemplate):

    def __init__(self):
        super().__init__(
            id="organizer.reminder",
            name="Event Reminder",
            category="organizer",
            description="Reminder sent to attendees before the event",
            required_variables=[
                "customer_name", "event_title", "ticket_type",
                "quantity", "order_id", "venue", "event_date", "organizer_name",
            ],
            template_file="organizer/booking_reminder.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"Reminder: {variables['event_title']} is Coming Up!"


class EventUpdateTemplate(EmailTemplate):

    def __init__(self):
        super().__init__(
            id="organizer.update",
            name="Event Update",
            category="organizer",
            description="Important update notification sent to attendees",
            required_variables=[
                "customer_name", "event_title", "ticket_type",
                "quantity", "order_id", "update_message", "organizer_name",
            ],
            template_file="organizer/event_update.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"Important Update: {variables['event_title']}"


class ThankYouTemplate(EmailTemplate):

    def __init__(self):
        super().__init__(
            id="organizer.thank_you",
            name="Thank You",
            category="organizer",
            description="Post-event thank you message sent to attendees",
            required_variables=["customer_name", "event_title", "organizer_name"],
            template_file="organizer/thank_you.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"Thank You for Attending {variables['event_title']}!"


class EventCancellationTemplate(EmailTemplate):

    def __init__(self):
        super().__init__(
            id="organizer.cancellation",
            name="Event Cancellation",
            category="organizer",
            description="Notification sent to attendees when an event is cancelled",
            required_variables=[
                "customer_name", "event_title", "ticket_type",
                "quantity", "order_id", "total_price",
                "cancellation_reason", "organizer_name",
            ],
            template_file="organizer/event_cancellation.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"Important: {variables['event_title']} Has Been Cancelled"


class VenueChangeTemplate(EmailTemplate):

    def __init__(self):
        super().__init__(
            id="organizer.venue_change",
            name="Venue Change",
            category="organizer",
            description="Notification sent to attendees when the event venue is changed",
            required_variables=[
                "customer_name", "event_title", "ticket_type",
                "quantity", "order_id", "old_venue", "new_venue",
                "event_date", "organizer_name",
            ],
            template_file="organizer/venue_change.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"Venue Change: {variables['event_title']}"


class TimeChangeTemplate(EmailTemplate):

    def __init__(self):
        super().__init__(
            id="organizer.time_change",
            name="Time Change",
            category="organizer",
            description="Notification sent to attendees when the event date or time changes",
            required_variables=[
                "customer_name", "event_title", "ticket_type",
                "quantity", "order_id", "old_date_time", "new_date_time",
                "venue", "organizer_name",
            ],
            template_file="organizer/time_change.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"Time Change: {variables['event_title']}"


class CoOrganizerInvitationTemplate(EmailTemplate):
    """Invitation to an existing MGLTickets user."""

    def __init__(self):
        super().__init__(
            id="organizer.co_organizer_invitation",
            name="Co-Organizer Invitation (Existing User)",
            category="organizer",
            description="Invitation sent to an existing MGLTickets user to co-organise an event",
            required_variables=[
                "recipient_name", "inviter_name", "event_title",
                "venue", "event_date", "accept_url",
            ],
            template_file="organizer/co_organizer_invitation_existing.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"You've Been Invited to Co-Organise: {variables['event_title']}"


class CoOrganizerInvitationNewUserTemplate(EmailTemplate):
    """Invitation to someone who does not yet have an MGLTickets account."""

    def __init__(self):
        super().__init__(
            id="organizer.co_organizer_invitation_new_user",
            name="Co-Organizer Invitation (New User)",
            category="organizer",
            description="Invitation sent to a non-registered email to join and co-organise an event",
            required_variables=[
                "recipient_name", "inviter_name", "event_title",
                "venue", "event_date", "signup_url",
            ],
            template_file="organizer/co_organizer_invitation_new_user.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"You're Invited to Co-Organise: {variables['event_title']} on MGLTickets"


class EventCreatedTemplate(EmailTemplate):

    def __init__(self):
        super().__init__(
            id="organizer.event_created",
            name="Event Submitted for Review",
            category="organizer",
            description="Confirmation sent to the organizer when a new event is submitted",
            required_variables=[
                "organizer_name", "event_title", "venue",
                "event_date", "dashboard_url",
            ],
            template_file="organizer/event_created.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"Event Submitted: {variables['event_title']} is Under Review"


class EventApprovedTemplate(EmailTemplate):

    def __init__(self):
        super().__init__(
            id="organizer.event_approved",
            name="Event Approved",
            category="organizer",
            description="Sent to the organizer when their event is approved by an admin",
            required_variables=[
                "organizer_name", "event_title", "venue",
                "event_date", "admin_name", "event_url",
            ],
            template_file="organizer/event_approved.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"🎉 Your Event Has Been Approved: {variables['event_title']}"


class EventRejectedTemplate(EmailTemplate):

    def __init__(self):
        super().__init__(
            id="organizer.event_rejected",
            name="Event Rejected",
            category="organizer",
            description="Sent to the organizer when their event submission is rejected",
            required_variables=[
                "organizer_name", "event_title", "admin_name", "dashboard_url",
            ],
            template_file="organizer/event_rejected.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"Event Submission Not Approved: {variables['event_title']}"


class EventPendingDeletionTemplate(EmailTemplate):

    def __init__(self):
        super().__init__(
            id="organizer.event_pending_deletion",
            name="Event Pending Deletion",
            category="organizer",
            description="Sent to the organizer when their event is marked pending_deletion due to unresolved bookings",
            required_variables=[
                "organizer_name", "event_title", "unresolved_count",
            ],
            template_file="organizer/event_pending_deletion.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"Action Required: {variables['event_title']} is Pending Deletion"


class EventDeletionConfirmedTemplate(EmailTemplate):

    def __init__(self):
        super().__init__(
            id="organizer.event_deletion_confirmed",
            name="Event Deletion Confirmed",
            category="organizer",
            description="Sent to the organizer when their event is permanently deleted after all refunds",
            required_variables=[
                "organizer_name", "event_title", "deleted_at",
                "refund_count", "dashboard_url",
            ],
            template_file="organizer/event_deletion_confirmed.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"Event Permanently Deleted: {variables['event_title']}"


class TicketTypeSuspendedTemplate(EmailTemplate):

    def __init__(self):
        super().__init__(
            id="organizer.ticket_type_suspended",
            name="Ticket Type Suspended",
            category="organizer",
            description="Sent to the organizer when an admin suspends one of their ticket types",
            required_variables=[
                "organizer_name", "event_title", "ticket_type_name",
                "admin_name", "suspension_reason",
            ],
            template_file="organizer/ticket_type_suspended.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"Ticket Type Suspended: {variables['ticket_type_name']} – {variables['event_title']}"


class TicketTypeUnsuspendedTemplate(EmailTemplate):

    def __init__(self):
        super().__init__(
            id="organizer.ticket_type_unsuspended",
            name="Ticket Type Suspension Lifted",
            category="organizer",
            description="Sent to the organizer when an admin lifts a ticket type suspension",
            required_variables=[
                "organizer_name", "event_title", "ticket_type_name", "dashboard_url",
            ],
            template_file="organizer/ticket_type_unsuspended.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"Suspension Lifted: {variables['ticket_type_name']} – {variables['event_title']}"