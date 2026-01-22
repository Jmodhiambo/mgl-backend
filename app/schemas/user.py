#!/usr/bin/env python3
"""Schemas for User model in MGLTickets."""

from datetime import datetime
from pydantic import EmailStr
from typing import Optional
from app.schemas.base import BaseModelEAT

class UserOut(BaseModelEAT):
    """Schema for outputting User data."""
    id: int
    name: str
    email: EmailStr
    phone_number: str
    role: str
    email_verified: bool
    email_verification_token_expires: Optional[datetime]
    is_active: bool
    password_reset_token_expires: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
    
class UserCreate(BaseModelEAT):
    """Schema for creating a new User."""
    name: str
    email: EmailStr
    password: str
    phone_number: str

    class Config:
        from_attributes = True

class UserUpdate(BaseModelEAT):
    """Schema for updating an existing User."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    role: Optional[str] = None

    class Config:
        from_attributes = True


class OrganizerCreate(BaseModelEAT):
    """Schema for creating a new Organizer."""
    bio: Optional[str] = None
    organization_name: Optional[str] = None
    website_url: Optional[str] = None
    social_media_links: Optional[list[str]] = None
    area_of_expertise: Optional[list[str]] = None

    class Config:
        from_attributes = True

class OrganizerUpdate(UserUpdate):
    """Schema for updating an existing Organizer."""
    bio: Optional[str] = None
    organization_name: Optional[str] = None
    website_url: Optional[str] = None
    social_media_links: Optional[list[str]] = None
    area_of_expertise: Optional[list[str]] = None

    class Config:
        from_attributes = True

class OrganizerInfo(BaseModelEAT):
    """Schema for outputting Organizer data."""
    bio: Optional[str] = None
    organization_name: Optional[str] = None
    website_url: Optional[str] = None
    profile_picture_url: Optional[str] = None
    social_media_links: Optional[list[str]] = None
    area_of_expertise: Optional[list[str]] = None

    class Config:
        from_attributes = True

class OrganizerOut(UserOut):
    """Schema for outputting User data."""
    organizer_info: Optional["OrganizerInfo"] = None

    class Config:
        from_attributes = True

class UserPublic(UserOut, OrganizerInfo):
    """Schema for public User data. Includes organizer info if applicable."""
    class Config:
        from_attributes = True

class UserOutWithPWD(UserOut):
    """Schema for outputting User data with password."""
    password_hash: str

    class Config:
        from_attributes = True

class UserPasswordChange(BaseModelEAT):
    """Schema for updating an existing User."""
    old_password: str
    new_password: str

    class Config:
        from_attributes = True

class UserPasswordUpdate(BaseModelEAT):
    """Schema for updating an existing User's password."""
    new_password: str

    class Config:
        from_attributes = True

class UserEmailVerification(BaseModelEAT):
    """Schema for verifying a User's email."""
    token: str

    class Config:
        from_attributes = True