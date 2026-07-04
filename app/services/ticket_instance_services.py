#!/usr/bin/env python3
"""TicketInstance services for MGLTickets."""

from uuid import uuid4
from typing import Optional
from datetime import datetime

from app.core.logging_config import logger
import app.db.repositories.ticket_instance_repo as ti_repo
from app.schemas.ticket_instance import (
    TicketInstanceCreate,
    TicketInstanceUpdate,
    CheckInResponse,
    CheckInTicketInfo,
)


async def create_ticket_instance(ticket_instance_create: TicketInstanceCreate) -> dict:
    """Create a new TicketInstance. event_id must be set on the create schema."""
    logger.info("Creating a new TicketInstance")
    return await ti_repo.create_ticket_instance_repo(ticket_instance_create)


async def get_ticket_instance_by_id(ticket_instance_id: int) -> Optional[dict]:
    """Retrieve a TicketInstance by its ID."""
    logger.info(f"Retrieving TicketInstance with ID: {ticket_instance_id}")
    return await ti_repo.get_ticket_instance_by_id_repo(ticket_instance_id)


async def update_ticket_instance(
    ticket_instance_id: int,
    ticket_instance_update: TicketInstanceUpdate,
) -> Optional[dict]:
    """Update an existing TicketInstance."""
    logger.info(f"Updating TicketInstance with ID: {ticket_instance_id}")
    return await ti_repo.update_ticket_instance_repo(ticket_instance_id, ticket_instance_update)


async def delete_ticket_instance(ticket_instance_id: int) -> bool:
    """Delete a TicketInstance by its ID."""
    logger.info(f"Deleting TicketInstance with ID: {ticket_instance_id}")
    return await ti_repo.delete_ticket_instance_repo(ticket_instance_id)


async def list_ticket_instances() -> list[dict]:
    """List all TicketInstances in the database."""
    logger.info("Listing all TicketInstances")
    return await ti_repo.list_ticket_instances_repo()


async def list_ticket_instances_in_date_range(
    start_date: datetime, end_date: datetime
) -> list[dict]:
    """List TicketInstances created within a specific date range."""
    logger.info(f"Listing TicketInstances from {start_date} to {end_date}")
    return await ti_repo.list_ticket_instances_in_date_range_repo(start_date, end_date)


async def get_ticket_instances_by_user(user_id: int) -> list[dict]:
    """List TicketInstances for a specific user."""
    logger.info(f"Listing TicketInstances for user ID: {user_id}")
    return await ti_repo.get_ticket_instances_by_user_repo(user_id)


async def get_ticket_instances_by_status(status: str) -> list[dict]:
    """List TicketInstances filtered by their status."""
    logger.info(f"Listing TicketInstances with status: {status}")
    return await ti_repo.get_ticket_instances_by_status_repo(status)


async def get_ticket_instance_by_seat_number(seat_number: str) -> Optional[dict]:
    """Retrieve a TicketInstance by its seat number."""
    logger.info(f"Retrieving TicketInstance with seat number: {seat_number}")
    return await ti_repo.get_ticket_instance_by_seat_number_repo(seat_number)


# ── Enriched query for MyTickets.tsx ─────────────────────────────────────────

async def get_ticket_instances_by_user_enriched(user_id: int) -> list[dict]:
    """Retrieve enriched TicketInstances for MyTickets.tsx and Dashboard.
    Includes event_title, venue, event_date, ticket_type_name, qr_payload."""
    logger.info(f"Retrieving enriched TicketInstances for user ID: {user_id}")
    return await ti_repo.get_ticket_instances_by_user_enriched_repo(user_id)


# ── Ticket issuance after payment confirmation ────────────────────────────────

async def create_ticket_instances_for_booking(
    booking_id: int,
    user_id: int,
    event_id: int,
    ticket_type_id: int,
    quantity: int,
    price_per_ticket: int,
    issued_to: Optional[str] = None,
) -> list:
    """
    Create one TicketInstance per ticket in a confirmed booking line item.

    Called from handle_mpesa_callback_service and the free-order path,
    once per Booking row under the Order. event_id is passed directly and
    stored on each instance — no join through bookings needed for future reads.

    Code format: TKT-<BOOKING_ID>-<UUID4_SHORT_UPPERCASE>
    """
    logger.info(f"Creating {quantity} ticket instance(s) for booking {booking_id}")
    instances = []
    for _ in range(quantity):
        code = f"TKT-{booking_id}-{uuid4().hex[:8].upper()}"
        instance = await ti_repo.create_ticket_instance_repo(
            TicketInstanceCreate(
                booking_id=booking_id,
                event_id=event_id,
                ticket_type_id=ticket_type_id,
                user_id=user_id,
                price=price_per_ticket,
                code=code,
                status="issued",
                issued_to=issued_to,
            )
        )
        instances.append(instance)
        logger.info(f"Issued ticket instance {instance.id} with code {code}")

    return instances


# ── Check-in ──────────────────────────────────────────────────────────────────

async def check_in_ticket_service(raw_payload: str) -> CheckInResponse:
    """
    Verify a scanned QR payload's HMAC signature, then attempt the atomic
    check-in. Signature verification always happens server-side regardless
    of any pre-check the scanning device may have done.
    """
    from app.core.ticket_signing import verify_ticket_qr_payload

    parsed = verify_ticket_qr_payload(raw_payload)
    if parsed is None:
        logger.warning("Check-in rejected: invalid or unparseable QR signature")
        return CheckInResponse(accepted=False, reason="invalid_signature")

    result = await ti_repo.check_in_ticket_instance_repo(
        ticket_instance_id=parsed["t"],
        code=parsed["c"],
    )

    if result["outcome"] == "not_found":
        logger.warning(f"Check-in rejected: ticket instance {parsed['t']} not found")
        return CheckInResponse(accepted=False, reason="not_found")

    ticket_info = CheckInTicketInfo(
        ticket_instance_id=result["ticket_instance_id"],
        code=result["code"],
        event_id=result["event_id"],
        event_title=result["event_title"],
        ticket_type_name=result["ticket_type_name"],
        holder_name=result["holder_name"],
    )

    if result["outcome"] == "accepted":
        logger.info(f"Checked in ticket instance {result['ticket_instance_id']}")
        return CheckInResponse(accepted=True, ticket=ticket_info)

    logger.info(
        f"Check-in rejected for ticket {result['ticket_instance_id']}: {result['outcome']}"
    )
    return CheckInResponse(
        accepted=False,
        reason=result["outcome"],
        ticket=ticket_info,
        first_used_at=result["first_used_at"],
    )