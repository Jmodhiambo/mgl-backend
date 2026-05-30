#!/usr/bin/env python3
"""Auth routes for MGLTickets."""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status, Depends, Response, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import COOKIE_DOMAIN
from app.schemas.user import UserCreate, UserOut
from app.schemas.auth import (
    EmailVerifyRequest, EmailVerifiyResponse, ResendVerificationRequest,
    ForgotPasswordRequest, ResetPasswordRequest, ReactivateAccountRequest,
    PasswordResetResponse,
)
from app.services.notification_services import notify_user_registered
from app.utils.eat_to_utc import convert_eat_to_utc
from app.services.user_services import (
    get_user_by_email_service,
    authenticate_user_service,
    register_user_service,
    verify_user_email_service,
    resend_verification_email_service,
    request_password_reset_service,
    reset_password_with_token_service,
    reactivate_account_service,
    deactivate_user_service,
)
from app.services.ref_session_services import (
    create_refresh_session_service,
    get_refresh_session_service,
    revoke_refresh_session_service,
    delete_refresh_session_service,
    get_user_session_stats_service,
    cleanup_user_sessions_service,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
    verify_token,
    require_user,
)

router = APIRouter()


@router.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, background_tasks: BackgroundTasks):
    """Register a new user."""
    user = await register_user_service(
        user_data.name,
        user_data.email,
        user_data.password,
        user_data.phone_number,
    )
    background_tasks.add_task(notify_user_registered, user.id, user.name, user.email)
    return user


@router.post("/auth/verify-email", response_model=EmailVerifiyResponse, status_code=status.HTTP_200_OK)
async def verify_user_email(user_data: EmailVerifyRequest):
    """Verify user's email address with token."""
    return await verify_user_email_service(user_data.token)


@router.post("/auth/resend-verification", response_model=EmailVerifiyResponse, status_code=status.HTTP_200_OK)
async def resend_verification_email(user_data: ResendVerificationRequest):
    """Resend verification email to user."""
    return await resend_verification_email_service(user_data.email)


