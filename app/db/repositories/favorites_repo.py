#!/usr/bin/env python3
"""Repository for Favorite model operations."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_async_session
from app.db.models.favorites import Favorite
from app.schemas.favorites import FavoriteOut, FavoriteWithEventOut


async def create_favorite_repo(user_id: int, event_id: int) -> FavoriteOut:
    """Create a new favorite. Returns bare FavoriteOut."""
    async with get_async_session() as session:
        favorite = Favorite(user_id=user_id, event_id=event_id)
        session.add(favorite)
        await session.commit()
        await session.refresh(favorite)
        return FavoriteOut.model_validate(favorite)


async def get_favorite_by_id_repo(favorite_id: int) -> Optional[FavoriteOut]:
    """Retrieve a favorite by its ID."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Favorite).where(Favorite.id == favorite_id)
        )
        favorite = result.scalars().unique().one_or_none()
        if not favorite:
            return None
        return FavoriteOut.model_validate(favorite)


async def delete_favorite_repo(user_id: int, event_id: int) -> bool:
    """Delete a favorite by user_id + event_id pair."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Favorite)
            .where(Favorite.user_id == user_id)
            .where(Favorite.event_id == event_id)
        )
        favorite = result.scalars().unique().one_or_none()
        if favorite is None:
            return False
        await session.delete(favorite)
        await session.commit()
        return True


async def get_favorites_by_user_id_repo(user_id: int) -> list[FavoriteWithEventOut]:
    """
    Get all favorites for a user with the event object eagerly loaded.

    Uses selectinload(Favorite.event) so SQLAlchemy fetches the related
    Event rows in a single IN query rather than N separate queries.
    Returns FavoriteWithEventOut so the router can return the full event
    data without a second fetch.
    """
    async with get_async_session() as session:
        result = await session.execute(
            select(Favorite)
            .where(Favorite.user_id == user_id)
            .options(selectinload(Favorite.event))
            .order_by(Favorite.created_at.desc())
        )
        favorites = result.scalars().unique().all()
        return [FavoriteWithEventOut.model_validate(f) for f in favorites]