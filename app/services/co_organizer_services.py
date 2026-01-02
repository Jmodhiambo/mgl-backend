#!/usr/bin/env python3
"""Service layer fot the CoOrganizer model in MGLTickets."""

import app.db.repositories.co_organizer_repo as co_repo
from app.schemas.co_organizer import CoOrganizerOut
from typing import Optional
from datetime import datetime
from app.core.logging_config import logger

async def create_co_organizer_service(user_id: int, organizer_id: int, event_id: int) -> CoOrganizerOut:
    """Create a new event co-organizer in the database."""
    logger.info(f"Creating a new co-organizer for user with ID: {user_id}, organizer with ID: {organizer_id}, and event with ID: {event_id}")
    return await co_repo.create_co_organizer_repo(user_id=user_id, organizer_id=organizer_id, event_id=event_id)

async def get_all_event_co_organizers_service(event_id: int) -> Optional[list[CoOrganizerOut]]:
    """Get all co-organizers for an event."""
    logger.info(f"Getting all co-organizers for event with ID: {event_id}")
    return await co_repo.get_all_event_co_organizers_repo(event_id=event_id)

async def get_user_co_organizing_events_service(user_id: int) -> Optional[list[CoOrganizerOut]]:
    """Get all events that a user is co-organizing."""
    logger.info(f"Getting all events that user with ID: {user_id} is co-organizing")
    return await co_repo.get_user_co_organizing_events_repo(user_id=user_id)