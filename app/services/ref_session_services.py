#!/usr/bin/env python3
"""RefreshSession services for MGLTickets."""

from datetime import datetime
from app.core.logging_config import logger
import app.db.repositories.ref_sessions_repo as ref_sessions_repo
from app.schemas.refresh_session import RefreshSessionCreate, RefreshSessionUpdate, RefreshSessionOut
from typing import Optional

async def create_refresh_session_service(session_id, user_id, refresh_token_hash, expires_at) -> RefreshSessionOut:
    """Create a new RefreshSession."""
    logger.info(f"Creating RefreshSession for user_id: {user_id}")
    return await ref_sessions_repo.create_refresh_session_repo(
        RefreshSessionCreate(
            session_id=session_id,
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at
        )
    )

async def get_refresh_session_service(session_id: str) -> Optional[RefreshSessionOut]:
    """Get a RefreshSession by session_id."""
    logger.info(f"Getting RefreshSession for session_id: {session_id}")
    return await ref_sessions_repo.get_refresh_session_repo(session_id)

async def get_refresh_session_by_user_id_service(user_id: int) -> Optional[RefreshSessionOut]:
    """Get a RefreshSession by user_id."""
    logger.info(f"Getting RefreshSession for user_id: {user_id}")
    return await ref_sessions_repo.get_refresh_session_by_user_id_repo(user_id)

async def update_refresh_session_service(session_id: str, refresh_session_update: RefreshSessionUpdate) -> Optional[RefreshSessionOut]:
    """Update a RefreshSession by session_id."""
    logger.info(f"Updating RefreshSession for session_id: {session_id}")
    return await ref_sessions_repo.update_refresh_session_repo(session_id, refresh_session_update)

async def delete_refresh_session_service(session_id: str) -> bool:
    """Delete a RefreshSession by session_id."""
    logger.info(f"Deleting RefreshSession for session_id: {session_id}")
    return await ref_sessions_repo.delete_refresh_session_repo(session_id)