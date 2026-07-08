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
    ticket_type_in: TicketTypeCreate
) -> dict:
    """
    Create a new TicketType."""
    logger.info(f"Creating TicketType with data: {ticket_type_in.model_dump()}")
    ticket_type = await tt_repo.create_ticket_type_repo(ticket_type_in)
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
    """
    Update an existing TicketType.

    Supports partial updates (e.g. the reactivate/deactivate toggle, which
    only sends `is_active`). The "can't drop capacity below quantity_sold"
    guard only applies when `total_quantity` is actually part of the
    payload — otherwise `ticket_type_in.total_quantity` is None and
    `None < ticket.quantity_sold` raises a TypeError, which is what was
    breaking the is_active-only toggle.
    """
    ticket = await get_ticket_type_by_id_service(ticket_type_id)
    if not ticket:
        logger.warning(f"TicketType with ID {ticket_type_id} not found for update")
        return None

    # Admin suspension freezes the ticket type entirely — not just is_active.
    # Letting an organizer (or anyone using this shared update path) still
    # change price/quantity/name while under suspension would undermine
    # whatever the suspension was for (fraud review, dispute, policy
    # violation). To change anything, the suspension must be lifted first.
    if ticket.suspended_by_admin_id is not None:
        logger.warning(
            f"Blocked update attempt on admin-suspended TicketType {ticket_type_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This ticket type has been suspended by an administrator and cannot be edited. Contact support.",
        )

    if (
        ticket_type_in.total_quantity is not None
        and ticket_type_in.total_quantity < ticket.quantity_sold
    ):
        logger.warning(
            f"Total quantity cannot be less than quantity sold for TicketType with ID {ticket_type_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Total quantity cannot be less than quantity sold",
        )

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


async def update_ticket_type_status_service(ticket_type_id: int, is_active: bool) -> Optional[dict]:
    """Update the active status of a TicketType."""
    logger.info(f"Updating status of TicketType with ID: {ticket_type_id} to is_active={is_active}")
    ticket_type = await tt_repo.update_ticket_type_status_repo(ticket_type_id, is_active)
    if ticket_type:
        logger.info(f"Updated TicketType status: {ticket_type}")
    else:
        logger.warning(f"TicketType with ID {ticket_type_id} not found for status update")
    return ticket_type


async def suspend_ticket_type_service(
    ticket_type_id: int,
    admin_id: int,
    admin_name: str,
    reason: str,
) -> Optional[dict]:
    """
    Admin-only: suspend a TicketType. Forces is_active False and stamps
    who suspended it, when, and why.
    """
    logger.info(
        f"[ADMIN] Suspending TicketType {ticket_type_id} "
        f"(by admin_id={admin_id}, reason={reason!r})"
    )
    ticket_type = await tt_repo.suspend_ticket_type_repo(
        ticket_type_id, admin_id=admin_id, admin_name=admin_name, reason=reason
    )
    if not ticket_type:
        logger.warning(f"TicketType with ID {ticket_type_id} not found for suspension")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TicketType not found")
    logger.info(f"Suspended TicketType: {ticket_type}")
    return ticket_type


async def unsuspend_ticket_type_service(ticket_type_id: int) -> Optional[dict]:
    """
    Admin-only: lift a suspension. Deliberately leaves is_active untouched —
    the organizer must explicitly reactivate the ticket type afterward.
    """
    logger.info(f"[ADMIN] Lifting suspension on TicketType with ID: {ticket_type_id}")
    ticket_type = await tt_repo.unsuspend_ticket_type_repo(ticket_type_id)
    if not ticket_type:
        logger.warning(f"TicketType with ID {ticket_type_id} not found for unsuspend")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TicketType not found")
    logger.info(f"Unsuspended TicketType: {ticket_type}")
    return ticket_type

async def delete_ticket_type_service(ticket_type_id: int) -> bool:
    """
    Delete a TicketType by ID.
    If the type has existing ticket instances it is deactivated instead
    of deleted, and a 400 is raised to inform the caller.
    """
    ticket = await get_ticket_type_by_id_service(ticket_type_id)
    if not ticket:
        logger.warning(f"TicketType with ID {ticket_type_id} not found for deletion")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TicketType not found")

    # Same reasoning as update_ticket_type_service: nothing should change
    # about a suspended ticket type — including deleting it — until an
    # admin lifts the suspension. Otherwise an organizer could just delete
    # their way around a suspension instead of resolving whatever caused it.
    if ticket.suspended_by_admin_id is not None:
        logger.warning(
            f"Blocked delete attempt on admin-suspended TicketType {ticket_type_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This ticket type has been suspended by an administrator and cannot be deleted. Contact support.",
        )

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


async def list_all_ticket_types_by_event_id_service(event_id: int) -> list[dict]:
    """
    List every TicketType for a given Event ID, active or not.
    Used by the organizer and admin routers.
    """
    logger.info(f"Listing ALL TicketTypes for Event ID: {event_id}")
    ticket_types = await tt_repo.list_all_ticket_types_by_event_id_repo(event_id)
    logger.info(f"Found {len(ticket_types)} TicketTypes (all) for Event ID: {event_id}")
    return ticket_types


async def list_active_ticket_types_by_event_id_service(event_id: int) -> list[dict]:
    """
    List only is_active TicketTypes for a given Event ID.
    Used by the public/buyer-facing router.
    """
    logger.info(f"Listing ACTIVE TicketTypes for Event ID: {event_id}")
    ticket_types = await tt_repo.list_active_ticket_types_by_event_id_repo(event_id)
    logger.info(f"Found {len(ticket_types)} active TicketTypes for Event ID: {event_id}")
    return ticket_types