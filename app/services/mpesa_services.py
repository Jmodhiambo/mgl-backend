#!/usr/bin/env python3
"""
M-Pesa Daraja API integration for MGLTickets.

Flow:
  1. Frontend POSTs booking_id + phone → POST /payments/mpesa/stk-push
  2. We call Daraja STK Push → get CheckoutRequestID back
  3. We create a Payment row (status=pending) storing CheckoutRequestID
  4. We return payment_id + checkout_request_id to frontend
  5. Daraja POSTs result to POST /payments/mpesa/callback (no auth)
  6. Callback updates Payment status + mpesa_ref, then confirms Booking
"""

import base64
import httpx
from datetime import datetime, timezone

from app.core.config import (
    MPESA_CONSUMER_KEY,
    MPESA_CONSUMER_SECRET,
    MPESA_SHORTCODE,
    MPESA_PASSKEY,
    MPESA_CALLBACK_URL,
    MPESA_ENV,
)
from app.core.logging_config import logger


# ── Daraja base URL ───────────────────────────────────────────────────────────

def _base_url() -> str:
    if MPESA_ENV == "production":
        return "https://api.safaricom.co.ke"
    return "https://sandbox.safaricom.co.ke"


# ── Access token ──────────────────────────────────────────────────────────────

async def get_mpesa_access_token() -> str:
    """
    Fetch a short-lived OAuth token from Daraja.
    In production, cache this for ~55 minutes to avoid rate limits.
    """
    credentials = base64.b64encode(
        f"{MPESA_CONSUMER_KEY}:{MPESA_CONSUMER_SECRET}".encode()
    ).decode()

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_base_url()}/oauth/v1/generate?grant_type=client_credentials",
            headers={"Authorization": f"Basic {credentials}"},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["access_token"]


# ── STK push ──────────────────────────────────────────────────────────────────

async def initiate_stk_push(
    phone_number: str,
    amount: int,
    booking_id: int,
    account_reference: str = "MGLTickets",
) -> dict:
    """
    Trigger an STK push to the user's phone.

    Returns the full Daraja response dict, which includes:
      - CheckoutRequestID  (store this in payment row for callback matching)
      - ResponseCode       ("0" = success)
      - CustomerMessage

    phone_number must be in format 2547XXXXXXXX (no +, no leading 0).
    """
    token = await get_mpesa_access_token()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(
        f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}".encode()
    ).decode()

    payload = {
        "BusinessShortCode": MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": MPESA_CALLBACK_URL,
        "AccountReference": account_reference,
        "TransactionDesc": f"Booking #{booking_id}",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_base_url()}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        logger.info(f"STK push response for booking {booking_id}: {data}")
        return data


# ── Callback parsing ──────────────────────────────────────────────────────────

def parse_mpesa_callback(body: dict) -> dict:
    """
    Extract the key fields from a Daraja STK callback body.

    Returns a dict with:
      checkout_request_id  — matches what we stored at STK push time
      result_code          — "0" = success, anything else = failure
      result_desc
      mpesa_ref            — MpesaReceiptNumber (only present on success)
      amount               — (only present on success)
      phone                — (only present on success)
    """
    stk_callback = body.get("Body", {}).get("stkCallback", {})
    result_code = str(stk_callback.get("ResultCode", "1"))
    result_desc = stk_callback.get("ResultDesc", "Unknown")
    checkout_request_id = stk_callback.get("CheckoutRequestID", "")

    mpesa_ref = None
    amount = None
    phone = None

    if result_code == "0":
        items = stk_callback.get("CallbackMetadata", {}).get("Item", [])
        meta = {item["Name"]: item.get("Value") for item in items}
        mpesa_ref = meta.get("MpesaReceiptNumber")
        amount = meta.get("Amount")
        phone = str(meta.get("PhoneNumber", ""))

    return {
        "checkout_request_id": checkout_request_id,
        "result_code": result_code,
        "result_desc": result_desc,
        "mpesa_ref": mpesa_ref,
        "amount": amount,
        "phone": phone,
    }