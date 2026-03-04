#!/usr/bin/env python3
"""Booking reminder email template for organizers."""

from app.emails.templates.email_template_base import EmailTemplate
from typing import Dict
from datetime import datetime


class BookingReminderTemplate(EmailTemplate):
    """Email template for event reminders sent by organizers."""
    
    def __init__(self):
        super().__init__(
            id='organizer.reminder',
            name='Event Reminder',
            category='organizer',
            description='Reminder email sent to attendees before the event',
            required_variables=[
                'customer_name', 'event_title', 'ticket_type', 'quantity',
                'booking_id', 'venue', 'event_date', 'organizer_name'
            ]
        )
    
    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"Reminder: {variables['event_title']} is Coming Up!"
    
    def get_body(self, variables: Dict[str, str]) -> str:
        """Get email body with variables replaced."""
        current_year: int = datetime.now().year

        template = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f9fafb;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" style="width: 600px; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center; background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">Event Reminder</h1>
                            <p style="margin: 10px 0 0; color: #dbeafe; font-size: 14px;">Your event is coming up soon!</p>
                        </td>
                    </tr>
                    
                    <tr>
                        <td style="padding: 40px;">
                            <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px;">
                                Dear <strong>{customer_name}</strong>,
                            </p>
                            
                            <p style="margin: 0 0 30px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                This is a friendly reminder that <strong>{event_title}</strong> is coming up soon!
                            </p>
                            
                            <div style="background-color: #eff6ff; border-left: 4px solid #2563eb; padding: 25px; border-radius: 4px; margin: 30px 0;">
                                <h3 style="margin: 0 0 15px; color: #1e40af; font-size: 18px;">Event Details</h3>
                                <table style="width: 100%; border-collapse: collapse;">
                                    <tr>
                                        <td style="padding: 8px 0; color: #6b7280; font-size: 14px;">📅 Event:</td>
                                        <td style="padding: 8px 0; color: #1f2937; font-size: 14px; font-weight: 600;">{event_title}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; color: #6b7280; font-size: 14px;">📍 Venue:</td>
                                        <td style="padding: 8px 0; color: #1f2937; font-size: 14px; font-weight: 600;">{venue}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; color: #6b7280; font-size: 14px;">🗓️ Date & Time:</td>
                                        <td style="padding: 8px 0; color: #1f2937; font-size: 14px; font-weight: 600;">{event_date}</td>
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
                            
                            <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; border-radius: 4px; margin: 20px 0;">
                                <h4 style="margin: 0 0 10px; color: #92400e; font-size: 15px;">Important Information</h4>
                                <ul style="margin: 0; padding-left: 20px; color: #78350f; font-size: 14px; line-height: 1.8;">
                                    <li>Please arrive 30 minutes before the event starts</li>
                                    <li>Bring a valid ID for verification</li>
                                    <li>Your booking confirmation will be checked at the entrance</li>
                                </ul>
                            </div>
                            
                            <p style="margin: 30px 0 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                We look forward to seeing you at the event!
                            </p>
                            
                            <p style="margin: 20px 0 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                If you have any questions, please don't hesitate to contact us.
                            </p>
                            
                            <p style="margin: 30px 0 0; color: #6b7280; font-size: 14px;">
                                Best regards,<br>
                                <strong>{organizer_name}</strong>
                            </p>
                        </td>
                    </tr>
                    
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

        return template.format(
            year=current_year,
            **variables
        )