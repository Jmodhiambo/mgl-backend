#!/usr/bin/env python3
"""User-facing ticket instance routes for MGLTickets."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.ticket_instance import (
    TicketInstanceEnrichedOut,
    TicketInstanceOut,
    TicketHolderNameUpdate,
)
import app.services.ticket_instance_services as ti_services
from app.core.security import require_user

router = APIRouter()

@router.get(
    "/users/me/ticket-instances",
    response_model=list[TicketInstanceEnrichedOut],
    status_code=status.HTTP_200_OK,
)
async def get_ticket_instances_by_user(user=Depends(require_user)):
    """Get all ticket instances for the current user.

    Returns enriched rows including event_title, venue, event_date,
    ticket_type_name via a joined query. MyTickets.tsx and Dashboard depends on these fields.
    """
    return await ti_services.get_ticket_instances_by_user_enriched(user.id)


@router.get(
    "/users/me/ticket-instances/{ticket_instance_id}",
    response_model=TicketInstanceOut,
    status_code=status.HTTP_200_OK,
)
async def get_ticket_instance(ticket_instance_id: int, user=Depends(require_user)):
    """Get a specific ticket instance by ID."""
    ti = await ti_services.get_ticket_instance_by_id(ticket_instance_id)
    if not ti:
        raise HTTPException(status_code=404, detail="Ticket instance not found")
    return ti


@router.patch(
    "/users/me/ticket-instances/{ticket_instance_id}/holder-name",
    response_model=TicketInstanceOut,
    status_code=status.HTTP_200_OK,
)
async def update_ticket_holder_name(
    ticket_instance_id: int,
    payload: TicketHolderNameUpdate,
    user=Depends(require_user),
):
    """Rename the holder of a ticket instance the current user owns.

    Only allowed while the ticket is still 'issued' — once it's been
    scanned or cancelled, the name is locked. This lets us skip collecting
    a per-ticket holder name during checkout (avoiding a bottleneck at
    booking time) while still letting the buyer assign tickets afterward.
    """
    result = await ti_services.update_ticket_holder_name_service(
        ticket_instance_id, user.id, payload.issued_to
    )
    if result["outcome"] == "not_found":
        raise HTTPException(status_code=404, detail="Ticket instance not found")
    if result["outcome"] == "invalid_status":
        raise HTTPException(
            status_code=409,
            detail="Ticket holder name can only be changed while the ticket is 'issued'",
        )
    return result["ticket_instance"]