#!/usr/bin/env python3
"""User-related services for MGLTickets."""

import app.db.repositories.user_repo as user_repo
from typing import Optional
from fastapi import HTTPException, status
from datetime import datetime
from passlib.hash import argon2
from app.core.logging_config import logger
from app.utils.token_verification import (
    generate_verification_token, create_verification_token_expiry, is_token_expired
)
from app.schemas.user import (
    UserOut, UserUpdate
)
from app.services.ref_session_services import cleanup_user_sessions_service
# from app.emails.templates.verification_email import send_verification_email
# from app.emails.templates.password_reset_email import send_password_reset_email, send_password_changed_notification_email
# from app.emails.templates.account_reactivation_email import send_account_reactivated_email
# from app.emails.templates.account_deactivation_email import send_account_deactivated_email

async def register_user_service(name: str, email: str, password: str, phone_number: str) -> dict:
    """Create a new user and return the user"""
    logger.info("Registering user...")

    if len(name) < 3:  # Ensure name is at least 3 chars long
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name must be at least 3 characters long.")
    
    if '@' not in email or '.' not in email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format.")
    
    if len(password) < 8:  # Ensure password is at least 8 chars long
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters long.")
    
    if await user_repo.get_user_by_email_repo(email):  # Check if the email exists
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists.")
    
    password_hash = argon2.hash(password)

    # Generate and set token for email verification
    token = generate_verification_token()
    expires_at = create_verification_token_expiry(hours=24)

    user = await user_repo.create_user_repo(name, email, password_hash, phone_number, token, expires_at)

    logger.info(f"User {user.name} with ID {user.id} registered successfully.")

    # I will work on email sending later

    # Send verification email
    # send_verification_email(user, token)


    return user