@router.post("/auth/login", response_model=dict, status_code=status.HTTP_200_OK)
async def login(
    response: Response,
    request: Request,
    background_tasks: BackgroundTasks,
    form: OAuth2PasswordRequestForm = Depends(),
):
    """Authenticate user and issue access + refresh tokens."""
    email: str = form.username
    user: UserOut = await get_user_by_email_service(email)

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    if not await authenticate_user_service(user.id, email, form.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(user.id)

    session_id = str(uuid.uuid4().hex)
    refresh_token = create_refresh_token(user.id, session_id)
    refresh_token_hash = hash_token(refresh_token)

    # ── Device / network fingerprint ──────────────────────────────────────────
    device_info = request.headers.get("User-Agent")

    # X-Real-IP is set by nginx/caddy to the single real client IP.
    # Fall back to ASGI's request.client.host when running without a proxy
    # (local dev, tests).  Do NOT use X-Forwarded-For here — it is a
    # comma-separated proxy chain, not a single address.
    ip_address = (
        request.headers.get("X-Real-IP")
        or (request.client.host if request.client else None)
    )

    # Location requires a GeoIP lookup.  Leave NULL for now; the column
    # exists so you can back-fill it later without a migration.
    # Example when ready:
    #   from app.utils.geoip import resolve_location
    #   location = await resolve_location(ip_address)
    location = None

    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    await create_refresh_session_service(
        session_id=session_id,
        user_id=user.id,
        refresh_token_hash=refresh_token_hash,
        expires_at=expires_at,
        device_info=device_info,
        ip_address=ip_address,
        location=location,
    )

    response = JSONResponse(
        content={
            "message": "Login successful",
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 900,
            "session_id": session_id,
        }
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        domain=COOKIE_DOMAIN,
        path="/",
        max_age=7 * 24 * 60 * 60,
    )
    return response


@router.post("/auth/refresh")
async def refresh_token(request: Request, response: Response):
    """Rotate refresh token and issue a new access token."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token provided")

    payload = decode_token(refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = payload.get("id")
    session_id = payload.get("sid")

    if not user_id or not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    session = await get_refresh_session_service(session_id)

    if not session or session.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if session.revoked_at:
        time_since_revoked = datetime.now(timezone.utc) - convert_eat_to_utc(session.revoked_at)
        if time_since_revoked.total_seconds() < 5:
            new_session = await get_refresh_session_service(session_id)
            if new_session and not new_session.revoked_at:
                return {
                    "access_token": create_access_token(user_id),
                    "token_type": "bearer",
                    "expires_in": 3600,
                }
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")

    if session.expires_at < datetime.now():
        await delete_refresh_session_service(session_id)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    if not verify_token(refresh_token, session.refresh_token_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    new_session_id = str(uuid.uuid4().hex)
    new_refresh_token = create_refresh_token(user_id, new_session_id)
    refresh_token_hash = hash_token(new_refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    device_info = request.headers.get("User-Agent")
    ip_address = (
        request.headers.get("X-Real-IP")
        or (request.client.host if request.client else None)
    )
    location = None  # see login endpoint comment

    await create_refresh_session_service(
        session_id=new_session_id,
        user_id=user_id,
        refresh_token_hash=refresh_token_hash,
        expires_at=expires_at,
        device_info=device_info,
        ip_address=ip_address,
        location=location,
    )

    await revoke_refresh_session_service(session_id, new_session_id)

    response = JSONResponse(
        content={
            "message": "Login successful",
            "access_token": create_access_token(user_id),
            "token_type": "bearer",
            "expires_in": 900,
            "session_id": new_session_id,
        }
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="none",
        domain=COOKIE_DOMAIN,
        path="/",
        max_age=7 * 24 * 60 * 60,
    )
    return response


@router.post("/auth/forgot-password", response_model=PasswordResetResponse, status_code=status.HTTP_200_OK)
async def forgot_password(request_data: ForgotPasswordRequest):
    """Request a password reset link."""
    return await request_password_reset_service(request_data.email)


@router.post("/auth/reset-password", response_model=PasswordResetResponse, status_code=status.HTTP_200_OK)
async def reset_password(request_data: ResetPasswordRequest):
    """Reset password using token from email."""
    return await reset_password_with_token_service(request_data.token, request_data.new_password)


@router.post("/auth/reactivate", response_model=PasswordResetResponse, status_code=status.HTTP_200_OK)
async def reactivate_account(request_data: ReactivateAccountRequest):
    """Reactivate a deactivated account."""
    return await reactivate_account_service(request_data.email)


@router.patch("/auth/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(user=Depends(require_user)):
    """Deactivate the current user's account."""
    await deactivate_user_service(user.id)


@router.post("/auth/logout")
async def logout(request: Request, response: Response, user=Depends(require_user)):
    """Delete the refresh token and its session record."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token provided")

    payload = decode_token(refresh_token)
    session_id = payload.get("sid")

    response.delete_cookie("refresh_token")
    await delete_refresh_session_service(session_id)

    return {"message": "User logged out successfully"}


@router.post("/auth/logout-all-devices", response_model=dict, status_code=status.HTTP_200_OK)
async def logout_all_devices(user=Depends(require_user)) -> dict:
    """Logout all devices by deleting all user sessions."""
    # user.id is int — matches the now-corrected service signature
    return await cleanup_user_sessions_service(user.id)


@router.get("/auth/session-stats", response_model=dict, status_code=status.HTTP_200_OK)
async def get_user_session_stats(user=Depends(require_user)) -> dict:
    """Get session stats for the current user.

    FIXED: now passes user.id to the service.
    Original called get_user_session_stats_service() with no argument,
    which would raise TypeError at runtime.
    """
    return await get_user_session_stats_service(user.id)