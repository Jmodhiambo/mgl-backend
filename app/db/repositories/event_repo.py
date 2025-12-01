#!/usr/bin/env python3
"""Repository for Event model operations."""

from app.db.models.event import Event
from app.db.session import get_session
from typing import Optional
from app.schemas.event import EventOut, EventCreateWithFlyer, EventCreate, EventUpdate
from datetime import datetime

def create_event_repo(event_data: EventCreateWithFlyer) -> EventOut:
    """Create a new event in the database."""
    with get_session() as session:
        new_event = Event(
            title=event_data.title,
            description=event_data.description,
            venue=event_data.venue,
            start_time=event_data.start_time,
            end_time=event_data.end_time,
            original_filename=event_data.original_filename,
            flyer_url=event_data.flyer_url,
            organizer_id=event_data.organizer_id,
        )
        session.add(new_event)
        session.commit()
        session.refresh(new_event)  # Refresh to get updated fields
        return EventOut.model_validate(new_event)
    
def update_event_repo(event_id: int, event_data: EventUpdate) -> EventOut:
    """Update an event in the database."""
    with get_session() as session:
        event = session.query(Event).filter(Event.id == event_id).first()
        if event:
            event.title = event_data.title
            event.description = event_data.description
            event.venue = event_data.venue
            event.start_time = event_data.start_time
            event.end_time = event_data.end_time
            session.commit()
            session.refresh(event)  # Refresh to get updated fields
            return EventOut.model_validate(event)
        return None
def get_approved_events_repo() -> list[EventOut]:
    """Get all approved events from the database."""
    with get_session() as session:
        events = session.query(Event).filter(Event.approved == True).all()
        return [EventOut.model_validate(event) for event in events]
    
def get_unapproved_events_repo() -> list[EventOut]:
    """Get all unapproved events from the database."""
    with get_session() as session:
        events = session.query(Event).filter(Event.approved == False).all()
        return [EventOut.model_validate(event) for event in events]

def get_all_events_repo() -> list[EventOut]:
    """Get all events from the database."""
    with get_session() as session:
        events = session.query(Event).all()
        return [EventOut.model_validate(event) for event in events]
    
def get_event_by_id_repo(event_id: int) -> Optional[EventOut]:
    """Retrieve an event by its ID."""
    with get_session() as session:
        event = session.query(Event).filter(Event.id == event_id).first()
        return EventOut.model_validate(event) if event else None
    
def approve_event_repo(event_id: int) -> Optional[EventOut]:
    """Approve an event."""
    with get_session() as session:
        event = session.query(Event).filter(Event.id == event_id).first()
        if event:
            event.approved = True
            session.commit()
            return EventOut.model_validate(event)
        return None
    
def activate_event_repo(event_id: int) -> bool:
    """Activate an event."""
    with get_session() as session:
        event = session.query(Event).filter(Event.id == event_id).first()
        if event:
            event.is_active = True
            session.commit()
            return True
        return False
    
def deactivate_event_repo(event_id: int) -> bool:
    """Deactivate an event."""
    with get_session() as session:
        event = session.query(Event).filter(Event.id == event_id).first()
        if event:
            event.is_active = False
            session.commit()
            return True
        return False
    
def reject_event_repo(event_id: int) -> bool:
    """Reject an event."""
    with get_session() as session:
        event = session.query(Event).filter(Event.id == event_id).first()
        if event:
            event.rejected = True
            session.commit()
            return True
        return False
    
def delete_event_repo(event_id: int) -> bool:
    """Delete an event by its ID."""
    with get_session() as session:
        event = session.query(Event).filter(Event.id == event_id).first()
        if event:
            session.delete(event)
            session.commit()
            return True
        return False
    
def update_event_status_repo(event_id: int, new_status: str) -> Optional[EventOut]:
    """Update the status of an event."""
    with get_session() as session:
        event = session.query(Event).filter(Event.id == event_id).first()
        if event:
            event.status = new_status
            session.commit()
            return EventOut.model_validate(event)
        return None
    
def get_events_by_organizer_repo(organizer_id: int) -> list[EventOut]:
    """Get all events organized by a specific user."""
    with get_session() as session:
        events = session.query(Event).filter(Event.organizer_id == organizer_id).all()
        return [EventOut.model_validate(event) for event in events]
    
def get_events_in_date_range_repo(start_date: datetime, end_date: datetime) -> list[EventOut]:
    """Get all events within a specific date range."""
    with get_session() as session:
        events = session.query(Event).filter(
            Event.start_time >= start_date,
            Event.end_time <= end_date
        ).all()
        return [EventOut.model_validate(event) for event in events]
    
