#!/usr/bin/env python3
"""Service layer for Payment operations."""

import json
from typing import Optional
from datetime import datetime
import app.db.repositories.payment_repo as payment_repo
import app.db.repositories.order_repo as order_repo
import app.db.repositories.ticket_type_repo as ticket_type_repo
from app.schemas.payment import PaymentCreate, PaymentUpdate, MpesaStkPushRequest, MpesaStkPushResponse
from app.services.mpesa_services import initiate_stk_push, parse_mpesa_callback
from app.services.ticket_instance_services import create_ticket_instances_for_booking
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


async def get_payments_by_order_id_service(order_id: int) -> list[dict]:
    logger.info(f"Retrieving payments for order ID: {order_id}.")
    return await payment_repo.get_payments_by_order_id_repo(order_id)


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


async def get_total_by_order_id_service(order_id: int) -> float:
    logger.info(f"Calculating total payment amount for order ID: {order_id}.")
    return await payment_repo.get_total_amount_by_order_id_repo(order_id)


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
    """List all payments with user name via order join.
    Used by GET /admin/payments — returns AdminPayment-shaped rows."""
    logger.info("Listing all payment records (enriched).")
    return await payment_repo.list_payments_enriched_repo()

# ── M-Pesa flow ───────────────────────────────────────────────────────────────

async def initiate_mpesa_payment_service(
    request: MpesaStkPushRequest,
) -> MpesaStkPushResponse:
    """
    Orchestrates the payment flow for an order.

    For FREE orders (total_price == 0):
      - No STK push is initiated (Daraja rejects zero-amount requests).
      - A Payment row is created immediately with status='completed'.
      - The order and all its bookings are confirmed right away.
      - Ticket instances are issued just as they would be after a paid callback.
      - Returns a response flagged as free (payment_id set, checkout_request_id=None).

    For PAID orders:
      1. Validate the order exists and is still pending.
      2. Normalise phone number to 2547XXXXXXXX format.
      3. Call Daraja STK push for the order's total_price.
      4. Create a Payment row (status=pending) with CheckoutRequestID.
      5. Return payment_id + checkout_request_id to the caller for polling.
    """
    # 1. Validate order
    order = await order_repo.get_order_by_id_repo(request.order_id)
    if not order:
        raise ValueError(f"Order {request.order_id} not found")
    if order.status not in ("pending", "confirmed"):
        raise ValueError(f"Order {request.order_id} has status '{order.status}' — cannot pay")

    # ── Free order fast-path ───────────────────────────────────────────────────
    if order.total_price == 0:
        logger.info(f"Order {request.order_id} is free — bypassing STK push")

        # Create a completed payment record for audit purposes
        payment = await payment_repo.create_payment_repo(
            PaymentCreate(
                order_id=request.order_id,
                amount=0,
                currency="KES",
                method="free",
                mpesa_phone=None,
                mpesa_checkout_request_id=None,
            )
        )
        await payment_repo.update_payment_status_repo(payment.id, "completed")

        # Confirm order + all bookings immediately
        await order_repo.update_order_status_repo(request.order_id, "confirmed")

        # Issue ticket instances for every booking line item
        bookings = await order_repo.get_order_bookings_repo(request.order_id)
        for booking in bookings:
            ticket_type = await ticket_type_repo.get_ticket_type_by_id_repo(
                booking.ticket_type_id
            )
            await create_ticket_instances_for_booking(
                booking_id=booking.id,
                user_id=booking.user_id,
                ticket_type_id=booking.ticket_type_id,
                quantity=booking.quantity,
                price_per_ticket=0,
            )
            await ticket_type_repo.increment_quantity_sold_repo(
                booking.ticket_type_id, booking.quantity
            )

        logger.info(
            f"Free order {request.order_id} confirmed — "
            f"{len(bookings)} booking line(s), ticket instances issued."
        )

        return MpesaStkPushResponse(
            payment_id=payment.id,
            checkout_request_id=None,   # signals to frontend: no PIN needed
            message="Free tickets confirmed. Check your email for your tickets.",
        )

    # ── Paid order — normal STK push flow ─────────────────────────────────────

    # 2. Normalise phone: strip leading 0 or + and ensure 2547XXXXXXXX format
    phone = request.phone_number.strip().lstrip("+")
    if phone.startswith("0"):
        phone = "254" + phone[1:]

    # 3. Initiate STK push for the order's total (sum of all line items)
    logger.info(f"Initiating STK push for order {request.order_id} to {phone}")
    daraja_response = await initiate_stk_push(
        phone_number=phone,
        amount=order.total_price,
        order_id=request.order_id,
    )

    if str(daraja_response.get("ResponseCode", "1")) != "0":
        raise RuntimeError(
            f"Daraja STK push failed: {daraja_response.get('ResponseDescription', 'Unknown error')}"
        )

    checkout_request_id = daraja_response["CheckoutRequestID"]

    # 4. Persist a pending payment row, linked to the order
    payment = await payment_repo.create_payment_repo(
        PaymentCreate(
            order_id=request.order_id,
            amount=order.total_price,
            currency="KES",
            method="mpesa",
            mpesa_phone=phone,
            mpesa_checkout_request_id=checkout_request_id,
        )
    )

    logger.info(f"Created pending payment {payment.id} for order {request.order_id}")

    return MpesaStkPushResponse(
        payment_id=payment.id,
        checkout_request_id=checkout_request_id,
        message=f"STK push sent to {phone}. Enter your M-PESA PIN to complete payment.",
    )


