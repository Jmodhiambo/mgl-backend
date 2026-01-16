#!/usr/bin/env python3
"""Admin API routes for Contact Message operations."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.core.security import require_admin
from app.schemas.contact_message import (
    ContactMessageOut,
    ContactMessageUpdate,
    ContactMessageStats
)
import app.services.contact_messages_services as contact_service

router = APIRouter()


@router.get("/admin/contact/{message_id}", response_model=ContactMessageOut, status_code=status.HTTP_200_OK)
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


@router.get(
    "/admin/contact/reference/{reference_id}",
    response_model=ContactMessageOut,
    status_code=status.HTTP_200_OK
)
async def get_contact_message_by_reference(reference_id: str):
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


@router.put(
    "/admin/contact/{message_id}",
    response_model=ContactMessageOut,
    status_code=status.HTTP_200_OK
)
async def update_contact_message(
    message_id: int,
    update_data: ContactMessageUpdate,
    admin=Depends(require_admin)
):
    """
    Update a contact message.
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
    
    return contact_message


@router.patch(
    "/admin/contact/{message_id}/respond",
    response_model=ContactMessageOut,
    status_code=status.HTTP_200_OK
)
async def mark_as_responded(message_id: int, admin=Depends(require_admin)):
    """
    Mark a contact message as responded.
    """
    contact_message = await contact_service.mark_as_responded_service(
        user_id=admin.id,
        message_id=message_id
    )
    
    if not contact_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact message not found"
        )
    
    return contact_message


@router.patch(
    "/admin/contact/{message_id}/close",
    response_model=ContactMessageOut,
    status_code=status.HTTP_200_OK
)
async def mark_as_closed(message_id: int, admin=Depends(require_admin)):
    """
    Mark a contact message as closed.
    """
    contact_message = await contact_service.mark_as_closed_service(
        user_id=admin.id,
        message_id=message_id
    )
    
    if not contact_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact message not found"
        )
    
    return contact_message


@router.patch(
    "/admin/contact/{message_id}/spam",
    response_model=ContactMessageOut,
    status_code=status.HTTP_200_OK
)
async def mark_as_spam(message_id: int, admin=Depends(require_admin)):
    """
    Mark a contact message as spam.
    """
    contact_message = await contact_service.mark_as_spam_service(
        user_id=admin.id,
        message_id=message_id
    )
    
    if not contact_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact message not found"
        )
    
    return contact_message


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