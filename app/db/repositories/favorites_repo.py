#!/usr/bin/env python3
"""Repository for Favorite model operations."""

from typing import Optional
from sqlalchemy import select
from app.db.session import get_async_session
from app.db.models.favorites import Favorite
from app.schemas.favorites import FavoriteOut

async def create_favorite_repo(user_id: int, event_id: int) -> FavoriteOut:
    """Create a new favorite in the database."""
    async with get_async_session() as session:
        favorite = Favorite(user_id=user_id, event_id=event_id)
        session.add(favorite)
        await session.commit()
        await session.refresh(favorite)
        return FavoriteOut.model_validate(favorite)

async def get_favorite_by_id_repo(favorite_id: int) -> Optional[FavoriteOut]:
    """Retrieve a favorite by its ID."""
    async with get_async_session() as session:
        favorite = await session.execute(select(Favorite).where(Favorite.id == favorite_id))
        favorite = favorite.scalars().unique().one_or_none()
        return FavoriteOut.model_validate(favorite)
    

async def delete_favorite_repo(user_id: int, event_id: int) -> bool:
    """Delete a favorite from the database."""
    async with get_async_session() as session:
        favorite = await session.execute(select(Favorite).where(Favorite.user_id == user_id).where(Favorite.event_id == event_id))
        favorite = favorite.scalars().unique().one_or_none()
        if favorite is None:
            return False
        await session.delete(favorite)
        await session.commit()
        return True


async def get_favorites_by_user_id_repo(user_id: int) -> list[FavoriteOut]:
    """Get all favorites for a user."""
    async with get_async_session() as session:
        favorites = await session.execute(select(Favorite).where(Favorite.user_id == user_id))
        favorites = favorites.scalars().unique().all()
        return [FavoriteOut.model_validate(favorite) for favorite in favorites]