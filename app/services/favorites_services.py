#!/usr/bin/env python3
"""Service layer for Co-Organizer model in MGLTickets."""

import app.db.repositories.favorites_repo as favorites_repo
from app.schemas.favorites import FavoriteOut
from typing import Optional
from app.core.logging_config import logger


async def create_favorite_service(user_id: int, event_id: int) -> FavoriteOut:
    """Service to create a new favorite."""
    logger.info(f"Creating a new favorite for user with ID: {user_id} and event with ID: {event_id}")
    favorite = await favorites_repo.create_favorite_repo(user_id, event_id)
    logger.info(f"Created favorite with ID: {favorite.id}")
    return favorite

async def get_favorites_by_id_service(favorite_id: int) -> Optional[FavoriteOut]:
    """Get a favorite by its ID."""
    logger.info(f"Getting favorite with ID: {favorite_id} for user with ID: {favorite_id}")
    return await favorites_repo.get_favorite_by_id_repo(favorite_id)

async def delete_favorite_service(user_id: int, event_id: int) -> bool:
    """Delete a favorite."""
    logger.info(f"Deleting favorite for user with ID: {user_id} and event with ID: {event_id}")
    return await favorites_repo.delete_favorite_repo(user_id, event_id)

async def get_favorites_by_user_id_service(user_id: int) -> list[FavoriteOut]:
    """Get all favorites for a user."""
    logger.info(f"Getting favorites for user with ID: {user_id}")
    return await favorites_repo.get_favorites_by_user_id_repo(user_id)