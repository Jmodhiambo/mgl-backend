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

import asyncio
import base64
import time
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


# ── Access token (cached) ──────────────────────────────────────────────────────
#
# Daraja OAuth tokens are valid for ~3600 seconds. Fetching a fresh one on every
# STK push/query call is wasteful and risks hitting Safaricom's rate limit
# during traffic bursts, so we cache it in-process and refresh a little early.
#
# NOTE: this cache is per-process. If you run multiple worker processes
# (e.g. multiple uvicorn/gunicorn workers), each will hold its own token —
# that's fine, Daraja doesn't mind multiple valid tokens for the same app.

_TOKEN_CACHE: dict = {"access_token": None, "expires_at": 0.0}
_TOKEN_REFRESH_MARGIN_SECONDS = 300  # refresh 5 min before actual expiry
_token_lock = asyncio.Lock()


async def get_mpesa_access_token() -> str:
    """
    Return a cached OAuth token from Daraja, refreshing it only when it's
    missing or close to expiry. Safe for concurrent callers — only one
    refresh request is made at a time even if several coroutines race in.
    """
    now = time.monotonic()

    if _TOKEN_CACHE["access_token"] and now < _TOKEN_CACHE["expires_at"]:
        return _TOKEN_CACHE["access_token"]

    async with _token_lock:
        # Re-check after acquiring the lock — another coroutine may have
        # already refreshed it while we were waiting.
        now = time.monotonic()
        if _TOKEN_CACHE["access_token"] and now < _TOKEN_CACHE["expires_at"]:
            return _TOKEN_CACHE["access_token"]

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
            data = response.json()

        access_token = data["access_token"]
        # Daraja returns expires_in as a string, typically "3599"
        expires_in = int(data.get("expires_in", 3600))

        _TOKEN_CACHE["access_token"] = access_token
        _TOKEN_CACHE["expires_at"] = now + expires_in - _TOKEN_REFRESH_MARGIN_SECONDS

        logger.info(f"Refreshed M-Pesa access token, expires in {expires_in}s")
        return access_token


# ── STK push ──────────────────────────────────────────────────────────────────

async def initiate_stk_push(
    phone_number: str,
    amount: int,
    order_id: int,
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
        "TransactionDesc": f"Order #{order_id}",
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
        logger.info(f"STK push response for order {order_id}: {data}")
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
        # Success — metadata items are in a list of {Name, Value} dicts
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