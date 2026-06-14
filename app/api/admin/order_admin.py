#!/usr/bin/env python3
"""Admin order routes.

This router replaces the old admin Bookings and Payments pages.
Each Order represents one checkout — one or more Booking line items
(one per ticket type) plus the single Payment that paid for all of them.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from app.schemas.order import OrderEnrichedOut
import app.services.order_services as order_services
from app.core.security import require_admin
from app.services.audit_log_services import log_admin_action_service

router = APIRouter()


@router.get("/admin/orders", response_model=list[OrderEnrichedOut])
async def list_orders(user=Depends(require_admin)):
    """List all orders with customer, event, payment, and ticket-type
    line-item details — the data source for the admin Orders page."""
    return await order_services.list_orders_enriched_service()


@router.delete("/admin/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: int, background_tasks: BackgroundTasks, user=Depends(require_admin)
):
    """
    Delete an order.

    Refuses (400) if the order has issued ticket instances — i.e. it was
    confirmed and customers already hold tickets. Cancel the order via a
    status update instead in that case.
    """
    try:
        deleted = await order_services.delete_order_service(order_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not deleted:
        raise HTTPException(status_code=404, detail="Order not found")

    background_tasks.add_task(
        log_admin_action_service,
        admin_id=user.id,
        admin_name=user.name,
        action="delete_order",
        target_type="order",
        target_id=order_id,
        details={"deleted_order_id": order_id},
    )