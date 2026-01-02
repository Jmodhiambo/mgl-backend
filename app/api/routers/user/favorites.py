#!/usr/bin/env python3
"""Favorite routes for MGLTickets."""

from fastapi import APIRouter, Depends, status
from app.schemas.favorites import FavoriteOut
from app.schemas.event import EventOut
import app.services.favorites_services as favorites_services
from app.services.event_services import get_event_by_id_service
from app.core.security import require_user

router = APIRouter()

@router.post("/users/me/favorites", response_model=FavoriteOut, status_code=status.HTTP_201_CREATED)
async def create_favorite(event_id: int, user=Depends(require_user)):
    """Create a new favorite."""
    return await favorites_services.create_favorite_service(user.id, event_id)

@router.get("/users/me/favorites", response_model=list[EventOut], status_code=status.HTTP_200_OK)
async def get_user_favorite_events(user=Depends(require_user)):
    """Get all favorite events for a user."""
    favorites = await favorites_services.get_favorites_by_user_id_service(user.id)

    return [await get_event_by_id_service(favorite.event_id) for favorite in favorites]

@router.delete("/users/me/favorites/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_favorite(event_id: int, user=Depends(require_user)):
    """Delete a favorite."""
    return await favorites_services.delete_favorite_service(user.id, event_id)