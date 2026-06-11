#!/usr/bin/env python3
"""Service layer for Payment operations."""

import json
from typing import Optional
from datetime import datetime
import app.db.repositories.payment_repo as payment_repo
import app.db.repositories.booking_repo as booking_repo
from app.schemas.payment import PaymentCreate, PaymentUpdate, MpesaStkPushRequest, MpesaStkPushResponse
from app.services.mpesa_services import initiate_stk_push, parse_mpesa_callback
from app.core.logging_config import logger


# ── Core CRUD ─────────────────────────────────────────────────────────────────

async def create_payment_service(payment: PaymentCreate) -> dict:
    logger.info("Creating a new payment record.")
    return await payment_repo.create_payment_repo(payment)


async def get_payment_by_id_service(payment_id: int) -> Optional[dict]:
    logger.info(f"Retrieving payment record with ID: {payment_id}.")
    return await payment_repo.get_payment_by_id_repo(payment_id)


async def update_payment_service(payment_id: int, payment_update: PaymentUpdate) -> Optional[dict]:
    logger.info(f"Updating payment record with ID: {payment_id}.")
    return await payment_repo.update_payment_repo(payment_id, payment_update)


async def update_payment_status_service(payment_id: int, status: str) -> Optional[dict]:
    logger.info(f"Updating status of payment {payment_id} to {status}.")
    return await payment_repo.update_payment_status_repo(payment_id, status)


async def delete_payment_service(payment_id: int) -> bool:
    logger.info(f"Deleting payment record with ID: {payment_id}.")
    return await payment_repo.delete_payment_repo(payment_id)


async def list_payments_service() -> list[dict]:
    logger.info("Listing all payment records.")
    return await payment_repo.list_payments_repo()


async def get_payments_by_booking_id_service(booking_id: int) -> list[dict]:
    logger.info(f"Retrieving payments for booking ID: {booking_id}.")
    return await payment_repo.get_payments_by_booking_id_repo(booking_id)


async def record_payment_callback_service(payment_id: int, callback_payload: str) -> Optional[dict]:
    logger.info(f"Recording callback payload for payment ID: {payment_id}.")
    return await payment_repo.record_callback_payload_repo(payment_id, callback_payload)


async def get_payment_by_mpesa_ref_service(mpesa_ref: str) -> Optional[dict]:
    logger.info(f"Retrieving payment with M-Pesa reference: {mpesa_ref}.")
    return await payment_repo.get_payment_by_mpesa_ref_repo(mpesa_ref)


async def list_payments_by_status_service(status: str) -> list[dict]:
    logger.info(f"Listing payment records with status: {status}.")
    return await payment_repo.list_payments_by_status_repo(status)


async def count_payments_service() -> int:
    logger.info("Counting total number of payment records.")
    return await payment_repo.count_payments_repo()


async def get_total_by_booking_id_service(booking_id: int) -> float:
    logger.info(f"Calculating total payment amount for booking ID: {booking_id}.")
    return await payment_repo.get_total_amount_by_booking_id_repo(booking_id)


async def get_payments_created_after_service(date_time: datetime) -> list[dict]:
    logger.info(f"Retrieving payment records created after: {date_time}.")
    return await payment_repo.get_payments_created_after_repo(date_time)


async def get_payments_updated_after_service(date_time: datetime) -> list[dict]:
    logger.info(f"Retrieving payment records updated after: {date_time}.")
    return await payment_repo.get_payments_updated_after_repo(date_time)


async def get_latest_payments_service(limit: int = 10) -> list[dict]:
    logger.info(f"Retrieving the latest {limit} payment records.")
    return await payment_repo.get_latest_payments_repo(limit)

async def list_payments_enriched_service() -> list[dict]:
    """List all payments with user name via booking join.
    Used by GET /admin/payments — returns AdminPayment-shaped rows."""
    logger.info("Listing all payment records (enriched).")
    return await payment_repo.list_payments_enriched_repo()


