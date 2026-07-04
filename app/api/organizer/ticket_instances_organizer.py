#!/usr/bin/env python3
"""TicketInstance routes for organizer operations."""

from fastapi import APIRouter, Depends, status
from app.schemas.ticket_instance import CheckInRequest, CheckInResponse
from app.core.security import require_organizer
import app.services.ticket_instance_services as ti_services

router = APIRouter()


@router.post(
    "/organizers/me/check-in",
    response_model=CheckInResponse,
    status_code=status.HTTP_200_OK,
)
async def check_in_ticket(
    body: CheckInRequest,
    organizer=Depends(require_organizer),
):
    """
    Scan and check in a ticket at the gate.

    Body carries the raw QR payload string exactly as scanned — the
    frontend never decodes or re-encodes it, just forwards what the
    camera read. The service layer verifies the embedded HMAC signature,
    then the repo performs a single atomic conditional UPDATE so a ticket
    can never be accepted twice, even under concurrent scans from multiple
    gates at the same event.

    Always returns HTTP 200 — rejection is communicated via `accepted: false`
    and a `reason` field, not an error status, since "already scanned" is a
    normal, frequent outcome the scanner UI needs to render clearly.

    TODO: gate access by event ownership — currently any organizer can
    check in tickets for any event. Once you have a shared
    "does this organizer own/co-own this event" helper, wire it in here
    using the event_id returned from verify_ticket_qr_payload (parsed["e"])
    before delegating to check_in_ticket_service.
    """
    return await ti_services.check_in_ticket_service(body.payload)