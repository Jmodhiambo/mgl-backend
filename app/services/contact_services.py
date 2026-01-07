#!/usr/bin/env python3
"""Service layer for ContactMessage operations."""

from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.core.logging_config import logger
from app.schemas.contact_message import (
    ContactMessageCreate, 
    ContactMessageOut,
    ContactMessageUpdate
)
import app.db.repositories.contact_message_repo as contact_repo
from app.core.recaptcha import verify_recaptcha
from app.core.email import send_contact_confirmation, send_support_notification


async def create_contact_message_service(
    db: Session,
    contact_data: ContactMessageCreate,
    client_ip: str,
    user_agent: str
) -> ContactMessageOut:
    """
    Create a new contact message.
    
    - Verifies reCAPTCHA
    - Checks rate limits
    - Stores in database
    - Sends confirmation email to user
    - Sends notification email to support
    """
    
    logger.info(f"Processing contact form from {contact_data.email}")
    
    # Verify reCAPTCHA
    recaptcha_score = await verify_recaptcha(
        token=contact_data.recaptcha_token,
        action='contact_form',
        client_ip=client_ip
    )
    
    if not recaptcha_score or recaptcha_score < 0.5:
        logger.warning(f"reCAPTCHA failed for {contact_data.email} (score: {recaptcha_score})")
        raise HTTPException(
            status_code=400,
            detail="reCAPTCHA verification failed. Please try again."
        )
    
    # Check rate limits - Email
    email_count = await contact_repo.count_recent_messages_by_email_repo(
        db=db,
        email=contact_data.email,
        hours=1
    )
    
    if email_count >= 3:
        logger.warning(f"Rate limit exceeded for email: {contact_data.email}")
        raise HTTPException(
            status_code=429,
            detail="Too many messages from this email. Please try again in 1 hour."
        )
    
    # Check rate limits - IP
    ip_count = await contact_repo.count_recent_messages_by_ip_repo(
        db=db,
        ip_address=client_ip,
        hours=1
    )
    
    if ip_count >= 5:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=429,
            detail="Too many messages from your network. Please try again in 1 hour."
        )
    
    # Create contact message in database
    contact_message = await contact_repo.create_contact_message_repo(
        db=db,
        contact_data=contact_data,
        client_ip=client_ip,
        user_agent=user_agent,
        recaptcha_score=recaptcha_score
    )
    
    logger.info(f"Contact message created: {contact_message.reference_id}")
    
    # Send confirmation email to user (async in background)
    try:
        await send_contact_confirmation(
            to_email=contact_message.email,
            name=contact_message.name,
            category=contact_message.category,
            subject=contact_message.subject,
            reference_id=contact_message.reference_id
        )
        logger.info(f"Confirmation email sent to {contact_message.email}")
    except Exception as e:
        logger.error(f"Failed to send confirmation email: {str(e)}")
        # Don't fail the request if email fails
    
    # Send notification to support team (async in background)
    try:
        await send_support_notification(
            contact_message=contact_message
        )
        logger.info(f"Support notification sent for {contact_message.reference_id}")
    except Exception as e:
        logger.error(f"Failed to send support notification: {str(e)}")
        # Don't fail the request if email fails
    
    return ContactMessageOut.model_validate(contact_message)


async def get_contact_message_service(
    db: Session,
    message_id: int
) -> Optional[ContactMessageOut]:
    """Get a contact message by ID."""
    logger.info(f"Retrieving contact message: {message_id}")
    
    contact_message = await contact_repo.get_contact_message_by_id_repo(db, message_id)
    
    if not contact_message:
        logger.warning(f"Contact message {message_id} not found")
        return None
    
    return ContactMessageOut.model_validate(contact_message)


async def get_contact_message_by_reference_service(
    db: Session,
    reference_id: str
) -> Optional[ContactMessageOut]:
    """Get a contact message by reference ID."""
    logger.info(f"Retrieving contact message: {reference_id}")
    
    contact_message = await contact_repo.get_contact_message_by_reference_repo(
        db, reference_id
    )
    
    if not contact_message:
        logger.warning(f"Contact message {reference_id} not found")
        return None
    
    return ContactMessageOut.model_validate(contact_message)


async def list_contact_messages_service(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    category: Optional[str] = None
) -> List[ContactMessageOut]:
    """List contact messages with filters."""
    logger.info(f"Listing contact messages (skip={skip}, limit={limit})")
    
    messages = await contact_repo.list_contact_messages_repo(
        db=db,
        skip=skip,
        limit=limit,
        status=status,
        category=category
    )
    
    return [ContactMessageOut.model_validate(msg) for msg in messages]


async def update_contact_message_service(
    db: Session,
    message_id: int,
    update_data: ContactMessageUpdate
) -> Optional[ContactMessageOut]:
    """Update a contact message (admin only)."""
    logger.info(f"Updating contact message: {message_id}")
    
    contact_message = await contact_repo.update_contact_message_repo(
        db=db,
        message_id=message_id,
        update_data=update_data
    )
    
    if not contact_message:
        logger.warning(f"Contact message {message_id} not found for update")
        return None
    
    return ContactMessageOut.model_validate(contact_message)


async def mark_as_responded_service(
    db: Session,
    message_id: int
) -> Optional[ContactMessageOut]:
    """Mark a message as responded."""
    logger.info(f"Marking message {message_id} as responded")
    
    contact_message = await contact_repo.mark_as_responded_repo(db, message_id)
    
    if not contact_message:
        return None
    
    return ContactMessageOut.model_validate(contact_message)


async def mark_as_closed_service(
    db: Session,
    message_id: int
) -> Optional[ContactMessageOut]:
    """Mark a message as closed."""
    logger.info(f"Marking message {message_id} as closed")
    
    contact_message = await contact_repo.mark_as_closed_repo(db, message_id)
    
    if not contact_message:
        return None
    
    return ContactMessageOut.model_validate(contact_message)


async def mark_as_spam_service(
    db: Session,
    message_id: int
) -> Optional[ContactMessageOut]:
    """Mark a message as spam."""
    logger.info(f"Marking message {message_id} as spam")
    
    contact_message = await contact_repo.mark_as_spam_repo(db, message_id)
    
    if not contact_message:
        return None
    
    return ContactMessageOut.model_validate(contact_message)


async def get_contact_stats_service(db: Session) -> dict:
    """Get contact message statistics."""
    logger.info("Retrieving contact message statistics")
    
    return await contact_repo.get_contact_stats_repo(db)