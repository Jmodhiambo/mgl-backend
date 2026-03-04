#!/usr/bin/env python3
"""Event cancellation email template for organizers."""

from app.emails.templates.email_template_base import EmailTemplate
from typing import Dict
from datetime import datetime


class EventCancellationTemplate(EmailTemplate):
    """Email template for event cancellation notifications."""
    
    def __init__(self):
        super().__init__(
            id='organizer.cancellation',
            name='Event Cancellation',
            category='organizer',
            description='Notification sent when event is cancelled',
            required_variables=[
                'customer_name', 'event_title', 'ticket_type', 'quantity',
                'booking_id', 'total_price', 'cancellation_reason', 'organizer_name'
            ]
        )
    
    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"Important: {variables['event_title']} Has Been Cancelled"
    
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
                <table role="presentation" style="width: 600px; background-color: #ffffff; border-radius: 8px;">
                    <tr>
                        <td style="padding: 40px; text-align: center; background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px;">❌ Event Cancelled</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px;">
                            <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px;">Dear <strong>{customer_name}</strong>,</p>
                            <p style="margin: 0 0 30px; color: #4b5563; font-size: 16px;">We regret to inform you that <strong>{event_title}</strong> has been cancelled.</p>
                            
                            <div style="background-color: #fee2e2; border-left: 4px solid: #dc2626; padding: 20px; border-radius: 4px; margin: 20px 0;">
                                <h3 style="margin: 0 0 10px; color: #991b1b;">Reason for Cancellation:</h3>
                                <p style="margin: 0; color: #7f1d1d; font-size: 15px;">{cancellation_reason}</p>
                            </div>
                            
                            <div style="background-color: #eff6ff; padding: 20px; border-radius: 4px; margin: 20px 0;">
                                <h3 style="margin: 0 0 15px; color: #1e40af;">Your Booking Information:</h3>
                                <p style="margin: 5px 0; color: #4b5563;">Ticket Type: <strong>{ticket_type}</strong></p>
                                <p style="margin: 5px 0; color: #4b5563;">Quantity: <strong>{quantity} ticket(s)</strong></p>
                                <p style="margin: 5px 0; color: #4b5563;">Amount Paid: <strong>KES {total_price}</strong></p>
                                <p style="margin: 5px 0; color: #4b5563;">Booking ID: <strong>#{booking_id}</strong></p>
                            </div>
                            
                            <div style="background-color: #d1fae5; border-left: 4px solid #10b981; padding: 20px; border-radius: 4px; margin: 20px 0;">
                                <h3 style="margin: 0 0 10px; color: #065f46;">💸 Refund Information:</h3>
                                <p style="margin: 0; color: #047857; font-size: 14px; line-height: 1.8;">
                                    • Full refund will be processed within 5-7 business days<br>
                                    • Refund will be credited to your original payment method
                                </p>
                            </div>
                            
                            <p style="margin: 30px 0; color: #4b5563; font-size: 16px;">We sincerely apologize for any inconvenience caused.</p>
                            <p style="margin: 30px 0 0; color: #6b7280; font-size: 14px;">Best regards,<br><strong>{organizer_name}</strong></p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 30px; background-color: #f9fafb; border-radius: 0 0 8px 8px; text-align: center;">
                            <p style="margin: 0; color: #9ca3af; font-size: 12px;">This email was sent via MGLTickets<br>© {year} MGLTickets. All rights reserved.</p>
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