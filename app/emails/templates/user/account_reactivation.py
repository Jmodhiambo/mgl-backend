#!/usr/bin/env python3
"""Account reactivation email template."""

from app.emails.templates.email_template_base import EmailTemplate
from typing import Dict
from datetime import datetime


class AccountReactivationEmailTemplate(EmailTemplate):
    """Email template for account reactivation confirmation."""
    
    def __init__(self):
        super().__init__(
            id='user.account_reactivation',
            name='Account Reactivation',
            category='user',
            description='Email sent when user account is reactivated',
            required_variables=['name', 'login_url']
        )
    
    def get_subject(self, variables: Dict[str, str]) -> str:
        return 'Your MGLTickets Account Has Been Reactivated'
    
    def get_body(self, variables: Dict[str, str]) -> str:
        """Get email body with variables replaced."""
        current_year: int = datetime.now().year

        template = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Account Reactivated</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f9fafb;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" style="width: 600px; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px; text-align: center; background: linear-gradient(135deg, #10b981 0%, #059669 100%); border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">MGLTickets</h1>
                            <p style="margin: 10px 0 0; color: #d1fae5; font-size: 14px;">Welcome Back!</p>
                        </td>
                    </tr>
                    
                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 20px; color: #1f2937; font-size: 24px;">
                                Welcome Back! 🎉
                            </h2>
                            
                            <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                Hi <strong>{name}</strong>,
                            </p>
                            
                            <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                Great news! Your MGLTickets account has been successfully reactivated. You can now log in and start booking tickets again!
                            </p>
                            
                            <div style="background-color: #d1fae5; border-left: 4px solid #10b981; padding: 20px; border-radius: 4px; margin: 20px 0;">
                                <p style="margin: 0; color: #065f46; font-size: 15px; line-height: 1.6;">
                                    <strong>✓ Your account is now active</strong><br>
                                    <span style="font-size: 14px;">All your previous bookings and preferences have been restored.</span>
                                </p>
                            </div>
                            
                            <!-- CTA Button -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="{login_url}" style="display: inline-block; padding: 16px 32px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #ffffff; text-decoration: none; border-radius: 8px; font-size: 16px; font-weight: bold; box-shadow: 0 4px 6px rgba(16, 185, 129, 0.3);">
                                            Log In Now
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 30px 0 0; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                We're glad to have you back! Start exploring amazing events and booking your tickets today.
                            </p>
                            
                            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                            
                            <p style="margin: 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                                If you didn't request to reactivate your account, please contact our support team immediately.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; background-color: #f9fafb; border-radius: 0 0 8px 8px;">
                            <p style="margin: 0 0 10px; color: #6b7280; font-size: 14px; text-align: center;">
                                Need help? Contact us at <a href="mailto:support@mgltickets.com" style="color: #10b981; text-decoration: none;">support@mgltickets.com</a>
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