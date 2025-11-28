#!/usr/bin/env python3
"""Schemas for User model in MGLTickets."""

from datetime import datetime
from pydantic import EmailStr
from typing import Optional
from app.schemas.base import BaseModelEAT
# from app.schemas.event import EventOut

class UserOut(BaseModelEAT):
    """Schema for outputting User data."""
    id: int
    name: str
    email: EmailStr
    phone_number: str
    role: str
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # events: Optional[list["EventOut"]] = []

    class Config:
        from_attributes = True

class OrganizerInfo(UserOut):
    """Schema for outputting Organizer data."""
    bio: Optional[str] = None
    organization_name: Optional[str] = None
    website: Optional[str] = None
    profile_picture: Optional[str] = None
    address: Optional[str] = None
    area_of_specialty: Optional[str] = None

    class Config:
        from_attributes = True

class OrganizerOut(UserOut):
    """Schema for outputting User data."""
    organizer_info: Optional["OrganizerInfo"] = None

    class Config:
        from_attributes = True

class UserOutWithPWD(UserOut):
    """Schema for outputting User data with password."""
    password_hash: str

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
    password: Optional[str] = None
    phone_number: Optional[str] = None
    role: Optional[str] = None
    is_verified: Optional[bool] = None

    class Config:
        from_attributes = True