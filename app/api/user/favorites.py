#!/usr/bin/env python3
"""Favorite routes for MGLTickets."""

from fastapi import APIRouter, Depends, status, HTTPException
from app.schemas.favorites import FavoriteOut, FavoriteWithEventOut
import app.services.favorites_services as favorites_services
from app.core.security import require_user

router = APIRouter()


@router.post(
    "/users/me/favorites",
    response_model=FavoriteOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_favorite(event_id: int, user=Depends(require_user)):
    """
    Add an event to the current user's favorites.
    Returns the bare FavoriteOut (id, user_id, event_id, timestamps).
    The frontend uses event_id to update its local favorites state
    without needing the full event object returned again.
    """
    return await favorites_services.create_favorite_service(user.id, event_id)


@router.get(
    "/users/me/favorites",
    response_model=list[FavoriteWithEventOut],
    status_code=status.HTTP_200_OK,
)
async def get_user_favorites(user=Depends(require_user)):
    """
    Get all favorites for the current user with the full event
    object embedded on each record.

    Returns list[FavoriteWithEventOut]:
      { id, user_id, event_id, created_at, event: EventOut }

    The frontend maps over this to render event cards directly
    without a second API call per favorite.
    """
    return await favorites_services.get_favorites_by_user_id_service(user.id)


@router.delete(
    "/users/me/favorites/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_favorite(event_id: int, user=Depends(require_user)):
    """
    Remove an event from the current user's favorites.
    Takes event_id (not favorite row id) — simpler for the frontend.
    Returns 404 if the favorite doesn't exist.
    """
    deleted = await favorites_services.delete_favorite_service(user.id, event_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found.",
        )