# ── M-Pesa flow ───────────────────────────────────────────────────────────────

async def initiate_mpesa_payment_service(
    request: MpesaStkPushRequest,
) -> MpesaStkPushResponse:
    """
    Orchestrates the STK push flow:
      1. Validate the booking exists and is still pending.
      2. Call Daraja STK push.
      3. Create a Payment row (status=pending) with CheckoutRequestID.
      4. Return payment_id + checkout_request_id to the caller.
    """
    # 1. Validate booking
    booking = await booking_repo.get_booking_by_id_repo(request.booking_id)
    if not booking:
        raise ValueError(f"Booking {request.booking_id} not found")
    if booking.status not in ("pending", "confirmed"):
        raise ValueError(f"Booking {request.booking_id} has status '{booking.status}' — cannot pay")

    # 2. Normalise phone: strip leading 0 or + and ensure 2547XXXXXXXX format
    phone = request.phone_number.strip().lstrip("+")
    if phone.startswith("0"):
        phone = "254" + phone[1:]

    # 3. Initiate STK push
    logger.info(f"Initiating STK push for booking {request.booking_id} to {phone}")
    daraja_response = await initiate_stk_push(
        phone_number=phone,
        amount=booking.total_price,
        booking_id=request.booking_id,
    )

    if str(daraja_response.get("ResponseCode", "1")) != "0":
        raise RuntimeError(
            f"Daraja STK push failed: {daraja_response.get('ResponseDescription', 'Unknown error')}"
        )

    checkout_request_id = daraja_response["CheckoutRequestID"]

    # 4. Persist a pending payment row
    payment = await payment_repo.create_payment_repo(
        PaymentCreate(
            booking_id=request.booking_id,
            amount=booking.total_price,
            currency="KES",
            method="mpesa",
            mpesa_phone=phone,
            mpesa_checkout_request_id=checkout_request_id,
        )
    )

    logger.info(f"Created pending payment {payment.id} for booking {request.booking_id}")

    return MpesaStkPushResponse(
        payment_id=payment.id,
        checkout_request_id=checkout_request_id,
        message=f"STK push sent to {phone}. Enter your M-PESA PIN to complete payment.",
    )


async def handle_mpesa_callback_service(raw_body: dict) -> None:
    """
    Processes the Daraja callback:
      1. Parse the callback to extract result + mpesa_ref.
      2. Look up the Payment row by CheckoutRequestID.
      3. Update payment status (completed | failed) + store mpesa_ref.
      4. On success, confirm the Booking status → 'confirmed'.
      5. On success, decrement ticket quantity_sold (handled by booking confirm logic).
    """
    parsed = parse_mpesa_callback(raw_body)
    checkout_request_id = parsed["checkout_request_id"]
    logger.info(f"M-Pesa callback received: {parsed}")

    # Find the payment row
    payment = await payment_repo.get_payment_by_checkout_request_id_repo(checkout_request_id)
    if not payment:
        logger.error(f"No payment found for CheckoutRequestID: {checkout_request_id}")
        return

    # Store the full raw callback for auditing regardless of result
    await payment_repo.record_callback_payload_repo(payment.id, json.dumps(raw_body))

    if parsed["result_code"] == "0":
        # Success
        await payment_repo.update_payment_mpesa_success_repo(
            payment_id=payment.id,
            mpesa_ref=parsed["mpesa_ref"],
        )
        # Confirm the booking
        await booking_repo.update_booking_status_repo(payment.booking_id, "confirmed")
        logger.info(
            f"Payment {payment.id} completed (ref: {parsed['mpesa_ref']}). "
            f"Booking {payment.booking_id} confirmed."
        )
    else:
        # Failure
        await payment_repo.update_payment_status_repo(payment.id, "failed")
        logger.warning(
            f"Payment {payment.id} failed: {parsed['result_desc']}"
        )