#!/usr/bin/env python3
"""Async repository for Payment model operations."""

from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy import select, func
from app.db.models.payment import Payment
from app.db.session import get_async_session
from app.schemas.payment import PaymentOut, PaymentCreate, PaymentUpdate


async def create_payment_repo(payment: PaymentCreate) -> PaymentOut:
    async with get_async_session() as session:
        db_payment = Payment(
            order_id=payment.order_id,
            amount=payment.amount,
            currency=payment.currency,
            method=payment.method,
            mpesa_phone=payment.mpesa_phone,
            mpesa_checkout_request_id=payment.mpesa_checkout_request_id,
            mpesa_ref=payment.mpesa_ref,
            callback_payload=payment.callback_payload,
        )
        session.add(db_payment)
        await session.commit()
        await session.refresh(db_payment)
        return PaymentOut.model_validate(db_payment)


async def get_payment_by_id_repo(payment_id: int) -> Optional[PaymentOut]:
    async with get_async_session() as session:
        db_payment = await session.get(Payment, payment_id)
        return PaymentOut.model_validate(db_payment) if db_payment else None


async def get_payment_by_checkout_request_id_repo(
    checkout_request_id: str,
) -> Optional[PaymentOut]:
    """Look up a payment by Daraja CheckoutRequestID — used in callback handling."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Payment).where(
                Payment.mpesa_checkout_request_id == checkout_request_id
            )
        )
        db_payment = result.scalars().first()
        return PaymentOut.model_validate(db_payment) if db_payment else None


async def update_payment_repo(
    payment_id: int, payment_update: PaymentUpdate
) -> Optional[PaymentOut]:
    async with get_async_session() as session:
        db_payment = await session.get(Payment, payment_id)
        if not db_payment:
            return None
        for field, value in payment_update.model_dump(exclude_unset=True).items():
            setattr(db_payment, field, value)
        session.add(db_payment)
        await session.commit()
        await session.refresh(db_payment)
        return PaymentOut.model_validate(db_payment)


async def update_payment_status_repo(
    payment_id: int, status: str
) -> Optional[PaymentOut]:
    async with get_async_session() as session:
        db_payment = await session.get(Payment, payment_id)
        if not db_payment:
            return None
        db_payment.status = status
        session.add(db_payment)
        await session.commit()
        await session.refresh(db_payment)
        return PaymentOut.model_validate(db_payment)


async def update_payment_mpesa_success_repo(
    payment_id: int, mpesa_ref: str
) -> Optional[PaymentOut]:
    """Set status=completed and store the MpesaReceiptNumber."""
    async with get_async_session() as session:
        db_payment = await session.get(Payment, payment_id)
        if not db_payment:
            return None
        db_payment.status = "completed"
        db_payment.mpesa_ref = mpesa_ref
        session.add(db_payment)
        await session.commit()
        await session.refresh(db_payment)
        return PaymentOut.model_validate(db_payment)


async def delete_payment_repo(payment_id: int) -> bool:
    async with get_async_session() as session:
        db_payment = await session.get(Payment, payment_id)
        if not db_payment:
            return False
        await session.delete(db_payment)
        await session.commit()
        return True


async def list_payments_repo() -> List[PaymentOut]:
    async with get_async_session() as session:
        result = await session.execute(select(Payment))
        return [PaymentOut.model_validate(p) for p in result.scalars().all()]


async def get_payments_by_order_id_repo(order_id: int) -> List[PaymentOut]:
    async with get_async_session() as session:
        result = await session.execute(
            select(Payment).where(Payment.order_id == order_id)
        )
        return [PaymentOut.model_validate(p) for p in result.scalars().all()]


async def record_callback_payload_repo(
    payment_id: int, payload: str
) -> Optional[PaymentOut]:
    async with get_async_session() as session:
        db_payment = await session.get(Payment, payment_id)
        if not db_payment:
            return None
        db_payment.callback_payload = payload
        await session.commit()
        await session.refresh(db_payment)
        return PaymentOut.model_validate(db_payment)


async def get_payment_by_mpesa_ref_repo(mpesa_ref: str) -> Optional[PaymentOut]:
    async with get_async_session() as session:
        result = await session.execute(
            select(Payment).where(Payment.mpesa_ref == mpesa_ref)
        )
        payment = result.scalars().first()
        return PaymentOut.model_validate(payment) if payment else None


async def list_payments_by_status_repo(status: str) -> List[PaymentOut]:
    async with get_async_session() as session:
        result = await session.execute(
            select(Payment).where(Payment.status == status)
        )
        return [PaymentOut.model_validate(p) for p in result.scalars().all()]


async def count_payments_repo() -> int:
    async with get_async_session() as session:
        result = await session.execute(select(func.count(Payment.id)))
        return result.scalar_one()


async def get_total_amount_by_order_id_repo(order_id: int) -> float:
    async with get_async_session() as session:
        result = await session.execute(
            select(func.sum(Payment.amount)).where(Payment.order_id == order_id)
        )
        return float(result.scalar() or 0.0)


async def get_payments_created_after_repo(timestamp) -> List[PaymentOut]:
    async with get_async_session() as session:
        result = await session.execute(
            select(Payment).where(Payment.created_at > timestamp)
        )
        return [PaymentOut.model_validate(p) for p in result.scalars().all()]


async def get_payments_updated_after_repo(timestamp) -> List[PaymentOut]:
    async with get_async_session() as session:
        result = await session.execute(
            select(Payment).where(Payment.updated_at > timestamp)
        )
        return [PaymentOut.model_validate(p) for p in result.scalars().all()]


async def get_latest_payments_repo(limit: int = 10) -> List[PaymentOut]:
    async with get_async_session() as session:
        result = await session.execute(
            select(Payment).order_by(Payment.created_at.desc()).limit(limit)
        )
        return [PaymentOut.model_validate(p) for p in result.scalars().all()]


# ── Layer 1: reconciliation sweep support ─────────────────────────────────────

async def list_stuck_pending_mpesa_payments_repo(
    older_than_minutes: int = 5,
) -> List[PaymentOut]:
    """
    Payments that have been sitting in 'pending' for longer than expected —
    candidates for the STK status query sweep. Scoped to method='mpesa' with
    a stored CheckoutRequestID (free-order payments resolve synchronously
    and never sit pending).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=older_than_minutes)
    async with get_async_session() as session:
        result = await session.execute(
            select(Payment).where(
                Payment.status == "pending",
                Payment.method == "mpesa",
                Payment.mpesa_checkout_request_id.is_not(None),
                Payment.created_at < cutoff,
            )
        )
        return [PaymentOut.model_validate(p) for p in result.scalars().all()]


