#!/usr/bin/env python3
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
            description="Notification sent when an event is cancelled",
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
            description="Notification sent when the event venue is changed",
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
            description="Notification sent when the event date or time is changed",
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

    def __init__(self):
        super().__init__(
            id="organizer.co_organizer_invitation",
            name="Co-Organizer Invitation",
            category="organizer",
            description="Invitation sent to potential co-organisers",
            required_variables=[
                "recipient_name", "inviter_name", "event_title",
                "event_id", "activation_url",
            ],
            template_file="organizer/co_organizer_invitation.html",
        )

    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"You've Been Invited to Co-Organise: {variables['event_title']}"