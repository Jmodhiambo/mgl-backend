#!/usr/bin/env python3
"""Thank you email template for organizers."""

from app.emails.templates.email_template_base import EmailTemplate
from typing import Dict
from datetime import datetime


class ThankYouTemplate(EmailTemplate):
    """Email template for post-event thank you messages."""
    
    def __init__(self):
        super().__init__(
            id='organizer.thank_you',
            name='Thank You',
            category='organizer',
            description='Thank you message sent after the event',
            required_variables=[
                'customer_name', 'event_title', 'organizer_name'
            ]
        )
    
    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"Thank You for Attending {variables['event_title']}!"
    
    def get_body(self, variables: Dict[str, str]) -> str:
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
                        <td style="padding: 40px; text-align: center; background: linear-gradient(135deg, #10b981 0%, #059669 100%); border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px;">Thank You! 🎉</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px;">
                            <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px;">Dear <strong>{customer_name}</strong>,</p>
                            <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                Thank you so much for attending <strong>{event_title}</strong>! We hope you had a wonderful experience.
                            </p>
                            
                            <div style="background-color: #d1fae5; border-left: 4px solid #10b981; padding: 25px; border-radius: 4px; margin: 30px 0;">
                                <h3 style="margin: 0 0 15px; color: #065f46; font-size: 18px;">We'd Love Your Feedback!</h3>
                                <p style="margin: 0 0 10px; color: #047857; font-size: 15px; line-height: 1.8;">
                                    Your opinion matters to us. Please take a moment to share your experience:
                                </p>
                                <ul style="margin: 10px 0 0; padding-left: 20px; color: #047857; font-size: 14px; line-height: 1.8;">
                                    <li>What did you enjoy most about the event?</li>
                                    <li>Is there anything we could improve?</li>
                                    <li>Would you attend similar events in the future?</li>
                                </ul>
                            </div>
                            
                            <p style="margin: 30px 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                We look forward to seeing you at our future events!
                            </p>
                            
                            <p style="margin: 30px 0 0; color: #6b7280; font-size: 14px;">
                                Warm regards,<br><strong>{organizer_name}</strong>
                            </p>
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
