#!/usr/bin/env python 3
"""User routes for MGLTickets."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from app.schemas.user import UserEmailVerification, UserOut, UserCreate, UserUpdate, UserPasswordChange, UserPasswordUpdate
from app.core.security import get_current_user
from app.services.user_services import (
    register_user_service,
    get_user_by_id_service,
    update_user_contact_service,
    update_user_password_service,
    deactivate_user_service,
    reactivate_user_service,
    verify_user_email_service,
    change_user_password_service
)

router = APIRouter()

@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """
    Register a new user.
    """
    return register_user_service(
        user_data.name,
        user_data.email,
        user_data.password,
        user_data.phone_number
    )

@router.get("/users/{user_id}", response_model=Optional[UserOut], status_code=status.HTTP_200_OK)
async def get_user_by_id(user_id: int): #, user=Depends(get_current_user)
    """
    Get a user by their ID.
    """
    return get_user_by_id_service(user_id)

@router.patch("/users/{user_id}/contact", response_model=UserOut, status_code=status.HTTP_200_OK)
async def update_user_contact(user_id: int, user_data: UserUpdate, user=Depends(get_current_user)):
    """
    Update a user's contact information.
    """
    if user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user.")
    return update_user_contact_service(user_id, user_data)

@router.patch("/users/{user_id}/password", response_model=UserOut, status_code=status.HTTP_200_OK)
async def update_user_password(user_id: int, password: UserPasswordUpdate, user=Depends(get_current_user)):
    """
    Update a user's password.
    """
    if user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user.")
    return update_user_password_service(user_id, password.new_password)

@router.patch("/users/{user_id}/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_user_password(user_id: int, user_data: UserPasswordChange, user=Depends(get_current_user)):
    """
    Change a user's password.
    """
    if user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to change this user's password.")
    change_user_password_service(user_id, user_data.old_password, user_data.new_password)

@router.patch("/users/{user_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(user_id: int, user=Depends(get_current_user)):
    """
    Deactivate a user account.
    """
    if user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to deactivate this user.")
    deactivate_user_service(user_id)

@router.patch("/users/{user_id}/reactivate", response_model=UserOut, status_code=status.HTTP_200_OK)
async def reactivate_user(user_id: int, user=Depends(get_current_user)):
    """
    Activate a user account.
    """
    if user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to activate this user.")
    return reactivate_user_service(user_id)

@router.patch("/users/{user_id}/verify-email", response_model=UserOut, status_code=status.HTTP_200_OK)
async def verify_user_email(user_id: int, data: UserEmailVerification, user=Depends(get_current_user)):
    """
    Verify a user's email.
    """
    if user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to verify this user's email.")
    return verify_user_email_service(user_id, data.token)