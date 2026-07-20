#!/usr/bin/env python3
"""TicketInstance services for MGLTickets."""

import asyncio
from uuid import uuid4
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.logging_config import logger
from app.emails.email_manager import email_manager
import app.db.repositories.ticket_instance_repo as ti_repo
import app.db.repositories.user_repo as user_repo
from app.schemas.ticket_instance import (
    TicketInstanceCreate,
    TicketInstanceUpdate,
    CheckInResponse,
    CheckInTicketInfo,
)


# ── Email background helper ───────────────────────────────────────────────────
# Matches the pattern used across event_services.py, user_services.py, etc.

async def _safe_email(coro) -> None:
    """Await an email coroutine and log — rather than silently swallow —
    any failure. Without this, an exception raised inside a fire-and-forget
    asyncio.Task (e.g. a template validation error, or the send itself
    failing) never surfaces anywhere except an easy-to-miss 'exception was
    never retrieved' warning from asyncio's default handler."""
    try:
        await coro
    except Exception as exc:
        logger.error(f"Background email task failed: {exc}")


def _bg_email(coro) -> None:
    """
    Schedule an email coroutine as a background task.
    Falls back to direct await if no running event loop exists (tests, CLI).
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_safe_email(coro))
    except RuntimeError:
        asyncio.run(_safe_email(coro))


async def _dispatch_check_in_confirmed_email(
    ticket_instance_id: int,
    event_title: str,
    ticket_type_name: str,
    code: str,
) -> None:
    """
    Look up the ticket instance's owner and schedule user.check_in_confirmed
    in the background. Wrapped so an email failure can never affect the
    check-in outcome that's already been committed to the database.
    """
    try:
        instance = await ti_repo.get_ticket_instance_by_id_repo(ticket_instance_id)
        if not instance:
            logger.warning(f"Could not send check_in_confirmed email — ticket instance {ticket_instance_id} not found")
            return

        user = await user_repo.get_user_by_id_repo(instance.user_id)
        if not user:
            logger.warning(f"Could not send check_in_confirmed email — user for ticket instance {ticket_instance_id} not found")
            return

        _bg_email(email_manager.send_from_template(
            template_id="user.check_in_confirmed",
            to_email=user.email,
            variables={
                "name": user.name,
                "event_title": event_title,
                "ticket_type_name": ticket_type_name,
                "code": code,
                "checked_in_at": datetime.now(ZoneInfo("Africa/Nairobi")).strftime("%d %b %Y at %H:%M EAT"),
            },
        ))
    except Exception as exc:
        logger.warning(f"Could not schedule check_in_confirmed email for ticket instance {ticket_instance_id}: {exc}")


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

async def check_in_ticket_service(
    raw_payload: str,
    event_id: int,
    scanned_by: str = "",
    scan_method: str = "qr_scan",
) -> CheckInResponse:
    """
    Verify a scanned QR payload's HMAC signature, then validate the
    payload's embedded event_id matches the organizer's selected event
    before the atomic check-in. Prevents a ticket for Event A being
    accepted at Event B's gate even though the signature is valid.
    scanned_by is the authenticated user's name, stored on the row for audit.
    On acceptance, schedules a check-in confirmation email to the ticket holder.
    """
    from app.core.ticket_signing import verify_ticket_qr_payload

    parsed = verify_ticket_qr_payload(raw_payload)
    if parsed is None:
        logger.warning("Check-in rejected: invalid or unparseable QR signature")
        return CheckInResponse(accepted=False, reason="invalid_signature")

    if parsed["e"] != event_id:
        logger.warning(
            f"Organizer check-in rejected: payload event_id={parsed['e']} "
            f"!= selected event_id={event_id}"
        )
        return CheckInResponse(accepted=False, reason="wrong_event")

    result = await ti_repo.check_in_ticket_instance_repo(
        ticket_instance_id=parsed["t"],
        code=parsed["c"],
        scanned_by=scanned_by,
        scan_method=scan_method,
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
        scanned_by=result.get("scanned_by"),
        scan_method=result.get("scan_method"),
    )

    if result["outcome"] == "accepted":
        logger.info(
            f"Checked in ticket {result['ticket_instance_id']} "
            f"(scanned_by={result.get('scanned_by')!r})"
        )
        await _dispatch_check_in_confirmed_email(
            ticket_instance_id=result["ticket_instance_id"],
            event_title=result["event_title"],
            ticket_type_name=result["ticket_type_name"],
            code=result["code"],
        )
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

async def check_in_ticket_by_code_service(
    code: str,
    event_id: int,
    scanned_by: str = "",
    scan_method: str = "manual_code",
) -> CheckInResponse:
    """
    Check in a ticket by its human-readable code (manual fallback).
    Scoped to event_id. Logged as method=manual_code in logs.
    scanned_by is stored on the ticket row for audit.
    On acceptance, schedules a check-in confirmation email to the ticket holder.
    """
    result = await ti_repo.check_in_ticket_by_code_repo(
        code=code.strip().upper(),
        event_id=event_id,
        scanned_by=scanned_by,
        scan_method=scan_method,
    )

    if result["outcome"] == "not_found":
        logger.warning(f"Manual check-in: code {code!r} not found for event {event_id}")
        return CheckInResponse(accepted=False, reason="not_found")

    ticket_info = CheckInTicketInfo(
        ticket_instance_id=result["ticket_instance_id"],
        code=result["code"],
        event_id=result["event_id"],
        event_title=result["event_title"],
        ticket_type_name=result["ticket_type_name"],
        holder_name=result["holder_name"],
        scanned_by=result.get("scanned_by"),
        scan_method=result.get("scan_method"),
    )

    if result["outcome"] == "accepted":
        logger.info(
            f"Manual check-in: ticket {result['ticket_instance_id']} admitted "
            f"(scanned_by={scanned_by!r})"
        )
        await _dispatch_check_in_confirmed_email(
            ticket_instance_id=result["ticket_instance_id"],
            event_title=result["event_title"],
            ticket_type_name=result["ticket_type_name"],
            code=result["code"],
        )
        return CheckInResponse(accepted=True, ticket=ticket_info)

    if result["outcome"] == "wrong_event":
        logger.warning(
            f"Manual check-in: code {code!r} belongs to event "
            f"{result['event_id']} not selected event {event_id}"
        )
    else:
        logger.info(
            f"Manual check-in rejected: ticket {result['ticket_instance_id']} "
            f"status={result['outcome']}"
        )
    return CheckInResponse(
        accepted=False,
        reason=result["outcome"],
        ticket=ticket_info,
        first_used_at=result["first_used_at"],
    )


async def check_in_ticket_admin_service(
    raw_payload: str,
    event_id: int,
    scanned_by: str = "",
    scan_method: str = "qr_scan",
) -> CheckInResponse:
    """
    Admin QR check-in. Verifies HMAC then confirms the payload's event_id
    matches the admin's selected event before the atomic update.
    On acceptance, schedules a check-in confirmation email to the ticket holder.
    """
    from app.core.ticket_signing import verify_ticket_qr_payload

    parsed = verify_ticket_qr_payload(raw_payload)
    if parsed is None:
        logger.warning("Admin QR check-in rejected: invalid signature")
        return CheckInResponse(accepted=False, reason="invalid_signature")

    if parsed["e"] != event_id:
        logger.warning(
            f"Admin QR check-in rejected: payload event_id={parsed['e']} "
            f"!= selected event_id={event_id}"
        )
        return CheckInResponse(accepted=False, reason="wrong_event")

    result = await ti_repo.check_in_ticket_instance_repo(
        ticket_instance_id=parsed["t"],
        code=parsed["c"],
        scanned_by=scanned_by,
        scan_method=scan_method,
    )

    if result["outcome"] == "not_found":
        return CheckInResponse(accepted=False, reason="not_found")

    ticket_info = CheckInTicketInfo(
        ticket_instance_id=result["ticket_instance_id"],
        code=result["code"],
        event_id=result["event_id"],
        event_title=result["event_title"],
        ticket_type_name=result["ticket_type_name"],
        holder_name=result["holder_name"],
        scanned_by=result.get("scanned_by"),
        scan_method=result.get("scan_method"),
    )

    if result["outcome"] == "accepted":
        logger.info(
            f"Admin check-in: ticket {result['ticket_instance_id']} admitted "
            f"(scanned_by={scanned_by!r})"
        )
        await _dispatch_check_in_confirmed_email(
            ticket_instance_id=result["ticket_instance_id"],
            event_title=result["event_title"],
            ticket_type_name=result["ticket_type_name"],
            code=result["code"],
        )
        return CheckInResponse(accepted=True, ticket=ticket_info)

    return CheckInResponse(
        accepted=False,
        reason=result["outcome"],
        ticket=ticket_info,
        first_used_at=result["first_used_at"],
    )


async def check_in_ticket_admin_by_code_service(
    code: str,
    event_id: int,
    scanned_by: str = "",
) -> CheckInResponse:
    """Admin manual code fallback — delegates to the shared by-code service.
    Check-in confirmation email is dispatched there too."""
    return await check_in_ticket_by_code_service(
        code, event_id, scanned_by, scan_method="manual_code"
    )