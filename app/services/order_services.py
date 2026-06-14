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
    logger.info(f"Retrieving order {order_id}")
    return await order_repo.get_order_by_id_repo(order_id)


async def list_orders_by_user_service(user_id: int) -> list[OrderOut]:
    logger.info(f"Listing orders for user {user_id}")
    return await order_repo.list_orders_by_user_repo(user_id)


async def update_order_status_service(order_id: int, status: str) -> None:
    logger.info(f"Updating order {order_id} status to {status}")
    await order_repo.update_order_status_repo(order_id, status)


async def list_orders_enriched_service() -> list[OrderEnrichedOut]:
    """List all orders with customer, event, payment, and line-item details.
    Used by GET /admin/orders."""
    logger.info("Listing all orders (enriched)")
    return await order_repo.list_orders_enriched_repo()
 
 
async def delete_order_service(order_id: int) -> bool:
    """Delete an order. Raises ValueError if the order has issued ticket
    instances (router converts this to a 400)."""
    logger.info(f"Deleting order {order_id}")
    return await order_repo.delete_order_repo(order_id)