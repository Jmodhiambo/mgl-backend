#!/usr/bin/env python3
"""Service layer for Favorite model in MGLTickets."""

import app.db.repositories.favorites_repo as favorites_repo
from app.schemas.favorites import FavoriteOut, FavoriteWithEventOut
from typing import Optional
from app.core.logging_config import logger


async def create_favorite_service(user_id: int, event_id: int) -> FavoriteOut:
    """Create a new favorite."""
    logger.info(f"Creating favorite for user {user_id}, event {event_id}")
    favorite = await favorites_repo.create_favorite_repo(user_id, event_id)
    logger.info(f"Created favorite with ID: {favorite.id}")
    return favorite


async def get_favorite_by_id_service(favorite_id: int) -> Optional[FavoriteOut]:
    """Get a favorite by its ID."""
    logger.info(f"Getting favorite with ID: {favorite_id}")
    return await favorites_repo.get_favorite_by_id_repo(favorite_id)


async def delete_favorite_service(user_id: int, event_id: int) -> bool:
    """Delete a favorite."""
    logger.info(f"Deleting favorite for user {user_id}, event {event_id}")
    return await favorites_repo.delete_favorite_repo(user_id, event_id)


async def get_favorites_by_user_id_service(user_id: int) -> list[FavoriteWithEventOut]:
    """
    Get all favorites for a user with events eagerly loaded.
    Returns FavoriteWithEventOut — each record includes the full EventOut.
    """
    logger.info(f"Getting favorites for user {user_id}")
    return await favorites_repo.get_favorites_by_user_id_repo(user_id)