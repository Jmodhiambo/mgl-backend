#!/usr/bin/env python 3
"""User routes for MGLTickets."""

from fastapi import APIRouter, Depends, status, HTTPException
from typing import Optional
from app.schemas.user import UserOut, UserUpdate, OrganizerUpdate, UserPasswordChange, UserOrganizerProfileOut
from app.core.security import require_user, get_current_user
from app.services.user_services import (
    get_user_by_id_service,
    get_user_by_email_service,
    update_user_info_service,
    change_user_password_service
)
from app.utils.generate_image_url import delete_profile_picture

router = APIRouter()

@router.get("/users/me", response_model=UserOut, status_code=status.HTTP_200_OK)
async def get_current_user(user=Depends(require_user)):
    """
    Get the currently authenticated user.
    """
    return user

@router.get("/users/me/organizer", response_model=UserOrganizerProfileOut, status_code=status.HTTP_200_OK)
async def get_organizer_profile_status(user=Depends(get_current_user)):
    """Get the current user's organizer profile completion status."""
    if user.role != "organizer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not an organizer"
        )

    required = {
        "bio":                 user.bio,
        "profile_picture_url": user.profile_picture_url,
        "organization_name":   user.organization_name,
        "area_of_expertise":   user.area_of_expertise,
    }

    missing_fields = [field for field, value in required.items() if not value]
    profile_completed = len(missing_fields) == 0

    return UserOrganizerProfileOut(
        profile_completed=profile_completed,
        missing_fields=missing_fields
    )

@router.patch("/users/me/profile-update", response_model=UserOut, status_code=status.HTTP_200_OK)
async def update_user_profile(user_data: OrganizerUpdate, user=Depends(require_user)):
    """
    Update a user's profile information. Accepts both base contact fields
    (name, phone_number) and organizer-specific fields (bio, organization_name,
    website_url, social_media_links, area_of_expertise). All fields are optional;
    only supplied fields are written to the database.
    """
    data = {k: v for k, v in user_data.model_dump().items() if v is not None}
    return await update_user_info_service(user.id, data)

@router.patch("/users/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_user_password(user_data: UserPasswordChange, user=Depends(require_user)):
    """
    Change a user's password.
    """
    await change_user_password_service(user.id, user_data.old_password, user_data.new_password)

@router.delete("/users/me/profile-picture", response_model=bool, status_code=status.HTTP_200_OK)
async def delete_user_profile_picture(user: UserOut = Depends(require_user)):
    """
    Delete the current user's profile picture.
    Fetches the stored URL, removes the file via the shared utility,
    then nulls out profile_picture_url on the user row.
    """
    current_user = await get_user_by_id_service(user.id)

    if not current_user.profile_picture_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No profile picture to delete."
        )

    await delete_profile_picture(current_user.profile_picture_url)
    await update_user_info_service(user.id, {"profile_picture_url": None})

    return True

@router.patch("/users/email/{email}", response_model=UserOut, status_code=status.HTTP_200_OK)
async def get_user_by_email(email: str, user=Depends(require_user)):
    """
    Get a user by their email.
    """
    return await get_user_by_email_service(email)

@router.get("/users/{user_id}", response_model=Optional[UserOut], status_code=status.HTTP_200_OK)
async def get_user_by_id(user_id: int):
    """
    Get a user by their ID.
    """
    return await get_user_by_id_service(user_id)