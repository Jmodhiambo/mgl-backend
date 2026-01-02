#!/usr/bin/env python 3
"""User routes for MGLTickets."""

from fastapi import APIRouter, Depends, status
from typing import Optional
from app.schemas.user import UserEmailVerification, UserOut, UserUpdate, UserPasswordChange, UserPasswordUpdate, UserPublic
from app.core.security import require_user
from app.services.user_services import (
    get_user_by_id_service,
    get_user_by_email_service,
    update_user_info_service,
    update_user_password_service,
    deactivate_user_service,
    reactivate_user_service,
    verify_user_email_service,
    change_user_password_service
)

router = APIRouter()

@router.get("/users/me", response_model=UserOut, status_code=status.HTTP_200_OK)
async def get_current_user(user=Depends(require_user)):
    """
    Get the currently authenticated user.
    """
    return user

@router.get("/users/{user_id}", response_model=Optional[UserOut], status_code=status.HTTP_200_OK)
async def get_user_by_id(user_id: int):
    """
    Get a user by their ID.
    """
    return await get_user_by_id_service(user_id)

@router.patch("/users/me/{email}", response_model=UserOut, status_code=status.HTTP_200_OK)
async def get_user_by_email(email: str, user=Depends(require_user)):
    """
    Get a user by their email.
    """
    return await get_user_by_email_service(email)

@router.patch("/users/me/contact", response_model=UserOut, status_code=status.HTTP_200_OK)
async def update_user_contact(user_data: UserUpdate, user=Depends(require_user)):
    """
    Update a user's contact information.
    """
    return await update_user_info_service(user.id, user_data)

@router.patch("/users/me/password", response_model=UserOut, status_code=status.HTTP_200_OK)
async def update_user_password(password: UserPasswordUpdate, user=Depends(require_user)):
    """
    Update a user's password.
    """
    return await update_user_password_service(user.id, password.new_password)

@router.patch("/users/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_user_password(user_data: UserPasswordChange, user=Depends(require_user)):
    """
    Change a user's password.
    """
    await change_user_password_service(user.id, user_data.old_password, user_data.new_password)

@router.patch("/users/me/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(user=Depends(require_user)):
    """
    Deactivate a user account.
    """
    await deactivate_user_service(user.id)

@router.patch("/users/me/reactivate", response_model=UserOut, status_code=status.HTTP_200_OK)
async def reactivate_user(user=Depends(require_user)):
    """
    Activate a user account.
    """
    return await reactivate_user_service(user.id)

@router.patch("/users/me/verify-email", response_model=UserOut, status_code=status.HTTP_200_OK)
async def verify_user_email(data: UserEmailVerification, user=Depends(require_user)):
    """
    Verify a user's email.
    """
    return await verify_user_email_service(user.id, data.token)