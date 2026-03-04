#!/usr/bin/env python3
"""Async repository for OrganizerEmails model operations."""

from sqlalchemy import select, func, and_, or_
from datetime import datetime, timezone
from typing import Optional, List
from app.db.models.organizer_emails import OrganizerEmails
from app.db.models.organizer_email_recipients import OrganizerEmailRecipients
from app.db.session import get_async_session
from app.schemas.organizer_emails import (
    OrganizerEmailOut,
    OrganizerEmailDetail,
    EmailDetailWithRecipients
)
from app.core.logging_config import logger


# ==================== OrganizerEmails Repository ====================

async def create_organizer_email_repo(
    organizer_id: int,
    event_id: Optional[int],
    recipient_type: str,
    recipient_count: int,
    subject: str,
    message: str,
    template_used: str,
    booking_ids: List[int],
    recipient_emails: List[str]
) -> OrganizerEmailOut:
    """Create a new organizer email record."""
    async with get_async_session() as session:
        new_email = OrganizerEmails(
            organizer_id=organizer_id,
            event_id=event_id,
            recipient_type=recipient_type,
            recipient_count=recipient_count,
            subject=subject,
            message=message,
            template_used=template_used,
            booking_ids=booking_ids,
            recipient_emails=recipient_emails,
            status='pending',
            failed_count=0,
            success_count=0
        )
        session.add(new_email)
        await session.commit()
        await session.refresh(new_email)
        return OrganizerEmailOut.model_validate(new_email)


async def get_organizer_email_by_id_repo(email_id: int) -> Optional[OrganizerEmailDetail]:
    """Get an organizer email by ID."""
    async with get_async_session() as session:
        result = await session.execute(
            select(OrganizerEmails).where(OrganizerEmails.id == email_id)
        )
        email = result.scalar_one_or_none()
        return OrganizerEmailDetail.model_validate(email) if email else None


async def get_organizer_email_with_recipients_repo(email_id: int) -> Optional[EmailDetailWithRecipients]:
    """Get an organizer email with all recipient details."""
    async with get_async_session() as session:
        # Get email
        result = await session.execute(
            select(OrganizerEmails).where(OrganizerEmails.id == email_id)
        )
        email = result.scalar_one_or_none()
        
        if not email:
            return None
        
        # Get recipients
        recipients_result = await session.execute(
            select(OrganizerEmailRecipients).where(
                OrganizerEmailRecipients.email_id == email_id
            )
        )
        recipients = recipients_result.scalars().all()
        
        # Combine
        email_dict = {
            **email.__dict__,
            'recipients': [r.__dict__ for r in recipients]
        }
        return EmailDetailWithRecipients.model_validate(email_dict)


