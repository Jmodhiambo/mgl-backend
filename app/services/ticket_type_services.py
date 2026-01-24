#!/usr/bin/env python3
"""Service layer for TicketType operations."""

from fastapi import HTTPException, status
from typing import Optional
import app.db.repositories.ticket_type_repo as tt_repo
from app.schemas.ticket_type import TicketTypeCreate, TicketTypeUpdate
from datetime import datetime
from app.core.logging_config import logger

async def create_ticket_type_service(ticket_type_in: TicketTypeCreate) -> dict:
    """Service to create a new TicketType."""
    logger.info(f"Creating TicketType with data: {ticket_type_in.model_dump()}")
    ticket_type = await tt_repo.create_ticket_type_repo(ticket_type_in)
    logger.info(f"Created TicketType with ID: {ticket_type.id}")
    return ticket_type

async def get_ticket_type_by_id_service(ticket_type_id: int) -> Optional[dict]:
    """Service to get a TicketType by ID."""
    logger.info(f"Retrieving TicketType with ID: {ticket_type_id}")
    ticket_type = await tt_repo.get_ticket_type_by_id_repo(ticket_type_id)
    if ticket_type:
        logger.info(f"Retrieved TicketType: {ticket_type}")
    else:
        logger.warning(f"TicketType with ID {ticket_type_id} not found")
    return ticket_type

async def update_ticket_type_service(ticket_type_id: int, ticket_type_in: TicketTypeUpdate) -> Optional[dict]:
    """Service to update an existing TicketType."""
    logger.info(f"Updating TicketType with ID: {ticket_type_id} using data: {ticket_type_in.model_dump(exclude_unset=True)}")
    ticket_type = await tt_repo.update_ticket_type_repo(ticket_type_id, ticket_type_in)
    if ticket_type:
        logger.info(f"Updated TicketType: {ticket_type}")
    else:
        logger.warning(f"TicketType with ID {ticket_type_id} not found for update")
    return ticket_type

async def delete_ticket_type_service(ticket_type_id: int) -> bool:
    """Service to delete a TicketType by ID."""
    # Check if the ticket type has ticket instances. If so make it inactive instead of deleting it.
    ticket_type = await tt_repo.check_if_ticket_type_has_instances_repo(ticket_type_id)
    if ticket_type:
        logger.warning(f"TicketType with ID {ticket_type_id} has ticket instances and cannot be deleted, but has been marked as inactive and will not have any future bookings.")
        await tt_repo.update_ticket_type_status_repo(ticket_type_id, False)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TicketType has bookings and cannot be deleted, but has been marked as inactive and will not have any future bookings.")

    logger.info(f"Deleting TicketType with ID: {ticket_type_id}")
    success = await tt_repo.delete_ticket_type_repo(ticket_type_id)
    if success:
        logger.info(f"Deleted TicketType with ID: {ticket_type_id}")
    else:
        logger.warning(f"TicketType with ID {ticket_type_id} not found for deletion")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TicketType not found")
    return success

async def list_ticket_types_by_event_id_service(event_id: int) -> list[dict]:
    """Service to list all TicketTypes for a given Event ID."""
    logger.info(f"Listing TicketTypes for Event ID: {event_id}")
    ticket_types = await tt_repo.list_ticket_types_event_id_repo(event_id)
    logger.info(f"Found {len(ticket_types)} TicketTypes for Event ID: {event_id}")
    return ticket_types