#!/usr/bin/env python3
"""Auth schemas for MGLTickets."""

from app.schemas.base import BaseModelEAT
from pydantic import EmailStr
from typing import Optional

class Login(BaseModelEAT):

    email: EmailStr
    password: str

    class Config:
        from_attributes = True


class EmailVerifyRequest(BaseModelEAT):
    token: str

    class Config:
        from_attributes = True


class ResendVerificationRequest(BaseModelEAT):
    email: EmailStr

    class Config:
        from_attributes = True


class EmailVerifiyResponse(BaseModelEAT):
    success: bool
    message: str
    user: Optional[dict] = None

    class Config:
        from_attributes = True