async def get_organizer_emails_by_organizer_repo(
    organizer_id: int,
    event_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> tuple[List[OrganizerEmailOut], int]:
    """Get all emails for an organizer with filters."""
    async with get_async_session() as session:
        # Build query
        query = select(OrganizerEmails).where(
            OrganizerEmails.organizer_id == organizer_id
        )
        
        # Apply filters
        if event_id:
            query = query.where(OrganizerEmails.event_id == event_id)
        
        if status:
            query = query.where(OrganizerEmails.status == status)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar_one()
        
        # Get paginated results
        query = query.order_by(OrganizerEmails.created_at.desc()).offset(offset).limit(limit)
        result = await session.execute(query)
        emails = result.scalars().all()
        
        return [OrganizerEmailOut.model_validate(email) for email in emails], total


async def update_organizer_email_status_repo(
    email_id: int,
    status: str,
    success_count: int,
    failed_count: int,
    sent_at: Optional[datetime] = None
) -> Optional[OrganizerEmailOut]:
    """Update organizer email status."""
    async with get_async_session() as session:
        result = await session.execute(
            select(OrganizerEmails).where(OrganizerEmails.id == email_id)
        )
        email = result.scalar_one_or_none()
        
        if email:
            email.status = status
            email.success_count = success_count
            email.failed_count = failed_count
            if sent_at:
                email.sent_at = sent_at
            
            await session.commit()
            await session.refresh(email)
            return OrganizerEmailOut.model_validate(email)
        
        return None


async def delete_organizer_email_repo(email_id: int) -> bool:
    """Delete an organizer email."""
    async with get_async_session() as session:
        result = await session.execute(
            select(OrganizerEmails).where(OrganizerEmails.id == email_id)
        )
        email = result.scalar_one_or_none()
        
        if email:
            await session.delete(email)
            await session.commit()
            return True
        
        return False


async def get_email_stats_repo(organizer_id: int) -> dict:
    """Get email statistics for an organizer."""
    async with get_async_session() as session:
        # Total sent
        total_sent_result = await session.execute(
            select(func.count()).select_from(OrganizerEmails).where(
                and_(
                    OrganizerEmails.organizer_id == organizer_id,
                    OrganizerEmails.status == 'sent'
                )
            )
        )
        total_sent = total_sent_result.scalar_one()
        
        # Total recipients
        total_recipients_result = await session.execute(
            select(func.sum(OrganizerEmails.recipient_count)).where(
                and_(
                    OrganizerEmails.organizer_id == organizer_id,
                    OrganizerEmails.status == 'sent'
                )
            )
        )
        total_recipients = total_recipients_result.scalar_one() or 0
        
        # Success/failure counts
        success_result = await session.execute(
            select(func.sum(OrganizerEmails.success_count)).where(
                OrganizerEmails.organizer_id == organizer_id
            )
        )
        total_success = success_result.scalar_one() or 0
        
        failed_result = await session.execute(
            select(func.sum(OrganizerEmails.failed_count)).where(
                OrganizerEmails.organizer_id == organizer_id
            )
        )
        total_failed = failed_result.scalar_one() or 0
        
        # Calculate success rate
        total_attempts = total_success + total_failed
        success_rate = (total_success / total_attempts * 100) if total_attempts > 0 else 0
        
        # This month stats
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        first_day_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        
        emails_this_month_result = await session.execute(
            select(func.count()).select_from(OrganizerEmails).where(
                and_(
                    OrganizerEmails.organizer_id == organizer_id,
                    OrganizerEmails.created_at >= first_day_of_month
                )
            )
        )
        emails_this_month = emails_this_month_result.scalar_one()
        
        recipients_this_month_result = await session.execute(
            select(func.sum(OrganizerEmails.recipient_count)).where(
                and_(
                    OrganizerEmails.organizer_id == organizer_id,
                    OrganizerEmails.created_at >= first_day_of_month
                )
            )
        )
        recipients_this_month = recipients_this_month_result.scalar_one() or 0
        
        # By template
        template_result = await session.execute(
            select(
                OrganizerEmails.template_used,
                func.count(OrganizerEmails.id)
            ).where(
                OrganizerEmails.organizer_id == organizer_id
            ).group_by(OrganizerEmails.template_used)
        )
        by_template = {row[0]: row[1] for row in template_result.all()}
        
        # By status
        status_result = await session.execute(
            select(
                OrganizerEmails.status,
                func.count(OrganizerEmails.id)
            ).where(
                OrganizerEmails.organizer_id == organizer_id
            ).group_by(OrganizerEmails.status)
        )
        by_status = {row[0]: row[1] for row in status_result.all()}
        
        return {
            'total_sent': total_sent,
            'total_recipients': int(total_recipients),
            'success_rate': round(success_rate, 2),
            'emails_this_month': emails_this_month,
            'recipients_this_month': int(recipients_this_month),
            'by_template': by_template,
            'by_status': by_status
        }


# ==================== Admin Functions ====================

async def get_all_organizer_emails_repo(
    limit: int = 50,
    offset: int = 0
) -> tuple[List[OrganizerEmailOut], int]:
    """Get all organizer emails (admin only)."""
    async with get_async_session() as session:
        # Get total count
        count_result = await session.execute(
            select(func.count()).select_from(OrganizerEmails)
        )
        total = count_result.scalar_one()
        
        # Get paginated results
        result = await session.execute(
            select(OrganizerEmails)
            .order_by(OrganizerEmails.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        emails = result.scalars().all()
        
        return [OrganizerEmailOut.model_validate(email) for email in emails], total


async def get_all_email_stats_repo() -> dict:
    """Get overall email statistics (admin only)."""
    async with get_async_session() as session:
        # Total emails
        total_result = await session.execute(
            select(func.count()).select_from(OrganizerEmails)
        )
        total_emails = total_result.scalar_one()
        
        # Total recipients
        recipients_result = await session.execute(
            select(func.sum(OrganizerEmails.recipient_count))
        )
        total_recipients = recipients_result.scalar_one() or 0
        
        # By status
        status_result = await session.execute(
            select(
                OrganizerEmails.status,
                func.count(OrganizerEmails.id)
            ).group_by(OrganizerEmails.status)
        )
        by_status = {row[0]: row[1] for row in status_result.all()}
        
        return {
            'total_emails': total_emails,
            'total_recipients': int(total_recipients),
            'by_status': by_status
        }