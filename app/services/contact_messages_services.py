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
    user_id: Optional[int]
) -> dict:
    """
    Create a new contact message.

    - Verifies reCAPTCHA
    - Checks rate limits
    - Stores in database
    - Sends confirmation email to user
    - Sends notification email to support
    - Creates a unique reference ID
    """

    logger.info(f"Processing contact form from {contact_data.email}")

    # Verify reCAPTCHA
    recaptcha_score = await verify_recaptcha(
        token=contact_data.recaptcha_token,
        action='contact_form',
        email=contact_data.email,
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
        ip_address=client_ip,
        hours=1
    )

    if ip_count >= 5:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=429,
            detail="Too many messages from your network. Please try again in 1 hour."
        )

    # Generate unique reference ID
    reference_id = generate_reference_id(contact_data.category)

    # Ensure the reference ID is unique
    while await contact_repo.get_contact_message_by_reference_id_repo(reference_id):
        reference_id = generate_reference_id(contact_data.category)

    # Create contact message in database
    contact_message = await contact_repo.create_contact_message_repo(
        contact_data=contact_data,
        client_ip=client_ip,
        user_agent=user_agent,
        reference_id=reference_id,
        recaptcha_score=recaptcha_score,
        user_id=user_id
    )

    logger.info(f"Contact message created: {contact_message.reference_id}")

    # Send confirmation email to user (async in background)
    # try:
    #     await send_contact_confirmation(
    #         to_email=contact_message.email,
    #         name=contact_message.name,
    #         category=contact_message.category,
    #         subject=contact_message.subject,
    #         reference_id=contact_message.reference_id
    #     )
    #     logger.info(f"Confirmation email sent to {contact_message.email}")
    # except Exception as e:
    #     logger.error(f"Failed to send confirmation email: {str(e)}")

    # # Send notification to support team (async in background)
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
    category: Optional[str] = None
) -> List[dict]:
    """List contact messages with filters."""
    logger.info(f"Listing contact messages (skip={skip}, limit={limit})")

    messages = await contact_repo.list_contact_messages_repo(
        skip=skip,
        limit=limit,
        status=status,
        category=category
    )

    return messages


async def update_contact_message_service(
    admin_id: int,
    message_id: int,
    update_data: ContactMessageUpdate
) -> Optional[dict]:
    """Update a contact message (general fields)."""
    logger.info(f"Updating contact message: {message_id} by admin {admin_id}")

    contact_message = await contact_repo.update_contact_message_repo(
        message_id=message_id,
        update_data=update_data
    )

    if not contact_message:
        logger.warning(f"Contact message {message_id} not found for update")
        return None

    return contact_message


async def update_contact_message_status_service(
    admin_id: int,
    message_id: int,
    new_status: str
) -> Optional[dict]:
    """
    Update the status of a contact message.

    Handles all status transitions in one place:
      new -> pending | responded | closed | spam
      pending -> responded | closed | spam
      responded -> closed
      closed -> new  (reopen)
      spam -> new    (reopen)

    Automatically sets responded_at / closed_at timestamps where relevant,
    and clears them on reopen.
    """
    if new_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{new_status}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}"
        )

    logger.info(f"Updating message {message_id} status to '{new_status}' by admin {admin_id}")

    now = datetime.now(timezone.utc)

    data: dict = {"status": new_status}

    if new_status == "responded":
        data["responded_at"] = now
    elif new_status == "closed":
        data["closed_at"] = now
    elif new_status == "new":
        # Reopen — clear any previous timestamps
        data["responded_at"] = None
        data["closed_at"] = None

    contact_message = await contact_repo.update_contact_message_repo(
        message_id=message_id,
        update_data=data
    )

    if not contact_message:
        return None

    return contact_message


async def delete_contact_message_service(admin_id: int, message_id: int) -> bool:
    """Hard-delete a contact message."""
    logger.info(f"Deleting message {message_id} by admin {admin_id}")

    deleted = await contact_repo.delete_contact_message_repo(message_id=message_id)

    if not deleted:
        return False

    return True


async def get_contact_stats_service() -> dict:
    """Get contact message statistics."""
    logger.info("Retrieving contact message statistics")

    return await contact_repo.get_contact_stats_repo()