#!/usr/bin/env python3
"""Save file and generate a unique URL for uploaded images."""

import os
from uuid import uuid4

import aiofiles
from fastapi import HTTPException, UploadFile, status

from app.core.config import (
    API_URL,
    UPLOADS_EVENTS_DIR,
    UPLOADS_EVENTS_URL_PATH,
    UPLOADS_PROFILES_DIR,
    UPLOADS_PROFILES_URL_PATH,
)
from app.core.logging_config import logger

# ── Create upload sub-directories on startup ──────────────────────────────────
os.makedirs(UPLOADS_EVENTS_DIR, exist_ok=True)
os.makedirs(UPLOADS_PROFILES_DIR, exist_ok=True)

# ── Allowed extensions ────────────────────────────────────────────────────────
EVENT_ALLOWED_EXTENSIONS:   set[str] = {".jpg", ".jpeg", ".png", ".gif", ".pdf"}
PROFILE_ALLOWED_EXTENSIONS: set[str] = {".jpg", ".jpeg", ".png"}

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _read_and_validate(image: UploadFile, allowed_exts: set[str]) -> bytes:
    """
    Read the file contents once, validate extension and size, then return the
    raw bytes so the caller can write them without a second read().

    Raises HTTP 400 on invalid extension or oversized file.
    """
    ext = os.path.splitext(image.filename or "")[1].lower()

    if ext not in allowed_exts:
        logger.error(f"Invalid file type uploaded: {ext!r}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{ext}'. Allowed: {', '.join(sorted(allowed_exts))}",
        )

    contents = await image.read()

    if len(contents) > MAX_FILE_SIZE:
        logger.error(f"Upload rejected — file size {len(contents)} exceeds 5 MB limit.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the maximum allowed size (5 MB).",
        )

    return contents


async def _save_image(
    image: UploadFile,
    upload_dir: str,
    url_path: str,
    allowed_exts: set[str],
) -> str:
    """
    Validate, save an uploaded image to *upload_dir*, and return its
    fully-qualified public URL built from API_URL + url_path.

    Args:
        image:        The FastAPI UploadFile instance.
        upload_dir:   Filesystem directory to write the file into.
        url_path:     URL path segment that maps to upload_dir via the
                      static-files mount (e.g. "uploads/events").
        allowed_exts: Set of permitted file extensions.

    Returns:
        Absolute URL string, e.g.
        "https://api.mgltickets.com/uploads/events/mgltickets-<uuid>.png"
    """
    contents = await _read_and_validate(image, allowed_exts)

    ext             = os.path.splitext(image.filename or "")[1].lower()
    unique_filename = f"mgltickets-{uuid4().hex}{ext}"
    file_path       = os.path.join(upload_dir, unique_filename)

    logger.info(f"Saving uploaded file to {file_path}")
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(contents)
    logger.info(f"Saved uploaded file to {file_path}")

    # Build a full absolute URL — frontend uses this directly as <img src>
    return f"{API_URL.rstrip('/')}/{url_path.strip('/')}/{unique_filename}"


async def _delete_image(image_url: str, upload_dir: str) -> bool:
    """
    Delete an image from disk given its public URL and the corresponding
    upload directory.

    Returns True if deleted, False if the file was not found.
    """
    filename  = os.path.basename(image_url)
    file_path = os.path.join(upload_dir, filename)

    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"Deleted image at {file_path}")
        return True

    logger.warning(f"Image not found for deletion: {file_path}")
    return False


# ── Public API ────────────────────────────────────────────────────────────────

async def save_flyer_and_get_url(flyer: UploadFile) -> str:
    """Save an event flyer and return its absolute URL."""
    return await _save_image(
        flyer,
        upload_dir=UPLOADS_EVENTS_DIR,
        url_path=UPLOADS_EVENTS_URL_PATH,
        allowed_exts=EVENT_ALLOWED_EXTENSIONS,
    )


async def save_profile_picture_and_get_url(profile_picture: UploadFile) -> str:
    """Save a user/organizer profile picture and return its absolute URL."""
    return await _save_image(
        profile_picture,
        upload_dir=UPLOADS_PROFILES_DIR,
        url_path=UPLOADS_PROFILES_URL_PATH,
        allowed_exts=PROFILE_ALLOWED_EXTENSIONS,
    )


async def delete_event_flyer(flyer_url: str) -> bool:
    """Delete an event flyer from disk given its public URL."""
    return await _delete_image(flyer_url, UPLOADS_EVENTS_DIR)


async def delete_profile_picture(profile_picture_url: str) -> bool:
    """Delete a profile picture from disk given its public URL."""
    return await _delete_image(profile_picture_url, UPLOADS_PROFILES_DIR)