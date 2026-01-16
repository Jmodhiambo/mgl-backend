#!/usr/bin/env python3
"""API routes for Contact Message operations."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import List, Optional
from app.core.security import get_current_user_optional
from app.schemas.contact_message import ContactMessageCreate, ContactMessageOut
import app.services.contact_messages_services as contact_service

router = APIRouter()


@router.post("/contact", response_model=ContactMessageOut, status_code=status.HTTP_201_CREATED)
async def submit_contact_form(
    contact: ContactMessageCreate,
    request: Request,
    user = Depends(get_current_user_optional)
):
    """
    Submit a contact form message.
    
    Public endpoint - user can either be authenticated or not.
    Protected by reCAPTCHA and rate limiting.
    """
    # Get client info
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "Unknown")
    
    # Get user ID if authenticated else None
    user_id = user.id if user else None

    
    try:
        contact_message = await contact_service.create_contact_message_service(
            contact_data=contact,
            client_ip=client_ip,
            user_agent=user_agent,
            user_id=user_id
        )
        
        return contact_message
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit contact form: {str(e)}"
        )