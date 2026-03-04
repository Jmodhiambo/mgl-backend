#!/usr/bin/env python3
"""Co-organizer invitation email template."""

from app.emails.templates.email_template_base import EmailTemplate
from typing import Dict
from datetime import datetime

class CoOrganizerInvitationTemplate(EmailTemplate):
    """Email template for co-organizer invitation."""
    
    def __init__(self):
        super().__init__(
            id='organizer.co_organizer_invitation',
            name='Co-Organizer Invitation',
            category='organizer',
            description='Invitation sent to potential co-organizers',
            required_variables=[
                'recipient_name', 'inviter_name', 'event_title',
                'event_id', 'activation_url'
            ]
        )
    
    def get_subject(self, variables: Dict[str, str]) -> str:
        return f"You've Been Invited to Co-Organize: {variables['event_title']}"
    
    def get_body(self, variables: Dict[str, str]) -> str:
        current_year: int = datetime.now().year

        template = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Co-Organizer Invitation</title>
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
                            <p style="margin: 10px 0 0; color: #fed7aa; font-size: 14px;">Organizer Portal</p>
                        </td>
                    </tr>
                    
                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 20px; color: #1f2937; font-size: 24px;">
                                🎉 You've Been Invited!
                            </h2>
                            
                            <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                Hi <strong>{recipient_name}</strong>,
                            </p>
                            
                            <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                <strong>{inviter_name}</strong> has invited you to be a co-organizer for the event:
                            </p>
                            
                            <!-- Event Info -->
                            <div style="background-color: #fff7ed; border-left: 4px solid #ea580c; padding: 20px; margin: 20px 0; border-radius: 4px;">
                                <h3 style="margin: 0 0 10px; color: #ea580c; font-size: 20px;">{event_title}</h3>
                                <p style="margin: 0; color: #9a3412; font-size: 14px;">Event ID: #{event_id}</p>
                            </div>
                            
                            <p style="margin: 0 0 30px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                As a co-organizer, you'll be able to help manage this event, view bookings, and coordinate with the main organizer.
                            </p>
                            
                            <!-- Benefits -->
                            <div style="background-color: #eff6ff; border-left: 4px solid #2563eb; padding: 20px; margin: 20px 0; border-radius: 4px;">
                                <h4 style="margin: 0 0 15px; color: #1e40af; font-size: 16px;">What you can do as a co-organizer:</h4>
                                <ul style="margin: 0; padding-left: 20px; color: #4b5563; font-size: 14px; line-height: 1.8;">
                                    <li>View and manage event bookings</li>
                                    <li>Send emails to attendees</li>
                                    <li>Access event analytics and reports</li>
                                    <li>Coordinate with the main organizer</li>
                                    <li>Help with event promotion</li>
                                </ul>
                            </div>
                            
                            <!-- CTA Button -->
                            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="{activation_url}" style="display: inline-block; padding: 16px 32px; background: linear-gradient(135deg, #ea580c 0%, #dc2626 100%); color: #ffffff; text-decoration: none; border-radius: 8px; font-size: 16px; font-weight: bold; box-shadow: 0 4px 6px rgba(234, 88, 12, 0.3);">
                                            Accept Invitation
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 30px 0 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                                Or copy and paste this link into your browser:<br>
                                <a href="{activation_url}" style="color: #ea580c; word-break: break-all;">{activation_url}</a>
                            </p>
                            
                            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                            
                            <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; border-radius: 4px; margin: 20px 0;">
                                <p style="margin: 0; color: #92400e; font-size: 14px; line-height: 1.6;">
                                    <strong>⏰ Important:</strong> This invitation link will expire in 7 days. Please accept it soon to start collaborating!
                                </p>
                            </div>
                            
                            <p style="margin: 20px 0 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                                This invitation was sent by {inviter_name}. If you don't want to accept this invitation, you can safely ignore this email.
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