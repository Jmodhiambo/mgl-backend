#!/usr/bin/env python3
"""User-related services for MGLTickets."""

import asyncio
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from passlib.hash import argon2

from app.core.config import FRONTEND_URL
from app.core.logging_config import logger
from app.emails.email_manager import email_manager
from app.schemas.organizer import DashboardStats
from app.schemas.user import UserOut, UserPublic, UserUpdate
from app.services.ref_session_services import cleanup_user_sessions_service
from app.utils.token_verification import (
    create_verification_token_expiry,
    generate_verification_token,
    is_token_expired,
)
import app.db.repositories.booking_repo as booking_repo
import app.db.repositories.event_repo as event_repo
import app.db.repositories.user_repo as user_repo

# ── Email background helper ───────────────────────────────────────────────────
 
def _bg_email(coro) -> None:
    """
    Schedule an email coroutine as a background task.
    Falls back to direct await if no running event loop exists (tests, CLI).
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        asyncio.run(coro)
    except Exception as e:
        logger.error(f"Error sending email: {e}")

# ─── Registration ─────────────────────────────────────────────────────────────

async def register_user_service(
    name: str, email: str, password: str, phone_number: str
) -> dict:
    """Create a new user, send verification email."""
    logger.info("Registering user...")

    if len(name) < 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name must be at least 3 characters long.")
    if "@" not in email or "." not in email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format.")
    if len(password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters long.")
    if await user_repo.get_user_by_email_repo(email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists.")

    password_hash = argon2.hash(password)
    token = generate_verification_token()
    expires_at = create_verification_token_expiry(hours=24)
    user = await user_repo.create_user_repo(name, email, password_hash, phone_number, token, expires_at)

    logger.info(f"User {user.name} with ID {user.id} registered successfully.")

    _bg_email(email_manager.send_from_template(
        template_id="user.verification",
        to_email=user.email,
        variables={
            "name": user.name,
            "verification_url": f"{FRONTEND_URL}/verify?token={token}",
        },
    ))

    return user


# ─── Authentication ───────────────────────────────────────────────────────────

async def authenticate_user_service(user_id: int, email: str, password: str) -> dict:
    """Authenticate a user and return the user."""
    logger.info(f"Authenticating user with ID: {user_id}")

    if "@" not in email or "." not in email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format.")

    user = await user_repo.get_user_with_password_by_id_repo(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found. Auth Request Failed.")
    if not argon2.verify(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password.")

    return user.__dict__.pop("password_hash")


# ─── Lookup ───────────────────────────────────────────────────────────────────

async def get_user_by_email_service(email: str) -> Optional[dict]:
    """Retrieve a user by email."""
    user = await user_repo.get_user_by_email_repo(email)
    if not user:
        logger.error("User not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User with the email not found.")
    return user


async def get_user_by_id_service(user_id: int) -> Optional[UserPublic]:
    """Retrieve a user by ID."""
    logger.info(f"Getting user by ID for user with ID: {user_id}")
    return await user_repo.get_user_by_id_repo(user_id)


async def search_users_by_name_service(name_query: str) -> list[dict]:
    """Search users by name."""
    logger.info(f"Searching users by name: {name_query}")
    return await user_repo.search_users_by_name_repo(name_query)


# ─── Role management ──────────────────────────────────────────────────────────

async def update_user_role_service(user_id: int, new_role: str) -> dict:
    """Promote or demote a user role."""
    user = await user_repo.get_user_by_id_repo(user_id)
    if not user:
        logger.error(f"User not found. Updating role for user with ID {user_id} failed.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.role == new_role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{new_role.title()} with ID {user_id} is already {new_role}.")

    logger.info(f"Updating role of user with ID {user_id} to {new_role}.")
    return await user_repo.update_user_role_repo(user_id, new_role)


# ─── Profile updates ──────────────────────────────────────────────────────────

async def update_user_info_service(user_id: int, info: dict) -> dict:
    """Update a user's contact information."""
    logger.info(f"Updating contact information of user with ID: {user_id}")

    if info.get("email"):
        if "@" not in info["email"] or "." not in info["email"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format.")

        existing = await user_repo.get_user_by_email_repo(info["email"])
        if existing and existing.id != user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"The email {info['email']} already exists! Please use a different email.")
        if existing and existing.role == "admin":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin email addresses cannot be changed. Please contact support.")

        info["email_verified"] = False

    user = await user_repo.update_user_info_repo(user_id, info)

    if info.get("email"):
        _bg_email(email_manager.send_from_template(
            template_id="user.verification",
            to_email=info["email"],
            variables={
                "name": user.name,
                "verification_url": f"{FRONTEND_URL}/verify?token={user.email_verification_token}",
            },
        ))

    return user