def search_events_by_title_repo(keyword: str) -> list[EventOut]:
    """Search events by title keyword."""
    with get_session() as session:
        events = session.query(Event).filter(Event.title.ilike(f"%{keyword}%")).all()
        return [EventOut.model_validate(event) for event in events]
    
def count_events_by_organizer_repo(organizer_id: int) -> int:
    """Count the number of events organized by a specific user."""
    with get_session() as session:
        count = session.query(Event).filter(Event.organizer_id == organizer_id).count()
        return count

def count_events_repo() -> int:
    """Count the total number of events in the database."""
    with get_session() as session:
        count = session.query(Event).count()
        return count
    
def get_latest_events_repo(limit: int = 5) -> list[EventOut]:
    """Get the latest added events."""
    with get_session() as session:
        events = session.query(Event).filter(Event.approved == True).order_by(Event.created_at.desc()).limit(limit).all()
        return [EventOut.model_validate(event) for event in events]
    
def get_events_by_status_repo(status: str) -> list[EventOut]:
    """Get events by their status."""
    with get_session() as session:
        events = session.query(Event).filter(Event.status == status).all()
        return [EventOut.model_validate(event) for event in events]
    
def get_events_with_bookings_repo() -> list[EventOut]:
    """Get all events that have bookings."""
    with get_session() as session:
        events = session.query(Event).join(Event.bookings).all()
        return [EventOut.model_validate(event) for event in events]
    
def get_events_without_bookings_repo() -> list[EventOut]:
    """Get all events that do not have any bookings."""
    with get_session() as session:
        events = session.query(Event).outerjoin(Event.bookings).filter(Event.bookings == None).all()
        return [EventOut.model_validate(event) for event in events]
    
def search_events_by_venue_repo(venue: str) -> list[EventOut]:
    """Get events by venue."""
    with get_session() as session:
        events = session.query(Event).filter(Event.approved == True, Event.venue.ilike(f"%{venue}%")).all()
        return [EventOut.model_validate(event) for event in events]
    
def get_events_created_after_repo(date: datetime) -> list[EventOut]:
    """Get events created after a specific date."""
    with get_session() as session:
        events = session.query(Event).filter(Event.created_at > date).all()
        return [EventOut.model_validate(event) for event in events]
    
def get_events_created_before_repo(date: datetime) -> list[EventOut]:
    """Get events created before a specific date."""
    with get_session() as session:
        events = session.query(Event).filter(Event.created_at < date).all()
        return [EventOut.model_validate(event) for event in events]
    
def get_events_updated_after_repo(date: datetime) -> list[EventOut]:
    """Get events updated after a specific date."""
    with get_session() as session:
        events = session.query(Event).filter(Event.updated_at > date).all()
        return [EventOut.model_validate(event) for event in events]
    
def get_events_updated_before_repo(date: datetime) -> list[EventOut]:
    """Get events updated before a specific date."""
    with get_session() as session:
        events = session.query(Event).filter(Event.updated_at < date).all()
        return [EventOut.model_validate(event) for event in events]

def get_events_sorted_by_start_time_repo(ascending: bool = True) -> list[EventOut]:
    """Get events sorted by their start time."""
    with get_session() as session:
        if ascending:
            events = session.query(Event).order_by(Event.start_time.asc()).all()
        else:
            events = session.query(Event).order_by(Event.start_time.desc()).all()
        return [EventOut.model_validate(event) for event in events]
    
def get_events_sorted_by_end_time_repo(ascending: bool = True) -> list[EventOut]:
    """Get events sorted by their end time."""
    with get_session() as session:
        if ascending:
            events = session.query(Event).order_by(Event.end_time.asc()).all()
        else:
            events = session.query(Event).order_by(Event.end_time.desc()).all()
        return [EventOut.model_validate(event) for event in events]
    
def get_events_sorted_by_creation_date_repo(ascending: bool = True) -> list[EventOut]:
    """Get events sorted by their creation date."""
    with get_session() as session:
        if ascending:
            events = session.query(Event).order_by(Event.created_at.asc()).all()
        else:
            events = session.query(Event).order_by(Event.created_at.desc()).all()
        return [EventOut.model_validate(event) for event in events]

def get_events_by_country_repo(country: str) -> list[EventOut]:
    """Get events by country."""
    with get_session() as session:
        events = session.query(Event).filter(Event.country.ilike(f"%{country}%")).all()
        return [EventOut.model_validate(event) for event in events]