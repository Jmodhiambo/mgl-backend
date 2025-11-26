#!/usr/bin/env python3
"""Save file and Generate a unique URL for the uploaded images."""

from uuid import uuid4
import os
import aiofiles
from fastapi import UploadFile, HTTPException, status
from app.core.logging_config import logger

# Upload directories
EVENTS_UPLOAD_DIR = "app/uploads/events"
PROFILES_UPLOAD_DIR = "app/uploads/profiles"


# Create the events and profiles upload sub-directories in the uploads folder
os.makedirs(EVENTS_UPLOAD_DIR, exist_ok=True)
os.makedirs(PROFILES_UPLOAD_DIR, exist_ok=True)

# Allowed file extensions
EVENT_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf"}
PROFILE_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

MAX_FILE_SIZE = 5 * 1024 * 1024

async def validate_file(image: UploadFile, allowed_exts: set[str]) -> None:
    """Validate file type and size."""
    ext = os.path.splitext(image.filename)[1].lower()

    if ext not in allowed_exts:
        logger.error(f"Invalid file type: {ext}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Allowed types: " + ", ".join(allowed_exts),
        )

    # Check file size (UploadFile does not expose size, so read chunk)
    contents = await image.read()
    if len(contents) > MAX_FILE_SIZE:
        logger.error("File size exceeds the maximum allowed size (5MB).")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the maximum allowed size (5MB)."
        )

    # Reset the pointer since we already consumed read()
    await image.seek(0)

async def save_image_and_get_url(image: UploadFile, url_prefix: str, upload_dir: str, allowed_exts: set[str], ) -> str:
    """Save an uploaded image and return its URL."""
    # Validate image
    await validate_file(image, allowed_exts)

    # Extract the file extension and generate unique filename
    file_extension = os.path.splitext(image.filename)[1].lower()
    unique_filename = f"mgltickets-{uuid4().hex}{file_extension}"

    file_path = os.path.join(upload_dir, unique_filename)
    url = f"/uploads/{url_prefix}/{unique_filename}"

    # Save image to the specified path
    logger.info(f"Saving image to {file_path}")
    async with aiofiles.open(file_path, "wb") as buffer:
        await buffer.write(await image.read())

    logger.info(f"Saved image to {file_path}")

    return url

async def save_flyer_and_get_url(flyer: UploadFile) -> str:
    """Save flyer and return the URL."""
    return await save_image_and_get_url(
        flyer, "events", EVENTS_UPLOAD_DIR, EVENT_ALLOWED_EXTENSIONS
    )

async def save_profile_and_get_url(profile: UploadFile) -> str:
    """Save profile picture and return the URL."""
    return await save_image_and_get_url(
        profile, "profiles", PROFILES_UPLOAD_DIR, PROFILE_ALLOWED_EXTENSIONS
    )


async def delete_image(image_url: str, upload_dir: str) -> bool:
    """Delete the image from the disk based on URL."""
    filename = os.path.basename(image_url)
    file_path = os.path.join(upload_dir, filename)

    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"Deleted image from {file_path}")
        return True
    
    logger.warning(f"Image {file_path} not found for deletion")
    
    return False

async def delete_event_flyer(flyer_url: str) -> bool:
    """Delete the flyer from the server."""
    return await delete_image(flyer_url, EVENTS_UPLOAD_DIR)

async def delete_profile(profile_url: str) -> bool:
    """Delete the profile picture from the server."""
    return await delete_image(profile_url, PROFILES_UPLOAD_DIR)