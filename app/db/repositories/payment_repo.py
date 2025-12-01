#!/usr/bin/env python3
"""Repository for Payment model operations."""

from sqlalchemy import func
from app.db.models.payment import Payment
from app.db.session import get_session
from typing import Optional
from app.schemas.payment import PaymentOut, PaymentCreate, PaymentUpdate

def create_payment_repo(payment: PaymentCreate) -> PaymentOut:
    """Create a new payment record in the database."""
    with get_session() as session:
        db_payment = Payment(
            booking_id=payment.booking_id,
            amount=payment.amount,
            currency=payment.currency,
            method=payment.method,
            mpesa_ref=payment.mpesa_ref,
            callback_payload=payment.callback_payload
        )
        session.add(db_payment)
        session.commit()
        session.refresh(db_payment)
        return PaymentOut.model_validate(db_payment)

def get_payment_by_id_repo(payment_id: int) -> Optional[PaymentOut]:
    """Retrieve a payment record by its ID."""
    with get_session() as session:
        db_payment = session.get(Payment, payment_id)
        if db_payment:
            return PaymentOut.model_validate(db_payment)
        return None
    
def update_payment_repo(payment_id: int, payment_update: PaymentUpdate) -> Optional[PaymentOut]:
    """Update payment details."""
    with get_session() as session:
        db_payment = session.get(Payment, payment_id)
        if db_payment:
            db_payment.amount = payment_update.amount
            db_payment.currency = payment_update.currency
            db_payment.method = payment_update.method
            db_payment.mpesa_ref = payment_update.mpesa_ref
            db_payment.callback_payload = payment_update.callback_payload
            session.commit()
            session.refresh(db_payment)
            return PaymentOut.model_validate(db_payment)
        return None
    
def update_payment_status_repo(payment_id: int, status: str) -> Optional[PaymentOut]:
    """Update the status of a payment record."""
    with get_session() as session:
        db_payment = session.get(Payment, payment_id)
        if db_payment:
            db_payment.status = status
            session.commit()
            session.refresh(db_payment)
            return PaymentOut.model_validate(db_payment)
        return None
    
def delete_payment_repo(payment_id: int) -> bool:
    """Delete a payment record by its ID."""
    with get_session() as session:
        db_payment = session.get(Payment, payment_id)
        if db_payment:
            session.delete(db_payment)
            session.commit()
            return True
        return False
    
def list_payments_repo() -> list[PaymentOut]:
    """List all payment records."""
    with get_session() as session:
        db_payments = session.query(Payment).all()
        return [PaymentOut.model_validate(payment) for payment in db_payments]
    
def get_payments_by_booking_id_repo(booking_id: int) -> list[PaymentOut]:
    """Retrieve all payment records for a specific booking ID."""
    with get_session() as session:
        db_payments = session.query(Payment).filter(Payment.booking_id == booking_id).all()
        return [PaymentOut.model_validate(payment) for payment in db_payments]
    
def record_callback_payload_repo(payment_id: int, payload: str) -> Optional[PaymentOut]:
    """Record the callback payload for a payment."""
    with get_session() as session:
        db_payment = session.get(Payment, payment_id)
        if db_payment:
            db_payment.callback_payload = payload
            session.commit()
            session.refresh(db_payment)
            return PaymentOut.model_validate(db_payment)
        return None
    
def get_payment_by_mpesa_ref_repo(mpesa_ref: str) -> Optional[PaymentOut]:
    """Retrieve a payment record by its M-Pesa reference."""
    with get_session() as session:
        db_payment = session.query(Payment).filter(Payment.mpesa_ref == mpesa_ref).first()
        if db_payment:
            return PaymentOut.model_validate(db_payment)
        return None
    
def list_payments_by_status_repo(status: str) -> list[PaymentOut]:
    """List all payment records with a specific status."""
    with get_session() as session:
        db_payments = session.query(Payment).filter(Payment.status == status).all()
        return [PaymentOut.model_validate(payment) for payment in db_payments]
    
def count_payments_repo() -> int:
    """Count the total number of payment records."""
    with get_session() as session:
        count = session.query(Payment).count()
        return count
    
def get_total_amount_by_booking_id_repo(booking_id: int) -> float:
    """Get the total amount paid for a specific booking ID."""
    with get_session() as session:
        total = session.query(Payment).filter(Payment.booking_id == booking_id).with_entities(func.sum(Payment.amount)).scalar()
        return total if total else 0.0
    
def get_payments_created_after_repo(timestamp: str) -> list[PaymentOut]:
    """Retrieve all payment records created after a specific timestamp."""
    with get_session() as session:
        db_payments = session.query(Payment).filter(Payment.created_at > timestamp).all()
        return [PaymentOut.model_validate(payment) for payment in db_payments]
    
def get_payments_updated_after_repo(timestamp: str) -> list[PaymentOut]:
    """Retrieve all payment records updated after a specific timestamp."""
    with get_session() as session:
        db_payments = session.query(Payment).filter(Payment.updated_at > timestamp).all()
        return [PaymentOut.model_validate(payment) for payment in db_payments]
    
def get_latest_payments_repo(limit: int = 10) -> Optional[PaymentOut]:
    """Retrieve the most recently created payment record."""
    with get_session() as session:
        db_payment = session.query(Payment).order_by(Payment.created_at.desc()).limit(limit).all()
        return [PaymentOut.model_validate(payment) for payment in db_payment]