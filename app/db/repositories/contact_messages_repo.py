#!/usr/bin/env python3
"""Repository layer for ContactMessage operations."""

from typing import Optional, List
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, and_, desc
from app.db.session import get_async_session
from app.db.models.contact_messages import ContactMessage
from app.schemas.contact_message import (
    ContactMessageOut, ContactMessageCreate, ContactMessageUpdate, ContactMessageStats
)


async def create_contact_message_repo(
    contact_data: ContactMessageCreate,
    client_ip: str,
    user_agent: str,
    reference_id: str,
    recaptcha_score: float,
    user_id: Optional[int],
    source: str,
) -> ContactMessageOut:
    """Create a new contact message."""
    async with get_async_session() as session:
        contact_message = ContactMessage(
            reference_id=reference_id,
            source=source,
            user_id=user_id,
            name=contact_data.name,
            email=contact_data.email,
            phone=contact_data.phone,
            subject=contact_data.subject,
            category=contact_data.category,
            message=contact_data.message,
            # event_title is only present on organizer submissions; None for user submissions
            event_title=getattr(contact_data, "event_title", None),
            status="new",
            priority="normal",
            client_ip=client_ip,
            user_agent=user_agent,
            recaptcha_score=recaptcha_score,
        )

        session.add(contact_message)
        await session.commit()
        await session.refresh(contact_message)

        return ContactMessageOut.model_validate(contact_message) if contact_message else None


async def get_contact_message_by_id_repo(message_id: int) -> Optional[ContactMessageOut]:
    """Get a contact message by ID."""
    async with get_async_session() as session:
        result = await session.execute(select(ContactMessage).where(ContactMessage.id == message_id))
        contact = result.scalar_one_or_none()
        return ContactMessageOut.model_validate(contact) if contact else None


async def get_contact_message_by_reference_id_repo(reference_id: str) -> Optional[ContactMessageOut]:
    """Get a contact message by reference ID."""
    async with get_async_session() as session:
        result = await session.execute(
            select(ContactMessage).where(ContactMessage.reference_id == reference_id)
        )
        contact = result.scalar_one_or_none()
        return ContactMessageOut.model_validate(contact) if contact else None


async def list_contact_messages_repo(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    category: Optional[str] = None,
    source: Optional[str] = None,
) -> List[ContactMessageOut]:
    """List contact messages with optional filters, newest first."""
    async with get_async_session() as session:
        query = select(ContactMessage).order_by(desc(ContactMessage.created_at)).offset(skip).limit(limit)

        if status:
            query = query.where(ContactMessage.status == status)

        if category:
            query = query.where(ContactMessage.category == category)

        if source:
            query = query.where(ContactMessage.source == source)

        result = await session.execute(query)
        contacts = result.scalars().all()
        return [ContactMessageOut.model_validate(contact) for contact in contacts]


async def update_contact_message_repo(
    message_id: int,
    update_data: ContactMessageUpdate | dict,
) -> Optional[ContactMessageOut]:
    """Update a contact message. Accepts either a ContactMessageUpdate schema or a plain dict."""
    async with get_async_session() as session:
        result = await session.execute(select(ContactMessage).where(ContactMessage.id == message_id))
        contact = result.scalar_one_or_none()

        if not contact:
            return None

        fields = update_data if isinstance(update_data, dict) else update_data.model_dump(exclude_unset=True)

        for field, value in fields.items():
            setattr(contact, field, value)

        await session.commit()
        await session.refresh(contact)

        return ContactMessageOut.model_validate(contact)


async def get_contact_stats_repo() -> ContactMessageStats:
    """Get contact message statistics."""
    async with get_async_session() as session:
        async def _count(where_clause=None):
            q = select(func.count(ContactMessage.id))
            if where_clause is not None:
                q = q.where(where_clause)
            r = await session.execute(q)
            return r.scalar() or 0

        return ContactMessageStats(
            total=     await _count(),
            new=       await _count(ContactMessage.status == "new"),
            pending=   await _count(ContactMessage.status == "pending"),
            responded= await _count(ContactMessage.status == "responded"),
            closed=    await _count(ContactMessage.status == "closed"),
            spam=      await _count(ContactMessage.status == "spam"),
        )


async def delete_contact_message_repo(message_id: int) -> bool:
    """Hard-delete a contact message. Returns True if deleted, False if not found."""
    async with get_async_session() as session:
        result = await session.execute(select(ContactMessage).where(ContactMessage.id == message_id))
        contact = result.scalar_one_or_none()

        if not contact:
            return False

        await session.delete(contact)
        await session.commit()
        return True


async def count_recent_messages_by_email_repo(email: str, hours: int = 1) -> int:
    """Count messages from an email in the last N hours."""
    async with get_async_session() as session:
        time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
        result = await session.execute(
            select(func.count(ContactMessage.id)).where(
                and_(
                    ContactMessage.email == email,
                    ContactMessage.created_at >= time_threshold,
                )
            )
        )
        return result.scalar() or 0


async def count_recent_messages_by_ip_repo(ip_address: str, hours: int = 1) -> int:
    """Count messages from an IP in the last N hours."""
    async with get_async_session() as session:
        time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
        result = await session.execute(
            select(func.count(ContactMessage.id)).where(
                and_(
                    ContactMessage.client_ip == ip_address,
                    ContactMessage.created_at >= time_threshold,
                )
            )
        )
        return result.scalar() or 0