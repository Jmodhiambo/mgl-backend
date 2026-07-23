#!/usr/bin/env python3
"""Service layer for Payment operations."""

import asyncio
import json
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import HTTPException, status

from app.core.config import FRONTEND_URL
import app.db.repositories.payment_repo as payment_repo
import app.db.repositories.order_repo as order_repo
import app.db.repositories.ticket_type_repo as ticket_type_repo
import app.db.repositories.event_repo as event_repo
import app.db.repositories.user_repo as user_repo
from app.schemas.payment import (
    PaymentCreate,
    PaymentUpdate,
    MpesaStkPushRequest,
    MpesaStkPushResponse,
    PaymentStatusCheckResponse,
    ReconcileStuckPaymentsResponse,
    ReportManualPaymentRequest,
)
from app.services.mpesa_services import initiate_stk_push, parse_mpesa_callback, query_stk_push_status
from app.services.ticket_instance_services import create_ticket_instances_for_booking
from app.emails.email_manager import email_manager
from app.core.logging_config import logger


# ── Email links ───────────────────────────────────────────────────────────────

def _user_tickets_url() -> str:
    return f"{FRONTEND_URL}/my-tickets"

def _user_order_url(order_id: int) -> str:
    return f"{FRONTEND_URL}/orders/{order_id}"

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


# ── Email background helpers ────────────────────────────────────────────────

async def _safe_email(coro) -> None:
    """Await an email coroutine and log — rather than silently swallow —
    any failure. Without this, an exception raised inside a fire-and-forget
    asyncio.Task never surfaces anywhere except an easy-to-miss 'exception
    was never retrieved' warning from asyncio's default handler."""
    try:
        await coro
    except Exception as exc:
        logger.error(f"Background email task failed: {exc}")


