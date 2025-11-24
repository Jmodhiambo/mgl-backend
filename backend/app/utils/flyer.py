#!/usr/bin/env python3
"""Save file and Generate a unique flyer URL for the saved flyer."""

from uuid import uuid4
import os, aiofiles
from fastapi import UploadFile, HTTPException, status

UPLOAD_DIR = "app/uploads"

# Create the uploads directory if it doesn't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf"}
MAX_FILE_SIZE = 5 * 1024 * 1024

async def save_flyer_and_get_url(flyer: UploadFile) -> str:
    """Generate path and a unique flyer URL for the uploaded flyer."""
    # Extract the file extension
    file_extension = os.path.splitext(flyer.filename)[1]

    # Check if the file is of a valid type
    if file_extension.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid flyer type. Only JPG, JPEG, PNG, GIF, and PDF files are allowed.")
    
    # Check if the file size is within the allowed limit
    # if flyer.size > MAX_FILE_SIZE:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Flyer size exceeds the maximum allowed size (5MB).")

    unique_filename = f"mgltickets-{uuid4().hex}{file_extension}"

    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    flyer_url = f"/uploads/{unique_filename}"

    # Save the flyer to the specified path
    async with aiofiles.open(file_path, "wb") as buffer:
        await buffer.write(await flyer.read())

    return flyer_url