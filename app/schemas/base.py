#!/usr/bin/env python3
"""Base schemas for converting UTC to EAT."""

from pydantic import BaseModel, field_validator
from datetime import datetime
from app.utils.datetime import to_eat

class BaseModelEAT(BaseModel):
    """Base model that converts UTC datetime fields to EAT."""

    class Config:
        from_attributes = True

    @field_validator('*', mode='before')
    @classmethod
    def convert_utc_to_eat(cls, value):
        # Only convert datetime fields
        if isinstance(value, datetime):
            return to_eat(value)
        return value