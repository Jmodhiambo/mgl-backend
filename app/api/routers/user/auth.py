#!/usr/bin/env python3
"""Auth routes for MGLTickets."""

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.services.user_services import (
    get_user_by_email_service,
    authenticate_user_service
)
from app.core.security import (
    create_access_token,
    get_current_user,
)

router = APIRouter()


@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate user and return an access token.
    """
    # OAuth2PasswordRequestForm has username and password, so email in this case is username.
    email = form.username
    user = get_user_by_email_service(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not authenticate_user_service(user.id, email, form.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
    )

    token = create_access_token(user.id)

    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 3600,
    }

@router.post("/refresh")
async def refresh_token(user=Depends(get_current_user)):
    """
    Generate a fresh JWT for an authenticated user.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return {
        "access_token": create_access_token(user.id),
        "token_type": "bearer",
        "expires_in": 3600,
    }


@router.post("/logout")
async def logout(user=Depends(get_current_user)):
    """
    'Logout' by instructing client to delete the token.
    JWT invalidation is client-side unless you use a blacklist.
    """
    return {
        "message": "Logout successful. Client should delete the token."
    }
