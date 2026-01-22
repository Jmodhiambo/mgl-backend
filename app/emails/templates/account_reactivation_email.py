#!/usr/bin/env python3
"""Password reset email utilities for MGLTickets."""

from typing import Optional
from app.core.config import FRONTEND_URL
from app.core.logging_config import logger


async def send_account_reactivated_email(to_email: str, name: str) -> bool:
    """
    Send notification email when account is reactivated.
    
    Args:
        to_email: User's email address
        name: User's name
        
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        login_url = f"{FRONTEND_URL}/login"
        
        email_subject = "Your MGLTickets Account Has Been Reactivated"
        
        email_body_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Account Reactivated</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #ea580c;">Welcome Back!</h2>
                
                <p>Hi {name},</p>
                
                <p>Your MGLTickets account has been successfully reactivated. You can now log in and start booking tickets again!</p>
                
                <div style="margin: 30px 0;">
                    <a href="{login_url}" 
                       style="background-color: #ea580c; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Log In Now
                    </a>
                </div>
                
                <p>We're glad to have you back!</p>
                
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
        logger.info(f"Account reactivation notification would be sent to {to_email}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to send account reactivation email to {to_email}: {str(e)}")
        return False