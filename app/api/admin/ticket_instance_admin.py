#!/usr/bin/env python3
"""TicketInstance admin routes."""

from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends, status
from app.schemas.ticket_instance import (
    TicketInstanceOut, TicketInstanceCreate, TicketInstanceUpdate,
    CheckInRequest, CheckInByCodeRequest, CheckInResponse
)
import app.services.ticket_instance_services as ti_services
from app.core.security import require_admin
from app.services.audit_log_services import log_admin_action_service

router = APIRouter()


@router.post("/admin/ticket-instances", response_model=TicketInstanceOut, status_code=status.HTTP_201_CREATED)
async def create_ticket_instance_admin(
    ticket_instance_create: TicketInstanceCreate,
    background_tasks: BackgroundTasks,
    admin=Depends(require_admin),
):
    """Create a new TicketInstance as an admin.

    event_id must be included in the request body (part of TicketInstanceCreate)
    so the signed QR payload can be computed server-side. Supply it alongside
    the other fields: booking_id, ticket_type_id, user_id, price, code, etc.
    """
    ticket_instance = await ti_services.create_ticket_instance(ticket_instance_create)

    background_tasks.add_task(
        log_admin_action_service,
        admin_id=admin.id,
        admin_name=admin.name,
        action="create_ticket_instance",
        target_type="ticket_instance",
        target_id=ticket_instance.id,
        details={"admin": admin.name},
    )

    return ticket_instance


@router.post(
    "/admin/check-in",
    response_model=CheckInResponse,
    status_code=status.HTTP_200_OK,
)
async def admin_check_in_ticket(
    body: CheckInRequest,
    admin=Depends(require_admin),
):
    """
    Admin QR gate scan. Validates HMAC signature and checks the payload's
    embedded event_id matches body.event_id (admin must select the event
    before scanning). Admin name stored as scanned_by on the ticket row.
    """
    return await ti_services.check_in_ticket_admin_service(
        raw_payload=body.payload,
        event_id=body.event_id,
        scanned_by=admin.name,
    )
 
 
@router.post(
    "/admin/check-in/by-code",
    response_model=CheckInResponse,
    status_code=status.HTTP_200_OK,
)
async def admin_check_in_by_code(
    body: CheckInByCodeRequest,
    admin=Depends(require_admin),
):
    """
    Admin manual code fallback. Scoped to body.event_id.
    Admin name stored as scanned_by on the ticket row.
    """
    return await ti_services.check_in_ticket_admin_by_code_service(
        code=body.code,
        event_id=body.event_id,
        scanned_by=admin.name,
    )

@router.put("/admin/ticket-instances/{ticket_instance_id}", response_model=TicketInstanceOut, status_code=status.HTTP_200_OK)
async def update_ticket_instance_admin(
    ticket_instance_id: int,
    ticket_instance_update: TicketInstanceUpdate,
    background_tasks: BackgroundTasks,
    admin=Depends(require_admin),
):
    """Update an existing TicketInstance as an admin."""
    ticket_instance = await ti_services.update_ticket_instance(ticket_instance_id, ticket_instance_update)
    if not ticket_instance:
        raise HTTPException(status_code=404, detail="TicketInstance not found")

    background_tasks.add_task(
        log_admin_action_service,
        admin_id=admin.id,
        admin_name=admin.name,
        action="update_ticket_instance",
        target_type="ticket_instance",
        target_id=ticket_instance.id,
        details={"admin": admin.name, "status": ticket_instance_update.status},
    )

    return ticket_instance


@router.delete("/admin/ticket-instances/{ticket_instance_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_ticket_instance_admin(
    ticket_instance_id: int,
    background_tasks: BackgroundTasks,
    admin=Depends(require_admin),
):
    """Delete a TicketInstance as an admin."""
    success = await ti_services.delete_ticket_instance(ticket_instance_id)
    if not success:
        raise HTTPException(status_code=404, detail="TicketInstance not found")

    background_tasks.add_task(
        log_admin_action_service,
        admin_id=admin.id,
        admin_name=admin.name,
        action="delete_ticket_instance",
        target_type="ticket_instance",
        target_id=ticket_instance_id,
        details={"admin": admin.name},
    )

    return {"detail": "TicketInstance deleted successfully"}


# Specific GET routes BEFORE /{ticket_instance_id} to avoid route shadowing

@router.get("/admin/ticket-instances", response_model=list[TicketInstanceOut], status_code=status.HTTP_200_OK)
async def list_ticket_instances_admin(admin=Depends(require_admin)):
    """List all TicketInstances as an admin."""
    return await ti_services.list_ticket_instances()


@router.get("/admin/ticket-instances/date-range/{start_date}-{end_date}", response_model=list[TicketInstanceOut], status_code=status.HTTP_200_OK)
async def list_ticket_instances_in_date_range_admin(
    start_date: datetime, end_date: datetime, admin=Depends(require_admin)
):
    """List TicketInstances created within a specific date range as an admin."""
    return await ti_services.list_ticket_instances_in_date_range(start_date, end_date)


@router.get("/admin/ticket-instances/status/{status}", response_model=list[TicketInstanceOut], status_code=status.HTTP_200_OK)
async def get_ticket_instances_by_status_admin(status: str, admin=Depends(require_admin)):
    """Get TicketInstances filtered by their status as an admin."""
    return await ti_services.get_ticket_instances_by_status(status)


@router.get("/admin/ticket-instances/users/{user_id}", response_model=list[TicketInstanceOut], status_code=status.HTTP_200_OK)
async def get_ticket_instances_by_user_admin(user_id: int, admin=Depends(require_admin)):
    """Get TicketInstances for a specific user as an admin."""
    return await ti_services.get_ticket_instances_by_user(user_id)


@router.get("/admin/ticket-instances/{ticket_instance_id}", response_model=TicketInstanceOut, status_code=status.HTTP_200_OK)
async def get_ticket_instance_admin(ticket_instance_id: int, admin=Depends(require_admin)):
    """Get a specific TicketInstance by ID as an admin."""
    ticket_instance = await ti_services.get_ticket_instance_by_id(ticket_instance_id)
    if not ticket_instance:
        raise HTTPException(status_code=404, detail="TicketInstance not found")
    return ticket_instance