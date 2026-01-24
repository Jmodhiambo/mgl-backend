#!/usr/bin/env python3
"""Auth routes for MGLTickets."""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status, Depends, Response, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.user import UserCreate, UserOut
from app.schemas.auth import (
    EmailVerifyRequest, EmailVerifiyResponse, ResendVerificationRequest,
    ForgotPasswordRequest, ResetPasswordRequest, ReactivateAccountRequest, PasswordResetResponse
)
from app.services.user_services import (
    get_user_by_email_service,
    authenticate_user_service,
    register_user_service,
    verify_user_email_service,
    resend_verification_email_service,
    request_password_reset_service,
    reset_password_with_token_service,
    reactivate_account_service,
    deactivate_user_service
)
from app.services.ref_session_services import (
    create_refresh_session_service,
    get_refresh_session_service,
    revoke_refresh_session_service,
    delete_refresh_session_service,
    get_user_session_stats_service,
    cleanup_user_sessions_service

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

@router.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
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


@router.post("/auth/verify-email", response_model=EmailVerifiyResponse, status_code=status.HTTP_200_OK)
async def verify_user_email(user_data: EmailVerifyRequest):
    """
    Verify user's email address with token.
    
    - **token**: Verification token from email link
    
    Returns success message and user info if verification successful.
    Returns 410 GONE if token expired.
    Returns 400 BAD REQUEST if token invalid.
    """
    return await verify_user_email_service(user_data.token)


@router.post("/auth/resend-verification", response_model=EmailVerifiyResponse, status_code=status.HTTP_200_OK)
async def resend_verification_email(user_data: ResendVerificationRequest):
    """
    Resend verification email to user.
    """
    return await resend_verification_email_service(user_data.email)


@router.post("/auth/login", response_model=dict, status_code=status.HTTP_200_OK)
async def login(response: Response, form: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate user and return an access token along with a refresh token cookie.
    """
    # OAuth2PasswordRequestForm has username and password, so email in this case is username.
    email = form.username
    user = await get_user_by_email_service(email)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
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

    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

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
        secure=False,        # False impotart for localhost and True for production
        samesite="lax",
        # domain=".localhost", # Change to ".mgltickets.com" when deployed
        max_age=7 * 24 * 60 * 60  # 7 days
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

    # Verify session matches user
    if not session or session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Check if this session was just rotated (within last 5 seconds)
    if session.revoked_at:
        time_since_revoked = datetime.now(timezone.utc) - session.revoked_at
        if time_since_revoked.total_seconds() < 5:
            # This might be a race condition - allow it and return the new session
            new_session = await get_refresh_session_service(session_id)
            if new_session and not new_session.revoked_at:
                # Use the new session instead
                return {
                    "access_token": create_access_token(user_id),
                    "token_type": "bearer",
                    "expires_in": 3600,
                }
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked",
        )

    # Delete session if it is expired
    if session.expires_at < datetime.now():
        await delete_refresh_session_service(session_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )   
    
    # Verify token matches hashed token in the DB
    if not verify_token(refresh_token, session.refresh_token_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Rotate refresh token
    new_session_id = str(uuid.uuid4().hex)
    new_refresh_token = create_refresh_token(user_id, new_session_id)
    refresh_token_hash = hash_token(new_refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    # Create refresh token in DB
    await create_refresh_session_service(
        session_id=new_session_id,
        user_id=user_id,
        refresh_token_hash=refresh_token_hash,
        expires_at=expires_at
    )

    # Revoke older session for later deletion
    await revoke_refresh_session_service(session_id, new_session_id)

    # Set HttpOnlyCookie in response header
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=False,        # False impotart for localhost and True for production
        samesite="lax",
        # domain=".localhost", # Change to ".mgltickets.com" when deployed
        max_age=7 * 24 * 60 * 60  # 7 days
    )
      
    return {
        "access_token": create_access_token(user_id),
        "token_type": "bearer",
        "expires_in": 3600,
    }

@router.post("/auth/forgot-password", response_model=PasswordResetResponse, status_code=status.HTTP_200_OK)
async def forgot_password(request_data: ForgotPasswordRequest):
    """
    Request a password reset link.
    
    - **email**: User's email address
    
    Returns success message. For security, always returns success even if email doesn't exist.
    """
    return await request_password_reset_service(request_data.email)


@router.post("/auth/reset-password", response_model=PasswordResetResponse, status_code=status.HTTP_200_OK)
async def reset_password(request_data: ResetPasswordRequest):
    """
    Reset password using token from email.
    
    - **token**: Password reset token from email link
    - **new_password**: New password (minimum 8 characters)
    
    Returns success message if password reset successful.
    Returns 410 GONE if token expired.
    Returns 400 BAD REQUEST if token invalid or password requirements not met.
    Returns 403 FORBIDDEN if user is inactive.
    """
    return await reset_password_with_token_service(request_data.token, request_data.new_password)


@router.post("/auth/reactivate", response_model=PasswordResetResponse, status_code=status.HTTP_200_OK)
async def reactivate_account(request_data: ReactivateAccountRequest):
    """
    Reactivate a deactivated account.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns success message if account reactivated successfully.
    Returns 404 NOT FOUND if user doesn't exist.
    Returns 400 BAD REQUEST if account is already active.
    Returns 401 UNAUTHORIZED if password is incorrect.
    """
    return await reactivate_account_service(request_data.email)


@router.patch("/auth/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(user=Depends(require_user)):
    """
    Deactivate a user account.
    """
    await deactivate_user_service(user.id)

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

@router.post("/auth/logout-all-devices", response_model=dict, status_code=status.HTTP_200_OK)
async def logout_all_devices(user=Depends(require_user)) -> dict:
    """Logout all devices by deleting all user sessions."""
    return await cleanup_user_sessions_service(user.id)

@router.get("/auth/session-stats", response_model=dict, status_code=status.HTTP_200_OK)
async def get_user_session_stats(user=Depends(require_user)) -> dict:
    """Get user session stats."""
    return await get_user_session_stats_service()