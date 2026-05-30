#!/usr/bin/env python3
"""Admin API routes for Contact Message operations."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from typing import List, Optional
from app.core.security import require_admin
from app.schemas.contact_message import (
    ContactMessageOut,
    ContactMessageUpdate,
    ContactMessageStats,
    ContactMessageStatusUpdate
)
import app.services.contact_messages_services as contact_service
from app.services.audit_log_services import log_admin_action_service

router = APIRouter()


@router.get(
    "/admin/contact",
    response_model=List[ContactMessageOut],
    status_code=status.HTTP_200_OK
)
async def list_contact_messages(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    category: Optional[str] = None,
    admin=Depends(require_admin),
):
    """
    List all contact messages with optional filters.
    """
    if limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit cannot exceed 100"
        )

    return await contact_service.list_contact_messages_service(
        skip=skip,
        limit=limit,
        status=status,
        category=category
    )


@router.get(
    "/admin/contact/stats/overview",
    response_model=ContactMessageStats,
    status_code=status.HTTP_200_OK
)
async def get_contact_stats(admin=Depends(require_admin)):
    """
    Get contact message statistics.
    """
    stats = await contact_service.get_contact_stats_service()
    return stats


@router.get(
    "/admin/contact/reference/{reference_id}",
    response_model=ContactMessageOut,
    status_code=status.HTTP_200_OK
)
async def get_contact_message_by_reference(reference_id: str, admin=Depends(require_admin)):
    """
    Get a contact message by reference ID.
    """
    contact_message = await contact_service.get_contact_message_by_reference_id_service(reference_id)

    if not contact_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact message not found"
        )

    return contact_message


@router.get(
    "/admin/contact/{message_id}",
    response_model=ContactMessageOut,
    status_code=status.HTTP_200_OK
)
async def get_contact_message(message_id: int, admin=Depends(require_admin)):
    """
    Get a specific contact message by ID.
    """
    contact_message = await contact_service.get_contact_message_by_id_service(message_id)

    if not contact_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact message not found"
        )

    return contact_message


@router.put(
    "/admin/contact/{message_id}",
    response_model=ContactMessageOut,
    status_code=status.HTTP_200_OK
)
async def update_contact_message(
    message_id: int,
    update_data: ContactMessageUpdate,
    background_tasks: BackgroundTasks,
    admin=Depends(require_admin)
):
    """
    Update general fields of a contact message.
    """
    contact_message = await contact_service.update_contact_message_service(
        admin_id=admin.id,
        message_id=message_id,
        update_data=update_data
    )

    if not contact_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact message not found"
        )

    background_tasks.add_task(
        log_admin_action_service,
        admin_id=admin.id,
        admin_name=admin.name,
        action="update_contact_message",
        target_type="contact_message",
        target_id=message_id,
        details={"status": "updated"}
    )

    return contact_message


@router.patch(
    "/admin/contact/{message_id}/status",
    response_model=ContactMessageOut,
    status_code=status.HTTP_200_OK
)
async def update_contact_message_status(
    message_id: int,
    body: ContactMessageStatusUpdate,
    background_tasks: BackgroundTasks,
    admin=Depends(require_admin)
):
    """
    Update the status of a contact message.

    Valid transitions:
      new       -> pending | responded | closed | spam
      pending   -> responded | closed | spam
      responded -> closed
      closed    -> new  (reopen)
      spam      -> new  (reopen)
    """
    contact_message = await contact_service.update_contact_message_status_service(
        admin_id=admin.id,
        message_id=message_id,
        new_status=body.status
    )

    if not contact_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact message not found"
        )

    background_tasks.add_task(
        log_admin_action_service,
        admin_id=admin.id,
        admin_name=admin.name,
        action="contact_message_status_updated",
        target_type="contact_message",
        target_id=message_id,
        details={"new_status": body.status}
    )

    return contact_message


@router.delete(
    "/admin/contact/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_contact_message(
    message_id: int,
    background_tasks: BackgroundTasks,
    admin=Depends(require_admin)
):
    """
    Hard-delete a contact message.
    """
    deleted = await contact_service.delete_contact_message_service(
        admin_id=admin.id,
        message_id=message_id
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact message not found"
        )

    background_tasks.add_task(
        log_admin_action_service,
        admin_id=admin.id,
        admin_name=admin.name,
        action="delete_contact_message",
        target_type="contact_message",
        target_id=message_id,
        details={"status": "deleted"}
    )