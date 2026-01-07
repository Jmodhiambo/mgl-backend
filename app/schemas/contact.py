#!/usr/bin/env python3
"""Schemas for ContactMessage model in MGLTickets."""

from datetime import datetime
from typing import Optional
from pydantic import EmailStr, field_validator
from app.schemas.base import BaseModelEAT


class ContactMessageBase(BaseModelEAT):
    """Base schema for ContactMessage."""
    name: str
    email: EmailStr
    phone: Optional[str] = None
    subject: str
    category: str
    message: str

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters long')
        return v.strip()

    @field_validator('subject')
    @classmethod
    def validate_subject(cls, v: str) -> str:
        if len(v.strip()) < 3:
            raise ValueError('Subject must be at least 3 characters long')
        return v.strip()

    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        if len(v.strip()) < 10:
            raise ValueError('Message must be at least 10 characters long')
        return v.strip()

    @field_validator('category')
    @classmethod
    def validate_category(cls, v: str) -> str:
        allowed_categories = [
            'general', 'support', 'billing', 'refund', 
            'organizer', 'partnership', 'feedback'
        ]
        if v not in allowed_categories:
            raise ValueError(f'Category must be one of: {", ".join(allowed_categories)}')
        return v


class ContactMessageCreate(ContactMessageBase):
    """Schema for creating a new ContactMessage."""
    recaptcha_token: str
    user_id: Optional[int] = None  # Set by backend if user is logged in


class ContactMessageOut(ContactMessageBase):
    """Schema for outputting ContactMessage data."""
    id: int
    reference_id: str
    user_id: Optional[int] = None
    status: str
    priority: str
    assigned_to: Optional[int] = None
    client_ip: Optional[str] = None
    recaptcha_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    responded_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ContactMessageUpdate(BaseModelEAT):
    """Schema for updating a ContactMessage (admin only)."""
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[int] = None
    responded_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed_statuses = ['new', 'responded', 'closed', 'spam']
            if v not in allowed_statuses:
                raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed_priorities = ['low', 'normal', 'high', 'urgent']
            if v not in allowed_priorities:
                raise ValueError(f'Priority must be one of: {", ".join(allowed_priorities)}')
        return v


class ContactMessageStats(BaseModelEAT):
    """Schema for contact message statistics."""
    total: int
    new: int
    responded: int
    closed: int
    spam: int
    
    class Config:
        from_attributes = True