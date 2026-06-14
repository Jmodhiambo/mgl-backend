#!/usr/bin/env python3
"""User-facing ticket instance routes for MGLTickets."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.ticket_instance import TicketInstanceOut
import app.services.ticket_instance_services as ti_services
from app.core.security import require_user

router = APIRouter()

@router.get(
    "/users/me/ticket-instances",
    response_model=list[TicketInstanceOut],
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