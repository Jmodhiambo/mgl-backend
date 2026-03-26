#!/usr/bin/env python3
"""Custom email template for organizers. No template and variables, just a custom message."""

from app.core.logging_config import logger
from datetime import datetime


async def send_custom_email(
    to: str,
    subject: str,
    body: str,
    organizer_name: str
) -> bool:
    """
    Send custom email without template (for custom messages).
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body
        organizer_name: Name of the organizer sending the email
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        from app.emails.sendgrid_service import SendGridEmailService
        
        # Create a simple HTML email from the plain text message
        html_body = f'''
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
                <table role="presentation" style="width: 600px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <tr>
                        <td style="padding: 40px; text-align: center; background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px;">Message from {organizer_name}</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px;">
                            <div style="color: #4b5563; font-size: 16px; line-height: 1.6; white-space: pre-wrap;">
                                {body}
                            </div>
                            <p style="margin: 30px 0 0; color: #6b7280; font-size: 14px;">
                                Best regards,<br><strong>{organizer_name}</strong>
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 30px; background-color: #f9fafb; border-radius: 0 0 8px 8px; text-align: center;">
                            <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                                This email was sent via MGLTickets<br>© {datetime.now().year} MGLTickets. All rights reserved.
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
        
        email_service = SendGridEmailService()
        email_service.send_email(
            to_email=to,
            subject=subject,
            html_content=html_body,
            template_data={'from_email': 'no_reply'}
        )
        
        logger.info(f"Custom email sent to {to}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send custom email to {to}: {str(e)}")
        return False