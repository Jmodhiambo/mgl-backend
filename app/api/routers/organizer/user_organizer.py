#!/usr/bin/env python3
"""Organizer User API routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from app.schemas.user import OrganizerCreate, OrganizerUpdate, OrganizerOut
import app.services.user_services as user_services
from app.core.security import require_organizer, require_user
from app.utils.images import save_profile_picture_and_get_url, delete_profile_picture

router = APIRouter()

@router.patch("/organizers/{user_id}/promote", response_model=OrganizerOut, status_code=status.HTTP_201_CREATED)
async def upgrade_user_to_organizer(
    user_id: int,
    data: OrganizerCreate,
    profile_picture: Optional[UploadFile] = File(None),
    user=Depends(require_user)
):
    """Promote a regular user to an organizer."""
    if user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to promote this user.")
    
    # Check if user is already an organizer
    if user.role == "organizer":
        raise HTTPException(status_code=400, detail="User is already an organizer.")
    
    data_dict = data.model_dump()
    if profile_picture:
        profile_picture_url = await save_profile_picture_and_get_url(profile_picture)
        data_dict["profile_picture_url"] = profile_picture_url
    
    # Update user role to organizer
    data_dict["role"] = "organizer"
    organizer_data = OrganizerCreate(**data_dict)
    
    return user_services.update_user_info_service(user.id, organizer_data)

@router.get("/organizers/{user_id}/profile", response_model=OrganizerOut, status_code=status.HTTP_200_OK)
async def get_organizer_profile(user_id: int, user=Depends(require_organizer)):
    """Get the profile of the current organizer."""
    if user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this organizer.")
    
    return user_services.get_user_by_id_service(user_id)

@router.patch("/organizers/{user_id}/profile-update", response_model=OrganizerOut, status_code=status.HTTP_200_OK)
async def update_organizer_profile(
    user_id: int,
    data: OrganizerUpdate,
    profile_picture: Optional[UploadFile] = File(None),
    current_user=Depends(require_organizer)
):
    """Update the profile of the current organizer."""
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this organizer.")
    
    user = user_services.get_user_by_id_service(user_id)

    data_dict = data.model_dump()  # Convert to dict to modify
    if profile_picture:

        if user.profile_picture_url:
            # Delete the old profile picture
            await delete_profile_picture(user.profile_picture_url)

        profile_picture_url = await save_profile_picture_and_get_url(profile_picture)
        data_dict["profile_picture_url"] = profile_picture_url

    return user_services.update_user_info_service(user.id, OrganizerUpdate(**data_dict))

@router.delete("/organizers/{user_id}/profile-picture", response_model=bool, status_code=status.HTTP_200_OK)
async def delete_organizer_profile_picture(user_id: int, current_user=Depends(require_organizer)):
    """Delete the profile picture of the current organizer."""
    if current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this organizer's profile picture.")
    
    user = user_services.get_user_by_id_service(user_id)

    if not user.profile_picture_url:
        raise HTTPException(status_code=400, detail="No profile picture to delete.")

    # Delete the profile picture
    await delete_profile_picture(user.profile_picture_url)

    # Update user info to remove profile picture URL
    updated_data = {"profile_picture_url": None}
    user_services.update_user_info_service(user.id, OrganizerUpdate(**updated_data))

    return True