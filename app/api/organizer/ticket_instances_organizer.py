#!/usr/bin/env python3
"""Ticket Instance Organizer routes."""

from fastapi import APIRouter, Depends, status
from app.schemas.ticket_instance import CheckInRequest, CheckInByCodeRequest, CheckInResponse
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
    QR gate scan for organizers. Verifies HMAC signature then atomically
    marks the ticket used. Returns 200 always — rejection via accepted:false.
    The organizer's name is stored on the ticket row as scanned_by.
    """
    return await ti_services.check_in_ticket_service(
        raw_payload=body.payload,
        scanned_by=organizer.name,
    )


@router.post(
    "/organizers/me/check-in/by-code",
    response_model=CheckInResponse,
    status_code=status.HTTP_200_OK,
)
async def check_in_ticket_by_code(
    body: CheckInByCodeRequest,
    organizer=Depends(require_organizer),
):
    """
    Manual code fallback for organizers. Staff types the printed ticket code
    when the QR can't be scanned. Scoped to body.event_id.
    Logged as method=manual_code; organizer name stored as scanned_by.
    """
    return await ti_services.check_in_ticket_by_code_service(
        code=body.code,
        event_id=body.event_id,
        scanned_by=organizer.name,
    )