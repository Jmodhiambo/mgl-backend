#!/usr/bin/env python3
"""API routes for Contact Message operations — organizer scope."""

from fastapi import APIRouter, Depends, HTTPException, Request, status, BackgroundTasks
from app.core.security import require_organizer
from app.schemas.contact_message import OrganizerContactMessageCreate, ContactMessageOut
import app.services.contact_messages_services as contact_service
from app.services.notification_services import notify_new_contact_message

router = APIRouter()


@router.post("organizer/contact", response_model=ContactMessageOut, status_code=status.HTTP_201_CREATED)
async def submit_organizer_contact_form(
    contact: OrganizerContactMessageCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    organizer=Depends(require_organizer),
):
    """
    Submit a contact/support message from an organizer.

    Requires organizer authentication.
    Accepts an optional event_title to identify which event the message relates to.
    source is hardcoded to "organizer"; the client never controls it.
    Protected by reCAPTCHA and rate limiting (shared limits with user endpoint).
    """
    client_ip = request.headers.get("X-Real-IP") or (request.client.host if request.client else None)
    user_agent = request.headers.get("user-agent", "Unknown")

    try:
        contact_message = await contact_service.create_contact_message_service(
            contact_data=contact,
            client_ip=client_ip,
            user_agent=user_agent,
            user_id=organizer.id,
            source="organizer",
        )

        background_tasks.add_task(
            notify_new_contact_message,
            contact_message.id,
            contact_message.name,
            contact_message.email,
            contact_message.subject,
            contact_message.message,
            contact_message.category,
        )

        return contact_message

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit organizer contact form: {str(e)}",
        )