#!/usr/bin/env python3
"""
Pydantic schemas for ContactMessage.
"""

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime


# ── Shared base ───────────────────────────────────────────────────────────────

class ContactMessageBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    subject: str
    category: str
    message: str

    class Config:
        from_attributes = True


# ── Create schemas ────────────────────────────────────────────────────────────

class ContactMessageCreate(ContactMessageBase):
    """Used by the user/public contact endpoint."""
    recaptcha_token: str

    @field_validator("name")
    @classmethod
    def name_min_length(cls, v: str) -> str:
        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()

    @field_validator("subject")
    @classmethod
    def subject_min_length(cls, v: str) -> str:
        if len(v.strip()) < 3:
            raise ValueError("Subject must be at least 3 characters")
        return v.strip()

    @field_validator("message")
    @classmethod
    def message_min_length(cls, v: str) -> str:
        if len(v.strip()) < 10:
            raise ValueError("Message must be at least 10 characters")
        return v.strip()
    
    class Config:
        from_attributes = True


class OrganizerContactMessageCreate(ContactMessageCreate):
    """
    Used by the organizer contact endpoint.
    Extends ContactMessageCreate with the optional event_title field.
    Storing the title (not the ID) means the admin can read it directly
    without making a separate event lookup.
    """
    event_title: Optional[str] = None


# ── Out schema ────────────────────────────────────────────────────────────────

class ContactMessageOut(ContactMessageBase):
    """Returned by all contact message endpoints and the admin list."""
    id: int
    reference_id: str
    source: str                           # "user" | "organizer"
    event_title: Optional[str] = None    # only populated for organizer messages; human-readable title
    user_id: Optional[int] = None
    status: str
    priority: str
    assigned_to: Optional[int] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    recaptcha_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    responded_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Update schema ─────────────────────────────────────────────────────────────

class ContactMessageUpdate(BaseModel):
    """Used by admin to update mutable fields on a contact message."""
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[int] = None
    responded_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Stats schema ──────────────────────────────────────────────────────────────

class ContactMessageStats(BaseModel):
    total: int
    new: int
    pending: int
    responded: int
    closed: int
    spam: int

    class Config:
        from_attributes = True

class ContactMessageStatusUpdate(BaseModel):
    """Schema for updating the status of a contact message."""
    status: str  # new | pending | responded | closed | spam

    class Config:
        from_attributes = True