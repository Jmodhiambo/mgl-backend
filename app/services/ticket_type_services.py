#!/usr/bin/env python3
"""
Service layer for TicketType operations.

Signature fix applied:
  The original create_ticket_type_service(ticket_type_in) accepted one
  argument. The organizer router passes (event_id, ticket_type_in) while
  the admin router passes only (ticket_type_in). The service now accepts
  an optional event_id so both call sites work without changes to the
  routers.

  The event_id is written into the TicketTypeCreate payload before
  hitting the repo, so the repo stays unchanged.
"""

from fastapi import HTTPException, status
from typing import Optional
import app.db.repositories.ticket_type_repo as tt_repo
from app.schemas.ticket_type import TicketTypeCreate, TicketTypeUpdate
from app.core.logging_config import logger


async def create_ticket_type_service(
    ticket_type_in: TicketTypeCreate,
    event_id: Optional[int] = None,
) -> dict:
    """
    Create a new TicketType.

    If event_id is provided (organizer router passes it as a path param),
    it overrides whatever event_id is already in ticket_type_in.
    The admin router passes event_id inside the TicketTypeCreate body,
    so event_id will be None there and the body value is used as-is.
    """
    if event_id is not None:
        # Organizer path: event_id comes from the URL, inject it
        data = ticket_type_in.model_copy(update={"event_id": event_id})
    else:
        data = ticket_type_in

    logger.info(f"Creating TicketType with data: {data.model_dump()}")
    ticket_type = await tt_repo.create_ticket_type_repo(data)
    logger.info(f"Created TicketType with ID: {ticket_type.id}")
    return ticket_type


async def get_ticket_type_by_id_service(ticket_type_id: int) -> Optional[dict]:
    """Get a TicketType by ID."""
    logger.info(f"Retrieving TicketType with ID: {ticket_type_id}")
    ticket_type = await tt_repo.get_ticket_type_by_id_repo(ticket_type_id)
    if ticket_type:
        logger.info(f"Retrieved TicketType: {ticket_type}")
    else:
        logger.warning(f"TicketType with ID {ticket_type_id} not found")
    return ticket_type


async def update_ticket_type_service(
    ticket_type_id: int, ticket_type_in: TicketTypeUpdate
) -> Optional[dict]:
    """Update an existing TicketType."""
    logger.info(
        f"Updating TicketType with ID: {ticket_type_id} "
        f"using data: {ticket_type_in.model_dump(exclude_unset=True)}"
    )
    ticket_type = await tt_repo.update_ticket_type_repo(ticket_type_id, ticket_type_in)
    if ticket_type:
        logger.info(f"Updated TicketType: {ticket_type}")
    else:
        logger.warning(f"TicketType with ID {ticket_type_id} not found for update")
    return ticket_type


async def delete_ticket_type_service(ticket_type_id: int) -> bool:
    """
    Delete a TicketType by ID.
    If the type has existing ticket instances it is deactivated instead
    of deleted, and a 400 is raised to inform the caller.
    """
    has_instances = await tt_repo.check_if_ticket_type_has_instances_repo(ticket_type_id)
    if has_instances:
        logger.warning(
            f"TicketType {ticket_type_id} has instances — marking inactive instead of deleting."
        )
        await tt_repo.update_ticket_type_status_repo(ticket_type_id, False)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "TicketType has existing bookings and cannot be deleted. "
                "It has been marked inactive and will not accept new bookings."
            ),
        )

    logger.info(f"Deleting TicketType with ID: {ticket_type_id}")
    success = await tt_repo.delete_ticket_type_repo(ticket_type_id)
    if not success:
        logger.warning(f"TicketType with ID {ticket_type_id} not found for deletion")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="TicketType not found"
        )
    logger.info(f"Deleted TicketType with ID: {ticket_type_id}")
    return success


async def list_ticket_types_by_event_id_service(event_id: int) -> list[dict]:
    """List all TicketTypes for a given Event ID."""
    logger.info(f"Listing TicketTypes for Event ID: {event_id}")
    ticket_types = await tt_repo.list_ticket_types_by_event_id_repo(event_id)
    logger.info(f"Found {len(ticket_types)} TicketTypes for Event ID: {event_id}")
    return ticket_types