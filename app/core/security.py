#!/usr/bin/env python3
"""Security for MGLTickets."""

from datetime import datetime, timedelta

from fastapi import Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.core.config import SECRET_KEY, ALGORITHM
from app.schemas.user import UserOut, UserPublic

# FastAPI security scheme
bearer_scheme = HTTPBearer()

def create_access_token(user_id: int, expires_minutes: int = 60) -> str:
    """Create a signed JWT."""
    if not "user_id":
        raise ValueError("Token payload must contain user_id")
    
    payload = {
        "id": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=expires_minutes)
    }

    return jwt.encode(payload, str(SECRET_KEY), algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT."""
    try:
        payload = jwt.decode(token, str(SECRET_KEY), algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from e

def get_current_user(
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
        return None

    payload = decode_access_token(token)
    
    user_id = payload.get("id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    
    user = get_user_by_id_service(user_id)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Attach user to request state - picked up by logging middleware
    request.state.user = user

    return user

def require_user(user=Depends(get_current_user)) -> UserOut:
    """Require user to be authenticated to access this route."""
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required to access this route.")
    return user

def require_organizer(user=Depends(get_current_user)) -> UserPublic:
    """Require user to be at least an organizer to access this route."""
    if user.role != "organizer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You must be an organizer to access this route.")
    return user

def require_admin(user=Depends(get_current_user)) -> UserPublic:
    """Require user to be an admin to access this route."""
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You must be an admin to access this route.")
    return user

def require_superadmin(user=Depends(get_current_user)) -> UserPublic:
    """Require user to be a superadmin to access this route."""
    if user.role != "sysadmin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You must be a superadmin to access this route.")
    return user