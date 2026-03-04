#!/usr/bin/env python3
"""Async repository for OrganizerEmailRecipients model operations."""

from sqlalchemy import select, func, and_
from datetime import datetime, timezone
from typing import Optional, List
from app.db.models.organizer_email_recipients import OrganizerEmailRecipients
from app.db.session import get_async_session
from app.schemas.organizer_emails import (
    OrganizerEmailRecipientOut,
    OrganizerEmailRecipientUpdate
)
from app.core.logging_config import logger


async def create_email_recipient_repo(
    email_id: int,
    booking_id: int,
    recipient_name: str,
    recipient_email: str
) -> OrganizerEmailRecipientOut:
    """Create a new email recipient record."""
    async with get_async_session() as session:
        new_recipient = OrganizerEmailRecipients(
            email_id=email_id,
            booking_id=booking_id,
            recipient_name=recipient_name,
            recipient_email=recipient_email,
            status='pending'
        )
        session.add(new_recipient)
        await session.commit()
        await session.refresh(new_recipient)
        return OrganizerEmailRecipientOut.model_validate(new_recipient)


async def get_email_recipient_by_id_repo(recipient_id: int) -> Optional[OrganizerEmailRecipientOut]:
    """Get an email recipient by ID."""
    async with get_async_session() as session:
        result = await session.execute(
            select(OrganizerEmailRecipients).where(
                OrganizerEmailRecipients.id == recipient_id
            )
        )
        recipient = result.scalar_one_or_none()
        return OrganizerEmailRecipientOut.model_validate(recipient) if recipient else None


async def get_recipients_by_email_id_repo(email_id: int) -> List[OrganizerEmailRecipientOut]:
    """Get all recipients for a specific email."""
    async with get_async_session() as session:
        result = await session.execute(
            select(OrganizerEmailRecipients).where(
                OrganizerEmailRecipients.email_id == email_id
            ).order_by(OrganizerEmailRecipients.created_at)
        )
        recipients = result.scalars().all()
        return [OrganizerEmailRecipientOut.model_validate(r) for r in recipients]


async def get_recipients_by_booking_id_repo(booking_id: int) -> List[OrganizerEmailRecipientOut]:
    """Get all email recipients for a specific booking."""
    async with get_async_session() as session:
        result = await session.execute(
            select(OrganizerEmailRecipients).where(
                OrganizerEmailRecipients.booking_id == booking_id
            ).order_by(OrganizerEmailRecipients.created_at.desc())
        )
        recipients = result.scalars().all()
        return [OrganizerEmailRecipientOut.model_validate(r) for r in recipients]


async def update_recipient_status_repo(
    recipient_id: int,
    status: str,
    sent_at: Optional[datetime] = None,
    error_message: Optional[str] = None
) -> Optional[OrganizerEmailRecipientOut]:
    """Update email recipient status."""
    async with get_async_session() as session:
        result = await session.execute(
            select(OrganizerEmailRecipients).where(
                OrganizerEmailRecipients.id == recipient_id
            )
        )
        recipient = result.scalar_one_or_none()
        
        if recipient:
            recipient.status = status
            if sent_at:
                recipient.sent_at = sent_at
            if error_message:
                recipient.error_message = error_message
            
            await session.commit()
            await session.refresh(recipient)
            return OrganizerEmailRecipientOut.model_validate(recipient)
        
        return None


async def update_recipient_tracking_repo(
    recipient_id: int,
    opened_at: Optional[datetime] = None,
    clicked_at: Optional[datetime] = None
) -> Optional[OrganizerEmailRecipientOut]:
    """Update email recipient tracking (opened, clicked)."""
    async with get_async_session() as session:
        result = await session.execute(
            select(OrganizerEmailRecipients).where(
                OrganizerEmailRecipients.id == recipient_id
            )
        )
        recipient = result.scalar_one_or_none()
        
        if recipient:
            if opened_at:
                recipient.opened_at = opened_at
            if clicked_at:
                recipient.clicked_at = clicked_at
            
            await session.commit()
            await session.refresh(recipient)
            return OrganizerEmailRecipientOut.model_validate(recipient)
        
        return None


