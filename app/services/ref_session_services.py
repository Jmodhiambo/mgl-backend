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

async def update_refresh_session_service(session_id: str, token_hash: str, expires_at: datetime) -> Optional[RefreshSessionOut]:
    """Update a RefreshSession by session_id."""
    logger.info(f"Updating RefreshSession for session_id: {session_id}")
    return await ref_sessions_repo.update_refresh_session_repo(
        RefreshSessionUpdate(
            session_id=session_id,
            refresh_token_hash=token_hash,
            expires_at=expires_at            
        )
    )

async def revoke_refresh_session_service(session_id: str, new_session_id: str) -> Optional[RefreshSessionOut]:
    """Revoke a RefreshSession by session_id."""
    logger.info(f"Revoking RefreshSession for session_id: {session_id} to {new_session_id}")
    return await ref_sessions_repo.revoke_refresh_session_repo(session_id, new_session_id)

async def delete_refresh_session_service(session_id: str) -> bool:
    """Delete a RefreshSession by session_id."""
    logger.info(f"Deleting RefreshSession for session_id: {session_id}")
    return await ref_sessions_repo.delete_refresh_session_repo(session_id)

async def cleanup_expired_and_revoked_sessions_service(hours: int = 24) -> dict:
    """
    Clean up expired and revoked sessions older than specified hours.
    Returns count of deleted sessions and remaining active sessions.
    """
    logger.info(f"Starting cleanup of sessions older than {hours} hours...")
    
    deleted_count = await ref_sessions_repo.cleanup_expired_and_revoked_sessions_repo(hours)
    active_count = await ref_sessions_repo.get_active_session_count_repo()
    
    logger.info(
        f"Cleanup completed: {deleted_count} sessions deleted, "
        f"{active_count} active sessions remaining"
    )
    
    return {
        "deleted_count": deleted_count,
        "active_sessions": active_count,
        "cleanup_threshold_hours": hours
    }


async def cleanup_user_sessions_service(user_id: str) -> dict:
    """
    Clean up all sessions for a specific user.
    Useful for 'logout from all devices' functionality.
    """
    logger.info(f"Cleaning up all sessions for user {user_id}...")
    
    deleted_count = await ref_sessions_repo.cleanup_all_user_sessions_repo(user_id)
    
    logger.info(f"Deleted {deleted_count} sessions for user {user_id}")
    
    return {
        "deleted_count": deleted_count,
        "user_id": user_id
    }


async def get_user_session_stats_service(user_id: str) -> dict:
    """Get session statistics for a user"""
    active_sessions = await ref_sessions_repo.get_user_active_sessions_repo(user_id)
    
    return {
        "user_id": user_id,
        "active_sessions": active_sessions
    }