async def delete_user_service(user_id: int) -> bool:
    """Delete a user by ID."""
    logger.info(f"Deleting user with ID: {user_id}")
    return await user_repo.delete_user_repo(user_id)


# ─── Password management ──────────────────────────────────────────────────────

async def update_user_password_service(user_id: int, new_password: str) -> None:
    """Update a user's password (admin-initiated, no old password check)."""
    if len(new_password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters long.")

    user = await user_repo.get_user_with_password_by_id_repo(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found here.")

    if argon2.verify(new_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password cannot be the same as the current password.")

    logger.info(f"Updating password of user with ID: {user_id}")
    new_password_hash = argon2.hash(new_password)
    await user_repo.update_user_password_repo(user_id, new_password_hash)


async def change_user_password_service(
    user_id: int, old_password: str, new_password: str
) -> None:
    """Self-service password change — verifies old password, notifies by email."""
    user = await user_repo.get_user_with_password_by_id_repo(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found in the database.")
    if not argon2.verify(old_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect.")

    await update_user_password_service(user_id, new_password)
    logger.info(f"Password changed successfully for user with ID: {user_id}")

    # Fetch the full user for email (get_user_with_password doesn't include email on all impls)
    full_user = await user_repo.get_user_by_id_repo(user_id)
    _bg_email(email_manager.send_from_template(
        template_id="user.password_changed",
        to_email=full_user.email,
        variables={
            "name": full_user.name,
            "email": full_user.email,
            "changed_at": datetime.now(timezone.utc).strftime("%d %b %Y at %H:%M UTC"),
            "login_url": f"{FRONTEND_URL}/login",
        },
    ))


# ─── Email verification ───────────────────────────────────────────────────────

async def verify_user_email_service(token: str) -> dict:
    """Verify a user's email with token."""
    logger.info(f"Email verification attempt with token: {token[:10]}...")

    user = await user_repo.get_user_by_verification_token_repo(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token.")

    if user.email_verified:
        return {
            "success": True,
            "message": "Email already verified. You can log in now.",
            "user": {"email": user.email, "name": user.name},
        }

    if is_token_expired(user.email_verification_token_expires):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Verification token expired. Please request a new one.")

    verified_user = await user_repo.verify_user_email_repo(user.id)
    logger.info(f"Email verified successfully for user: {verified_user.email}")

    return {
        "success": True,
        "message": "Email verified successfully! You can now log in.",
        "user": {"email": verified_user.email, "name": verified_user.name},
    }


async def admin_force_verify_email_service(user_id: int) -> dict:
    """
    Mark a user's email as verified without requiring their original
    verification token.
 
    NEW — added to support the admin CLI's `users force-verify-email`
    command. There was previously no service exposing
    user_repo.verify_user_email_repo() without going through the
    token-based verify_user_email_service() flow above, which is the
    right path for self-service verification but unusable for an admin
    helping a user whose token expired or whose email never arrived.
 
    If the web admin console ever needs this too (e.g. a "force verify"
    button on the user detail page), it can call this same function —
    no router currently exposes it.
    """
    logger.info(f"Admin force-verifying email for user_id={user_id}")
    user = await user_repo.verify_user_email_repo(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


async def resend_verification_email_service(user_id: int) -> dict:
    """Resend a verification email."""
    logger.info(f"Resending verification email to user with ID: {user_id}")

    user = await user_repo.get_user_by_id_repo(user_id)
    if not user:
        return {"success": True, "message": "If an account exists with this email, a verification link has been sent."}

    if user.email_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already verified.")

    new_token = generate_verification_token()
    expires_at = create_verification_token_expiry(hours=24)
    await user_repo.update_verification_token_repo(user.id, new_token, expires_at)

    _bg_email(email_manager.send_from_template(
        template_id="user.verification",
        to_email=user.email,
        variables={
            "name": user.name,
            "verification_url": f"{FRONTEND_URL}/verify-email?token={new_token}",
        },
    ))

    return {"success": True, "message": "Verification email sent! Please check your inbox."}


async def unverify_user_email_service(user_id: int) -> dict:
    """Unverify a user's email (admin action)."""
    logger.info(f"Unverifying email of user with ID: {user_id}")
    return await user_repo.unverify_user_email_repo(user_id)


# ─── Password reset ───────────────────────────────────────────────────────────

async def request_password_reset_service(email: str) -> dict:
    """Request a password reset link."""
    logger.info(f"Password reset requested for email: {email}")

    user = await user_repo.get_user_by_email_repo(email)
    if not user or not user.is_active:
        return {"success": True, "message": "If an account exists with this email, a password reset link has been sent. Please check your inbox."}

    reset_token = generate_verification_token()
    expires_at = create_verification_token_expiry(hours=1)
    await user_repo.update_password_reset_token_repo(user.id, reset_token, expires_at)

    _bg_email(email_manager.send_from_template(
        template_id="user.password_reset",
        to_email=user.email,
        variables={
            "name": user.name,
            "reset_url": f"{FRONTEND_URL}/reset-password?token={reset_token}",
        },
    ))

    return {"success": True, "message": "If an account exists with this email, a password reset link has been sent. Please check your inbox."}


async def reset_password_with_token_service(token: str, new_password: str) -> dict:
    """Reset password using a valid reset token."""
    logger.info(f"Password reset attempt with token: {token[:10]}...")

    if len(new_password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters long.")

    user = await user_repo.get_user_by_password_reset_token_repo(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired password reset token.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive. Please contact support.")
    if is_token_expired(user.password_reset_token_expires):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Password reset token has expired. Please request a new one.")

    user_with_pwd = await user_repo.get_user_with_password_by_id_repo(user.id)
    if argon2.verify(new_password, user_with_pwd.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password cannot be the same as your current password.")

    new_password_hash = argon2.hash(new_password)
    await user_repo.update_user_password_repo(user.id, new_password_hash)
    await user_repo.clear_password_reset_token_repo(user.id)

    logger.info(f"Password reset successfully for user: {user.email}")

    _bg_email(email_manager.send_from_template(
        template_id="user.password_changed",
        to_email=user.email,
        variables={
            "name": user.name,
            "email": user.email,
            "changed_at": datetime.now(timezone.utc).strftime("%d %b %Y at %H:%M UTC"),
            "login_url": f"{FRONTEND_URL}/login",
        },
    ))

    return {"success": True, "message": "Password has been reset successfully. You can now log in with your new password."}


# ─── Account lifecycle ────────────────────────────────────────────────────────

async def deactivate_user_service(user_id: int) -> None:
    """Deactivate a user account and notify them."""
    logger.info(f"Deactivating a user account with ID: {user_id}")

    # Fetch user before deactivation so we have their name/email
    user = await user_repo.get_user_by_id_repo(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account deactivation failed.")

    response = await user_repo.deactivate_user_repo(user_id)
    if not response:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account deactivation failed.")

    logger.info(f"User account with ID: {user_id} has been deactivated.")

    _bg_email(email_manager.send_from_template(
        template_id="user.account_deactivated",
        to_email=user.email,
        variables={"name": user.name},
    ))


async def reactivate_account_service(email: str) -> dict:
    """Reactivate a deactivated user account."""
    logger.info(f"Account reactivation requested for email: {email}")

    if "@" not in email or "." not in email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format.")

    user = await user_repo.get_user_by_email_repo(email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account is already active. Please log in.")

    await user_repo.reactivate_user_repo(user.id)
    logger.info(f"Account reactivated successfully for user: {email}")

    _bg_email(email_manager.send_from_template(
        template_id="user.account_reactivation",
        to_email=user.email,
        variables={
            "name": user.name,
            "login_url": f"{FRONTEND_URL}/login",
        },
    ))

    return {"success": True, "message": "Your account has been reactivated successfully. You can now log in."}


# ─── Listing / counting ───────────────────────────────────────────────────────

async def list_all_users_service() -> list[dict]:
    logger.info("Listing all users...")
    return await user_repo.list_all_users_repo()


async def list_active_users_service() -> list[dict]:
    logger.info("Listing active users...")
    return await user_repo.list_active_users_repo()


async def list_verified_users_service() -> list[dict]:
    logger.info("Listing verified users...")
    return await user_repo.list_verified_users_repo()


async def list_unverified_users_service() -> list[dict]:
    return await user_repo.list_unverified_users_repo()


async def count_users_by_role_service(role: str) -> int:
    logger.info(f"Counting users by role: {role.upper()}")
    return await user_repo.count_users_by_role_repo(role)


async def count_active_users_service() -> int:
    return await user_repo.count_active_users_repo()


async def count_verified_users_service() -> int:
    return await user_repo.count_verified_users_repo()


async def count_unverified_users_service() -> int:
    return await user_repo.count_unverified_users_repo()


async def list_users_created_after_service(date: datetime) -> list[dict]:
    return await user_repo.list_users_created_after_repo(date)


async def list_users_created_before_service(date: datetime) -> list[dict]:
    return await user_repo.list_users_created_before_repo(date)


async def list_users_updated_after_service(date: datetime) -> list[dict]:
    return await user_repo.list_users_updated_after_repo(date)


async def list_users_updated_before_service(date: datetime) -> list[dict]:
    return await user_repo.list_users_updated_before_repo(date)


async def count_users_created_between_service(start_date: datetime, end_date: datetime) -> int:
    return await user_repo.count_users_created_between_repo(start_date, end_date)


async def count_users_updated_between_service(start_date: datetime, end_date: datetime) -> int:
    return await user_repo.count_users_updated_between_repo(start_date, end_date)