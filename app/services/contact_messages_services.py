#!/usr/bin/env python3
# app/services/contact_messages_services.py
"""Service layer for ContactMessage operations."""
 
import asyncio
from datetime import datetime, timezone
from typing import List, Optional
 
from fastapi import HTTPException
 
from app.core.config import FRONTEND_URL
from app.core.logging_config import logger
from app.core.recaptcha import verify_recaptcha
from app.emails.email_manager import email_manager
from app.schemas.contact_message import (
    ContactMessageCreate,
    ContactMessageUpdate,
    OrganizerContactMessageCreate,
)
from app.utils.generate_reference_id import generate_reference_id
import app.db.repositories.contact_messages_repo as contact_repo
 
 
# ── Email background helper ───────────────────────────────────────────────────
 
def _bg_email(coro) -> None:
    """
    Schedule an email coroutine as a background task.
    Falls back to direct await if no running event loop exists (tests, CLI).
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        asyncio.run(coro)
 
 
VALID_STATUSES = {"new", "pending", "responded", "closed", "spam"}
_HIGH_PRIORITY_CATEGORIES = {"payment", "booking"}
_ADMIN_MESSAGES_URL = f"{FRONTEND_URL}/admin/messages"
 
 
# ── Create ────────────────────────────────────────────────────────────────────
 
async def create_contact_message_service(
    contact_data: ContactMessageCreate | OrganizerContactMessageCreate,
    client_ip: str,
    user_agent: str,
    user_id: Optional[int],
    source: str,
) -> dict:
    """
    Create a contact message then dispatch two emails in background:
    - Sender confirmation (user.contact_confirmation)
    - Internal support alert (admin.contact_notification)
    """
    logger.info(f"Processing contact form from {contact_data.email} (source={source})")
 
    recaptcha_score: Optional[float] = None
    if source == "user":
        recaptcha_score = await verify_recaptcha(
            token=contact_data.recaptcha_token,
            action="contact_form",
            email=contact_data.email,
            client_ip=client_ip,
        )
 
    email_count = await contact_repo.count_recent_messages_by_email_repo(email=contact_data.email, hours=1)
    if email_count >= 3:
        raise HTTPException(status_code=429, detail="Too many messages from this email. Please try again in 1 hour.")
 
    ip_count = await contact_repo.count_recent_messages_by_ip_repo(ip_address=client_ip, hours=1)
    if ip_count >= 5:
        raise HTTPException(status_code=429, detail="Too many messages from your network. Please try again in 1 hour.")
 
    reference_id = generate_reference_id(contact_data.category)
    while await contact_repo.get_contact_message_by_reference_id_repo(reference_id):
        reference_id = generate_reference_id(contact_data.category)
 
    contact_message = await contact_repo.create_contact_message_repo(
        contact_data=contact_data,
        client_ip=client_ip,
        user_agent=user_agent,
        reference_id=reference_id,
        recaptcha_score=recaptcha_score,
        user_id=user_id,
        source=source,
    )
 
    logger.info(f"Contact message created: {contact_message.reference_id}")
 
    # ── Sender confirmation ────────────────────────────────────────────────────
    _bg_email(email_manager.send_from_template(
        template_id="user.contact_confirmation",
        to_email=contact_message.email,
        variables={
            "name": contact_message.name,
            "email": contact_message.email,
            "reference_id": contact_message.reference_id,
            "category": contact_message.category.replace("_", " ").title(),
            "subject": contact_message.subject,
        },
    ))
 
    # ── Internal support notification ──────────────────────────────────────────
    priority = "high" if contact_message.category in _HIGH_PRIORITY_CATEGORIES else "normal"
    _bg_email(email_manager.send_from_template(
        template_id="admin.contact_notification",
        to_email="support@mgltickets.com",
        variables={
            "reference_id": contact_message.reference_id,
            "sender_name": contact_message.name,
            "sender_email": contact_message.email,
            "category": contact_message.category.replace("_", " ").title(),
            "subject": contact_message.subject,
            "message": contact_message.message,
            "source": source.title(),
            "priority": priority,
            "admin_url": _ADMIN_MESSAGES_URL,
        },
        from_email="support",
    ))
 
    return contact_message


# ── Read ──────────────────────────────────────────────────────────────────────

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


# ── Update ────────────────────────────────────────────────────────────────────

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


# ── Delete ────────────────────────────────────────────────────────────────────

async def delete_contact_message_service(admin_id: int, message_id: int) -> bool:
    """Hard-delete a contact message."""
    logger.info(f"Deleting message {message_id} by admin {admin_id}")
    return await contact_repo.delete_contact_message_repo(message_id=message_id)


# ── Stats ─────────────────────────────────────────────────────────────────────

async def get_contact_stats_service() -> dict:
    """Get contact message statistics."""
    logger.info("Retrieving contact message statistics")
    return await contact_repo.get_contact_stats_repo()