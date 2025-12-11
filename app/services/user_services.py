#!/usr/bin/env python3
"""User-related services for MGLTickets."""

import app.db.repositories.user_repo as user_repo
from typing import Optional
from datetime import datetime
from passlib.hash import argon2
from app.core.logging_config import logger
from app.core.security import create_access_token, decode_access_token


async def register_user_service(name: str, email: str, password: str, phone_number: str) -> dict:
    """Create a new user and return the user"""
    logger.info("Registering user...")

    if len(name) < 3:  # Ensure name is at least 3 chars long
        raise ValueError("Name must be at least 3 characters long.")
    
    if '@' not in email or '.' not in email:
        raise ValueError("Invalid email format.")
    
    if len(password) < 8:  # Ensure password is at least 8 chars long
        raise ValueError("Password must be at least 8 characters long.")
    
    if user_repo.get_user_by_email_repo(email):  # Check if the email exists
        raise ValueError("Email already exists! Please use a different email.")
    
    password_hash = argon2.hash(password)

    user = user_repo.create_user_repo(name, email, password_hash, phone_number)

    logger.info(f"User {user.name} with ID {user.id} registered successfully.")

    # Generate and set access token for email verification or immediate access
    access_token = create_access_token(user.id)

    # I will work on email sending later


    return user

async def authenticate_user_service(user_id: int, email: str, password: str) -> dict:
    """Authenticate a user and return the user"""
    logger.info(f"Authenticating user with ID: {user_id}")

    if '@' not in email or '.' not in email:
        raise ValueError("Invalid email format.")
    
    user = user_repo.get_user_with_password_by_id_repo(user_id)
    if not user:
        raise ValueError("User not found.")
    
    if not argon2.verify(password, user.password_hash):
        raise ValueError("Invalid password.")
    
    return user.pop("password_hash")  # Remove password from response

async def get_user_by_email_service(email: str) -> Optional[dict]:
    """Retrieve a user by email."""
    logger.info("Getting user by email...")
    user = await user_repo.get_user_by_email_repo(email)

    if not user:
        logger.error("User not found.")
        raise ValueError("User not found.")

    return user

async def get_user_by_id_service(user_id: int) -> Optional[dict]:
    """Retrieve a user by ID."""
    logger.info(f"Getting user by ID for user with ID: {user_id}")
    return await user_repo.get_user_by_id_repo(user_id)

async def search_users_by_name_service(name_query: str) -> list[dict]:
    """Search users by name."""
    logger.info(f"Searching users by name: {name_query}")
    return user_repo.search_users_by_name_repo(name_query)

async def update_user_role_service(user_id: int, new_role: str) -> dict:
    """Promote a user to admin role."""
    user = user_repo.get_user_by_id_repo(user_id)
    if not user:
        logger.error(f"User not found. Updating role for user with ID {user_id} failed.")
        raise ValueError("User not found. Please try again.")
    if user.role == new_role:
        logger.error(f"{new_role.title()} with ID {user_id} is already {new_role}.")
        raise ValueError(f"User is already {new_role}.")
    
    logger.info(f"Updating role of user with ID {user_id} to {new_role}.")
    return user_repo.update_user_role_repo(user_id, new_role)


async def update_user_info_service(user_id: int, info: dict) -> dict:
    """Update a user's contact information."""
    logger.info(f"Updating contact information of user with ID: {user_id}")
    if info.get("email"):
        if '@' not in info["email"] or '.' not in info["email"]:
            raise ValueError("Invalid email format.")
        if user_repo.get_user_by_email_repo(info["email"]):
            raise ValueError("Email already exists! Please use a different email.")
    
    return user_repo.update_user_info_repo(user_id, info)

async def delete_user_service(user_id: int) -> bool:
    """Delete a user by ID."""
    logger.info(f"Deleting user with ID: {user_id}")
    user_repo.delete_user_repo(user_id)

async def deactivate_user_service(user_id: int) -> Optional[dict]:
    """Deactivate a user account."""
    logger.info(f"Deactivating a user account with ID: {user_id}")
    return user_repo.deactivate_user_repo(user_id)

async def reactivate_user_service(user_id: int) -> Optional[dict]:
    """Reactivate a user account."""
    logger.info(f"Reactivating user account with ID: {user_id}")
    return user_repo.reactivate_user_repo(user_id)

