#!/usr/bin/env python3
"""Admin TicketType API routes."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.ticket_type import TicketTypeOut, TicketTypeCreate, TicketTypeUpdate
import app.services.ticket_type_services as tt_services
from app.core.security import require_admin

router = APIRouter()

# Adding "tt_admin" to route functions to prevent duplicate ID issues
@router.post("/admin/ticket-types", response_model=TicketTypeOut)
async def tt_admin_create_ticket_type(ticket_type_in: TicketTypeCreate, admin=Depends(require_admin)):
    """Create a new TicketType."""
    return tt_services.create_ticket_type_service(ticket_type_in)

@router.put("/admin/ticket-types/{ticket_type_id}", response_model=TicketTypeOut)
async def tt_admin_update_ticket_type(ticket_type_id: int, ticket_type_in: TicketTypeUpdate, admin=Depends(require_admin)):
    """Update an existing TicketType."""
    ticket_type = tt_services.update_ticket_type_service(ticket_type_id, ticket_type_in)
    if not ticket_type:
        raise HTTPException(status_code=404, detail="TicketType not found")
    return ticket_type

@router.delete("/admin/ticket-types/{ticket_type_id}", response_model=dict)
async def tt_admin_delete_ticket_type(ticket_type_id: int, admin=Depends(require_admin)):
    """Delete a TicketType by ID."""
    success = tt_services.delete_ticket_type_service(ticket_type_id)
    if not success:
        raise HTTPException(status_code=404, detail="TicketType not found")
    return {"detail": "TicketType deleted successfully"}

@router.get("/admin/ticket-types/{ticket_type_id}", response_model=TicketTypeOut)
async def tt_admin_get_ticket_type(ticket_type_id: int, admin=Depends(require_admin)):
    """Get a specific TicketType by ID."""
    ticket_type = tt_services.get_ticket_type_by_id_service(ticket_type_id)
    if not ticket_type:
        raise HTTPException(status_code=404, detail="TicketType not found")
    return ticket_type

@router.get("/admin/events/{event_id}/ticket-types", response_model=list[TicketTypeOut])
async def tt_admin_get_ticket_types_by_event(event_id: int, admin=Depends(require_admin)):
    """Get TicketTypes for a specific event."""
    return tt_services.list_ticket_types_by_event_id_service(event_id)