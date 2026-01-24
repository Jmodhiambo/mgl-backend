#!/usr/bin/env python3
"""Organizer TicketType API routes."""

from fastapi import APIRouter, HTTPException, Depends
from app.schemas.ticket_type import TicketTypeOut, TicketTypeCreate, TicketTypeUpdate
import app.services.ticket_type_services as tt_services
from app.core.security import require_organizer

router = APIRouter()

@router.post("/organizers/me/events/{event_id}/ticket-types", response_model=TicketTypeOut)
async def create_ticket_type(event_id: int, ticket_type_in: TicketTypeCreate, organizer=Depends(require_organizer)):
    """Create a new TicketType."""
    return await tt_services.create_ticket_type_service(event_id, ticket_type_in)

@router.put("/organizers/me/ticket-types/{ticket_type_id}", response_model=TicketTypeOut)
async def update_ticket_type(ticket_type_id: int, ticket_type_in: TicketTypeUpdate, organizer=Depends(require_organizer)):
    """Update an existing TicketType."""
    ticket_type = await tt_services.update_ticket_type_service(ticket_type_id, ticket_type_in)
    if not ticket_type:
        raise HTTPException(status_code=404, detail="TicketType not found")
    return ticket_type

@router.delete("/organizers/me/ticket-types/{ticket_type_id}", response_model=dict)
async def delete_ticket_type(ticket_type_id: int, organizer=Depends(require_organizer)):
    """Delete a TicketType by ID."""
    success = await tt_services.delete_ticket_type_service(ticket_type_id)
    if not success:
        raise HTTPException(status_code=404, detail="TicketType not found")
    return {"detail": "TicketType deleted successfully"}

@router.get("/organizers/me/events/{event_id}/ticket-types", response_model=list[TicketTypeOut])
async def get_ticket_types_by_event(event_id: int, organizer=Depends(require_organizer)):
    """Get TicketTypes for a specific event."""
    return await tt_services.list_ticket_types_by_event_id_service(event_id)

@router.get("/organizers/me/ticket-types/{ticket_type_id}", response_model=TicketTypeOut)
async def fetch_ticket_type(ticket_type_id: int, organizer=Depends(require_organizer)):
    """Get a specific TicketType by ID."""
    ticket_type = await tt_services.get_ticket_type_by_id_service(ticket_type_id)
    if not ticket_type:
        raise HTTPException(status_code=404, detail="TicketType not found")
    return ticket_type