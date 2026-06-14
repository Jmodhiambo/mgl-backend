#!/usr/bin/env python3
"""User-facing order routes for MGLTickets."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.order import OrderCreate, OrderOut
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


@router.get("/users/me/orders", response_model=list[OrderOut])
async def list_orders(user=Depends(require_user)):
    """List all orders for the current user."""
    return await order_services.list_orders_by_user_service(user.id)


@router.get("/users/me/orders/{order_id}", response_model=OrderOut)
async def get_order(order_id: int, user=Depends(require_user)):
    """Get a specific order by ID, including its line-item bookings."""
    order = await order_services.get_order_by_id_service(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order