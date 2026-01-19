#!/usr/bin/env python3
"""Email verification utils for MGLTickets."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

def generate_verification_token() -> str:
    """Generate a secure random verification token"""
    return secrets.token_urlsafe(32)

def create_verification_token_expiry(hours: int = 24) -> datetime:
    """Create expiration time for verification token (default 24 hours)"""
    return datetime.now(timezone.utc) + timedelta(hours=hours)

def is_token_expired(expires_at: Optional[datetime]) -> bool:
    """Check if verification token has expired"""
    if not expires_at:
        return True
    return datetime.now(timezone.utc) > expires_at