#!/usr/bin/env python3
"""Email templates for co-organizer invitations."""

from typing import Optional


def send_co_organizer_invitation_email_to_existing_user(
    to_email: str,
    to_name: str,
    inviter_name: str,
    event_title: str,
    event_id: int,
    activation_token: str,
    base_url: str = "http://localhost:3000"
) -> bool:
    """
    Send invitation email to an existing user to become a co-organizer.
    
    Args:
        to_email: Recipient email address
        to_name: Recipient's name
        inviter_name: Name of the organizer who sent the invitation
        event_title: Title of the event
        event_id: ID of the event
        activation_token: Token to activate co-organizer status
        base_url: Base URL of the frontend application
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Activation link
    activation_url = f"{base_url}/accept-co-organizer-invitation?token={activation_token}&event_id={event_id}"
    
    subject = f"You've been invited to co-organize: {event_title}"
    
    html_body = f"""
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
                            <td style="padding: 40px 40px 20px; text-align: center; background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); border-radius: 8px 8px 0 0;">
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
                                    Hi <strong>{to_name}</strong>,
                                </p>
                                
                                <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    <strong>{inviter_name}</strong> has invited you to be a co-organizer for the event:
                                </p>
                                
                                <div style="background-color: #fff7ed; border-left: 4px solid #f97316; padding: 20px; margin: 20px 0; border-radius: 4px;">
                                    <h3 style="margin: 0 0 10px; color: #ea580c; font-size: 20px;">{event_title}</h3>
                                    <p style="margin: 0; color: #9a3412; font-size: 14px;">Event ID: #{event_id}</p>
                                </div>
                                
                                <p style="margin: 0 0 30px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    As a co-organizer, you'll be able to help manage this event, view bookings, and coordinate with the main organizer.
                                </p>
                                
                                <!-- CTA Button -->
                                <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                    <tr>
                                        <td align="center" style="padding: 20px 0;">
                                            <a href="{activation_url}" style="display: inline-block; padding: 16px 32px; background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); color: #ffffff; text-decoration: none; border-radius: 8px; font-size: 16px; font-weight: bold; box-shadow: 0 4px 6px rgba(249, 115, 22, 0.3);">
                                                Accept Invitation
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="margin: 30px 0 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                                    Or copy and paste this link into your browser:<br>
                                    <a href="{activation_url}" style="color: #f97316; word-break: break-all;">{activation_url}</a>
                                </p>
                                
                                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                                
                                <p style="margin: 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                                    This invitation was sent by {inviter_name}. If you don't want to accept this invitation, you can safely ignore this email.
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 30px 40px; background-color: #f9fafb; border-radius: 0 0 8px 8px;">
                                <p style="margin: 0 0 10px; color: #6b7280; font-size: 14px; text-align: center;">
                                    Need help? Contact us at <a href="mailto:support@mgltickets.com" style="color: #f97316; text-decoration: none;">support@mgltickets.com</a>
                                </p>
                                <p style="margin: 0; color: #9ca3af; font-size: 12px; text-align: center;">
                                    © 2025 MGLTickets. All rights reserved.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # TODO: Implement actual email sending logic
    # Example:
    # from app.core.email import send_email
    # return send_email(
    #     to_email=to_email,
    #     subject=subject,
    #     html_content=html_body
    # )
    
    print(f"Email would be sent to: {to_email}")
    print(f"Subject: {subject}")
    print(f"Activation URL: {activation_url}")
    
    return True


