#!/usr/bin/env python3
"""Schemas for User model in MGLTickets."""

import json
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional


def _decode_json_list(value):
    """
    Shared validator: the User.social_media_links / User.area_of_expertise
    columns are plain VARCHAR — not JSON or ARRAY — so whatever lands in
    them from a DB read arrives as a JSON-encoded string (e.g. '[]' or
    '["https://..."]'), never a real Python list.

    Every schema below that types these fields as Optional[list[str]] needs
    this decode step, or Pydantic raises "Input should be a valid list"
    whenever a raw User row (string column) is validated straight into one
    of these schemas — which is exactly what UserPublic.model_validate(user)
    does inside update_user_info_repo.

    Accepts None, an already-decoded list (so constructing the schema
    directly from Python code, e.g. in a service layer, still works), or a
    JSON-encoded string. Anything else is left for Pydantic's normal type
    validation to reject with its standard error.
    """
    if value is None or isinstance(value, list):
        return value
    if isinstance(value, str):
        if value.strip() == "":
            return None
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return value  # let Pydantic raise its normal type error
        return decoded
    return value


class UserOut(BaseModel):
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
    
class UserCreate(BaseModel):
    """Schema for creating a new User."""
    name: str
    email: EmailStr
    password: str
    phone_number: str

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    """Schema for updating an existing User."""
    name: Optional[str] = None
    # email: Optional[EmailStr] = None
    phone_number: Optional[str] = None

    class Config:
        from_attributes = True

class OrganizerCreate(BaseModel):
    """Schema for creating a new Organizer."""
    bio: Optional[str] = None
    organization_name: Optional[str] = None
    website_url: Optional[str] = None
    social_media_links: Optional[list[str]] = None
    area_of_expertise: Optional[list[str]] = None

    @field_validator("social_media_links", "area_of_expertise", mode="before")
    @classmethod
    def _decode_lists(cls, value):
        return _decode_json_list(value)

    class Config:
        from_attributes = True

class OrganizerUpdate(UserUpdate):
    """Schema for updating an existing Organizer."""
    bio: Optional[str] = None
    organization_name: Optional[str] = None
    website_url: Optional[str] = None
    social_media_links: Optional[list[str]] = None
    area_of_expertise: Optional[list[str]] = None

    @field_validator("social_media_links", "area_of_expertise", mode="before")
    @classmethod
    def _decode_lists(cls, value):
        return _decode_json_list(value)

    class Config:
        from_attributes = True

class OrganizerInfo(BaseModel):
    """Schema for outputting Organizer data."""
    bio: Optional[str] = None
    organization_name: Optional[str] = None
    website_url: Optional[str] = None
    profile_picture_url: Optional[str] = None
    social_media_links: Optional[list[str]] = None
    area_of_expertise: Optional[list[str]] = None

    @field_validator("social_media_links", "area_of_expertise", mode="before")
    @classmethod
    def _decode_lists(cls, value):
        return _decode_json_list(value)

    class Config:
        from_attributes = True

class OrganizerOut(UserOut, OrganizerInfo):
    """
    Schema for outputting User data, with organizer fields flattened
    directly onto the same object — bio, organization_name, website_url,
    profile_picture_url, social_media_links, area_of_expertise all live at
    the top level, exactly like UserPublic.

    Previously this nested organizer fields under an `organizer_info`
    sub-object, which required a model_validator to assemble that nested
    object from the User row's flat columns. That validator had to account
    for three different input shapes (dict, raw ORM row, another flattened
    Pydantic model like UserPublic being re-validated at the FastAPI
    response-serialization boundary) and was a recurring source of bugs.
    Flattening removes the need for that validator entirely — from_attributes
    extraction now works the same way it already does for UserPublic.
    """

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

class UserPasswordChange(BaseModel):
    """Schema for updating an existing User."""
    old_password: str
    new_password: str

    class Config:
        from_attributes = True

class UserPasswordUpdate(BaseModel):
    """Schema for updating an existing User's password."""
    new_password: str

    class Config:
        from_attributes = True

class UserEmailVerification(BaseModel):
    """Schema for verifying a User's email."""
    token: str

    class Config:
        from_attributes = True

class UserOrganizerProfileOut(BaseModel):
    """Schema for outputting organizer profile data. Shows whether they have completed their organizer profile or not."""
    profile_completed: bool
    missing_fields: list[str] = []

    class Config:
        from_attributes = True

class AdminMeOut(BaseModel):
    """Schema for outputting Admin's own data."""
    id: int
    name: str
    email: EmailStr
    phone_number: str
    role: str
    is_active: bool
    email_verified: bool
    bio: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AdminMeUpdate(BaseModel):
    """Schema for updating Admin's own data."""
    name: Optional[str] = None
    phone_number: Optional[str] = None
    bio: Optional[str] = None

    class Config:
        from_attributes = True

class AdminUserEmailUpdate(BaseModel):
    """Schema for updating a User's email by an Admin."""
    user_id: int
    new_email: EmailStr

    class Config:
        from_attributes = True