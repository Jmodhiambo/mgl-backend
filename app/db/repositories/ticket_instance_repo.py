#!/usr/bin/env python3
"""Async repository for TicketInstance model operations."""

from typing import Optional, List
from sqlalchemy import select
from app.db.session import get_async_session
from app.db.models.ticket_instance import TicketInstance
from app.schemas.ticket_instance import (
    TicketInstanceOut,
    TicketInstanceCreate,
    TicketInstanceUpdate,
)


async def create_ticket_instance_repo(
    ticket_instance_create: TicketInstanceCreate,
) -> TicketInstanceOut:
    """Create a new TicketInstance in the database."""
    async with get_async_session() as session:
        ticket_instance = TicketInstance(
            booking_id=ticket_instance_create.booking_id,
            ticket_type_id=ticket_instance_create.ticket_type_id,
            user_id=ticket_instance_create.user_id,
            code=ticket_instance_create.code,
            status=ticket_instance_create.status,
            issued_to=ticket_instance_create.issued_to,
        )
        session.add(ticket_instance)
        await session.commit()
        await session.refresh(ticket_instance)
        return TicketInstanceOut.model_validate(ticket_instance)


async def get_ticket_instance_by_id_repo(
    ticket_instance_id: int,
) -> Optional[TicketInstanceOut]:
    """Retrieve a TicketInstance by its ID."""
    async with get_async_session() as session:
        ticket_instance = await session.get(TicketInstance, ticket_instance_id)
        if ticket_instance:
            return TicketInstanceOut.model_validate(ticket_instance)
        return None


async def update_ticket_instance_repo(
    ticket_instance_id: int,
    ticket_instance_update: TicketInstanceUpdate,
) -> Optional[TicketInstanceOut]:
    """Update an existing TicketInstance."""
    async with get_async_session() as session:
        ticket_instance = await session.get(TicketInstance, ticket_instance_id)
        if not ticket_instance:
            return None

        for field, value in ticket_instance_update.model_dump(exclude_unset=True).items():
            setattr(ticket_instance, field, value)

        session.add(ticket_instance)
        await session.commit()
        await session.refresh(ticket_instance)
        return TicketInstanceOut.model_validate(ticket_instance)


async def delete_ticket_instance_repo(ticket_instance_id: int) -> bool:
    """Delete a TicketInstance by its ID."""
    async with get_async_session() as session:
        ticket_instance = await session.get(TicketInstance, ticket_instance_id)
        if not ticket_instance:
            return False

        await session.delete(ticket_instance)
        await session.commit()
        return True


async def list_ticket_instances_repo() -> List[TicketInstanceOut]:
    """List all TicketInstances."""
    async with get_async_session() as session:
        result = await session.execute(select(TicketInstance))
        records = result.scalars().all()
        return [TicketInstanceOut.model_validate(ti) for ti in records]


async def list_ticket_instances_in_date_range_repo(
    start_date: str,
    end_date: str,
) -> List[TicketInstanceOut]:
    """List TicketInstances created within a specific date range."""
    async with get_async_session() as session:
        result = await session.execute(
            select(TicketInstance).where(
                TicketInstance.created_at >= start_date,
                TicketInstance.created_at <= end_date,
            )
        )
        records = result.scalars().all()
        return [TicketInstanceOut.model_validate(ti) for ti in records]


async def get_ticket_instances_by_user_repo(
    user_id: int,
) -> List[TicketInstanceOut]:
    """List TicketInstances for a specific user."""
    async with get_async_session() as session:
        result = await session.execute(
            select(TicketInstance).where(TicketInstance.user_id == user_id)
        )
        records = result.scalars().all()
        return [TicketInstanceOut.model_validate(ti) for ti in records]


async def get_ticket_instances_by_status_repo(
    status: str,
) -> List[TicketInstanceOut]:
    """List TicketInstances filtered by their status."""
    async with get_async_session() as session:
        result = await session.execute(
            select(TicketInstance).where(TicketInstance.status == status)
        )
        records = result.scalars().all()
        return [TicketInstanceOut.model_validate(ti) for ti in records]


async def get_ticket_instance_by_seat_number_repo(
    seat_number: str,
) -> Optional[TicketInstanceOut]:
    """Retrieve a TicketInstance by its seat number."""
    async with get_async_session() as session:
        result = await session.execute(
            select(TicketInstance).where(TicketInstance.seat_number == seat_number)
        )
        ticket_instance = result.scalars().first()
        if ticket_instance:
            return TicketInstanceOut.model_validate(ticket_instance)
        return None