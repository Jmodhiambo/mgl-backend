#!/usr/bin/env python
"""Generate reference ID for contact messages."""

import secrets
import string
from datetime import datetime


def generate_reference_id(category: str) -> str:
    """
    Generate unique reference ID.
    Format: MSG-{CATEGORY}-{DATE}-{RANDOM}
    Example: MSG-GEN-20260104-A1B2C3
    """
    category_code = category[:3].upper()
    date_str = datetime.now().strftime('%Y%m%d')
    random_str = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"MSG-{category_code}-{date_str}-{random_str}"