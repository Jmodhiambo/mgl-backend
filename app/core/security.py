#!/usr/bin/env python3
"""Security for MGLTickets."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.core.config import SECRET_KEY, ALGORITHM
from app.schemas.user import UserOut, UserPublic

# Token hashing
import hmac
import hashlib
import base64

# FastAPI security scheme
# Auto-error is set to false because we want to handle errors ourselves
bearer_scheme = HTTPBearer(auto_error=False)  # Makes it optional

ROLE_ORGANIZER = "organizer"
ROLE_ADMIN = "admin"
ROLE_SYSADMIN = "sysadmin"
ENCODED_SECRET_KEY = str(SECRET_KEY).encode("utf-8")  # Convert to bytes from Secret object

def create_access_token(user_id: int) -> str:
    """Create an access token valid for 15 minutes."""
    if not user_id:
        raise ValueError("Token payload must contain user_id")
    
    payload = {
        "id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15)
    }

    return jwt.encode(payload, str(SECRET_KEY), algorithm=ALGORITHM)

def create_refresh_token(user_id: int, session_id: str) -> str:
    """Create refresh token valid for 7 days."""
    if not user_id:
        raise ValueError("Token payload must contain user_id")
    
    payload = {
        "id": user_id,
        "sid": session_id,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }

    return jwt.encode(payload, str(SECRET_KEY), algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode and verify a JWT."""
    try:
        payload = jwt.decode(token, str(SECRET_KEY), algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from e

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> UserPublic:
    """
    Extract token from Authorization header, decode it, load user,
    and attach user to request.state.
    """
    from app.services.user_services import get_user_by_id_service
    
    # Extract token from Authorization header which is credetials in this case
    token = credentials.credentials

    if not token:
        request.state.user = None
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No token provided")

    payload = decode_token(token)
    
    user_id = payload.get("id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    
    user = await get_user_by_id_service(user_id)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive. Please contact support.")

    # Attach user to request state - picked up by logging middleware
    request.state.user = user

    return user

async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Optional[UserPublic]:
    """
    Same as get_current_user, but returns None if user is not authenticated.
    Good for routes that require optional authentication like articles.
    """
    if not credentials:
        return None
    return await get_current_user(request, credentials)

def require_user(user=Depends(get_current_user)) -> UserOut:
    """Require user to be authenticated to access this route."""
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required to access this route.")
    return user

def require_organizer(user=Depends(get_current_user)) -> UserPublic:
    """Require user to be at least an organizer to access this route."""
    if user.role != ROLE_ORGANIZER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You must be an organizer to access this route.")
    return user

def require_admin(user=Depends(get_current_user)) -> UserPublic:
    """Require user to be an admin to access this route."""
    if user.role != ROLE_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You must be an admin to access this route.")
    return user

def require_superadmin(user=Depends(get_current_user)) -> UserPublic:
    """Require user to be a superadmin to access this route."""
    if user.role != ROLE_SYSADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You must be a superadmin to access this route.")
    return user

def hash_token(token: str) -> str:
    """
    Hash a token using HMAC-SHA256.
    Returns a base64-encoded string.
    """
    digest = hmac.new(ENCODED_SECRET_KEY, token.encode("utf-8"), hashlib.sha256).digest()
    # Encode digest to URL-safe Base64
    return base64.urlsafe_b64encode(digest).decode("utf-8")


def verify_token(token: str, refresh_token_hash: str) -> bool:
    """
    Verify a token using HMAC-SHA256.
    Returns True if the token is valid, False otherwise.
    """
    hashed_token = hash_token(token)
    return hmac.compare_digest(hashed_token, refresh_token_hash)