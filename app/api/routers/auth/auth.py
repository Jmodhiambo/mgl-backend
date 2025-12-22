#!/usr/bin/env python3
"""Auth routes for MGLTickets."""
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status, Depends, Response, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.user import UserCreate, UserOut

from app.services.user_services import (
    get_user_by_email_service,
    authenticate_user_service,
    register_user_service,
)
from app.services.ref_session_services import (
    create_refresh_session_service,
    get_refresh_session_service,
    update_refresh_session_service,
    delete_refresh_session_service
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
    verify_token,
    require_user
)

router = APIRouter()

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """
    Register a new user.
    """
    user = await register_user_service(
        user_data.name,
        user_data.email,
        user_data.password,
        user_data.phone_number
    )
    return user

@router.post("/auth/login", response_model=dict, status_code=status.HTTP_200_OK)
async def login(response: Response, form: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate user and return an access token along with a refresh token cookie.
    """
    # OAuth2PasswordRequestForm has username and password, so email in this case is username.
    email = form.username
    user = await get_user_by_email_service(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not await authenticate_user_service(user.id, email, form.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
    )

    # Generate and set access token
    access_token = create_access_token(user.id)

    # Generate and set refresh token and session
    session_id = str(uuid.uuid4().hex)
    refresh_token = create_refresh_token(user.id, session_id)
    refresh_token_hash = hash_token(refresh_token)

    expires_at = datetime.utcnow() + timedelta(days=7)

    # Create a new refresh session
    await create_refresh_session_service(
        session_id=session_id,
        user_id=user.id,
        refresh_token_hash=refresh_token_hash,
        expires_at=expires_at,
    )

    # Set HttpOnlyCookie in response header
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=7 * 24 * 60 * 60
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 900,  # 15 minutes
    }

@router.post("/auth/refresh")
async def refresh_token(request: Request, response: Response):
    """
    Rotate refresh token and issue a new access token.
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )
    
    payload = decode_token(refresh_token)

    # Enforce refresh token type
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("id")
    session_id = payload.get("sid")

    if not user_id or not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    # Fetch session from DB
    session = await get_refresh_session_service(session_id)
    if not session or session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )        
    
    # Verify token matches hashed token in the DB
    if not verify_token(refresh_token, session.token_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    # Rotate refresh token
    new_refresh_token = create_refresh_token(user_id, session_id)
    token_hash = hash_token(new_refresh_token)
    expires_at = datetime.utcnow() + timedelta(days=7)

    # Update refresh token in DB
    await update_refresh_session_service(session_id, refresh_token_hash=token_hash, expires_at=expires_at)

    # Set HttpOnlyCookie in response header
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
      
    return {
        "access_token": create_access_token(user_id),
        "token_type": "bearer",
        "expires_in": 3600,
    }


@router.post("/auth/logout")
async def logout(request: Request, response: Response, user=Depends(require_user)):
    """
    Delete the refresh token from the database and response header.
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )
    
    payload = decode_token(refresh_token)

    session_id = payload.get("sid")

    # Delete refresh token from response header
    response.delete_cookie("refresh_token")

    # Delete refresh session from database
    await delete_refresh_session_service(session_id)
    return {
        "message": "User logged out successfully"
    }
