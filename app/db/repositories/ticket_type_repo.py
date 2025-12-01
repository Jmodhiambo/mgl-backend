#!/usr/bin/env python3
"""Repository for TicketType model operations."""

from app.db.session import get_session
from typing import Optional
from app.db.models.ticket_type import TicketType
from app.schemas.ticket_type import TicketTypeOut, TicketTypeCreate, TicketTypeUpdate

def create_ticket_type_repo(ticket_type_in: TicketTypeCreate) -> TicketTypeOut:
    """Create a new TicketType record in the database."""
    with get_session() as session:
        ticket_type = TicketType(**ticket_type_in.model_dump())
        session.add(ticket_type)
        session.commit()
        session.refresh(ticket_type)
        return TicketTypeOut.model_validate(ticket_type)
    
def get_ticket_type_by_id_repo(ticket_type_id: int) -> Optional[TicketTypeOut]:
    """Retrieve a TicketType by its ID."""
    with get_session() as session:
        ticket_type = session.get(TicketType, ticket_type_id)
        if ticket_type:
            return TicketTypeOut.model_validate(ticket_type)
        return None
    
def update_ticket_type_repo(ticket_type_id: int, ticket_type_in: TicketTypeUpdate) -> Optional[TicketTypeOut]:
    """Update an existing TicketType record."""
    with get_session() as session:
        ticket_type = session.get(TicketType, ticket_type_id)
        if not ticket_type:
            return None
        for field, value in ticket_type_in.model_dump(exclude_unset=True).items():
            setattr(ticket_type, field, value)
        session.commit()
        session.refresh(ticket_type)
        return TicketTypeOut.model_validate(ticket_type)
    
def delete_ticket_type_repo(ticket_type_id: int) -> bool:
    """Delete a TicketType record by its ID."""
    with get_session() as session:
        ticket_type = session.get(TicketType, ticket_type_id)
        if not ticket_type:
            return False
        session.delete(ticket_type)
        session.commit()
        return True
    
def list_ticket_types_event_id_repo(event_id: int) -> list[TicketTypeOut]:
    """List all TicketTypes for a given Event ID."""
    with get_session() as session:
        ticket_types = session.query(TicketType).filter(TicketType.event_id == event_id).all()
        return [TicketTypeOut.model_validate(tt) for tt in ticket_types]