#!/usr/bin/env python3
"""Organizer User API routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form, BackgroundTasks
from app.schemas.user import OrganizerCreate, OrganizerOut, UserOut
from app.schemas.organizer import DashboardStats, RecentBooking
from app.services.notification_services import notify_organizer_registered
import app.services.user_services as user_services
import app.services.organizer_analytics_services as oa_services
from app.core.security import require_organizer, require_user
from app.utils.generate_image_url import save_profile_picture_and_get_url, delete_profile_picture

router = APIRouter()

ROLE_ORGANIZER = "organizer"


@router.get("/organizers/me", response_model=OrganizerOut, status_code=status.HTTP_200_OK)
async def get_organizer_info(organizer: UserOut = Depends(require_user)):
    """Get the info of the current organizer.
    Using require_user as the route is being used in setting organizer profile.
    """
    return await user_services.get_user_by_id_service(organizer.id)


@router.patch("/organizers/me/promote", response_model=OrganizerOut, status_code=status.HTTP_201_CREATED)
async def upgrade_user_to_organizer(
    data: OrganizerCreate,
    background_tasks: BackgroundTasks,
    profile_picture: Optional[UploadFile] = File(None),
    user: UserOut = Depends(require_user)
):
    """Promote a regular user to an organizer."""
    if user.role == ROLE_ORGANIZER:
        raise HTTPException(status_code=400, detail="User is already an organizer.")

    data_dict = data.model_dump()
    if profile_picture:
        profile_picture_url = await save_profile_picture_and_get_url(profile_picture)
        data_dict["profile_picture_url"] = profile_picture_url

    data_dict["role"] = ROLE_ORGANIZER
    organizer = await user_services.update_user_info_service(user.id, data_dict)

    background_tasks.add_task(notify_organizer_registered, organizer.id, organizer.name)

    return organizer


@router.patch("/organizers/me/profile-update", response_model=OrganizerOut, status_code=status.HTTP_200_OK)
async def update_organizer_profile(
    name: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    organization_name: Optional[str] = Form(None),
    website_url: Optional[str] = Form(None),
    social_media_links: Optional[str] = Form(None),   # JSON-encoded string, e.g. '["https://..."]'
    area_of_expertise: Optional[str] = Form(None),    # JSON-encoded string
    profile_picture: Optional[UploadFile] = File(None),
    user: UserOut = Depends(require_organizer),
):
    """
    Update the profile of the current organizer.

    Accepts multipart/form-data so a profile picture can be uploaded alongside
    text fields in a single request. The frontend sends a FormData object with
    these exact field names; social_media_links and area_of_expertise arrive
    as JSON-encoded strings since multipart form fields are flat strings, not
    nested structures — they are parsed back into lists below.

    Previously this endpoint declared `data: OrganizerUpdate` as a JSON body
    param alongside `profile_picture: UploadFile`, which is not valid in
    FastAPI — a route cannot mix a Pydantic JSON body with multipart file
    fields. All text fields must be declared as Form(...) to match a
    multipart payload.
    """
    import json

    data_dict: dict = {}
    if name is not None:
        data_dict["name"] = name
    if phone_number is not None:
        data_dict["phone_number"] = phone_number
    if bio is not None:
        data_dict["bio"] = bio
    if organization_name is not None:
        data_dict["organization_name"] = organization_name
    if website_url is not None:
        data_dict["website_url"] = website_url

    # social_media_links and area_of_expertise arrive as JSON-encoded strings
    # from the frontend (multipart form fields are flat strings). The User
    # model stores both as plain VARCHAR columns (String(500) / String(200))
    # — NOT JSON or ARRAY columns — despite being typed as Optional[list[str]]
    # at the ORM/Pydantic level. asyncpg's VARCHAR codec only accepts `str`,
    # so we must validate the incoming JSON and then write the STRING back
    # (not the decoded list) onto data_dict, or the UPDATE statement fails
    # with "invalid input ... expected str, got list".
    if social_media_links is not None:
        try:
            parsed = json.loads(social_media_links)
            if not isinstance(parsed, list) or not all(isinstance(x, str) for x in parsed):
                raise ValueError
        except (json.JSONDecodeError, ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="social_media_links must be a JSON-encoded array of strings.",
            )
        data_dict["social_media_links"] = social_media_links  # store the validated JSON string as-is
    if area_of_expertise is not None:
        try:
            parsed = json.loads(area_of_expertise)
            if not isinstance(parsed, list) or not all(isinstance(x, str) for x in parsed):
                raise ValueError
        except (json.JSONDecodeError, ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="area_of_expertise must be a JSON-encoded array of strings.",
            )
        data_dict["area_of_expertise"] = area_of_expertise  # store the validated JSON string as-is

    # Get full organizer info (needed to check for an existing profile picture to delete)
    organizer = await user_services.get_user_by_id_service(user.id)

    if profile_picture:
        if organizer.profile_picture_url:
            await delete_profile_picture(organizer.profile_picture_url)
        data_dict["profile_picture_url"] = await save_profile_picture_and_get_url(profile_picture)

    # Update user info directly with a dict — update_user_info_service takes
    # a plain dict and passes it straight through to user_repo.update_user_info_repo,
    # which writes each key onto the User row as-is. We previously wrapped this
    # in OrganizerInfo(**data_dict), but OrganizerInfo types these two fields as
    # Optional[list[str]] for the READ path (organizer_info in OrganizerOut),
    # while the actual User columns are plain VARCHAR — not JSON/ARRAY. Passing
    # a real Python list through to asyncpg against a VARCHAR column fails with
    # "invalid input ... expected str, got list". Since update_user_info_service
    # never required a Pydantic model in the first place, the dict goes through
    # unwrapped, carrying the validated JSON strings as strings end to end.
    return await user_services.update_user_info_service(user.id, data_dict)


@router.delete("/organizers/me/profile-picture", response_model=bool, status_code=status.HTTP_200_OK)
async def delete_organizer_profile_picture(user: UserOut = Depends(require_organizer)):
    """Delete the profile picture of the current organizer."""
    organizer = await user_services.get_user_by_id_service(user.id)

    if not organizer.profile_picture_url:
        raise HTTPException(status_code=400, detail="No profile picture to delete.")

    await delete_profile_picture(organizer.profile_picture_url)

    await user_services.update_user_info_service(organizer.id, {"profile_picture_url": None})

    return True