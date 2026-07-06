#!/usr/bin/env python3
"""Admin TicketType API routes."""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from app.schemas.ticket_type import TicketTypeOut, TicketTypeCreate, TicketTypeUpdate
import app.services.ticket_type_services as tt_services
from app.core.security import require_admin
from app.services.audit_log_services import log_admin_action_service

router = APIRouter()

@router.post("/admin/ticket-types", response_model=TicketTypeOut)
async def tt_admin_create_ticket_type(
    ticket_type_in: TicketTypeCreate,
    background_tasks: BackgroundTasks,
    admin=Depends(require_admin),
):
    """Create a new TicketType."""
    ticket_type = await tt_services.create_ticket_type_service(ticket_type_in=ticket_type_in)

    background_tasks.add_task(
        log_admin_action_service,
        admin_id=admin.id,
        admin_name=admin.name,
        action="create_ticket_type",
        target_type="ticket_type",
        target_id=ticket_type.id,
        details={"admin": admin.name},
    )

    return ticket_type

# Specific GET routes BEFORE /{ticket_type_id} to avoid route shadowing
@router.get("/admin/events/{event_id}/ticket-types", response_model=list[TicketTypeOut])
async def tt_admin_get_ticket_types_by_event(event_id: int, admin=Depends(require_admin)):
    """Get all TicketTypes (active and inactive) for a specific event."""
    return await tt_services.list_all_ticket_types_by_event_id_service(event_id)

@router.get("/admin/ticket-types/{ticket_type_id}", response_model=TicketTypeOut)
async def tt_admin_get_ticket_type(ticket_type_id: int, admin=Depends(require_admin)):
    """Get a specific TicketType by ID."""
    ticket_type = await tt_services.get_ticket_type_by_id_service(ticket_type_id)
    if not ticket_type:
        raise HTTPException(status_code=404, detail="TicketType not found")
    return ticket_type

@router.put("/admin/ticket-types/{ticket_type_id}", response_model=TicketTypeOut)
async def tt_admin_update_ticket_type(
    ticket_type_id: int,
    ticket_type_in: TicketTypeUpdate,
    background_tasks: BackgroundTasks,
    admin=Depends(require_admin),
):
    """Update an existing TicketType."""
    ticket_type = await tt_services.update_ticket_type_service(ticket_type_id, ticket_type_in)
    if not ticket_type:
        raise HTTPException(status_code=404, detail="TicketType not found")

    background_tasks.add_task(
        log_admin_action_service,
        admin_id=admin.id,
        admin_name=admin.name,
        action="update_ticket_type",
        target_type="ticket_type",
        target_id=ticket_type.id,
        details={"admin": admin.name},
    )
    return ticket_type

@router.delete("/admin/ticket-types/{ticket_type_id}", response_model=dict)
async def tt_admin_delete_ticket_type(
    ticket_type_id: int,
    background_tasks: BackgroundTasks,
    admin=Depends(require_admin),
):
    """Delete a TicketType by ID."""
    success = await tt_services.delete_ticket_type_service(ticket_type_id)
    if not success:
        raise HTTPException(status_code=404, detail="TicketType not found")

    background_tasks.add_task(
        log_admin_action_service,
        admin_id=admin.id,
        admin_name=admin.name,
        action="delete_ticket_type",
        target_type="ticket_type",
        target_id=ticket_type_id,
        details={"admin": admin.name},
    )

    return {"detail": "TicketType deleted successfully"}