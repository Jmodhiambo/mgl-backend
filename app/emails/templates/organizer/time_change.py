#!/usr/bin/env python3
"""Time change email template for organizers."""

from app.emails.templates.email_template_base import EmailTemplate
from typing import Dict
from datetime import datetime


class TimeChangeTemplate(EmailTemplate):
    """Email template for event date/time change notifications."""
    
    def __init__(self):
        super().__init__(
            id='organizer.time_change',
            name='Time Change',
            category='organizer',
            description='Notification sent when event date or time is changed',
            required_variables=[
                'customer_name', 'event_title', 'ticket_type', 'quantity',
                'booking_id', 'old_date_time', 'new_date_time', 'venue',
                'organizer_name'
            ]
        )
    
    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"Time Change: {variables['event_title']}"
    
    def get_body(self, variables: Dict[str, str]) -> str:
        """Get email body with variables replaced."""
        current_year: int = datetime.now().year

        template = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0;">
    <title>Time Change</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f9fafb;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" style="width: 600px; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center; background: linear-gradient(135deg, #ec4899 0%, #db2777 100%); border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">🗓️ Date/Time Change</h1>
                            <p style="margin: 10px 0 0; color: #fce7f3; font-size: 14px;">Important Schedule Update</p>
                        </td>
                    </tr>
                    
                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px;">
                            <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px;">
                                Dear <strong>{customer_name}</strong>,
                            </p>
                            
                            <p style="margin: 0 0 30px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                Important notice: The date/time for <strong>{event_title}</strong> has been changed.
                            </p>
                            
                            <!-- Time Change Notice -->
                            <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 25px; border-radius: 4px; margin: 30px 0;">
                                <h3 style="margin: 0 0 15px; color: #92400e; font-size: 18px;">🗓️ New Date & Time</h3>
                                <table style="width: 100%; border-collapse: collapse;">
                                    <tr>
                                        <td style="padding: 8px 0; color: #78350f; font-size: 14px;">Previous:</td>
                                        <td style="padding: 8px 0; color: #78350f; font-size: 14px; text-decoration: line-through;">{old_date_time}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 8px 0; color: #92400e; font-size: 15px; font-weight: 600;">New:</td>
                                        <td style="padding: 8px 0; color: #92400e; font-size: 15px; font-weight: 700;">{new_date_time}</td>
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
                                        <td style="padding: 8px 0; color: #6b7280; font-size: 14px;">📍 Venue:</td>
                                        <td style="padding: 8px 0; color: #1f2937; font-size: 14px; font-weight: 600;">{venue} (UNCHANGED)</td>
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
                                Your booking is still valid for the new date and time.
                            </p>
                            
                            <!-- Refund Notice -->
                            <div style="background-color: #dbeafe; border-left: 4px solid #3b82f6; padding: 15px; border-radius: 4px; margin: 20px 0;">
                                <p style="margin: 0; color: #1e40af; font-size: 14px; line-height: 1.6;">
                                    <strong>💡 Note:</strong> If you cannot attend at the new time and would like to request a refund, please contact us within 48 hours.
                                </p>
                            </div>
                            
                            <p style="margin: 30px 0 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                We apologize for any inconvenience and hope to see you there!
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

        return template.format(
            year=current_year,
            **variables
        )