async def handle_mpesa_callback_service(raw_body: dict) -> None:
    """
    Processes the Daraja callback:
      1. Parse the callback to extract result + mpesa_ref.
      2. Look up the Payment row by CheckoutRequestID → get its order_id.
      3. Update payment status (completed | failed) + store mpesa_ref.
      4. On success:
         - confirm the Order and ALL of its Bookings (one per ticket type)
         - for EACH booking, look up its ticket type's price and create
           `quantity` TicketInstances, then increment quantity_sold
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
        # Success — update payment, confirm order + all its bookings, issue tickets
        await payment_repo.update_payment_mpesa_success_repo(
            payment_id=payment.id,
            mpesa_ref=parsed["mpesa_ref"],
        )

        # Confirm the order — cascades status="confirmed" to every booking under it
        await order_repo.update_order_status_repo(payment.order_id, "confirmed")

        # Fetch all booking line items (one per ticket type) under this order
        bookings = await order_repo.get_order_bookings_repo(payment.order_id)

        total_instances = 0
        for booking in bookings:
            # Look up this line item's ticket type to get the correct price —
            # never trust a client-supplied price. One DB read per line item,
            # in a background callback with no user waiting.
            ticket_type = await ticket_type_repo.get_ticket_type_by_id_repo(
                booking.ticket_type_id
            )
            price_per_ticket = ticket_type.price if ticket_type else 0

            await create_ticket_instances_for_booking(
                booking_id=booking.id,
                user_id=booking.user_id,
                ticket_type_id=booking.ticket_type_id,
                quantity=booking.quantity,
                price_per_ticket=price_per_ticket,
            )

            await ticket_type_repo.increment_quantity_sold_repo(
                booking.ticket_type_id, booking.quantity
            )

            total_instances += booking.quantity

        logger.info(
            f"Payment {payment.id} completed (ref: {parsed['mpesa_ref']}). "
            f"Order {payment.order_id} confirmed with {len(bookings)} booking line(s). "
            f"{total_instances} ticket instance(s) issued in total."
        )
    else:
        # Failure
        await payment_repo.update_payment_status_repo(payment.id, "failed")
        logger.warning(
            f"Payment {payment.id} failed: {parsed['result_desc']}"
        )