def send_co_organizer_invitation_email_to_non_existing_user(
    to_email: str,
    inviter_name: str,
    event_title: str,
    event_id: int,
    activation_token: str,
    base_url: str = "http://localhost:3000"
) -> bool:
    """
    Send invitation email to a non-existing user to sign up and become a co-organizer.
    
    This is a two-step process:
    1. User clicks signup link and creates an account
    2. After signup, user clicks activation link to accept co-organizer role
    
    Args:
        to_email: Recipient email address
        inviter_name: Name of the organizer who sent the invitation
        event_title: Title of the event
        event_id: ID of the event
        activation_token: Token to activate co-organizer status after signup
        base_url: Base URL of the frontend application
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Signup link with pre-filled email and redirect
    signup_url = f"{base_url}/register?email={to_email}&redirect=accept-co-organizer"
    
    # Activation link (to be used after signup)
    activation_url = f"{base_url}/accept-co-organizer-invitation?token={activation_token}&event_id={event_id}"
    
    subject = f"You've been invited to co-organize: {event_title}"
    
    html_body = f"""
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
                            <td style="padding: 40px 40px 20px; text-align: center; background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); border-radius: 8px 8px 0 0;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">MGLTickets</h1>
                                <p style="margin: 10px 0 0; color: #fed7aa; font-size: 14px;">Organizer Portal</p>
                            </td>
                        </tr>
                        
                        <!-- Body -->
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="margin: 0 0 20px; color: #1f2937; font-size: 24px;">
                                    🎉 You've Been Invited to Join MGLTickets!
                                </h2>
                                
                                <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    Hi there,
                                </p>
                                
                                <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    <strong>{inviter_name}</strong> has invited you to be a co-organizer for the event:
                                </p>
                                
                                <div style="background-color: #fff7ed; border-left: 4px solid #f97316; padding: 20px; margin: 20px 0; border-radius: 4px;">
                                    <h3 style="margin: 0 0 10px; color: #ea580c; font-size: 20px;">{event_title}</h3>
                                    <p style="margin: 0; color: #9a3412; font-size: 14px;">Event ID: #{event_id}</p>
                                </div>
                                
                                <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    To accept this invitation, you'll need to create a free MGLTickets account. Here's how:
                                </p>
                                
                                <!-- Steps -->
                                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                                    <ol style="margin: 0; padding-left: 20px; color: #374151; font-size: 15px; line-height: 1.8;">
                                        <li style="margin-bottom: 10px;"><strong>Step 1:</strong> Click the "Create Account" button below to sign up</li>
                                        <li style="margin-bottom: 10px;"><strong>Step 2:</strong> Complete the registration process</li>
                                        <li><strong>Step 3:</strong> After signup, click the "Accept Invitation" link in this email</li>
                                    </ol>
                                </div>
                                
                                <!-- CTA Buttons -->
                                <table role="presentation" style="width: 100%; border-collapse: collapse; margin: 30px 0;">
                                    <tr>
                                        <td align="center">
                                            <a href="{signup_url}" style="display: inline-block; padding: 16px 32px; background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); color: #ffffff; text-decoration: none; border-radius: 8px; font-size: 16px; font-weight: bold; box-shadow: 0 4px 6px rgba(249, 115, 22, 0.3); margin-bottom: 15px;">
                                                Step 1: Create Account
                                            </a>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td align="center">
                                            <a href="{activation_url}" style="display: inline-block; padding: 14px 28px; background-color: #ffffff; color: #f97316; text-decoration: none; border: 2px solid #f97316; border-radius: 8px; font-size: 15px; font-weight: bold;">
                                                Step 3: Accept Invitation
                                            </a>
                                            <p style="margin: 10px 0 0; color: #6b7280; font-size: 13px;">
                                                (Use this after creating your account)
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                                
                                <div style="background-color: #dbeafe; border-left: 4px solid #3b82f6; padding: 15px; margin: 20px 0; border-radius: 4px;">
                                    <p style="margin: 0; color: #1e40af; font-size: 14px; line-height: 1.6;">
                                        <strong>💡 Tip:</strong> Save this email! You'll need the "Accept Invitation" link after you create your account.
                                    </p>
                                </div>
                                
                                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                                
                                <p style="margin: 0 0 10px; color: #6b7280; font-size: 14px; line-height: 1.6;">
                                    <strong>Signup URL:</strong><br>
                                    <a href="{signup_url}" style="color: #f97316; word-break: break-all;">{signup_url}</a>
                                </p>
                                
                                <p style="margin: 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                                    <strong>Activation URL (use after signup):</strong><br>
                                    <a href="{activation_url}" style="color: #f97316; word-break: break-all;">{activation_url}</a>
                                </p>
                                
                                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                                
                                <p style="margin: 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                                    This invitation was sent by {inviter_name}. If you don't want to accept this invitation, you can safely ignore this email.
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 30px 40px; background-color: #f9fafb; border-radius: 0 0 8px 8px;">
                                <p style="margin: 0 0 10px; color: #6b7280; font-size: 14px; text-align: center;">
                                    Need help? Contact us at <a href="mailto:support@mgltickets.com" style="color: #f97316; text-decoration: none;">support@mgltickets.com</a>
                                </p>
                                <p style="margin: 0; color: #9ca3af; font-size: 12px; text-align: center;">
                                    © 2025 MGLTickets. All rights reserved.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # TODO: Implement actual email sending logic
    # Example:
    # from app.core.email import send_email
    # return send_email(
    #     to_email=to_email,
    #     subject=subject,
    #     html_content=html_body
    # )
    
    print(f"Email would be sent to: {to_email}")
    print(f"Subject: {subject}")
    print(f"Signup URL: {signup_url}")
    print(f"Activation URL: {activation_url}")
    
    return True