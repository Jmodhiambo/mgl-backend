#!/usr/bin/env python3
"""Verification email for MGLTickets."""
"""Handle it later."""
# from typing import Optional

# async def send_verification_email(
#     to_email: str,
#     name: str,
#     verification_token: str,
#     base_url: str = "http://localhost:3000"
# ) -> bool:
#     """
#     Send verification email to user
    
#     In production, implement this with your email service (SendGrid, AWS SES, etc.)
#     For now, this is a placeholder that logs the verification link
#     """
#     verification_link = f"{base_url}/verify-email?token={verification_token}&email={to_email}"
    
#     # TODO: Replace with actual email sending
#     print(f"""
#     ================================
#     VERIFICATION EMAIL
#     ================================
#     To: {to_email}
#     Subject: Verify Your MGLTickets Account
    
#     Hi {name},
    
#     Please verify your email address by clicking the link below:
#     {verification_link}
    
#     This link will expire in 24 hours.
    
#     If you didn't create an account, please ignore this email.
    
#     Best regards,
#     MGLTickets Team
#     ================================
#     """)
    
#     # For now, always return True (successful)
#     # In production, catch email sending errors and return False if failed
#     return True