async def update_user_password_service(user_id: int, new_password: str) -> None:
    """Update a user's password."""
    if len(new_password) < 8:
        logger.warning("Password must be at least 8 characters long.")
        raise ValueError("Password must be at least 8 characters long.")
    
    user = user_repo.get_user_with_password_by_id_repo(user_id)
    if not user:
        logger.error(f"User with ID {user_id} not found.")
        raise ValueError("User not found.")

    if argon2.verify(new_password, user.password_hash):
        logger.warning("New password cannot be the same as the current password.")
        raise ValueError("New password cannot be the same as the current password.")

    logger.info(f"Updating password of user with ID: {user_id}")
    new_password_hash = argon2.hash(new_password)
    user_repo.update_user_password_repo(user_id, new_password_hash)

async def change_user_password_service(user_id: int, old_password: str, new_password: str) -> None:
    """Change a user's password."""
    user = user_repo.get_user_with_password_by_id_repo(user_id)
    if not argon2.verify(old_password, user.password_hash):
        logger.warning(f"Old password is incorrect for user with ID: {user_id}.")
        raise ValueError("Old password is incorrect.")
    
    update_user_password_service(user_id, new_password)
    logger.info(f"Password changed successfully for user with ID: {user_id}")

    # Send email notification about password change
    # send_password_change_email_success(user_id)

async def count_users_by_role_service(role: str) -> int:
    """Count users by their role."""
    logger.info(f"Counting users by role: {role.upper()}")
    return user_repo.count_users_by_role_repo(role)

async def list_all_users_service() -> list[dict]:
    """List users with pagination."""
    logger.info("Listing all users...")
    return user_repo.list_all_users_repo()

async def list_active_users_service() -> list[dict]:
    """List active users with pagination."""
    logger.info("Listing active users...")
    return user_repo.list_active_users_repo()

async def verify_user_email_service(user_id: int, token: str) -> dict:
    """Verify a user's email."""
    payload = decode_access_token(token)
    token_user_id = payload.get("id")
    if token_user_id != user_id:
        logger.error("Token user ID does not match the provided user ID.")
        raise ValueError("Invalid token for the specified user.")
    
    # Send email verification email success to user
    # send_email_verification_email_success(user_id)

    logger.info(f"Verifying email of user with ID: {user_id}")
    return user_repo.verify_user_email_repo(user_id)

async def unverify_user_email_service(user_id: int) -> dict:
    """Unverify a user's email."""
    logger.info(f"Unverifying email of user with ID: {user_id}")
    return user_repo.unverify_user_email_repo(user_id)

async def list_verified_users_service() -> list[dict]:
    """List verified users."""
    logger.info("Listing verified users...")
    return user_repo.list_verified_users_repo()

async def list_unverified_users_service() -> list[dict]:
    """List unverified users."""
    return user_repo.list_unverified_users_repo()

async def count_active_users_service() -> int:
    """Count active users."""
    return user_repo.count_active_users_repo()

async def count_verified_users_service() -> int:
    """Count verified users."""
    return user_repo.count_verified_users_repo()

async def count_unverified_users_service() -> int:
    """Count unverified users."""
    return user_repo.count_unverified_users_repo()

async def list_users_created_after_service(date: datetime) -> list[dict]:
    """List users created after a specific date."""
    return user_repo.list_users_created_after_repo(date)

async def list_users_created_before_service(date: datetime) -> list[dict]:
    """List users created before a specific date."""
    return user_repo.list_users_created_before_repo(date)

async def list_users_updated_after_service(date: datetime) -> list[dict]:
    """List users updated after a specific date."""
    return user_repo.list_users_updated_after_repo(date)

async def list_users_updated_before_service(date: datetime) -> list[dict]:
    """List users updated before a specific date."""
    return user_repo.list_users_updated_before_repo(date)

async def count_users_created_between_service(start_date: datetime, end_date: datetime) -> int:
    """Count users created between two dates."""
    return user_repo.count_users_created_between_repo(start_date, end_date)

async def count_users_updated_between_service(start_date: datetime, end_date: datetime) -> int:
    """Count users updated between two dates."""
    return user_repo.count_users_updated_between_repo(start_date, end_date)