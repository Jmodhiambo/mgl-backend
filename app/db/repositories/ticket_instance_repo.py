#!/usr/bin/env python3
"""Repository for TicketInstance model operations."""

from app.db.session import get_session
from typing import Optional
from app.db.models.ticket_instance import TicketInstance
from app.schemas.ticket_instance import TicketInstanceOut, TicketInstanceCreate, TicketInstanceUpdate

def create_ticket_instance_repo(ticket_instance_create: TicketInstanceCreate) -> TicketInstanceOut:
    """Create a new TicketInstance in the database."""
    with get_session() as session:
        ticket_instance = TicketInstance(
            booking_id=ticket_instance_create.booking_id,
            ticket_type_id=ticket_instance_create.ticket_type_id,
            user_id=ticket_instance_create.user_id,
            code=ticket_instance_create.code,
            status=ticket_instance_create.status,
            issued_to=ticket_instance_create.issued_to,
        )
        session.add(ticket_instance)
        session.commit()
        session.refresh(ticket_instance)
        return TicketInstanceOut.model_validate(ticket_instance)
    
def get_ticket_instance_by_id_repo(ticket_instance_id: int) -> Optional[TicketInstanceOut]:
    """Retrieve a TicketInstance by its ID."""
    with get_session() as session:
        ticket_instance = session.get(TicketInstance, ticket_instance_id)
        if ticket_instance:
            return TicketInstanceOut.model_validate(ticket_instance)
        return None
    
def update_ticket_instance_repo(ticket_instance_id: int, ticket_instance_update: TicketInstanceUpdate) -> Optional[TicketInstanceOut]:
    """Update an existing TicketInstance."""
    with get_session() as session:
        ticket_instance = session.get(TicketInstance, ticket_instance_id)
        if not ticket_instance:
            return None
        
        for field, value in ticket_instance_update.model_dump(exclude_unset=True).items():
            setattr(ticket_instance, field, value)
        
        session.commit()
        session.refresh(ticket_instance)
        return TicketInstanceOut.model_validate(ticket_instance)
    
def delete_ticket_instance_repo(ticket_instance_id: int) -> bool:
    """Delete a TicketInstance by its ID."""
    with get_session() as session:
        ticket_instance = session.get(TicketInstance, ticket_instance_id)
        if not ticket_instance:
            return False
        
        session.delete(ticket_instance)
        session.commit()
        return True
    
def list_ticket_instances_repo() -> list[TicketInstanceOut]:
    """List all TicketInstances in the database."""
    with get_session() as session:
        ticket_instances = session.query(TicketInstance).all()
        return [TicketInstanceOut.model_validate(ti) for ti in ticket_instances]
    
def list_ticket_instances_in_date_range_repo(start_date: str, end_date: str) -> list[TicketInstanceOut]:
    """List TicketInstances created within a specific date range."""
    with get_session() as session:
        ticket_instances = session.query(TicketInstance).filter(
            TicketInstance.created_at >= start_date,
            TicketInstance.created_at <= end_date
        ).all()
        return [TicketInstanceOut.model_validate(ti) for ti in ticket_instances]
    
def get_ticket_instances_by_user_repo(user_id: int) -> list[TicketInstanceOut]:
    """List TicketInstances for a specific user."""
    with get_session() as session:
        ticket_instances = session.query(TicketInstance).filter(
            TicketInstance.user_id == user_id
        ).all()
        return [TicketInstanceOut.model_validate(ti) for ti in ticket_instances]
    
def get_ticket_instances_by_status_repo(status: str) -> list[TicketInstanceOut]:
    """List TicketInstances filtered by their status."""
    with get_session() as session:
        ticket_instances = session.query(TicketInstance).filter(
            TicketInstance.status == status
        ).all()
        return [TicketInstanceOut.model_validate(ti) for ti in ticket_instances]