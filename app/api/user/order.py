#!/usr/bin/env python3
"""User-facing order routes for MGLTickets."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.order import OrderCreate, OrderOut, OrderEnrichedOut
from app.core.security import require_user
import app.services.order_services as order_services

router = APIRouter()


@router.post("/users/me/orders", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderCreate, user=Depends(require_user)):
    """
    Create a new order — one or more ticket types for a single event.

    Pricing is computed entirely server-side from current TicketType prices.
    Returns the created Order with its line-item Bookings, ready to be
    paid via POST /payments/mpesa/stk-push using the returned order id.
    """
    try:
        return await order_services.create_order_service(order, user_id=user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Fixed paths BEFORE /{order_id} ────────────────────────────────────────────

@router.get("/users/me/orders/enriched", response_model=list[OrderEnrichedOut])
async def list_my_orders_enriched(user=Depends(require_user)):
    """
    List the current user's orders, enriched with event title, payment
    status/method, M-Pesa reference, and per-ticket-type booking line items.

    This is the single source of truth for the user Dashboard, My Tickets,
    and full Orders list pages — it replaces the old pattern of separately
    fetching plain bookings + ticket instances and joining them client-side
    by event title, which silently broke for pending orders that had no
    issued ticket instances yet (and therefore no event_title to join on).

    Mirrors GET /admin/orders (list_orders_enriched_service) but scoped to
    the authenticated user.
    """
    return await order_services.list_orders_enriched_user_app_service(user.id)


@router.get("/users/me/orders", response_model=list[OrderOut])
async def list_orders(user=Depends(require_user)):
    """List all orders for the current user (plain shape, no joins)."""
    return await order_services.list_orders_by_user_service(user.id)


@router.get("/users/me/orders/{order_id}", response_model=OrderOut)
async def get_order(order_id: int, user=Depends(require_user)):
    """Get a specific order by ID, including its line-item bookings."""
    order = await order_services.get_order_by_id_service(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this order")
    return order


@router.delete("/users/me/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_order(order_id: int, user=Depends(require_user)):
    """
    Delete one of the current user's own orders — from OrderDetail.tsx's
    "Delete Order" action.

    Refused (400) if the order is confirmed, or has issued ticket
    instances — cancel instead of delete in that case; this is enforced
    in order_repo.delete_order_repo regardless of what the frontend shows,
    so hiding the button for confirmed orders is a UX nicety, not the only
    line of defense. Refused (403) if the order doesn't belong to the
    requesting user.
    """
    try:
        deleted = await order_services.delete_own_order_service(order_id, user.id)
    except ValueError as e:
        message = str(e)
        if message == "Not authorized to delete this order":
            raise HTTPException(status_code=403, detail=message)
        if message == "Order not found":
            raise HTTPException(status_code=404, detail=message)
        raise HTTPException(status_code=400, detail=message)

    if not deleted:
        raise HTTPException(status_code=404, detail="Order not found")