# ── Layer 2: manual review ────────────────────────────────────────────────────

async def submit_manual_review_repo(
    payment_id: int, mpesa_code: str, phone_number: Optional[str]
) -> Optional[PaymentOut]:
    """User-reported M-Pesa code — queues for admin review. Does NOT touch
    payment.status; only manual_review_status moves to 'pending'."""
    async with get_async_session() as session:
        db_payment = await session.get(Payment, payment_id)
        if not db_payment:
            return None
        db_payment.manual_review_status = "pending"
        db_payment.user_reported_mpesa_code = mpesa_code
        db_payment.user_reported_at = datetime.now(timezone.utc)
        if phone_number:
            db_payment.mpesa_phone = phone_number
        session.add(db_payment)
        await session.commit()
        await session.refresh(db_payment)
        return PaymentOut.model_validate(db_payment)


async def list_pending_manual_reviews_repo() -> List[PaymentOut]:
    """Payments awaiting a manual decision (user-reported only)."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Payment)
            .where(Payment.manual_review_status == "pending")
            .order_by(Payment.user_reported_at.asc())
        )
        return [PaymentOut.model_validate(p) for p in result.scalars().all()]


async def resolve_manual_review_repo(
    payment_id: int, approved: bool, mpesa_code: Optional[str] = None
) -> Optional[PaymentOut]:
    """
    Stamp the review outcome. If approved and a code is supplied — either
    the user's originally reported one, or one the admin typed in directly
    for a payment nobody reported — it's stored/overwritten here so
    mpesa_ref can be backfilled from it. Does NOT confirm the order itself;
    the service layer calls the shared confirmation helper separately.
    """
    async with get_async_session() as session:
        db_payment = await session.get(Payment, payment_id)
        if not db_payment:
            return None
        db_payment.manual_review_status = "approved" if approved else "rejected"
        if approved and mpesa_code:
            db_payment.user_reported_mpesa_code = mpesa_code
            if db_payment.user_reported_at is None:
                db_payment.user_reported_at = datetime.now(timezone.utc)
        session.add(db_payment)
        await session.commit()
        await session.refresh(db_payment)
        return PaymentOut.model_validate(db_payment)


# Enriched query for admin Payments page — joins user via booking

async def list_payments_enriched_repo() -> list:
    """List all payments with user name via booking join.
    Used by GET /admin/payments to return AdminPayment-shaped rows."""
    from app.db.models.order import Order
    from app.db.models.user import User

    async with get_async_session() as session:
        result = await session.execute(
            select(Payment, User.name)
            .join(Order, Payment.order_id == Order.id)
            .join(User, Order.user_id == User.id)
            .order_by(Payment.created_at.desc())
        )
        payments = []
        for payment, user_name in result:
            payments.append({
                'id': payment.id,
                'order_id': payment.order_id,
                'amount': payment.amount,
                'currency': payment.currency,
                'method': payment.method,
                'status': payment.status,
                'mpesa_phone': payment.mpesa_phone,
                'mpesa_checkout_request_id': payment.mpesa_checkout_request_id,
                'mpesa_ref': payment.mpesa_ref,
                'callback_payload': payment.callback_payload,
                'manual_review_status': payment.manual_review_status,
                'user_reported_mpesa_code': payment.user_reported_mpesa_code,
                'user_reported_at': payment.user_reported_at,
                'created_at': payment.created_at,
                'updated_at': payment.updated_at,
                # enriched
                'user_name': user_name,
            })
        return payments