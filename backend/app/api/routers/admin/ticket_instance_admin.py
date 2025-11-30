#!/usr/bin/env python3
"""TicketInstance admin routes."""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.ticket_instance import TicketInstanceOut, TicketInstanceCreate, TicketInstanceUpdate
import app.services.ticket_instance_services as ti_services
from app.core.security import require_admin

router = APIRouter()
@router.post("/admin/ticket-instances", response_model=TicketInstanceOut)
async def create_ticket_instance_admin(ticket_instance_create: TicketInstanceCreate, admin=Depends(require_admin)):
    """Create a new TicketInstance as an admin."""
    return ti_services.create_ticket_instance(ticket_instance_create)

@router.put("/admin/ticket-instances/{ticket_instance_id}", response_model=TicketInstanceOut)
async def update_ticket_instance_admin(ticket_instance_id: int, ticket_instance_update: TicketInstanceUpdate, admin=Depends(require_admin)):
    """Update an existing TicketInstance as an admin."""
    ticket_instance = ti_services.update_ticket_instance(ticket_instance_id, ticket_instance_update)
    if not ticket_instance:
        raise HTTPException(status_code=404, detail="TicketInstance not found")
    return ticket_instance

@router.delete("/admin/ticket-instances/{ticket_instance_id}", response_model=dict)
async def delete_ticket_instance_admin(ticket_instance_id: int, admin=Depends(require_admin)):
    """Delete a TicketInstance as an admin."""
    success = ti_services.delete_ticket_instance(ticket_instance_id)
    if not success:
        raise HTTPException(status_code=404, detail="TicketInstance not found")
    return {"detail": "TicketInstance deleted successfully"}

@router.get("/admin/ticket-instances", response_model=list[TicketInstanceOut])
async def list_ticket_instances_admin(admin=Depends(require_admin)):
    """List all TicketInstances as an admin."""
    return ti_services.list_ticket_instances()

@router.get("/admin/ticket-instances/date-range/{start_date}-{end_date}", response_model=list[TicketInstanceOut])
async def list_ticket_instances_in_date_range_admin(start_date: datetime, end_date: datetime, admin=Depends(require_admin)):
    """List TicketInstances created within a specific date range as an admin."""    
    return ti_services.list_ticket_instances_in_date_range(start_date, end_date)

@router.get("/admin/ticket-instances/status/{status}", response_model=list[TicketInstanceOut])
async def get_ticket_instances_by_status_admin(status: str, admin=Depends(require_admin)):
    """Get TicketInstances filtered by their status as an admin."""
    return ti_services.get_ticket_instances_by_status(status)

@router.get("/admin/ticket-instances/users/{user_id}", response_model=list[TicketInstanceOut])
async def get_ticket_instances_by_user_admin(user_id: int, admin=Depends(require_admin)):
    """Get TicketInstances for a specific user as an admin."""
    return ti_services.get_ticket_instances_by_user(user_id)

@router.get("/admin/ticket-instances/{ticket_instance_id}", response_model=TicketInstanceOut)
async def get_ticket_instance_admin(ticket_instance_id: int, admin=Depends(require_admin)):
    """Get a specific TicketInstance by ID as an admin."""
    ticket_instance = ti_services.get_ticket_instance_by_id(ticket_instance_id)
    if not ticket_instance:
        raise HTTPException(status_code=404, detail="TicketInstance not found")
    return ticket_instance