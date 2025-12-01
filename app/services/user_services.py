#!/usr/bin/env python3
"""User-related services for MGLTickets."""

import app.db.repositories.user_repo as user_repo
from typing import Optional
from datetime import datetime
from passlib.hash import argon2
from app.core.logging_config import logger


def register_user_service(name: str, email: str, password: str, phone_number: str) -> dict:
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

    return user

def authenticate_user_service(user_id: int, email: str, password: str) -> dict:
    """Authenticate a user and return the user"""
    logger.info(f"Authenticating user with ID: {user_id}")

    if '@' not in email or '.' not in email:
        raise ValueError("Invalid email format.")
    
    user = user_repo.get_user_with_password_by_id_repo(user_id)
    if not user:
        raise ValueError("User not found.")
    
    if not argon2.verify(password, user.password_hash):
        raise ValueError("Invalid password.")
    
    return user.model_dump(exclude={"password_hash"})

def get_user_by_email_service(email: str) -> Optional[dict]:
    """Retrieve a user by email."""
    logger.info("Getting user by email...")
    user = user_repo.get_user_by_email_repo(email)

    if not user:
        logger.error("User not found.")
        raise ValueError("User not found.")

    return user

def get_user_by_id_service(user_id: int) -> Optional[dict]:
    """Retrieve a user by ID."""
    logger.info("Getting user by ID...")
    return user_repo.get_user_by_id_repo(user_id)

def search_users_by_name_service(name_query: str) -> list[dict]:
    """Search users by name."""
    logger.info(f"Searching users by name: {name_query}")
    return user_repo.search_users_by_name_repo(name_query)

def promote_user_to_admin_service(user_id: int) -> dict:
    """Promote a user to admin role."""
    user = user_repo.get_user_by_id_repo(user_id)
    if not user:
        logger.error("User not found.")
        raise ValueError("User not found.")
    if user.role == "admin":
        logger.error(f"User sith ID {user_id} is already an admin.")
        raise ValueError("User is already an admin.")
    
    logger.info(f"Promoting user with ID {user_id} to admin.")
    return user_repo.update_user_role_repo(user_id, "admin")

def demote_user_from_admin_service(user_id: int) -> dict:
    """Demote a user from admin role."""
    user = user_repo.get_user_by_id_repo(user_id)
    if not user:
        logger.error("User not found.")
        raise ValueError("User not found.")
    
    if user.role == "user":
        logger.error(f"User sith ID {user_id} is not an admin.")
        raise ValueError("User is not an admin.")
    
    logger.info(f"Demoting user with ID {user_id} from admin.")
    return user_repo.update_user_role_repo(user_id, "attendee")

def promote_user_to_organizer_service(user_id: int) -> dict:
    """Promote a user to organizer role."""
    logger.info(f"Promoting user with ID {user_id} to organizer.")
    return user_repo.update_user_role_repo(user_id, "organizer")

def demote_user_from_organizer_service(user_id: int) -> dict:
    """Demote a user from organizer role."""
    logger.info(f"Demoting user with ID {user_id} from organizer.")
    return user_repo.update_user_role_repo(user_id, "attendee")

def promote_organizer_to_admin_service(user_id: int) -> dict:
    """Promote an organizer to admin role."""
    logger.info(f"Promoting organizer with ID {user_id} to admin.")
    return user_repo.update_user_role_repo(user_id, "admin")

def demote_admin_to_organizer_service(user_id: int) -> dict:
    """Demote an admin to organizer role."""
    logger.info(f"Demoting admin with ID {user_id} from admin.")
    return user_repo.update_user_role_repo(user_id, "organizer")

def update_user_contact_service(user_id: int, new_email: Optional[str], new_phone_number: Optional[str]) -> dict:
    """Update a user's contact information."""
    logger.info(f"Updating contact information of user with ID: {user_id}")
    if new_email:
        if '@' not in new_email or '.' not in new_email:
            raise ValueError("Invalid email format.")
        if user_repo.get_user_by_email_repo(new_email):
            raise ValueError("Email already exists! Please use a different email.")
    
    return user_repo.update_user_contact_repo(user_id, new_email, new_phone_number)

