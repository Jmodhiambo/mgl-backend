#!/usr/bin/env python3
"""Auth schemas for MGLTickets."""

from app.schemas.base import BaseModelEAT
from pydantic import EmailStr

class Login(BaseModelEAT):

    email: EmailStr
    password: str

    class Config:
        from_attributes = True