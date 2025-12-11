#!/usr/bin/env python3
"""TicketType API routes for user operations."""

from fastapi import APIRouter, Depends
from app.schemas.ticket_type import TicketTypeOut
import app.services.ticket_type_services as tt_services
from app.core.security import require_user

router = APIRouter()

@router.get("/events/{event_id}/ticket-types", response_model=list[TicketTypeOut])
async def get_ticket_types_by_event(event_id: int, user=Depends(require_user)):
    """Get TicketTypes for a specific event."""
    return await tt_services.list_ticket_types_by_event_id_service(event_id)

@router.get("/ticket-types/{ticket_type_id}", response_model=TicketTypeOut)
async def get_ticket_type(ticket_type_id: int, user=Depends(require_user)):
    """Get a specific TicketType by ID."""
    return await tt_services.get_ticket_type_by_id_service(ticket_type_id)