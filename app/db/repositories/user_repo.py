#!/usr/bin/env python3
"""Async repository for User model operations."""

from sqlalchemy import select, func
from datetime import datetime
from app.db.models.user import User
from app.db.session import get_async_session
from typing import Optional
from app.schemas.user import UserOutWithPWD, UserPublic

async def create_user_repo(name: str, email: str, password_hash: str, phone_number: str) -> UserPublic:
    """Create a new user in the database."""
    async with get_async_session() as session:
        new_user = User(
            name=name,
            email=email,
            password_hash=password_hash,
            phone_number=phone_number,
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return UserPublic.model_validate(new_user)

async def get_user_by_email_repo(email: str) -> Optional[UserPublic]:
    """Retrieve a user by their email address."""
    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        return UserPublic.model_validate(user) if user else None
    
async def get_user_by_id_repo(user_id: int) -> Optional[UserPublic]:
    """Retrieve a user by their ID."""
    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()  # Returns None if no user found
        return UserPublic.model_validate(user) if user else None

async def get_user_with_password_by_id_repo(user_id: int) -> Optional[UserOutWithPWD]:
    """Retrieve a user by their ID including password hash."""
    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        return UserOutWithPWD.model_validate(user) if user else None

async def search_users_by_name_repo(name_substring: str) -> list[UserPublic]:
    """Search for users by a substring of their name."""
    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.name.ilike(f"%{name_substring}%")))
        users = result.scalars().all()
        return [UserPublic.model_validate(user) for user in users]

async def update_user_role_repo(user_id: int, new_role: str) -> Optional[UserPublic]:
    """Update the role of a user."""
    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.role = new_role
            await session.commit()
            await session.refresh(user)
            return UserPublic.model_validate(user)
        return None

async def deactivate_user_repo(user_id: int) -> Optional[UserPublic]:
    """Deactivate a user account."""
    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_active = False
            await session.commit()
            await session.refresh(user)
            return UserPublic.model_validate(user)
        return None

async def delete_user_repo(user_id: int) -> bool:
    """Delete a user from the database."""
    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            await session.delete(user)
            await session.commit()
            return True
        return False

async def list_all_users_repo() -> list[UserPublic]:
    """List all users in the database."""
    async with get_async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        return [UserPublic.model_validate(user) for user in users]

async def count_users_by_role_repo(role: str) -> int:
    """Count the number of users with a specific role."""
    async with get_async_session() as session:
        result = await session.execute(select(func.count()).select_from(User).where(User.role == role))
        return result.scalar_one()

async def update_user_info_repo(user_id: int, user_info: dict) -> Optional[UserPublic]:
    """Update user information."""
    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            for key, value in user_info.items():
                setattr(user, key, value)
            await session.commit()
            await session.refresh(user)
            return UserPublic.model_validate(user)
        return None

async def update_user_password_repo(user_id: int, new_password_hash: str) -> None:
    """Change the password of a user."""
    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.password_hash = new_password_hash
            await session.commit()

async def get_users_by_role_repo(role: str) -> list[UserPublic]:
    """Retrieve all users with a specific role."""
    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.role == role))
        users = result.scalars().all()
        return [UserPublic.model_validate(user) for user in users]

async def reactivate_user_repo(user_id: int) -> Optional[UserPublic]:
    """Reactivate a user account."""
    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_active = True
            await session.commit()
            await session.refresh(user)
            return UserPublic.model_validate(user)
        return None

async def verify_user_email_repo(user_id: int) -> Optional[UserPublic]:
    """Mark a user's email as verified."""
    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_verified = True
            await session.commit()
            await session.refresh(user)
            return UserPublic.model_validate(user)
        return None

async def unverify_user_email_repo(user_id: int) -> Optional[UserPublic]:
    """Mark a user's email as unverified."""
    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_verified = False
            await session.commit()
            await session.refresh(user)
            return UserPublic.model_validate(user)
        return None

async def list_active_users_repo() -> list[UserPublic]:
    """List all active users in the database."""
    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.is_active == True))
        users = result.scalars().all()
        return [UserPublic.model_validate(user) for user in users]

async def list_verified_users_repo() -> list[UserPublic]:
    """List all verified users in the database."""
    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.is_verified == True))
        users = result.scalars().all()
        return [UserPublic.model_validate(user) for user in users]

async def list_unverified_users_repo() -> list[UserPublic]:
    """List all unverified users in the database."""
    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.is_verified == False))
        users = result.scalars().all()
        return [UserPublic.model_validate(user) for user in users]

async def count_active_users_repo() -> int:
    """Count the number of active users."""
    async with get_async_session() as session:
        result = await session.execute(select(func.count()).select_from(User).where(User.is_active == True))
        return result.scalar_one()

async def count_verified_users_repo() -> int:
    """Count the number of verified users."""
    async with get_async_session() as session:
        result = await session.execute(select(func.count()).select_from(User).where(User.is_verified == True))
        return result.scalar_one()

async def count_unverified_users_repo() -> int:
    """Count the number of unverified users."""
    async with get_async_session() as session:
        result = await session.execute(select(func.count()).select_from(User).where(User.is_verified == False))
        return result.scalar_one()

async def list_users_created_after_repo(date_time: datetime) -> list[UserPublic]:
    """List all users created after a specific datetime."""
    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.created_at > date_time))
        users = result.scalars().all()
        return [UserPublic.model_validate(user) for user in users]

async def list_users_created_before_repo(date_time: datetime) -> list[UserPublic]:
    """List all users created before a specific datetime."""
    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.created_at < date_time))
        users = result.scalars().all()
        return [UserPublic.model_validate(user) for user in users]

async def list_users_updated_after_repo(date_time: datetime) -> list[UserPublic]:
    """List all users updated after a specific datetime."""
    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.updated_at > date_time))
        users = result.scalars().all()
        return [UserPublic.model_validate(user) for user in users]

async def list_users_updated_before_repo(date_time: datetime) -> list[UserPublic]:
    """List all users updated before a specific datetime."""
    async with get_async_session() as session:
        result = await session.execute(select(User).where(User.updated_at < date_time))
        users = result.scalars().all()
        return [UserPublic.model_validate(user) for user in users]

async def count_users_created_between_repo(start_datetime: datetime, end_datetime: datetime) -> int:
    """Count the number of users created between two datetimes."""
    async with get_async_session() as session:
        result = await session.execute(
            select(func.count()).select_from(User).where(
                User.created_at >= start_datetime,
                User.created_at <= end_datetime
            )
        )
        return result.scalar_one()

async def count_users_updated_between_repo(start_datetime: datetime, end_datetime: datetime) -> int:
    """Count the number of users updated between two datetimes."""
    async with get_async_session() as session:
        result = await session.execute(
            select(func.count()).select_from(User).where(
                User.updated_at >= start_datetime,
                User.updated_at <= end_datetime
            )
        )
        return result.scalar_one()
