#!/usr/bin/env python3
"""Email verification template for new users."""

from app.emails.templates.email_template_base import EmailTemplate
from typing import Dict
from datetime import datetime


class VerificationEmailTemplate(EmailTemplate):
    """Email template for user email verification."""
    
    def __init__(self):
        super().__init__(
            id='user.verification',
            name='Email Verification',
            category='user',
            description='Email sent to new users to verify their email address',
            required_variables=['name', 'verification_url']
        )
    
    def get_subject(self, variables: Dict[str, str]) -> str:
        return 'Verify Your MGLTickets Account'
    
    def get_body(self, variables: Dict[str, str]) -> str:
        """Get email body with variables replaced."""
        current_year: int = datetime.now().year

        template = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Email</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f9fafb;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" style="width: 600px; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center; background: linear-gradient(135deg, #ea580c 0%, #dc2626 100%); border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">MGLTickets</h1>
                            <p style="margin: 10px 0 0; color: #fed7aa; font-size: 14px;">Your Gateway to Amazing Events</p>
                        </td>
                    </tr>
                    
                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 20px; color: #1f2937; font-size: 24px;">
                                Welcome to MGLTickets! 🎉
                            </h2>
                            
                            <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                Hi <strong>{name}</strong>,
                            </p>
                            
                            <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                Thank you for signing up! We're excited to have you on board. To get started, please verify your email address by clicking the button below:
                            </p>
                            
                            <!-- CTA Button -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="{verification_url}" style="display: inline-block; padding: 16px 32px; background: linear-gradient(135deg, #ea580c 0%, #dc2626 100%); color: #ffffff; text-decoration: none; border-radius: 8px; font-size: 16px; font-weight: bold; box-shadow: 0 4px 6px rgba(234, 88, 12, 0.3);">
                                            Verify Email Address
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 30px 0 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                                Or copy and paste this link into your browser:<br>
                                <a href="{verification_url}" style="color: #ea580c; word-break: break-all;">{verification_url}</a>
                            </p>
                            
                            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                            
                            <p style="margin: 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                                <strong>This link will expire in 24 hours.</strong>
                            </p>
                            
                            <p style="margin: 20px 0 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                                If you didn't create an account with MGLTickets, you can safely ignore this email.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; background-color: #f9fafb; border-radius: 0 0 8px 8px;">
                            <p style="margin: 0 0 10px; color: #6b7280; font-size: 14px; text-align: center;">
                                Need help? Contact us at <a href="mailto:support@mgltickets.com" style="color: #ea580c; text-decoration: none;">support@mgltickets.com</a>
                            </p>
                            <p style="margin: 0; color: #9ca3af; font-size: 12px; text-align: center;">
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