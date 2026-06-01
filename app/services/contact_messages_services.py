#!/usr/bin/env python3
"""Service layer for ContactMessage operations."""

from datetime import datetime, timezone
from typing import Optional, List
from fastapi import HTTPException
from app.core.logging_config import logger
from app.schemas.contact_message import ContactMessageCreate, ContactMessageUpdate
import app.db.repositories.contact_messages_repo as contact_repo
from app.utils.generate_reference_id import generate_reference_id
from app.core.recaptcha import verify_recaptcha
# from app.core.email import send_contact_confirmation, send_support_notification

VALID_STATUSES = {"new", "pending", "responded", "closed", "spam"}


async def create_contact_message_service(
    contact_data: ContactMessageCreate,
    client_ip: str,
    user_agent: str,
    user_id: Optional[int],
    source: str,  # "user" | "organizer" — injected by the route, never trusted from the request body
) -> dict:
    """
    Create a new contact message.

    - Verifies reCAPTCHA
    - Checks rate limits (per email and per IP)
    - Stores in database
    - Sends confirmation email to user        (commented out — pending email integration)
    - Sends notification email to support     (commented out — pending email integration)
    - Returns the created message with its unique reference ID
    """
    logger.info(f"Processing contact form from {contact_data.email} (source={source})")

    # Verify reCAPTCHA
    recaptcha_score = await verify_recaptcha(
        token=contact_data.recaptcha_token,
        action="contact_form",
        email=contact_data.email,
        client_ip=client_ip,
    )

    if not recaptcha_score or recaptcha_score < 0.5:
        logger.warning(f"reCAPTCHA failed for {contact_data.email} (score: {recaptcha_score})")
        raise HTTPException(
            status_code=400,
            detail="reCAPTCHA verification failed. Please try again.",
        )

    # Rate limit — per email
    email_count = await contact_repo.count_recent_messages_by_email_repo(
        email=contact_data.email,
        hours=1,
    )
    if email_count >= 3:
        logger.warning(f"Rate limit exceeded for email: {contact_data.email}")
        raise HTTPException(
            status_code=429,
            detail="Too many messages from this email. Please try again in 1 hour.",
        )

    # Rate limit — per IP
    ip_count = await contact_repo.count_recent_messages_by_ip_repo(
        ip_address=client_ip,
        hours=1,
    )
    if ip_count >= 5:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=429,
            detail="Too many messages from your network. Please try again in 1 hour.",
        )

    # Generate a unique reference ID and ensure no collision
    reference_id = generate_reference_id(contact_data.category)
    while await contact_repo.get_contact_message_by_reference_id_repo(reference_id):
        reference_id = generate_reference_id(contact_data.category)

    # Persist
    contact_message = await contact_repo.create_contact_message_repo(
        contact_data=contact_data,
        client_ip=client_ip,
        user_agent=user_agent,
        reference_id=reference_id,
        recaptcha_score=recaptcha_score,
        user_id=user_id,
        source=source,
    )

    logger.info(f"Contact message created: {contact_message.reference_id} (source={source})")

    # Send confirmation email to user
    # try:
    #     await send_contact_confirmation(
    #         to_email=contact_message.email,
    #         name=contact_message.name,
    #         category=contact_message.category,
    #         subject=contact_message.subject,
    #         reference_id=contact_message.reference_id,
    #     )
    #     logger.info(f"Confirmation email sent to {contact_message.email}")
    # except Exception as e:
    #     logger.error(f"Failed to send confirmation email: {str(e)}")

    # Send notification to support team
    # try:
    #     await send_support_notification(contact_message=contact_message)
    #     logger.info(f"Support notification sent for {contact_message.reference_id}")
    # except Exception as e:
    #     logger.error(f"Failed to send support notification: {str(e)}")

    return contact_message


async def get_contact_message_by_id_service(message_id: int) -> Optional[dict]:
    """Get a contact message by ID."""
    logger.info(f"Retrieving contact message: {message_id}")
    contact_message = await contact_repo.get_contact_message_by_id_repo(message_id)
    if not contact_message:
        logger.warning(f"Contact message {message_id} not found")
        return None
    return contact_message


async def get_contact_message_by_reference_id_service(reference_id: str) -> Optional[dict]:
    """Get a contact message by reference ID."""
    logger.info(f"Retrieving contact message: {reference_id}")
    contact_message = await contact_repo.get_contact_message_by_reference_id_repo(reference_id)
    if not contact_message:
        logger.warning(f"Contact message {reference_id} not found")
        return None
    return contact_message


async def list_contact_messages_service(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    category: Optional[str] = None,
    source: Optional[str] = None,
) -> List[dict]:
    """List contact messages with filters."""
    logger.info(f"Listing contact messages (skip={skip}, limit={limit}, source={source})")
    return await contact_repo.list_contact_messages_repo(
        skip=skip,
        limit=limit,
        status=status,
        category=category,
        source=source,
    )


async def update_contact_message_service(
    admin_id: int,
    message_id: int,
    update_data: ContactMessageUpdate,
) -> Optional[dict]:
    """Update a contact message (general fields)."""
    logger.info(f"Updating contact message: {message_id} by admin {admin_id}")
    contact_message = await contact_repo.update_contact_message_repo(
        message_id=message_id,
        update_data=update_data,
    )
    if not contact_message:
        logger.warning(f"Contact message {message_id} not found for update")
        return None
    return contact_message


async def update_contact_message_status_service(
    admin_id: int,
    message_id: int,
    new_status: str,
) -> Optional[dict]:
    """
    Update the status of a contact message.

    Handles all status transitions:
      new        → pending | responded | closed | spam
      pending    → responded | closed | spam
      responded  → closed
      closed     → new  (reopen)
      spam       → new  (reopen)

    Sets responded_at / closed_at timestamps and clears them on reopen.
    """
    if new_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{new_status}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}",
        )

    logger.info(f"Updating message {message_id} status to '{new_status}' by admin {admin_id}")

    now = datetime.now(timezone.utc)
    data: dict = {"status": new_status}

    if new_status == "responded":
        data["responded_at"] = now
    elif new_status == "closed":
        data["closed_at"] = now
    elif new_status == "new":
        # Reopen — clear any previous resolution timestamps
        data["responded_at"] = None
        data["closed_at"] = None

    contact_message = await contact_repo.update_contact_message_repo(
        message_id=message_id,
        update_data=data,
    )

    if not contact_message:
        return None

    return contact_message


async def delete_contact_message_service(admin_id: int, message_id: int) -> bool:
    """Hard-delete a contact message."""
    logger.info(f"Deleting message {message_id} by admin {admin_id}")
    return await contact_repo.delete_contact_message_repo(message_id=message_id)


async def get_contact_stats_service() -> dict:
    """Get contact message statistics."""
    logger.info("Retrieving contact message statistics")
    return await contact_repo.get_contact_stats_repo()