async def get_recipient_stats_by_email_repo(email_id: int) -> dict:
    """Get recipient statistics for a specific email."""
    async with get_async_session() as session:
        # Total recipients
        total_result = await session.execute(
            select(func.count()).select_from(OrganizerEmailRecipients).where(
                OrganizerEmailRecipients.email_id == email_id
            )
        )
        total = total_result.scalar_one()
        
        # By status
        status_result = await session.execute(
            select(
                OrganizerEmailRecipients.status,
                func.count(OrganizerEmailRecipients.id)
            ).where(
                OrganizerEmailRecipients.email_id == email_id
            ).group_by(OrganizerEmailRecipients.status)
        )
        by_status = {row[0]: row[1] for row in status_result.all()}
        
        # Opened count
        opened_result = await session.execute(
            select(func.count()).select_from(OrganizerEmailRecipients).where(
                and_(
                    OrganizerEmailRecipients.email_id == email_id,
                    OrganizerEmailRecipients.opened_at.isnot(None)
                )
            )
        )
        opened = opened_result.scalar_one()
        
        # Clicked count
        clicked_result = await session.execute(
            select(func.count()).select_from(OrganizerEmailRecipients).where(
                and_(
                    OrganizerEmailRecipients.email_id == email_id,
                    OrganizerEmailRecipients.clicked_at.isnot(None)
                )
            )
        )
        clicked = clicked_result.scalar_one()
        
        # Calculate rates
        open_rate = (opened / total * 100) if total > 0 else 0
        click_rate = (clicked / total * 100) if total > 0 else 0
        
        return {
            'total': total,
            'by_status': by_status,
            'opened': opened,
            'clicked': clicked,
            'open_rate': round(open_rate, 2),
            'click_rate': round(click_rate, 2)
        }


async def delete_email_recipient_repo(recipient_id: int) -> bool:
    """Delete an email recipient."""
    async with get_async_session() as session:
        result = await session.execute(
            select(OrganizerEmailRecipients).where(
                OrganizerEmailRecipients.id == recipient_id
            )
        )
        recipient = result.scalar_one_or_none()
        
        if recipient:
            await session.delete(recipient)
            await session.commit()
            return True
        
        return False


async def delete_recipients_by_email_id_repo(email_id: int) -> int:
    """Delete all recipients for a specific email. Returns count of deleted recipients."""
    async with get_async_session() as session:
        result = await session.execute(
            select(OrganizerEmailRecipients).where(
                OrganizerEmailRecipients.email_id == email_id
            )
        )
        recipients = result.scalars().all()
        count = len(recipients)
        
        for recipient in recipients:
            await session.delete(recipient)
        
        await session.commit()
        return count


# ==================== Admin Functions ====================

async def get_all_email_recipients_repo(
    limit: int = 100,
    offset: int = 0
) -> tuple[List[OrganizerEmailRecipientOut], int]:
    """Get all email recipients (admin only)."""
    async with get_async_session() as session:
        # Get total count
        count_result = await session.execute(
            select(func.count()).select_from(OrganizerEmailRecipients)
        )
        total = count_result.scalar_one()
        
        # Get paginated results
        result = await session.execute(
            select(OrganizerEmailRecipients)
            .order_by(OrganizerEmailRecipients.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        recipients = result.scalars().all()
        
        return [OrganizerEmailRecipientOut.model_validate(r) for r in recipients], total


async def get_failed_recipients_repo(
    limit: int = 100,
    offset: int = 0
) -> tuple[List[OrganizerEmailRecipientOut], int]:
    """Get all failed email recipients (admin only)."""
    async with get_async_session() as session:
        # Get total count
        count_result = await session.execute(
            select(func.count()).select_from(OrganizerEmailRecipients).where(
                OrganizerEmailRecipients.status == 'failed'
            )
        )
        total = count_result.scalar_one()
        
        # Get paginated results
        result = await session.execute(
            select(OrganizerEmailRecipients)
            .where(OrganizerEmailRecipients.status == 'failed')
            .order_by(OrganizerEmailRecipients.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        recipients = result.scalars().all()
        
        return [OrganizerEmailRecipientOut.model_validate(r) for r in recipients], total