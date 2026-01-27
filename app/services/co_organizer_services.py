#!/usr/bin/env python3
"""Service layer for the CoOrganizer model in MGLTickets."""

from fastapi import HTTPException, status
import app.db.repositories.co_organizer_repo as co_repo
from app.schemas.co_organizer import CoOrganizerOut
from typing import Optional
from datetime import datetime
from app.db.repositories.user_repo import get_user_by_email_repo
from app.core.logging_config import logger
from app.utils.token_verification import generate_verification_token
# from app.emails.templates.co_organizer_invitation_email import {
#    send_co_organizer_invitation_email_to_non_existing_user, send_co_organizer_invitation_email_to_existing_user
# }

async def create_co_organizer_service(email: str, organizer_id: int, event_id: int, invited_by: int) -> CoOrganizerOut:
    """Create a new event co-organizer in the database."""
    # Get the user
    user = await get_user_by_email_repo(email=email)

    # Generate activation token
    #token = generate_verification_token()
    if not user:
        logger.info(f"User with Email: {email} not found. Sending invitation email...")
        # Send an email iniviting the user to create an account
        # send_co_organizer_invitation_email_to_non_existing_user(
        #     to_email=user.email,
        #     to_name=user.name,
        #     inviter_name=inviter.name,
        #     event_title=event.title,
        #     event_id=event_id,
        #     activation_token=token
        # )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Check if the user is already a co-organizer
    if await co_repo.check_if_co_organizer_repo(user_id=user.id, event_id=event_id):
        logger.info(f"User with Email: {email} is already a co-organizer for event with ID: {event_id}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a co-organizer")
        
    logger.info(f"Creating a new co-organizer for user with Email: {email}, organizer with ID: {organizer_id}, and event with ID: {event_id}")

    result = await co_repo.create_co_organizer_repo(user_id=user.id, organizer_id=organizer_id, event_id=event_id, invited_by=invited_by)
    if result:
        # Send an email iniviting the user to create an account
        # send_co_organizer_invitation_email_to_existing_user(email=email, invited_by=invited_by)
        pass
    return result

async def get_co_organizer_by_id_service(co_organizer_id: int) -> Optional[CoOrganizerOut]:
    """Get a co-organizer by ID."""
    logger.info(f"Getting co-organizer with ID: {co_organizer_id}")
    return await co_repo.get_co_organizer_by_id_repo(co_organizer_id=co_organizer_id)

async def update_create_co_organizer_status_service(co_organizer_id: int, create_co_organizer: bool) -> None:
    """Update the create_co_organizer status of a co-organizer.
    If True the user can invite co-organizers to the event.
    The previlage is only given to by the organizer.
    """
    logger.info(f"Updating create_co_organizer status for co-organizer with ID: {co_organizer_id}")
    return await co_repo.update_create_co_organizer_status_repo(co_organizer_id=co_organizer_id, create_co_organizer=create_co_organizer)

async def get_all_event_co_organizers_service(event_id: int) -> Optional[list[CoOrganizerOut]]:
    """Get all co-organizers for an event."""
    logger.info(f"Getting all co-organizers for event with ID: {event_id}")
    return await co_repo.get_all_event_co_organizers_repo(event_id=event_id)

async def get_user_co_organizing_events_service(user_id: int) -> Optional[list[CoOrganizerOut]]:
    """Get all events that a user is co-organizing."""
    logger.info(f"Getting all events that user with ID: {user_id} is co-organizing")
    return await co_repo.get_user_co_organizing_events_repo(user_id=user_id)

async def delete_co_organizer_service(co_organizer_id: int) -> None:
    """Delete a co-organizer from the database."""
    logger.info(f"Deleting co-organizer with ID: {co_organizer_id}")
    return await co_repo.delete_co_organizer_repo(co_organizer_id=co_organizer_id)