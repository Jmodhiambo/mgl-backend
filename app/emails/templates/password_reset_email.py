#!/usr/bin/env python3
"""Password reset email utilities for MGLTickets."""

from typing import Optional
from app.core.config import FRONTEND_URL
from app.core.logging_config import logger


async def send_password_reset_email(to_email: str, name: str, reset_token: str) -> bool:
    """
    Send password reset email to user.
    
    Args:
        to_email: User's email address
        name: User's name
        reset_token: The password reset token
        
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        reset_url = f"{FRONTEND_URL}/reset-password?token={reset_token}"
        
        # TODO: Implement actual email sending logic here
        # This is where you'd use your email service (SendGrid, AWS SES, etc.)
        
        # Example email content:
        email_subject = "Reset Your MGLTickets Password"
        
        email_body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Reset Your Password</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #ea580c;">Reset Your Password</h2>
                
                <p>Hi {name},</p>
                
                <p>We received a request to reset your password for your MGLTickets account. Click the button below to reset your password:</p>
                
                <div style="margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background-color: #ea580c; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                
                <p>Or copy and paste this link into your browser:</p>
                <p style="background-color: #f3f4f6; padding: 10px; border-radius: 5px; word-break: break-all;">
                    {reset_url}
                </p>
                
                <p><strong>This link will expire in 1 hour.</strong></p>
                
                <p>If you didn't request a password reset, you can safely ignore this email. Your password will not be changed.</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                
                <p style="color: #6b7280; font-size: 14px;">
                    Best regards,<br>
                    The MGLTickets Team
                </p>
                
                <p style="color: #9ca3af; font-size: 12px;">
                    If you're having trouble clicking the button, copy and paste the URL above into your web browser.
                </p>
            </div>
        </body>
        </html>
        """
        
        email_body_text = f"""
        Reset Your Password
        
        Hi {name},
        
        We received a request to reset your password for your MGLTickets account.
        
        Click the link below to reset your password:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request a password reset, you can safely ignore this email. Your password will not be changed.
        
        Best regards,
        The MGLTickets Team
        """
        
        # TODO: Replace with your actual email sending implementation
        # Example with a hypothetical email service:
        # success = await email_service.send(
        #     to=to_email,
        #     subject=email_subject,
        #     html=email_body_html,
        #     text=email_body_text
        # )
        
        # For now, just log the email (REMOVE IN PRODUCTION!)
        logger.info(f"Password reset email would be sent to {to_email}")
        logger.info(f"Reset URL: {reset_url}")
        
        # TODO: Return actual result from email service
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password reset email to {to_email}: {str(e)}")
        return False


async def send_password_changed_notification_email(to_email: str, name: str) -> bool:
    """
    Send notification email when password is successfully changed.
    
    Args:
        to_email: User's email address
        name: User's name
        
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        email_subject = "Your MGLTickets Password Was Changed"
        
        email_body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Password Changed</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #ea580c;">Password Changed Successfully</h2>
                
                <p>Hi {name},</p>
                
                <p>This is a confirmation that your MGLTickets account password was successfully changed.</p>
                
                <p>If you made this change, no further action is required.</p>
                
                <p><strong>If you did not make this change, please contact our support team immediately.</strong></p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                
                <p style="color: #6b7280; font-size: 14px;">
                    Best regards,<br>
                    The MGLTickets Team
                </p>
            </div>
        </body>
        </html>
        """
        
        # TODO: Implement actual email sending
        logger.info(f"Password changed notification would be sent to {to_email}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password changed notification to {to_email}: {str(e)}")
        return False
