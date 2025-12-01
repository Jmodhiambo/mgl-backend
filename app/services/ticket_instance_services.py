#!/usr/bin/env python3
"""TicketInstance services for MGLTickets."""

from app.core.logging_config import logger
import app.db.repositories.ticket_instance_repo as ti_repo
from app.schemas.ticket_instance import TicketInstanceCreate, TicketInstanceUpdate
from typing import Optional
from datetime import datetime

def create_ticket_instance(ticket_instance_create: TicketInstanceCreate) -> dict:
    """Create a new TicketInstance in the database."""
    logger.info("Creating a new TicketInstance")
    return ti_repo.create_ticket_instance_repo(ticket_instance_create)

def get_ticket_instance_by_id(ticket_instance_id: int) -> Optional[dict]:
    """Retrieve a TicketInstance by its ID."""
    logger.info(f"Retrieving TicketInstance with ID: {ticket_instance_id}")
    return ti_repo.get_ticket_instance_by_id_repo(ticket_instance_id)

def update_ticket_instance(ticket_instance_id: int, ticket_instance_update: TicketInstanceUpdate) -> Optional[dict]:
    """Update an existing TicketInstance."""
    logger.info(f"Updating TicketInstance with ID: {ticket_instance_id}")
    return ti_repo.update_ticket_instance_repo(ticket_instance_id, ticket_instance_update)

def delete_ticket_instance(ticket_instance_id: int) -> bool:
    """Delete a TicketInstance by its ID."""
    logger.info(f"Deleting TicketInstance with ID: {ticket_instance_id}")
    return ti_repo.delete_ticket_instance_repo(ticket_instance_id)

def list_ticket_instances() -> list[dict]:
    """List all TicketInstances in the database."""
    logger.info("Listing all TicketInstances")
    return ti_repo.list_ticket_instances_repo()

def list_ticket_instances_in_date_range(start_date: datetime, end_date: datetime) -> list[dict]:
    """List TicketInstances created within a specific date range."""
    logger.info(f"Listing TicketInstances from {start_date} to {end_date}")
    return ti_repo.list_ticket_instances_in_date_range_repo(start_date, end_date)

def get_ticket_instances_by_user(user_id: int) -> list[dict]:
    """List TicketInstances for a specific user."""
    logger.info(f"Listing TicketInstances for user ID: {user_id}")
    return ti_repo.get_ticket_instances_by_user_repo(user_id)

def get_ticket_instances_by_status(status: str) -> list[dict]:
    """List TicketInstances filtered by their status."""
    logger.info(f"Listing TicketInstances with status: {status}")
    return ti_repo.get_ticket_instances_by_status_repo(status)