#!/usr/bin/env python3
# app/services/ticket_type_services.py
"""Service layer for TicketType operations."""

import asyncio
from typing import Optional

from fastapi import HTTPException, status

from app.core.config import FRONTEND_URL
from app.core.logging_config import logger
from app.emails.email_manager import email_manager
from app.schemas.ticket_type import TicketTypeCreate, TicketTypeUpdate
import app.db.repositories.event_repo as event_repo
import app.db.repositories.ticket_type_repo as tt_repo
import app.db.repositories.user_repo as user_repo


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


def _organizer_dashboard_url() -> str:
    return f"organizer.{FRONTEND_URL}/dashboard"


# ── CRUD ──────────────────────────────────────────────────────────────────────

async def create_ticket_type_service(ticket_type_in: TicketTypeCreate) -> dict:
    logger.info(f"Creating TicketType: {ticket_type_in.model_dump()}")
    ticket_type = await tt_repo.create_ticket_type_repo(ticket_type_in)
    logger.info(f"Created TicketType {ticket_type.id}")
    return ticket_type


async def get_ticket_type_by_id_service(ticket_type_id: int) -> Optional[dict]:
    logger.info(f"Retrieving TicketType {ticket_type_id}")
    ticket_type = await tt_repo.get_ticket_type_by_id_repo(ticket_type_id)
    if not ticket_type:
        logger.warning(f"TicketType {ticket_type_id} not found")
    return ticket_type


async def update_ticket_type_service(
    ticket_type_id: int, ticket_type_in: TicketTypeUpdate
) -> Optional[dict]:
    """Update TicketType. Blocks updates on suspended ticket types."""
    ticket = await get_ticket_type_by_id_service(ticket_type_id)
    if not ticket:
        return None

    if ticket.suspended_by_admin_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This ticket type has been suspended by an administrator and cannot be edited. Contact support.",
        )

    if (
        ticket_type_in.total_quantity is not None
        and ticket_type_in.total_quantity < ticket.quantity_sold
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Total quantity cannot be less than quantity sold",
        )

    logger.info(f"Updating TicketType {ticket_type_id}")
    return await tt_repo.update_ticket_type_repo(ticket_type_id, ticket_type_in)


async def update_ticket_type_status_service(
    ticket_type_id: int, is_active: bool
) -> Optional[dict]:
    logger.info(f"Updating status of TicketType {ticket_type_id} to is_active={is_active}")
    return await tt_repo.update_ticket_type_status_repo(ticket_type_id, is_active)


async def suspend_ticket_type_service(
    ticket_type_id: int,
    admin_id: int,
    admin_name: str,
    reason: str,
) -> Optional[dict]:
    """Admin-only: suspend a TicketType and notify the organizer in background."""
    logger.info(f"[ADMIN] Suspending TicketType {ticket_type_id}")

    ticket_type = await tt_repo.suspend_ticket_type_repo(
        ticket_type_id, admin_id=admin_id, admin_name=admin_name, reason=reason
    )
    if not ticket_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TicketType not found")

    try:
        event = await event_repo.get_event_by_id_repo(ticket_type.event_id)
        if event:
            organizer = await user_repo.get_user_by_id_repo(event.organizer_id)
            if organizer:
                _bg_email(email_manager.send_from_template(
                    template_id="organizer.ticket_type_suspended",
                    to_email=organizer.email,
                    variables={
                        "organizer_name": organizer.name,
                        "event_title": event.title,
                        "ticket_type_name": ticket_type.name,
                        "admin_name": admin_name,
                        "suspension_reason": reason,
                    },
                ))
    except Exception as exc:
        logger.warning(f"Could not schedule ticket_type_suspended email for {ticket_type_id}: {exc}")

    return ticket_type


async def unsuspend_ticket_type_service(ticket_type_id: int) -> Optional[dict]:
    """Admin-only: lift suspension and notify the organizer in background."""
    logger.info(f"[ADMIN] Lifting suspension on TicketType {ticket_type_id}")

    ticket_type = await tt_repo.unsuspend_ticket_type_repo(ticket_type_id)
    if not ticket_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TicketType not found")

    try:
        event = await event_repo.get_event_by_id_repo(ticket_type.event_id)
        if event:
            organizer = await user_repo.get_user_by_id_repo(event.organizer_id)
            if organizer:
                _bg_email(email_manager.send_from_template(
                    template_id="organizer.ticket_type_unsuspended",
                    to_email=organizer.email,
                    variables={
                        "organizer_name": organizer.name,
                        "event_title": event.title,
                        "ticket_type_name": ticket_type.name,
                        "dashboard_url": _organizer_dashboard_url(),
                    },
                ))
    except Exception as exc:
        logger.warning(f"Could not schedule ticket_type_unsuspended email for {ticket_type_id}: {exc}")

    return ticket_type


async def delete_ticket_type_service(ticket_type_id: int) -> bool:
    """Delete TicketType. Deactivates instead if instances exist. Blocks if suspended."""
    ticket = await get_ticket_type_by_id_service(ticket_type_id)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TicketType not found")

    if ticket.suspended_by_admin_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This ticket type has been suspended by an administrator and cannot be deleted. Contact support.",
        )

    has_instances = await tt_repo.check_if_ticket_type_has_instances_repo(ticket_type_id)
    if has_instances:
        logger.warning(f"TicketType {ticket_type_id} has instances — marking inactive instead.")
        await tt_repo.update_ticket_type_status_repo(ticket_type_id, False)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TicketType has existing bookings and cannot be deleted. It has been marked inactive.",
        )

    logger.info(f"Deleting TicketType {ticket_type_id}")
    success = await tt_repo.delete_ticket_type_repo(ticket_type_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TicketType not found")
    return success


async def list_all_ticket_types_by_event_id_service(event_id: int) -> list[dict]:
    logger.info(f"Listing ALL TicketTypes for Event {event_id}")
    return await tt_repo.list_all_ticket_types_by_event_id_repo(event_id)


async def list_active_ticket_types_by_event_id_service(event_id: int) -> list[dict]:
    logger.info(f"Listing ACTIVE TicketTypes for Event {event_id}")
    return await tt_repo.list_active_ticket_types_by_event_id_repo(event_id)