#!/usr/bin/env python3
"""Event update email template for organizers."""

from app.emails.templates.email_template_base import EmailTemplate
from typing import Dict
from datetime import datetime


class EventUpdateTemplate(EmailTemplate):
    """Email template for event updates sent by organizers."""
    
    def __init__(self):
        super().__init__(
            id='organizer.update',
            name='Event Update',
            category='organizer',
            description='Important update notification sent to attendees',
            required_variables=[
                'customer_name', 'event_title', 'ticket_type', 'quantity',
                'booking_id', 'update_message', 'organizer_name'
            ]
        )
    
    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"Important Update: {variables['event_title']}"
    
    def get_body(self, variables: Dict[str, str]) -> str:
        """Get email body with variables replaced."""   
        current_year: int = datetime.now().year

        template = '''
<!DOCTYPE html>
<html>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f9fafb;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" style="width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <tr>
                        <td style="padding: 40px; text-align: center; background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px;">📢 Important Update</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px;">
                            <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px;">Dear <strong>{customer_name}</strong>,</p>
                            <p style="margin: 0 0 30px; color: #4b5563; font-size: 16px;">We have an important update regarding <strong>{event_title}</strong>.</p>
                            
                            <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 25px; border-radius: 4px; margin: 30px 0;">
                                <h3 style="margin: 0 0 15px; color: #92400e; font-size: 18px;">Update Details</h3>
                                <p style="margin: 0; color: #78350f; font-size: 15px; line-height: 1.8;">{update_message}</p>
                            </div>
                            
                            <div style="background-color: #eff6ff; padding: 20px; border-radius: 4px; margin: 20px 0;">
                                <p style="margin: 0 0 10px; color: #1e40af; font-weight: 600;">Your Booking Information:</p>
                                <p style="margin: 5px 0; color: #4b5563; font-size: 14px;">Ticket Type: <strong>{ticket_type}</strong></p>
                                <p style="margin: 5px 0; color: #4b5563; font-size: 14px;">Quantity: <strong>{quantity} ticket(s)</strong></p>
                                <p style="margin: 5px 0; color: #4b5563; font-size: 14px;">Booking ID: <strong>#{booking_id}</strong></p>
                            </div>
                            
                            <p style="margin: 30px 0 0; color: #4b5563; font-size: 16px;">If you have any questions or concerns, please contact us immediately.</p>
                            <p style="margin: 30px 0 0; color: #6b7280; font-size: 14px;">Best regards,<br><strong>{organizer_name}</strong></p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 30px; background-color: #f9fafb; border-radius: 0 0 8px 8px; text-align: center;">
                            <p style="margin: 0; color: #9ca3af; font-size: 12px;">This email was sent via MGLTickets<br>© {year} MGLTickets. All rights reserved</p>
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