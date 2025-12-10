#!/usr/bin/env python3
"""Async repository for Payment model operations."""

from typing import Optional, List
from sqlalchemy import select, func

from app.db.models.payment import Payment
from app.db.session import get_async_session
from app.schemas.payment import PaymentOut, PaymentCreate, PaymentUpdate


async def create_payment_repo(payment: PaymentCreate) -> PaymentOut:
    """Create a new payment record asynchronously."""
    async with get_async_session() as session:
        db_payment = Payment(
            booking_id=payment.booking_id,
            amount=payment.amount,
            currency=payment.currency,
            method=payment.method,
            mpesa_ref=payment.mpesa_ref,
            callback_payload=payment.callback_payload,
        )
        session.add(db_payment)
        await session.commit()
        await session.refresh(db_payment)
        return PaymentOut.model_validate(db_payment)


async def get_payment_by_id_repo(payment_id: int) -> Optional[PaymentOut]:
    """Retrieve a payment record by its ID."""
    async with get_async_session() as session:
        db_payment = await session.get(Payment, payment_id)
        return PaymentOut.model_validate(db_payment) if db_payment else None


async def update_payment_repo(
    payment_id: int, payment_update: PaymentUpdate
) -> Optional[PaymentOut]:
    """Update payment details."""
    async with get_async_session() as session:
        db_payment = await session.get(Payment, payment_id)
        if not db_payment:
            return None

        db_payment.amount = payment_update.amount
        db_payment.currency = payment_update.currency
        db_payment.method = payment_update.method
        db_payment.mpesa_ref = payment_update.mpesa_ref
        db_payment.callback_payload = payment_update.callback_payload

        session.add(db_payment)
        await session.commit()
        await session.refresh(db_payment)
        return PaymentOut.model_validate(db_payment)


async def update_payment_status_repo(
    payment_id: int, status: str
) -> Optional[PaymentOut]:
    """Update the status of a payment record."""
    async with get_async_session() as session:
        db_payment = await session.get(Payment, payment_id)
        if not db_payment:
            return None

        db_payment.status = status
        session.add(db_payment)
        await session.commit()
        await session.refresh(db_payment)
        return PaymentOut.model_validate(db_payment)


async def delete_payment_repo(payment_id: int) -> bool:
    """Delete a payment record."""
    async with get_async_session() as session:
        db_payment = await session.get(Payment, payment_id)
        if not db_payment:
            return False

        await session.delete(db_payment)
        await session.commit()
        return True


async def list_payments_repo() -> List[PaymentOut]:
    """List all payments."""
    async with get_async_session() as session:
        result = await session.execute(select(Payment))
        payments = result.scalars().all()
        return [PaymentOut.model_validate(p) for p in payments]


async def get_payments_by_booking_id_repo(
    booking_id: int,
) -> List[PaymentOut]:
    """Retrieve all payments for a specific booking."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Payment).where(Payment.booking_id == booking_id)
        )
        payments = result.scalars().all()
        return [PaymentOut.model_validate(p) for p in payments]


async def record_callback_payload_repo(
    payment_id: int, payload: str
) -> Optional[PaymentOut]:
    """Store callback payload JSON/string."""
    async with get_async_session() as session:
        db_payment = await session.get(Payment, payment_id)
        if not db_payment:
            return None

        db_payment.callback_payload = payload
        await session.commit()
        await session.refresh(db_payment)
        return PaymentOut.model_validate(db_payment)


async def get_payment_by_mpesa_ref_repo(
    mpesa_ref: str,
) -> Optional[PaymentOut]:
    """Retrieve a payment by M-Pesa reference."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Payment).where(Payment.mpesa_ref == mpesa_ref)
        )
        payment = result.scalars().first()
        return PaymentOut.model_validate(payment) if payment else None


async def list_payments_by_status_repo(
    status: str,
) -> List[PaymentOut]:
    """List payments filtered by status."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Payment).where(Payment.status == status)
        )
        payments = result.scalars().all()
        return [PaymentOut.model_validate(p) for p in payments]


async def count_payments_repo() -> int:
    """Count total number of payments."""
    async with get_async_session() as session:
        result = await session.execute(select(func.count(Payment.id)))
        return result.scalar_one()


async def get_total_amount_by_booking_id_repo(
    booking_id: int,
) -> float:
    """Sum total amount paid for a booking."""
    async with get_async_session() as session:
        result = await session.execute(
            select(func.sum(Payment.amount)).where(
                Payment.booking_id == booking_id
            )
        )
        total = result.scalar()
        return float(total or 0.0)


async def get_payments_created_after_repo(timestamp) -> List[PaymentOut]:
    """Retrieve payments created after a timestamp."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Payment).where(Payment.created_at > timestamp)
        )
        payments = result.scalars().all()
        return [PaymentOut.model_validate(p) for p in payments]


async def get_payments_updated_after_repo(timestamp) -> List[PaymentOut]:
    """Retrieve payments updated after a timestamp."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Payment).where(Payment.updated_at > timestamp)
        )
        payments = result.scalars().all()
        return [PaymentOut.model_validate(p) for p in payments]


async def get_latest_payments_repo(
    limit: int = 10,
) -> List[PaymentOut]:
    """Retrieve latest payments by creation date."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Payment)
            .order_by(Payment.created_at.desc())
            .limit(limit)
        )
        payments = result.scalars().all()
        return [PaymentOut.model_validate(p) for p in payments]