def _bg_email(coro) -> None:
    """
    Schedule an email coroutine as a background task.
    Falls back to direct await if no running event loop exists (tests, CLI).
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_safe_email(coro))
    except RuntimeError:
        asyncio.run(_safe_email(coro))


def _format_eat(dt: datetime) -> str:
    """Render a datetime in Africa/Nairobi (EAT) for user-facing emails —
    matches the format used by user.check_in_confirmed. dt is assumed to be
    timezone-aware (UTC, per how it's stored on the Event model)."""
    return dt.astimezone(ZoneInfo("Africa/Nairobi")).strftime("%d %b %Y at %H:%M EAT")


async def _dispatch_order_confirmed_email(
    order_id: int,
    mpesa_ref: Optional[str],
    payment_method: str,
) -> None:
    """
    Look up everything user.order_confirmed needs and schedule it in the
    background.

    Called only from the non-idempotent branch of
    _confirm_paid_order_and_issue_tickets — so this fires exactly once per
    order regardless of which of the three confirmation paths (real
    callback, STK status query, manual admin approval) resolved it first.
    """
    try:
        order = await order_repo.get_order_by_id_repo(order_id)
        if not order:
            logger.warning(f"Could not send order_confirmed email — order {order_id} not found")
            return

        user = await user_repo.get_user_by_id_repo(order.user_id)
        if not user:
            logger.warning(f"Could not send order_confirmed email — user for order {order_id} not found")
            return

        event = await event_repo.get_event_by_id_repo(order.event_id)
        if not event:
            logger.warning(f"Could not send order_confirmed email — event for order {order_id} not found")
            return

        ticket_lines = []
        for booking in order.bookings:
            ticket_type = await ticket_type_repo.get_ticket_type_by_id_repo(booking.ticket_type_id)
            ticket_lines.append({
                "ticket_type": ticket_type.name if ticket_type else "Ticket",
                "quantity": booking.quantity,
            })

        _bg_email(email_manager.send_from_template(
            template_id="user.order_confirmed",
            to_email=user.email,
            variables={
                "name": user.name,
                "order_id": order.id,
                "event_title": event.title,
                "venue": event.venue,
                "event_date": _format_eat(event.start_time),
                "total_price": order.total_price,
                "payment_method": payment_method,
                "mpesa_ref": mpesa_ref,
                "ticket_lines": ticket_lines,
                "tickets_url": _user_tickets_url(),
            },
        ))
    except Exception as exc:
        logger.warning(f"Could not schedule order_confirmed email for order {order_id}: {exc}")


async def _dispatch_payment_failed_email(
    order_id: int,
    amount,
    failure_reason: Optional[str],
) -> None:
    """
    Look up everything user.payment_failed needs and schedule it in the
    background.

    Shared by both surfaces a payment can fail on: the real Daraja callback
    (handle_mpesa_callback_service) and the STK status query, which is used
    both on-demand (check_payment_status_service) and by the scheduled
    reconciliation sweep (reconcile_stuck_payments_service) — via
    _resolve_payment_via_query.
    """
    try:
        order = await order_repo.get_order_by_id_repo(order_id)
        if not order:
            logger.warning(f"Could not send payment_failed email — order {order_id} not found")
            return

        user = await user_repo.get_user_by_id_repo(order.user_id)
        if not user:
            logger.warning(f"Could not send payment_failed email — user for order {order_id} not found")
            return

        event = await event_repo.get_event_by_id_repo(order.event_id)
        if not event:
            logger.warning(f"Could not send payment_failed email — event for order {order_id} not found")
            return

        _bg_email(email_manager.send_from_template(
            template_id="user.payment_failed",
            to_email=user.email,
            variables={
                "name": user.name,
                "order_id": order.id,
                "event_title": event.title,
                "amount": amount,
                "failure_reason": failure_reason or "Payment was not completed.",
                "retry_url": _user_order_url(order_id),
            },
        ))
    except Exception as exc:
        logger.warning(f"Could not schedule payment_failed email for order {order_id}: {exc}")


# ── Shared confirmation helper ────────────────────────────────────────────────
#
# Three different paths can resolve a pending payment:
#   1. The real Daraja callback (handle_mpesa_callback_service)
#   2. An on-demand or scheduled STK status query (check_payment_status_service /
#      reconcile_stuck_payments_service) — Layer 1
#   3. An admin manually approving a reported or self-supplied M-Pesa code
#      (approve_manual_payment_service) — Layer 2
#
# All three must do the exact same thing — mark the payment completed,
# confirm the order, issue ticket instances, bump quantity_sold — so that
# logic lives in exactly one place. This function is also the idempotency
# gate: if the payment is already completed, it's a no-op.

async def _confirm_paid_order_and_issue_tickets(
    payment_id: int,
    order_id: int,
    mpesa_ref: Optional[str],
) -> dict:
    """Idempotent: safe to call more than once for the same payment_id."""
    payment = await payment_repo.get_payment_by_id_repo(payment_id)
    if not payment:
        logger.error(f"_confirm_paid_order_and_issue_tickets: payment {payment_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    if payment.status == "completed":
        logger.info(
            f"Payment {payment_id} already completed — skipping duplicate confirmation "
            f"(resolved by another path first)."
        )
        return {"already_completed": True, "payment": payment}

    if mpesa_ref:
        await payment_repo.update_payment_mpesa_success_repo(payment_id, mpesa_ref)
    else:
        await payment_repo.update_payment_status_repo(payment_id, "completed")

    await order_repo.update_order_status_repo(order_id, "confirmed")

    bookings = await order_repo.get_order_bookings_repo(order_id)
    total_instances = 0
    for booking in bookings:
        ticket_type = await ticket_type_repo.get_ticket_type_by_id_repo(booking.ticket_type_id)
        price_per_ticket = ticket_type.price if ticket_type else 0

        await create_ticket_instances_for_booking(
            booking_id=booking.id,
            user_id=booking.user_id,
            ticket_type_id=booking.ticket_type_id,
            quantity=booking.quantity,
            price_per_ticket=price_per_ticket,
            event_id=booking.event_id,
        )
        await ticket_type_repo.increment_quantity_sold_repo(booking.ticket_type_id, booking.quantity)
        total_instances += booking.quantity

    await _dispatch_order_confirmed_email(
        order_id=order_id,
        mpesa_ref=mpesa_ref,
        payment_method=payment.method,
    )

    logger.info(
        f"Payment {payment_id} confirmed (ref: {mpesa_ref}). "
        f"Order {order_id} confirmed with {len(bookings)} booking line(s). "
        f"{total_instances} ticket instance(s) issued."
    )
    return {"already_completed": False, "bookings": len(bookings), "instances": total_instances}


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
        await _confirm_paid_order_and_issue_tickets(
            payment_id=payment.id, order_id=request.order_id, mpesa_ref=None
        )

        return MpesaStkPushResponse(
            payment_id=payment.id,
            checkout_request_id=None,
            message="Free tickets confirmed. Check your email for your tickets.",
        )

    # ── Paid order — normal STK push flow ─────────────────────────────────────

    phone = request.phone_number.strip().lstrip("+")
    if phone.startswith("0"):
        phone = "254" + phone[1:]

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
      3. Record the raw callback payload for auditing.
      4. On success, delegate to the shared confirm helper (idempotent —
         a no-op if the STK status check, the reconciliation sweep, or an
         admin's manual approval already resolved this payment first).
      5. On failure, mark the payment failed and notify the user — guarded
         by the same idempotency check, so a late callback arriving after
         another path already completed the payment can't downgrade it.
    """
    parsed = parse_mpesa_callback(raw_body)
    checkout_request_id = parsed["checkout_request_id"]
    logger.info(f"M-Pesa callback received: {parsed}")

    payment = await payment_repo.get_payment_by_checkout_request_id_repo(checkout_request_id)
    if not payment:
        logger.error(f"No payment found for CheckoutRequestID: {checkout_request_id}")
        return

    await payment_repo.record_callback_payload_repo(payment.id, json.dumps(raw_body))

    if parsed["result_code"] == "0":
        await _confirm_paid_order_and_issue_tickets(
            payment_id=payment.id,
            order_id=payment.order_id,
            mpesa_ref=parsed["mpesa_ref"],
        )
    else:
        if payment.status != "completed":
            await payment_repo.update_payment_status_repo(payment.id, "failed")
            await _dispatch_payment_failed_email(
                order_id=payment.order_id,
                amount=payment.amount,
                failure_reason=parsed["result_desc"],
            )
        logger.warning(f"Payment {payment.id} failed: {parsed['result_desc']}")


# ── Layer 1: on-demand + scheduled STK query ──────────────────────────────────

async def check_payment_status_service(payment_id: int, user_id: int) -> PaymentStatusCheckResponse:
    """
    Called by the frontend when its own polling gives up waiting for the
    callback. Queries Daraja directly using the CheckoutRequestID we
    already stored — no user input, no fraud surface.
    """
    payment = await payment_repo.get_payment_by_id_repo(payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    order = await order_repo.get_order_by_id_repo(payment.order_id)
    if not order or order.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    return await _resolve_payment_via_query(payment, order)


async def _resolve_payment_via_query(payment, order) -> PaymentStatusCheckResponse:
    """Shared by check_payment_status_service (on-demand, ownership-checked)
    and reconcile_stuck_payments_service (scheduled/admin-triggered sweep)."""

    if payment.status == "completed":
        return PaymentStatusCheckResponse(
            payment_id=payment.id,
            resolved=True,
            status="completed",
            order_status="confirmed",
            message="Payment already confirmed.",
        )

    if payment.status == "failed":
        return PaymentStatusCheckResponse(
            payment_id=payment.id,
            resolved=True,
            status="failed",
            order_status=order.status if order else None,
            message="This payment failed or was cancelled.",
        )

    if not payment.mpesa_checkout_request_id:
        return PaymentStatusCheckResponse(
            payment_id=payment.id,
            resolved=False,
            status=payment.status,
            order_status=order.status if order else None,
            message="No M-Pesa reference to check yet.",
        )

    query_result = await query_stk_push_status(payment.mpesa_checkout_request_id)

    if query_result["status"] == "completed":
        # The query response doesn't include MpesaReceiptNumber — only the
        # real callback does. Confirm with mpesa_ref=None here; if the
        # callback arrives later it's a no-op (already "completed").
        await _confirm_paid_order_and_issue_tickets(
            payment_id=payment.id, order_id=payment.order_id, mpesa_ref=None
        )
        return PaymentStatusCheckResponse(
            payment_id=payment.id,
            resolved=True,
            status="completed",
            order_status="confirmed",
            message="Payment confirmed via M-Pesa status check.",
        )

    if query_result["status"] == "failed":
        await payment_repo.update_payment_status_repo(payment.id, "failed")
        await _dispatch_payment_failed_email(
            order_id=payment.order_id,
            amount=payment.amount,
            failure_reason=query_result["result_desc"],
        )
        return PaymentStatusCheckResponse(
            payment_id=payment.id,
            resolved=True,
            status="failed",
            order_status=order.status if order else None,
            message=query_result["result_desc"],
        )

    return PaymentStatusCheckResponse(
        payment_id=payment.id,
        resolved=False,
        status="pending",
        order_status=order.status if order else None,
        message=query_result["result_desc"] or "Still waiting for M-Pesa confirmation.",
    )


async def reconcile_stuck_payments_service(
    older_than_minutes: int = 5,
) -> ReconcileStuckPaymentsResponse:
    """
    Sweeps Payments stuck in 'pending' for longer than `older_than_minutes`
    and queries Daraja for each one via CheckoutRequestID.

    No scheduler is wired up in this codebase yet, so this is exposed as
    POST /admin/payments/reconcile-stuck. Point a cron job or APScheduler
    task at it (e.g. every 2-5 minutes) once you set one up.
    """
    stuck = await payment_repo.list_stuck_pending_mpesa_payments_repo(older_than_minutes)
    logger.info(f"Reconciliation sweep: {len(stuck)} payment(s) stuck pending > {older_than_minutes}m")

    resolved_completed = 0
    resolved_failed = 0
    still_pending = 0

    for payment in stuck:
        order = await order_repo.get_order_by_id_repo(payment.order_id)
        result = await _resolve_payment_via_query(payment, order)
        if result.status == "completed":
            resolved_completed += 1
        elif result.status == "failed":
            resolved_failed += 1
        else:
            still_pending += 1

    logger.info(
        f"Reconciliation sweep complete: {resolved_completed} completed, "
        f"{resolved_failed} failed, {still_pending} still pending."
    )

    return ReconcileStuckPaymentsResponse(
        checked=len(stuck),
        resolved_completed=resolved_completed,
        resolved_failed=resolved_failed,
        still_pending=still_pending,
    )


# ── Layer 2: manual review fallback ────────────────────────────────────────────

async def report_manual_payment_service(
    user_id: int, request: ReportManualPaymentRequest
) -> dict:
    """
    User reports "I paid but my order is still stuck" with the M-Pesa code
    from their SMS. This NEVER auto-confirms — it only queues the payment
    for admin review. The admin must independently verify the code against
    the actual M-Pesa statement before approving.
    """
    payment = await payment_repo.get_payment_by_id_repo(request.payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    order = await order_repo.get_order_by_id_repo(payment.order_id)
    if not order or order.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    if payment.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This payment is already confirmed.",
        )

    if payment.manual_review_status == "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You've already reported this payment. An admin will review it shortly.",
        )

    updated = await payment_repo.submit_manual_review_repo(
        payment_id=request.payment_id,
        mpesa_code=request.mpesa_code.strip().upper(),
        phone_number=request.phone_number,
    )
    logger.info(
        f"User {user_id} reported manual payment for payment {request.payment_id} "
        f"(code={request.mpesa_code!r})"
    )
    return updated


async def list_manual_review_payments_service() -> list[dict]:
    """Payments with a user-submitted report awaiting a manual decision.
    Note: this does NOT include payments an admin might resolve proactively
    without a user report — those are surfaced via the Orders page itself
    (any pending mpesa order can be resolved, reported or not)."""
    logger.info("Listing payments pending manual review")
    return await payment_repo.list_pending_manual_reviews_repo()


async def approve_manual_payment_service(
    payment_id: int,
    mpesa_code: Optional[str] = None,
    admin_notes: Optional[str] = None,
) -> dict:
    """
    Admin confirms a payment by M-Pesa code. Works in both directions:
      - A user already reported a code (payment.manual_review_status == 'pending')
        and the admin is approving it — mpesa_code can be omitted, the
        previously reported one is used.
      - Nobody reported anything, but the admin spotted the payment on the
        M-Pesa till statement themselves and wants to resolve it directly —
        mpesa_code is required in this case.

    Either way, the admin is asserting they've independently verified the
    code against the actual statement. Confirms the order and issues
    tickets via the same shared helper the callback uses (which also
    dispatches the order_confirmed email).
    """
    payment = await payment_repo.get_payment_by_id_repo(payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    if payment.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This payment is already confirmed.",
        )

    code_to_use = (mpesa_code or payment.user_reported_mpesa_code or "").strip().upper()
    if not code_to_use:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An M-Pesa code is required to approve this payment.",
        )

    await payment_repo.resolve_manual_review_repo(
        payment_id, approved=True, mpesa_code=code_to_use
    )
    result = await _confirm_paid_order_and_issue_tickets(
        payment_id=payment_id,
        order_id=payment.order_id,
        mpesa_ref=code_to_use,
    )
    logger.info(f"Admin approved payment {payment_id} by M-Pesa code {code_to_use!r}")
    return result


async def reject_manual_payment_service(
    payment_id: int, admin_notes: Optional[str] = None
) -> dict:
    """Admin could not verify a user-reported code — leaves the payment
    exactly where it was (pending/failed) so the user can be told to try
    again. Only meaningful when there's an actual report to dismiss."""
    payment = await payment_repo.get_payment_by_id_repo(payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")

    if payment.manual_review_status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This payment has no pending manual review request to reject.",
        )

    updated = await payment_repo.resolve_manual_review_repo(payment_id, approved=False)
    logger.info(f"Admin rejected manual payment review for payment {payment_id}")
    return updated