def delete_user_service(user_id: int) -> bool:
    """Delete a user by ID."""
    logger.info(f"Deleting user with ID: {user_id}")
    user_repo.delete_user_repo(user_id)

def deactivate_user_service(user_id: int) -> Optional[dict]:
    """Deactivate a user account."""
    logger.info(f"Deactivating a user account with ID: {user_id}")
    return user_repo.deactivate_user_repo(user_id)

def activate_user_service(user_id: int) -> Optional[dict]:
    """Activate a user account."""
    logger.info(f"Activating user account with ID: {user_id}")
    return user_repo.activate_user_repo(user_id)

def update_user_password_service(user_id: int, new_password: str) -> dict:
    """Update a user's password."""
    if len(new_password) < 8:
        logger.warning("Password must be at least 8 characters long.")
        raise ValueError("Password must be at least 8 characters long.")
    
    user = user_repo.get_user_with_password_by_id_repo(user_id)
    if argon2.verify(new_password, user.password_hash):
        logger.warning("New password cannot be the same as the current password.")
        raise ValueError("New password cannot be the same as the current password.")

    logger.info(f"Updating password of user with ID: {user_id}")
    new_password_hash = argon2.hash(new_password)
    return user_repo.update_user_password_repo(user_id, new_password_hash)

def count_users_by_role_service(role: str) -> int:
    """Count users by their role."""
    logger.info(f"Counting users by role: {role.upper()}")
    return user_repo.count_users_by_role_repo(role)

def list_all_users_service() -> list[dict]:
    """List users with pagination."""
    logger.info("Listing all users...")
    return user_repo.list_all_users_repo()

def list_active_users_service() -> list[dict]:
    """List active users with pagination."""
    logger.info("Listing active users...")
    return user_repo.list_active_users_repo()

def verify_user_email_service(user_id: int) -> dict:
    """Verify a user's email."""
    logger.info("Verifying email of user with ID: {user_id}")
    return user_repo.verify_user_email_repo(user_id)

def unverify_user_email_service(user_id: int) -> dict:
    """Unverify a user's email."""
    logger.info("Unverifying email of user with ID: {user_id}")
    return user_repo.unverify_user_email_repo(user_id)

def list_verified_users_service() -> list[dict]:
    """List verified users."""
    logger.info("Listing verified users...")
    return user_repo.list_verified_users_repo()

def list_unverified_users_service() -> list[dict]:
    """List unverified users."""
    return user_repo.list_unverified_users_repo()

def count_active_users_service() -> int:
    """Count active users."""
    return user_repo.count_active_users_repo()

def count_verified_users_service() -> int:
    """Count verified users."""
    return user_repo.count_verified_users_repo()

def count_unverified_users_service() -> int:
    """Count unverified users."""
    return user_repo.count_unverified_users_repo()

def list_users_created_after_service(date: datetime) -> list[dict]:
    """List users created after a specific date."""
    return user_repo.list_users_created_after_repo(date)

def list_users_created_before_service(date: datetime) -> list[dict]:
    """List users created before a specific date."""
    return user_repo.list_users_created_before_repo(date)

def list_users_updated_after_service(date: datetime) -> list[dict]:
    """List users updated after a specific date."""
    return user_repo.list_users_updated_after_repo(date)

def list_users_updated_before_service(date: datetime) -> list[dict]:
    """List users updated before a specific date."""
    return user_repo.list_users_updated_before_repo(date)

def count_users_created_between_service(start_date: datetime, end_date: datetime) -> int:
    """Count users created between two dates."""
    return user_repo.count_users_created_between_repo(start_date, end_date)

def count_users_updated_between_service(start_date: datetime, end_date: datetime) -> int:
    """Count users updated between two dates."""
    return user_repo.count_users_updated_between_repo(start_date, end_date)