#!/usr/bin/env python3
"""Password reset email template."""

from app.emails.templates.email_template_base import EmailTemplate
from typing import Dict
from datetime import datetime


class PasswordResetEmailTemplate(EmailTemplate):
    """Email template for password reset requests."""
    
    def __init__(self):
        super().__init__(
            id='user.password_reset',
            name='Password Reset',
            category='user',
            description='Email sent when user requests password reset',
            required_variables=['name', 'reset_url']
        )
    
    def get_subject(self, variables: Dict[str, str]) -> str:
        return 'Reset Your MGLTickets Password'
    
    def get_body(self, variables: Dict[str, str]) -> str:
        """Get email body with variables replaced."""
        current_year: int = datetime.now().year

        template = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your Password</title>
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
                            <p style="margin: 10px 0 0; color: #fed7aa; font-size: 14px;">Password Reset Request</p>
                        </td>
                    </tr>
                    
                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 20px; color: #1f2937; font-size: 24px;">
                                Reset Your Password
                            </h2>
                            
                            <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                Hi <strong>{name}</strong>,
                            </p>
                            
                            <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                We received a request to reset your password for your MGLTickets account. Click the button below to reset your password:
                            </p>
                            
                            <!-- CTA Button -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="{reset_url}" style="display: inline-block; padding: 16px 32px; background: linear-gradient(135deg, #ea580c 0%, #dc2626 100%); color: #ffffff; text-decoration: none; border-radius: 8px; font-size: 16px; font-weight: bold; box-shadow: 0 4px 6px rgba(234, 88, 12, 0.3);">
                                            Reset Password
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 30px 0 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                                Or copy and paste this link into your browser:<br>
                                <a href="{reset_url}" style="color: #ea580c; word-break: break-all;">{reset_url}</a>
                            </p>
                            
                            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                            
                            <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; border-radius: 4px; margin: 20px 0;">
                                <p style="margin: 0; color: #92400e; font-size: 14px; line-height: 1.6;">
                                    <strong>⚠️ Important:</strong> This link will expire in 1 hour for security reasons.
                                </p>
                            </div>
                            
                            <p style="margin: 20px 0 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                                If you didn't request a password reset, you can safely ignore this email. Your password will not be changed.
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

        return template.format(
            year=current_year,
            **variables
        )