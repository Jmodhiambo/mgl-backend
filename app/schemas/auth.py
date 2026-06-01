#!/usr/bin/env python3
"""Auth schemas for MGLTickets."""

# from app.schemas.base import BaseModelEAT
from pydantic import BaseModel, EmailStr
from typing import Optional

class Login(BaseModel):

    email: EmailStr
    password: str

    class Config:
        from_attributes = True


class EmailVerifyRequest(BaseModel):
    token: str

    class Config:
        from_attributes = True


class ResendVerificationRequest(BaseModel):
    email: EmailStr

    class Config:
        from_attributes = True


class EmailVerifiyResponse(BaseModel):
    success: bool
    message: str
    user: Optional[dict] = None

    class Config:
        from_attributes = True


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for reset password request."""
    token: str
    new_password: str


class ReactivateAccountRequest(BaseModel):
    """Schema for reactivate account request."""
    email: EmailStr


class PasswordResetResponse(BaseModel):
    """Schema for password reset response."""
    success: bool
    message: str
