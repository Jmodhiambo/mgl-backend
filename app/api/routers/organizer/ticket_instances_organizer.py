#!/usr/bin/env python3
"""TicketInstance routes for organizer operations."""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.ticket_instance import TicketInstanceOut
import app.services.ticket_instance_services as ti_services
from app.core.security import require_organizer

router = APIRouter()

@router.get("/organizer/ticket-instances", response_model=list[TicketInstanceOut],)
async def list_ticket_instances_organizer(organizer=Depends(require_organizer)):
    """List all TicketInstances for organizers."""
    return await ti_services.list_ticket_instances()

@router.get("/organizer/ticket-instances/{ticket_instance_id}", response_model=TicketInstanceOut)
async def get_ticket_instance_organizer(ticket_instance_id: int, organizer=Depends(require_organizer)):
    """Get a specific TicketInstance by ID for organizers."""
    ticket_instance = await ti_services.get_ticket_instance_by_id(ticket_instance_id)
    if not ticket_instance:
        raise HTTPException(status_code=404, detail="TicketInstance not found")
    return ticket_instance

@router.get("/organizer/ticket-instances/status/{status}", response_model=list[TicketInstanceOut])
async def get_ticket_instances_by_status_organizer(status: str, organizer=Depends(require_organizer)):
    """Get TicketInstances filtered by status for organizers."""
    return await ti_services.get_ticket_instances_by_status(status)

@router.get("/organizer/ticket-instances/date-range/{start_date}-{end_date}", response_model=list[TicketInstanceOut])
async def list_ticket_instances_in_date_range_organizer(start_date: datetime, end_date: datetime, organizer=Depends(require_organizer)):
    """List TicketInstances created within a specific date range for organizers."""    
    return await ti_services.list_ticket_instances_in_date_range(start_date, end_date)