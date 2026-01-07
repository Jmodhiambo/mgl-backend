#!/usr/bin/env python3
"""Repository layer for ContactMessage operations."""

from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.db.models.contact import ContactMessage
from app.schemas.contact import ContactMessageCreate, ContactMessageUpdate
import secrets
import string


def generate_reference_id(category: str) -> str:
    """
    Generate unique reference ID.
    Format: MSG-{CATEGORY}-{DATE}-{RANDOM}
    Example: MSG-GEN-20260104-A1B2C3
    """
    category_code = category[:3].upper()
    date_str = datetime.now().strftime('%Y%m%d')
    random_str = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"MSG-{category_code}-{date_str}-{random_str}"


async def create_contact_message_repo(
    db: Session,
    contact_data: ContactMessageCreate,
    client_ip: str,
    user_agent: str,
    recaptcha_score: float
) -> ContactMessage:
    """Create a new contact message."""
    
    # Generate unique reference ID
    reference_id = generate_reference_id(contact_data.category)
    
    # Ensure uniqueness (very unlikely collision, but safe)
    while db.query(ContactMessage).filter(
        ContactMessage.reference_id == reference_id
    ).first():
        reference_id = generate_reference_id(contact_data.category)
    
    contact_message = ContactMessage(
        reference_id=reference_id,
        user_id=contact_data.user_id,
        name=contact_data.name,
        email=contact_data.email,
        phone=contact_data.phone,
        subject=contact_data.subject,
        category=contact_data.category,
        message=contact_data.message,
        status='new',
        priority='normal',
        client_ip=client_ip,
        user_agent=user_agent,
        recaptcha_score=recaptcha_score
    )
    
    db.add(contact_message)
    db.commit()
    db.refresh(contact_message)
    
    return contact_message


async def get_contact_message_by_id_repo(
    db: Session, 
    message_id: int
) -> Optional[ContactMessage]:
    """Get a contact message by ID."""
    return db.query(ContactMessage).filter(
        ContactMessage.id == message_id
    ).first()


async def get_contact_message_by_reference_repo(
    db: Session, 
    reference_id: str
) -> Optional[ContactMessage]:
    """Get a contact message by reference ID."""
    return db.query(ContactMessage).filter(
        ContactMessage.reference_id == reference_id
    ).first()


async def list_contact_messages_repo(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    category: Optional[str] = None
) -> List[ContactMessage]:
    """List contact messages with optional filters."""
    query = db.query(ContactMessage)
    
    if status:
        query = query.filter(ContactMessage.status == status)
    if category:
        query = query.filter(ContactMessage.category == category)
    
    return query.order_by(
        ContactMessage.created_at.desc()
    ).offset(skip).limit(limit).all()


async def update_contact_message_repo(
    db: Session,
    message_id: int,
    update_data: ContactMessageUpdate
) -> Optional[ContactMessage]:
    """Update a contact message."""
    contact_message = await get_contact_message_by_id_repo(db, message_id)
    
    if not contact_message:
        return None
    
    update_dict = update_data.model_dump(exclude_unset=True)
    
    for key, value in update_dict.items():
        setattr(contact_message, key, value)
    
    contact_message.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(contact_message)
    
    return contact_message


async def mark_as_responded_repo(
    db: Session,
    message_id: int
) -> Optional[ContactMessage]:
    """Mark a message as responded."""
    contact_message = await get_contact_message_by_id_repo(db, message_id)
    
    if not contact_message:
        return None
    
    contact_message.status = 'responded'
    contact_message.responded_at = datetime.utcnow()
    contact_message.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(contact_message)
    
    return contact_message


async def mark_as_closed_repo(
    db: Session,
    message_id: int
) -> Optional[ContactMessage]:
    """Mark a message as closed."""
    contact_message = await get_contact_message_by_id_repo(db, message_id)
    
    if not contact_message:
        return None
    
    contact_message.status = 'closed'
    contact_message.closed_at = datetime.utcnow()
    contact_message.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(contact_message)
    
    return contact_message


async def mark_as_spam_repo(
    db: Session,
    message_id: int
) -> Optional[ContactMessage]:
    """Mark a message as spam."""
    contact_message = await get_contact_message_by_id_repo(db, message_id)
    
    if not contact_message:
        return None
    
    contact_message.status = 'spam'
    contact_message.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(contact_message)
    
    return contact_message


async def get_contact_stats_repo(db: Session) -> dict:
    """Get contact message statistics."""
    total = db.query(func.count(ContactMessage.id)).scalar()
    new = db.query(func.count(ContactMessage.id)).filter(
        ContactMessage.status == 'new'
    ).scalar()
    responded = db.query(func.count(ContactMessage.id)).filter(
        ContactMessage.status == 'responded'
    ).scalar()
    closed = db.query(func.count(ContactMessage.id)).filter(
        ContactMessage.status == 'closed'
    ).scalar()
    spam = db.query(func.count(ContactMessage.id)).filter(
        ContactMessage.status == 'spam'
    ).scalar()
    
    return {
        'total': total or 0,
        'new': new or 0,
        'responded': responded or 0,
        'closed': closed or 0,
        'spam': spam or 0
    }


async def count_recent_messages_by_email_repo(
    db: Session,
    email: str,
    hours: int = 1
) -> int:
    """Count messages from an email in the last N hours."""
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    
    return db.query(func.count(ContactMessage.id)).filter(
        and_(
            ContactMessage.email == email,
            ContactMessage.created_at >= time_threshold
        )
    ).scalar() or 0


async def count_recent_messages_by_ip_repo(
    db: Session,
    ip_address: str,
    hours: int = 1
) -> int:
    """Count messages from an IP in the last N hours."""
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    
    return db.query(func.count(ContactMessage.id)).filter(
        and_(
            ContactMessage.client_ip == ip_address,
            ContactMessage.created_at >= time_threshold
        )
    ).scalar() or 0