async def authenticate_user_service(user_id: int, email: str, password: str) -> dict:
    """Authenticate a user and return the user"""
    logger.info(f"Authenticating user with ID: {user_id}")

    if '@' not in email or '.' not in email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format.")
    
    user = await user_repo.get_user_with_password_by_id_repo(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found. Auth Request Failed.")
    
    if not argon2.verify(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password.")
    
    return user.__dict__.pop("password_hash")  # Remove password from response

async def get_user_by_email_service(email: str) -> Optional[dict]:
    """Retrieve a user by email."""
    user = await user_repo.get_user_by_email_repo(email)

    if not user:
        logger.error("User not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    return user

async def get_user_by_id_service(user_id: int) -> Optional[UserOut]:
    """Retrieve a user by ID."""
    logger.info(f"Getting user by ID for user with ID: {user_id}")
    return await user_repo.get_user_by_id_repo(user_id)

async def search_users_by_name_service(name_query: str) -> list[dict]:
    """Search users by name."""
    logger.info(f"Searching users by name: {name_query}")
    return await user_repo.search_users_by_name_repo(name_query)

async def update_user_role_service(user_id: int, new_role: str) -> dict:
    """Promote a user to admin role."""
    user = await user_repo.get_user_by_id_repo(user_id)
    if not user:
        logger.error(f"User not found. Updating role for user with ID {user_id} failed.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.role == new_role:
        logger.error(f"{new_role.title()} with ID {user_id} is already {new_role}.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{new_role.title()} with ID {user_id} is already {new_role}.")
    
    logger.info(f"Updating role of user with ID {user_id} to {new_role}.")
    return await user_repo.update_user_role_repo(user_id, new_role)


async def update_user_info_service(user_id: int, info: dict) -> dict:
    """Update a user's contact information."""
    logger.info(f"Updating contact information of user with ID: {user_id}")

    # if info.get("email"):
    #     if '@' not in info["email"] or '.' not in info["email"]:
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail="Invalid email format."
    #         )
    #     if await user_repo.get_user_by_email_repo(info["email"]):
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail=f"The email {info['email']} already exists! Please use a different email."
    #         )
    
    return await user_repo.update_user_info_repo(user_id, info)

async def delete_user_service(user_id: int) -> bool:
    """Delete a user by ID."""
    logger.info(f"Deleting user with ID: {user_id}")
    return await user_repo.delete_user_repo(user_id)

async def update_user_password_service(user_id: int, new_password: str) -> None:
    """Update a user's password."""
    if len(new_password) < 8:
        logger.warning("Password must be at least 8 characters long.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long."
        )
    
    user = await user_repo.get_user_with_password_by_id_repo(user_id)
    if not user:
        logger.error(f"User with ID {user_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found here.")

    if argon2.verify(new_password, user.password_hash):
        logger.warning("New password cannot be the same as the current password.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the current password."
        )

    logger.info(f"Updating password of user with ID: {user_id}")
    new_password_hash = argon2.hash(new_password)
    await user_repo.update_user_password_repo(user_id, new_password_hash)

async def change_user_password_service(user_id: int, old_password: str, new_password: str) -> None:
    """Change a user's password."""
    user = await user_repo.get_user_with_password_by_id_repo(user_id)

    if not user:
        logger.error(f"User with ID {user_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found in the database.")
    
    if not argon2.verify(old_password, user.password_hash):
        logger.warning(f"Old password is incorrect for user with ID: {user_id}.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect."
        )
    
    await update_user_password_service(user_id, new_password)
    logger.info(f"Password changed successfully for user with ID: {user_id}")

    # Send email notification about password change
    # send_password_change_email_success(user_id)


async def count_users_by_role_service(role: str) -> int:
    """Count users by their role."""
    logger.info(f"Counting users by role: {role.upper()}")
    return await user_repo.count_users_by_role_repo(role)

async def list_all_users_service() -> list[dict]:
    """List users with pagination."""
    logger.info("Listing all users...")
    return await user_repo.list_all_users_repo()

async def list_active_users_service() -> list[dict]:
    """List active users with pagination."""
    logger.info("Listing active users...")
    return await user_repo.list_active_users_repo()

async def verify_user_email_service(token: str) -> dict:
    """Verify a user's email with token."""
    logger.info(f"Email verification attempt with token: {token[:10]}...")
    
    # Get user by token
    user = await user_repo.get_user_by_verification_token_repo(token)

    if not user:
        logger.warning(f"Invalid verification token: {token[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token."
        )

    # Check if user is already verified
    if user.email_verified:
        logger.info(f"Email already verified for user: {user.email}")
        return {
            "success": True,
            "message": "Email already verified. You can log in now.",
            "user": {
                "email": user.email,
                "name": user.name
            }
        }
    
    # Check if token is expired
    if is_token_expired(user.email_verification_token_expires):
        logger.warning(f"Verification token expired for user: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Verification token expired. Please request a new one."
        )

    # Verify user email
    verified_user = await user_repo.verify_user_email_repo(user.id)
    
    logger.info(f"Email verified successfully for user: {verified_user.email}")
    
    return {
        "success": True,
        "message": "Email verified successfully! You can now log in.",
        "user": {
            "email": verified_user.email,
            "name": verified_user.name
        }
    }

async def resend_verification_email_service(email: str) -> dict:
    """Resend a verification email to a user."""
    logger.info(f"Resending verification email to user with email: {email}")
    
    # Get user by email
    user = await user_repo.get_user_by_email_repo(email)

    if not user:
        # Does not reveal if the user if found or not for security purposes
        logger.warning(f"Resend verification email failed for user with email: {email}.")
        return {
            "success": True,
            "message": "If an account exists with this email, a verification link has been sent."
        }

    # Check if user is already verified
    if user.email_verified:
        logger.warning(f"User with email {email} is already verified.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already verified."
        )

    # Generate new token
    new_token = generate_verification_token()
    expires_at = create_verification_token_expiry(hours=24)

    # Update user with an new token
    await user_repo.update_verification_token_repo(user.id, new_token, expires_at)

    # Send verification email
    # email_sent = await send_verification_email(
    #         to_email=user.email,
    #         name=user.name,
    #         verification_token=new_token
    #     )
        
    # if not email_sent:
    #     logger.error(f"Failed to send verification email to: {email}")
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail="Failed to send verification email. Please try again later."
    #     )
    
    logger.info(f"Verification email resent successfully to: {email}")
    
    return {
        "success": True,
        "message": "Verification email sent! Please check your inbox."
    }


async def unverify_user_email_service(user_id: int) -> dict:
    """Unverify a user's email."""
    logger.info(f"Unverifying email of user with ID: {user_id}")
    return await user_repo.unverify_user_email_repo(user_id)

async def request_password_reset_service(email: str) -> dict:
    """Request a password reset for a user."""
    logger.info(f"Password reset requested for email: {email}")
    
    # Get user by email
    user = await user_repo.get_user_by_email_repo(email)
    
    if not user:
        # Don't reveal if user exists for security purposes
        logger.warning(f"Password reset requested for non-existent email: {email}")
        return {
            "success": True,
            "message": "If an account exists with this email, a password reset link has been sent. Please check your inbox."
        }
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"Password reset requested for inactive user: {email}")
        return {
            "success": True,
            "message": "If an account exists with this email, a password reset link has been sent. Please check your inbox."
        }
    
    # Generate reset token
    reset_token = generate_verification_token()
    expires_at = create_verification_token_expiry(hours=1)  # Token expires in 1 hour
    
    # Update user with reset token
    await user_repo.update_password_reset_token_repo(user.id, reset_token, expires_at)
    
    # Send password reset email
    # email_sent = await send_password_reset_email(
    #     to_email=user.email,
    #     name=user.name,
    #     reset_token=reset_token
    # )
    
    # if not email_sent:
    #     logger.error(f"Failed to send password reset email to: {email}")
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail="Failed to send password reset email. Please try again later."
    #     )
    
    logger.info(f"Password reset email sent successfully to: {email}")
    
    return {
        "success": True,
        "message": "If an account exists with this email, a password reset link has been sent. Please check your inbox."
    }


async def reset_password_with_token_service(token: str, new_password: str) -> dict:
    """Reset password using a valid reset token."""
    logger.info(f"Password reset attempt with token: {token[:10]}...")
    
    # Validate password length
    if len(new_password) < 8:
        logger.warning("Password reset failed: password too short")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long."
        )
    
    # Get user by reset token
    user = await user_repo.get_user_by_password_reset_token_repo(token)
    
    if not user:
        logger.warning(f"Invalid password reset token: {token[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token."
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"Password reset attempted for inactive user: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support."
        )
    
    # Check if token is expired
    if is_token_expired(user.password_reset_token_expires):
        logger.warning(f"Password reset token expired for user: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Password reset token has expired. Please request a new one."
        )
    
    # Get user with password to check if new password is same as old
    user_with_pwd = await user_repo.get_user_with_password_by_id_repo(user.id)
    
    if argon2.verify(new_password, user_with_pwd.password_hash):
        logger.warning(f"User {user.email} tried to reset to same password")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as your current password."
        )
    
    # Hash new password
    new_password_hash = argon2.hash(new_password)
    
    # Update password
    await user_repo.update_user_password_repo(user.id, new_password_hash)
    
    # Clear reset token
    await user_repo.clear_password_reset_token_repo(user.id)
    
    logger.info(f"Password reset successfully for user: {user.email}")
    
    # Send password change notification email
    # await send_password_changed_notification_email(user.email, user.name)
    
    return {
        "success": True,
        "message": "Password has been reset successfully. You can now log in with your new password."
    }


async def deactivate_user_service(user_id: int) -> None:
    """Deactivate a user account."""
    logger.info(f"Deactivating a user account with ID: {user_id}")
    response = await user_repo.deactivate_user_repo(user_id)

    if not response:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account deactivation failed.")
    
    logger.info(f"User account with ID: {user_id} has been deactivated.")

async def reactivate_account_service(email: str) -> dict:
    """Reactivate a deactivated user account."""
    logger.info(f"Account reactivation requested for email: {email}")
    
    # Validate email format
    if '@' not in email or '.' not in email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format."
        )
    
    # Get user by email
    user = await user_repo.get_user_by_email_repo(email)
    
    if not user:
        logger.warning(f"Reactivation attempted for non-existent email: {email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    
    # Check if user is already active
    if user.is_active:
        logger.warning(f"Reactivation attempted for already active user: {email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is already active. Please log in."
        )
    
    # Reactivate user
    await user_repo.reactivate_user_repo(user.id)
    
    logger.info(f"Account reactivated successfully for user: {email}")
    
    # Send account reactivation email
    # await send_account_reactivated_email(user.email, user.name)
    
    return {
        "success": True,
        "message": "Your account has been reactivated successfully. You can now log in."
    }

async def list_verified_users_service() -> list[dict]:
    """List verified users."""
    logger.info("Listing verified users...")
    return await user_repo.list_verified_users_repo()

async def list_unverified_users_service() -> list[dict]:
    """List unverified users."""
    return await user_repo.list_unverified_users_repo()

async def count_active_users_service() -> int:
    """Count active users."""
    return await user_repo.count_active_users_repo()

async def count_verified_users_service() -> int:
    """Count verified users."""
    return await user_repo.count_verified_users_repo()

async def count_unverified_users_service() -> int:
    """Count unverified users."""
    return await user_repo.count_unverified_users_repo()

async def list_users_created_after_service(date: datetime) -> list[dict]:
    """List users created after a specific date."""
    return await user_repo.list_users_created_after_repo(date)

async def list_users_created_before_service(date: datetime) -> list[dict]:
    """List users created before a specific date."""
    return await user_repo.list_users_created_before_repo(date)

async def list_users_updated_after_service(date: datetime) -> list[dict]:
    """List users updated after a specific date."""
    return await user_repo.list_users_updated_after_repo(date)

async def list_users_updated_before_service(date: datetime) -> list[dict]:
    """List users updated before a specific date."""
    return await user_repo.list_users_updated_before_repo(date)

async def count_users_created_between_service(start_date: datetime, end_date: datetime) -> int:
    """Count users created between two dates."""
    return await user_repo.count_users_created_between_repo(start_date, end_date)

async def count_users_updated_between_service(start_date: datetime, end_date: datetime) -> int:
    """Count users updated between two dates."""
    return await user_repo.count_users_updated_between_repo(start_date, end_date)