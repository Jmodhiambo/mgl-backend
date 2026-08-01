#!/usr/bin/env python3
"""Order services for MGLTickets."""

from typing import Optional
from app.core.logging_config import logger
import app.db.repositories.order_repo as order_repo
from app.schemas.order import OrderCreate, OrderEnrichedOut, OrderOut


async def create_order_service(order_data: OrderCreate, user_id: int) -> OrderOut:
    """Create an order with one booking per ticket type line item.
    Raises ValueError on validation failure (ticket type not found, inactive,
    insufficient availability, or mismatched event_id) — the router converts
    this to a 400 response."""
    logger.info(f"Creating order for user {user_id}: {len(order_data.items)} item(s)")
    order = await order_repo.create_order_repo(order_data, user_id)
    logger.info(f"Created order {order.id} with {len(order.bookings)} booking(s), total KES {order.total_price}")
    return order


async def get_order_by_id_service(order_id: int) -> Optional[OrderOut]:
    """Get an order by ID."""
    logger.info(f"Retrieving order {order_id}")
    return await order_repo.get_order_by_id_repo(order_id)


async def list_orders_by_user_service(user_id: int) -> list[OrderOut]:
    """List orders for a specific user."""
    logger.info(f"Listing orders for user {user_id}")
    return await order_repo.list_orders_by_user_repo(user_id)


async def update_order_status_service(order_id: int, status: str) -> None:
    """Update the status of an order."""
    logger.info(f"Updating order {order_id} status to {status}")
    await order_repo.update_order_status_repo(order_id, status)


async def list_orders_enriched_admin_app_service() -> list[OrderEnrichedOut]:
    """List all orders with customer, event, payment, and line-item details.
    Used by GET /admin/orders."""
    logger.info("Listing all orders (enriched)")
    return await order_repo.list_orders_enriched_admin_app_repo()
 

async def list_orders_enriched_user_app_service(user_id: int) -> list[OrderEnrichedOut]:
    """List a single user's orders with event, payment, and line-item details.
    Used by GET /users/me/orders/enriched — the data source for the user
    Dashboard and My Tickets pages."""
    logger.info(f"Listing enriched orders for user {user_id}")
    return await order_repo.list_orders_enriched_user_app_repo(user_id)

 
async def delete_order_service(order_id: int) -> bool:
    """Admin-initiated order deletion — no ownership check, any order.
    Raises ValueError if the order is confirmed or has issued ticket
    instances (router converts this to a 400)."""
    logger.info(f"Deleting order {order_id}")
    return await order_repo.delete_order_repo(order_id)


async def delete_own_order_service(order_id: int, user_id: int) -> bool:
    """
    User-initiated deletion of their own order.

    Raises ValueError if:
      - the order doesn't belong to the requesting user (router returns 403)
      - the order is confirmed, or has issued ticket instances — enforced
        by order_repo.delete_order_repo (router returns 400 either way)

    Deliberately a thin wrapper: the ownership check lives here since the
    repo has no concept of "who's asking"; everything else delegates to
    the same delete_order_repo the admin path uses, so there's exactly one
    place that decides what's safe to delete.
    """
    order = await order_repo.get_order_by_id_repo(order_id)
    if not order:
        raise ValueError("Order not found")
    if order.user_id != user_id:
        raise ValueError("Not authorized to delete this order")

    if order.status == "confirmed":
        raise ValueError(
            f"Order {order_id} is confirmed and cannot be deleted. "
            f"Cancel it instead to preserve audit history."
        )

    logger.info(f"User {user_id} deleting their own order {order_id}")
    return await order_repo.delete_order_repo(order_id)