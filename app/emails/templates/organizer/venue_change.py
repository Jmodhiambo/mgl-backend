#!/usr/bin/env python3
"""Venue change email template for organizers."""

from app.emails.templates.email_template_base import EmailTemplate
from typing import Dict
from datetime import datetime


class VenueChangeTemplate(EmailTemplate):
    """Email template for venue change notifications."""
    
    def __init__(self):
        super().__init__(
            id='organizer.venue_change',
            name='Venue Change',
            category='organizer',
            description='Notification sent when event venue is changed',
            required_variables=[
                'customer_name', 'event_title', 'ticket_type', 'quantity',
                'booking_id', 'old_venue', 'new_venue',
                'event_date', 'organizer_name'
            ]
        )
    
    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"Venue Change: {variables['event_title']}"
    
    def get_body(self, variables: Dict[str, str]) -> str:
        current_year: int = datetime.now().year

        template = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Venue Change</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f9fafb;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" style="width: 600px; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center; background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">📍 Venue Change</h1>
                            <p style="margin: 10px 0 0; color: #ede9fe; font-size: 14px;">Important Update</p>
                        </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px;">
                            <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px;">
                                Dear <strong>{customer_name}</strong>,
                            </p>

                            <p style="margin: 0 0 30px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                Important notice: The venue for <strong>{event_title}</strong> has been changed.
                            </p>

                            <!-- Venue Change Notice -->
                            <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 25px; border-radius: 4px; margin: 30px 0;">
                                <h3 style="margin: 0 0 15px; color: #92400e; font-size: 18px;">📍 New Venue Information</h3>
                                <table style="width: 100%; border-collapse: collapse;">
                                    <tr>
                                        <td style="padding: 8px 0; color: #78350f; font-size: 14px;">Previous Venue:</td>
                                        <td style="padding: 8px 0; color: #78350f; font-size: 14px; text-decoration: line-through;">{old_venue}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; color: #92400e; font-size: 15px; font-weight: 600;">New Venue:</td>
                                        <td style="padding: 8px 0; color: #92400e; font-size: 15px; font-weight: 700;">{new_venue}</td>
                                    </tr>
                                </table>
                            </div>

                            <!-- Event Details -->
                            <div style="background-color: #eff6ff; border-left: 4px solid #2563eb; padding: 25px; border-radius: 4px; margin: 30px 0;">
                                <h3 style="margin: 0 0 15px; color: #1e40af; font-size: 18px;">Event Details</h3>
                                <table style="width: 100%; border-collapse: collapse;">
                                    <tr>
                                        <td style="padding: 8px 0; color: #6b7280; font-size: 14px;">📅 Event:</td>
                                        <td style="padding: 8px 0; color: #1f2937; font-size: 14px; font-weight: 600;">{event_title}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; color: #6b7280; font-size: 14px;">🗓️ Date & Time:</td>
                                        <td style="padding: 8px 0; color: #1f2937; font-size: 14px; font-weight: 600;">{event_date} (UNCHANGED)</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; color: #6b7280; font-size: 14px;">🎫 Ticket Type:</td>
                                        <td style="padding: 8px 0; color: #1f2937; font-size: 14px; font-weight: 600;">{ticket_type}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; color: #6b7280; font-size: 14px;">🔢 Quantity:</td>
                                        <td style="padding: 8px 0; color: #1f2937; font-size: 14px; font-weight: 600;">{quantity} ticket(s)</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; color: #6b7280; font-size: 14px;">🆔 Booking ID:</td>
                                        <td style="padding: 8px 0; color: #1f2937; font-size: 14px; font-weight: 600;">#{booking_id}</td>
                                    </tr>
                                </table>
                            </div>

                            <p style="margin: 30px 0 20px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                All other event details remain the same. Your booking is still valid for the new venue.
                            </p>

                            <!-- Refund Notice -->
                            <div style="background-color: #dbeafe; border-left: 4px solid #3b82f6; padding: 15px; border-radius: 4px; margin: 20px 0;">
                                <p style="margin: 0; color: #1e40af; font-size: 14px; line-height: 1.6;">
                                    <strong>💡 Note:</strong> If this venue change is inconvenient for you and you'd like to request a refund, please contact us within 48 hours.
                                </p>
                            </div>

                            <p style="margin: 30px 0 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                We apologise for any inconvenience and look forward to seeing you!
                            </p>

                            <p style="margin: 30px 0 0; color: #6b7280; font-size: 14px;">
                                Best regards,<br>
                                <strong>{organizer_name}</strong>
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; background-color: #f9fafb; border-radius: 0 0 8px 8px;">
                            <p style="margin: 0; color: #9ca3af; font-size: 12px; text-align: center;">
                                This email was sent via MGLTickets<br>
                                © {year} MGLTickets. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
'''

        return template.format(year=current_year, **variables)