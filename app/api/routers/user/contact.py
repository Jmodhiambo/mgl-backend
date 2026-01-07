#!/usr/bin/env python3
"""API routes for Contact Message operations."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.schemas.contact import (
    ContactMessageCreate,
    ContactMessageOut,
    ContactMessageUpdate,
    ContactMessageStats
)
import app.services.contact_message_service as contact_service

router = APIRouter()


@router.post(
    "/contact",
    response_model=ContactMessageOut,
    status_code=status.HTTP_201_CREATED
)
async def submit_contact_form(
    contact: ContactMessageCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Submit a contact form message.
    
    Public endpoint - no authentication required.
    Protected by reCAPTCHA and rate limiting.
    """
    # Get client info
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "Unknown")
    
    # Try to get user_id if logged in (optional)
    try:
        user = await get_current_user(request)
        contact.user_id = user.id if user else None
    except:
        contact.user_id = None
    
    try:
        contact_message = await contact_service.create_contact_message_service(
            db=db,
            contact_data=contact,
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        return contact_message
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit contact form: {str(e)}"
        )


@router.get(
    "/contact/{message_id}",
    response_model=ContactMessageOut,
    dependencies=[Depends(require_admin)]
)
async def get_contact_message(
    message_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific contact message by ID.
    
    Admin only.
    """
    contact_message = await contact_service.get_contact_message_service(
        db=db,
        message_id=message_id
    )
    
    if not contact_message:
        raise HTTPException(
            status_code=404,
            detail="Contact message not found"
        )
    
    return contact_message


@router.get(
    "/contact/reference/{reference_id}",
    response_model=ContactMessageOut,
    dependencies=[Depends(require_admin)]
)
async def get_contact_message_by_reference(
    reference_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a contact message by reference ID.
    
    Admin only.
    """
    contact_message = await contact_service.get_contact_message_by_reference_service(
        db=db,
        reference_id=reference_id
    )
    
    if not contact_message:
        raise HTTPException(
            status_code=404,
            detail="Contact message not found"
        )
    
    return contact_message


@router.get(
    "/contact",
    response_model=List[ContactMessageOut],
    dependencies=[Depends(require_admin)]
)
async def list_contact_messages(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all contact messages with optional filters.
    
    Admin only.
    """
    if limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit cannot exceed 100"
        )
    
    return await contact_service.list_contact_messages_service(
        db=db,
        skip=skip,
        limit=limit,
        status=status,
        category=category
    )


@router.put(
    "/contact/{message_id}",
    response_model=ContactMessageOut,
    dependencies=[Depends(require_admin)]
)
async def update_contact_message(
    message_id: int,
    update_data: ContactMessageUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a contact message.
    
    Admin only.
    """
    contact_message = await contact_service.update_contact_message_service(
        db=db,
        message_id=message_id,
        update_data=update_data
    )
    
    if not contact_message:
        raise HTTPException(
            status_code=404,
            detail="Contact message not found"
        )
    
    return contact_message


@router.patch(
    "/contact/{message_id}/respond",
    response_model=ContactMessageOut,
    dependencies=[Depends(require_admin)]
)
async def mark_as_responded(
    message_id: int,
    db: Session = Depends(get_db)
):
    """
    Mark a contact message as responded.
    
    Admin only.
    """
    contact_message = await contact_service.mark_as_responded_service(
        db=db,
        message_id=message_id
    )
    
    if not contact_message:
        raise HTTPException(
            status_code=404,
            detail="Contact message not found"
        )
    
    return contact_message


@router.patch(
    "/contact/{message_id}/close",
    response_model=ContactMessageOut,
    dependencies=[Depends(require_admin)]
)
async def mark_as_closed(
    message_id: int,
    db: Session = Depends(get_db)
):
    """
    Mark a contact message as closed.
    
    Admin only.
    """
    contact_message = await contact_service.mark_as_closed_service(
        db=db,
        message_id=message_id
    )
    
    if not contact_message:
        raise HTTPException(
            status_code=404,
            detail="Contact message not found"
        )
    
    return contact_message


@router.patch(
    "/contact/{message_id}/spam",
    response_model=ContactMessageOut,
    dependencies=[Depends(require_admin)]
)
async def mark_as_spam(
    message_id: int,
    db: Session = Depends(get_db)
):
    """
    Mark a contact message as spam.
    
    Admin only.
    """
    contact_message = await contact_service.mark_as_spam_service(
        db=db,
        message_id=message_id
    )
    
    if not contact_message:
        raise HTTPException(
            status_code=404,
            detail="Contact message not found"
        )
    
    return contact_message


@router.get(
    "/contact/stats/overview",
    response_model=ContactMessageStats,
    dependencies=[Depends(require_admin)]
)
async def get_contact_stats(
    db: Session = Depends(get_db)
):
    """
    Get contact message statistics.
    
    Admin only.
    """
    stats = await contact_service.get_contact_stats_service(db=db)
    return ContactMessageStats(**stats)