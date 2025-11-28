#!/usr/bin/env python 3
"""User routes for MGLTickets."""

from fastapi import APIRouter, Depends, status
from typing import Optional
from app.schemas.user import UserOut, UserCreate, UserUpdate
from app.core.security import get_current_user
from app.services.user_services import (
    register_user_service,
    get_user_by_id_service,
    update_user_contact_service,
    update_user_password_service,
    deactivate_user_service,
    activate_user_service,
    verify_user_email_service
)

router = APIRouter()

@router.post("/users", response_model=UserOut)
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

@router.get("/users/{user_id}", response_model=Optional[UserOut])
async def get_user_by_id(user_id: int): #, user=Depends(get_current_user)
    """
    Get a user by their ID.
    """
    return get_user_by_id_service(user_id)

@router.patch("/users/{user_id}", response_model=UserOut)
async def update_user_contact(user_id: int, user_data: UserUpdate, user=Depends(get_current_user)):
    """
    Update a user's contact information.
    """
    return update_user_contact_service(user_id, user_data)

@router.patch("/users/{user_id}/password", response_model=UserOut)
async def update_user_password(user_id: int, new_password: str, user=Depends(get_current_user)):
    """
    Update a user's password.
    """
    return update_user_password_service(user_id, new_password)

@router.patch("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(user_id: int, user=Depends(get_current_user)):
    """
    Deactivate a user account.
    """
    deactivate_user_service(user_id)

@router.patch("/users/{user_id}", response_model=UserOut)
async def activate_user(user_id: int, user=Depends(get_current_user)):
    """
    Activate a user account.
    """
    return activate_user_service(user_id)

@router.patch("/users/{user_id}", response_model=UserOut)
async def verify_user_email(user_id: int, user=Depends(get_current_user)):
    """
    Verify a user's email.
    """
    return verify_user_email_service(user_id)