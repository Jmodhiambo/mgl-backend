#!/usr/bin/env python3
"""Organizer User API routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from app.schemas.user import OrganizerCreate, OrganizerUpdate, OrganizerOut, OrganizerInfo
import app.services.user_services as user_services
from app.core.security import require_organizer, require_user
from app.utils.images import save_profile_picture_and_get_url, delete_profile_picture

router = APIRouter()

ROLE_ORGANIZER = "organizer"

@router.patch("/organizers/me/promote", response_model=OrganizerOut, status_code=status.HTTP_201_CREATED)
async def upgrade_user_to_organizer(
    data: OrganizerCreate,
    profile_picture: Optional[UploadFile] = File(None),
    user=Depends(require_user)
):
    """Promote a regular user to an organizer."""
    # Check if user is already an organizer
    if user.role == ROLE_ORGANIZER:
        raise HTTPException(status_code=400, detail="User is already an organizer.")
    
    data_dict = data.model_dump()
    if profile_picture:
        profile_picture_url = await save_profile_picture_and_get_url(profile_picture)
        data_dict["profile_picture_url"] = profile_picture_url
    
    # Update user role to organizer
    data_dict["role"] = ROLE_ORGANIZER
    organizer_data = OrganizerCreate(**data_dict)
    
    return await user_services.update_user_info_service(user.id, organizer_data)

@router.get("/organizers/me/profile", response_model=OrganizerOut, status_code=status.HTTP_200_OK)
async def get_organizer_profile(user=Depends(require_organizer)):
    """Get the profile of the current organizer."""  
    return await user_services.get_user_by_id_service(user.id)

@router.patch("/organizers/me/profile-update", response_model=OrganizerOut, status_code=status.HTTP_200_OK)
async def update_organizer_profile(
    data: OrganizerUpdate,
    profile_picture: Optional[UploadFile] = File(None),
    user=Depends(require_organizer)
):
    """Update the profile of the current organizer."""
    data_dict = data.model_dump()  # Convert to dict to modify
    if profile_picture:

        if user.profile_picture_url:
            # Delete the old profile picture
            await delete_profile_picture(user.profile_picture_url)

        profile_picture_url = await save_profile_picture_and_get_url(profile_picture)
        data_dict["profile_picture_url"] = profile_picture_url

    # Update user info with OrganizerInfo since OrganizerUpdate does not have profile_picture_url
    return await user_services.update_user_info_service(user.id, OrganizerInfo(**data_dict))

@router.delete("/organizers/me/profile-picture", response_model=bool, status_code=status.HTTP_200_OK)
async def delete_organizer_profile_picture(user=Depends(require_organizer)):
    """Delete the profile picture of the current organizer."""

    if not user.profile_picture_url:
        raise HTTPException(status_code=400, detail="No profile picture to delete.")

    # Delete the profile picture
    await delete_profile_picture(user.profile_picture_url)

    # Update user info to remove profile picture URL
    updated_data = {"profile_picture_url": None}
    await user_services.update_user_info_service(user.id, OrganizerUpdate(**updated_data))

    return True