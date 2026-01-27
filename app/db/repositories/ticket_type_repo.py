#!/usr/bin/env python3
"""Async repository for TicketType model operations."""

from typing import Optional, List
from sqlalchemy import select, func
from app.db.session import get_async_session
from app.db.models.ticket_type import TicketType
from app.schemas.ticket_type import (
    TicketTypeOut,
    TicketTypeCreate,
    TicketTypeUpdate,
)


async def create_ticket_type_repo(
    ticket_type_in: TicketTypeCreate,
) -> TicketTypeOut:
    """Create a new TicketType record in the database."""
    async with get_async_session() as session:
        ticket_type = TicketType(**ticket_type_in.model_dump())
        session.add(ticket_type)
        await session.commit()
        await session.refresh(ticket_type)
        return TicketTypeOut.model_validate(ticket_type)


async def get_ticket_type_by_id_repo(
    ticket_type_id: int,
) -> Optional[TicketTypeOut]:
    """Retrieve a TicketType by its ID."""
    async with get_async_session() as session:
        ticket_type = await session.get(TicketType, ticket_type_id)
        if ticket_type:
            return TicketTypeOut.model_validate(ticket_type)
        return None


async def update_ticket_type_repo(
    ticket_type_id: int,
    ticket_type_in: TicketTypeUpdate,
) -> Optional[TicketTypeOut]:
    """Update an existing TicketType record."""
    async with get_async_session() as session:
        ticket_type = await session.get(TicketType, ticket_type_id)
        if not ticket_type:
            return None

        for field, value in ticket_type_in.model_dump(exclude_unset=True).items():
            setattr(ticket_type, field, value)

        session.add(ticket_type)
        await session.commit()
        await session.refresh(ticket_type)
        return TicketTypeOut.model_validate(ticket_type)


async def delete_ticket_type_repo(ticket_type_id: int) -> bool:
    """Delete a TicketType record by its ID."""
    async with get_async_session() as session:
        ticket_type = await session.get(TicketType, ticket_type_id)
        if not ticket_type:
            return False

        await session.delete(ticket_type)
        await session.commit()
        return True


async def list_ticket_types_by_event_id_repo(
    event_id: int,
) -> List[TicketTypeOut]:
    """List all TicketTypes for a given Event ID."""
    async with get_async_session() as session:
        result = await session.execute(
            select(TicketType).where(TicketType.event_id == event_id)
        )
        ticket_types = result.scalars().all()
        return [TicketTypeOut.model_validate(tt) for tt in ticket_types]
    

async def check_if_ticket_type_has_instances_repo(ticket_type_id: int) -> bool:
    """Check if a TicketType has any associated ticket instances to avoid deletion and mark as inactive instead."""
    async with get_async_session() as session:
        result = await session.execute(
            select(TicketType).where(TicketType.ticket_instances.any(id=ticket_type_id) and TicketType.is_active == True)
        )
        ticket_instances = result.scalars().all()
        return True if ticket_instances else False
    

async def update_ticket_type_status_repo(ticket_type_id: int, is_active: bool) -> Optional[TicketTypeOut]:
    """Update the status of a TicketType record."""
    async with get_async_session() as session:
        ticket_type = await session.get(TicketType, ticket_type_id)
        if not ticket_type:
            return None

        ticket_type.is_active = is_active
        session.add(ticket_type)
        await session.commit()
        await session.refresh(ticket_type)
        return TicketTypeOut.model_validate(ticket_type)
    

async def count_available_tickets_by_event_repo(event_id: int) -> int:
    """Count available tickets for an event."""
    async with get_async_session() as session:
        result = await session.execute(
            select(func.sum(TicketType.total_quantity))
            .select_from(TicketType)
            .where(TicketType.event_id == event_id)
        )
        return result.scalar_one()
    

async def count_tickets_sold_by_event_id_repo(event_id: int) -> int:
    """Count total tickets sold for an event."""
    async with get_async_session() as session:
        result = await session.execute(
            select(func.sum(TicketType.quantity_sold))
            .select_from(TicketType)
            .where(TicketType.event_id == event_id)
        )
        return result.scalar_one()