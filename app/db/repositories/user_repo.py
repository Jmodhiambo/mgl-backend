#!/usr/bin/env python3
"""Repository for User model operations."""

from datetime import datetime
from app.db.models.user import User
from app.db.session import get_session
from typing import Optional
from app.schemas.user import UserOutWithPWD, UserPublic

def create_user_repo(name: str, email: str, password_hash: str, phone_number: str) -> UserPublic:
    """Create a new user in the database."""
    with get_session() as session:
        new_user = User(
            name=name,
            email=email,
            password_hash=password_hash,
            phone_number=phone_number,
        )
        session.add(new_user)
        session.commit()
        session.refresh(new_user)  # Refresh to get updated fields
        return UserPublic.model_validate(new_user)
    
def get_user_by_email_repo(email: str) -> Optional[UserPublic]:
    """Retrieve a user by their email address."""
    with get_session() as session:
        user = session.query(User).filter(User.email == email).first()
        return UserPublic.model_validate(user) if user else None
    
def get_user_by_id_repo(user_id: int) -> Optional[UserPublic]:
    """Retrieve a user by their ID."""
    with get_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        return UserPublic.model_validate(user) if user else None
    
def get_user_with_password_by_id_repo(user_id: int) -> Optional[UserOutWithPWD]:
    """Retrieve a user by their ID including password hash."""
    with get_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        return UserOutWithPWD.model_validate(user) if user else None
    
def search_users_by_name_repo(name_substring: str) -> list[UserPublic]:
    """Search for users by a substring of their name."""
    with get_session() as session:
        users = session.query(User).filter(User.name.ilike(f"%{name_substring}%")).all()
        return [UserPublic.model_validate(user) for user in users]
    
def update_user_role_repo(user_id: int, new_role: str) -> Optional[UserPublic]:
    """Update the role of a user."""
    with get_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.role = new_role
            session.commit()
            session.refresh(user)
            return UserPublic.model_validate(user)
        return None
    
def deactivate_user_repo(user_id: int) -> Optional[UserPublic]:
    """Deactivate a user account."""
    with get_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.is_active = False
            session.commit()
            session.refresh(user)
            return UserPublic.model_validate(user)
        return None
    
def delete_user_repo(user_id: int) -> bool:
    """Delete a user from the database."""
    with get_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            session.delete(user)
            session.commit()
            return True
        return False
    
def list_all_users_repo() -> list[UserPublic]:
    """List all users in the database."""
    with get_session() as session:
        users = session.query(User).all()
        return [UserPublic.model_validate(user) for user in users]
    
def count_users_by_role_repo(role: str) -> int:
    """Count the number of users with a specific role."""
    with get_session() as session:
        count = session.query(User).filter(User.role == role).count()
        return count
    
def update_user_info_repo(user_id: int, user_info: dict) -> Optional[UserPublic]:
    """Update user information."""
    with get_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            for key, value in user_info.items():
                setattr(user, key, value)
            session.commit()
            session.refresh(user)
            return UserPublic.model_validate(user)
        return None
    
def update_user_password_repo(user_id: int, new_password_hash: str) -> None:
    """Change the password of a user."""
    with get_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.password_hash = new_password_hash
            session.commit()
        # No need to refresh since we are not returning the user object
 
def get_users_by_role_repo(role: str) -> list[UserPublic]:
    """Retrieve all users with a specific role."""
    with get_session() as session:
        users = session.query(User).filter(User.role == role).all()
        return [UserPublic.model_validate(user) for user in users]
    
def reactivate_user_repo(user_id: int) -> Optional[UserPublic]:
    """Reactivate a user account."""
    with get_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.is_active = True
            session.commit()
            session.refresh(user)
            return UserPublic.model_validate(user)
        return None
    
def verify_user_email_repo(user_id: int) -> Optional[UserPublic]:
    """Mark a user's email as verified."""
    with get_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.is_verified = True
            session.commit()
            session.refresh(user)
            return UserPublic.model_validate(user)
        return None
    
def unverify_user_email_repo(user_id: int) -> Optional[UserPublic]:
    """Mark a user's email as unverified."""
    with get_session() as session:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.is_verified = False
            session.commit()
            session.refresh(user)
            return UserPublic.model_validate(user)
        return None
    
def list_active_users_repo() -> list[UserPublic]:
    """List all active users in the database."""
    with get_session() as session:
        users = session.query(User).filter(User.is_active == True).all()
        return [UserPublic.model_validate(user) for user in users]
    
def list_verified_users_repo() -> list[UserPublic]:
    """List all verified users in the database."""
    with get_session() as session:
        users = session.query(User).filter(User.is_verified == True).all()
        return [UserPublic.model_validate(user) for user in users]
    
def list_unverified_users_repo() -> list[UserPublic]:
    """List all unverified users in the database."""
    with get_session() as session:
        users = session.query(User).filter(User.is_verified == False).all()
        return [UserPublic.model_validate(user) for user in users]
    
def count_active_users_repo() -> int:
    """Count the number of active users."""
    with get_session() as session:
        count = session.query(User).filter(User.is_active == True).count()
        return count
    
def count_verified_users_repo() -> int:
    """Count the number of verified users."""
    with get_session() as session:
        count = session.query(User).filter(User.is_verified == True).count()
        return count
    
def count_unverified_users_repo() -> int:
    """Count the number of unverified users."""
    with get_session() as session:
        count = session.query(User).filter(User.is_verified == False).count()
        return count
    
def list_users_created_after_repo(date_time: datetime) -> list[UserPublic]:
    """List all users created after a specific datetime."""
    with get_session() as session:
        users = session.query(User).filter(User.created_at > date_time).all()
        return [UserPublic.model_validate(user) for user in users]
    
def list_users_created_before_repo(date_time: datetime) -> list[UserPublic]:
    """List all users created before a specific datetime."""
    with get_session() as session:
        users = session.query(User).filter(User.created_at < date_time).all()
        return [UserPublic.model_validate(user) for user in users]
    
def list_users_updated_after_repo(date_time: datetime) -> list[UserPublic]:
    """List all users updated after a specific datetime."""
    with get_session() as session:
        users = session.query(User).filter(User.updated_at > date_time).all()
        return [UserPublic.model_validate(user) for user in users]
    
def list_users_updated_before_repo(date_time: datetime) -> list[UserPublic]:
    """List all users updated before a specific datetime."""
    with get_session() as session:
        users = session.query(User).filter(User.updated_at < date_time).all()
        return [UserPublic.model_validate(user) for user in users]
    
def count_users_created_between_repo(start_datetime: datetime, end_datetime: datetime) -> int:
    """Count the number of users created between two datetimes."""
    with get_session() as session:
        count = session.query(User).filter(
            User.created_at >= start_datetime,
            User.created_at <= end_datetime
        ).count()
        return count
    
def count_users_updated_between_repo(start_datetime: datetime, end_datetime: datetime) -> int:
    """Count the number of users updated between two datetimes."""
    with get_session() as session:
        count = session.query(User).filter(
            User.updated_at >= start_datetime,
            User.updated_at <= end_datetime
        ).count()
        return count