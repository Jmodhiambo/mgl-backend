#!/usr/bin/env python3
"""TicketType API routes for user operations."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.ticket_type import TicketTypeOut, TicketTypeCreate, TicketTypeUpdate
import app.services.ticket_type_services as tt_services
from app.core.security import get_current_user

router = APIRouter()

@router.get("/events/{event_id}/ticket-types", response_model=list[TicketTypeOut])
async def get_ticket_types_by_event(event_id: int, user=Depends(get_current_user)):
    """Get TicketTypes for a specific event."""
    return tt_services.list_ticket_types_by_event_id_service(event_id)