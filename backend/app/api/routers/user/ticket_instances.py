#!/usr/bin/env python3
"""API routes for TicketInstance operations."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.ticket_instance import TicketInstanceOut, TicketInstanceCreate, TicketInstanceUpdate
import app.services.ticket_instance_services as ti_services
from app.core.security import get_current_user

router = APIRouter()

@router.get("/users/{user_id}/ticket-instances", response_model=list[TicketInstanceOut])
async def get_ticket_instances_by_user(user_id: int, user=Depends(get_current_user)):
    """Get TicketInstances for a specific user."""
    return ti_services.get_ticket_instances_by_user(user_id)

@router.get("/ticket-instances/{ticket_instance_id}", response_model=TicketInstanceOut)
async def get_ticket_instance(ticket_instance_id: int, user=Depends(get_current_user)):
    """Get a specific TicketInstance by ID."""
    return ti_services.get_ticket_instance_by_id(ticket_instance_id)

# @router.get("/ticket-instances/{ticket_instance_id}/qr", response_model=TicketInstanceOut)
# async def get_ticket_instance_qr(ticket_instance_id: int, user=Depends(get_current_user)):
#     """Get the QR code for a specific TicketInstance by ID."""
#     # This is a placeholder implementation; actual QR code generation logic would go here.