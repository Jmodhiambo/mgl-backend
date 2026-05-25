#!/usr/bin/env python3
"""API routes for TicketInstance operations."""

from fastapi import APIRouter, Depends, status
from app.schemas.ticket_instance import TicketInstanceOut
import app.services.ticket_instance_services as ti_services
from app.core.security import require_user

router = APIRouter()

@router.get("/users/me/ticket-instances", response_model=list[TicketInstanceOut], status_code=status.HTTP_200_OK)
async def get_ticket_instances_by_user(user=Depends(require_user)):
    """Get TicketInstances for a specific user."""
    return await ti_services.get_ticket_instances_by_user(user.id)

@router.get("/users/me/ticket-instances/{ticket_instance_id}", response_model=TicketInstanceOut, status_code=status.HTTP_200_OK)
async def get_ticket_instance(ticket_instance_id: int, user=Depends(require_user)):
    """Get a specific TicketInstance by ID."""
    return await ti_services.get_ticket_instance_by_id(ticket_instance_id)

# @router.get("/ticket-instances/{ticket_instance_id}/qr", response_model=TicketInstanceOut)
# async def get_ticket_instance_qr(ticket_instance_id: int, user=Depends(require_user)):
#     """Get the QR code for a specific TicketInstance by ID."""
#     # This is a placeholder implementation; actual QR code generation logic would go here.