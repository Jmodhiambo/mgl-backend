#!/usr/bin/env python3
"""Service layer for Payment operations."""

from typing import Optional
from datetime import datetime
import app.db.repositories.payment_repo as payment_repo
from app.schemas.payment import PaymentCreate, PaymentUpdate
from app.core.logging_config import logger

async def create_payment_service(payment: PaymentCreate) -> dict:
    """Service to create a new payment."""
    logger.info("Creating a new payment record.")
    return payment_repo.create_payment_repo(payment)

async def get_payment_by_id_service(payment_id: int) -> Optional[dict]:
    """Service to retrieve a payment by its ID."""
    logger.info(f"Retrieving payment record with ID: {payment_id}.")
    return payment_repo.get_payment_by_id_repo(payment_id)

async def update_payment_service(payment_id: int, payment_update: PaymentUpdate) -> Optional[dict]:
    """Service to update payment details."""
    logger.info(f"Updating payment record with ID: {payment_id}.")
    return payment_repo.update_payment_repo(payment_id, payment_update)

async def update_payment_status_service(payment_id: int, status: str) -> Optional[dict]:
    """Service to update the status of a payment."""
    logger.info(f"Updating status of payment record with ID: {payment_id} to {status}.")
    return payment_repo.update_payment_status_repo(payment_id, status)

async def delete_payment_service(payment_id: int) -> bool:
    """Service to delete a payment record."""
    logger.info(f"Deleting payment record with ID: {payment_id}.")
    return payment_repo.delete_payment_repo(payment_id)

async def list_payments_service() -> list[dict]:
    """Service to list all payments."""
    logger.info("Listing all payment records.")
    return payment_repo.list_payments_repo()

async def get_payments_by_booking_id_service(booking_id: int) -> list[dict]:
    """Service to retrieve payments by booking ID."""
    logger.info(f"Retrieving payment records for booking ID: {booking_id}.")
    return payment_repo.get_payments_by_booking_id_repo(booking_id)

async def record_payment_callback_service(payment_id: int, callback_payload: str) -> Optional[dict]:
    """Service to record the callback payload for a payment."""
    logger.info(f"Recording callback payload for payment ID: {payment_id}.")
    return payment_repo.record_callback_payload_repo(payment_id, callback_payload)

async def get_payment_by_mpesa_ref_service(mpesa_ref: str) -> list[dict]:
    """Service to retrieve payments by M-Pesa reference."""
    logger.info(f"Retrieving payment records with M-Pesa reference: {mpesa_ref}.")
    return payment_repo.get_payment_by_mpesa_ref_repo(mpesa_ref)

async def list_payments_by_status_service(status: str) -> list[dict]:
    """Service to list payments by their status."""
    logger.info(f"Listing payment records with status: {status}.")
    return payment_repo.list_payments_by_status_repo(status)

async def count_payments_service() -> int:
    """Service to count total number of payments."""
    logger.info("Counting total number of payment records.")
    return payment_repo.count_payments_repo()

async def get_total_by_booking_id_service(booking_id: int) -> float:
    """Service to get the total payment amount for a specific booking ID."""
    logger.info(f"Calculating total payment amount for booking ID: {booking_id}.")
    return payment_repo.get_total_amount_by_booking_id_repo(booking_id)

async def get_payments_created_after_service(date_time: datetime) -> list[dict]:
    """Service to retrieve payments created after a specific date and time."""
    logger.info(f"Retrieving payment records created after: {date_time}.")
    return payment_repo.get_payments_created_after_repo(date_time)

async def get_payments_updated_after_service(date_time: datetime) -> list[dict]:
    """Service to retrieve payments updated after a specific date and time."""
    logger.info(f"Retrieving payment records updated after: {date_time}.")
    return payment_repo.get_payments_updated_after_repo(date_time)

async def get_latest_payments_service(limit: int = 10) -> list[dict]:
    """Service to retrieve the latest payment records."""
    logger.info(f"Retrieving the latest {limit} payment records.")
    return payment_repo.get_latest_payments_repo(limit)