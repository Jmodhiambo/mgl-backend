#!/usr/bin/env python3
"""Async repository for Order model operations."""

from typing import Optional
from sqlalchemy import select, func
from app.db.session import get_async_session
from app.db.models.order import Order
from app.db.models.booking import Booking
from app.db.models.ticket_type import TicketType
from app.schemas.order import OrderCreate, OrderOut, OrderEnrichedOut, OrderBookingLineOut
from app.schemas.booking import BookingOut


async def create_order_repo(order_data: OrderCreate, user_id: int) -> OrderOut:
    """
    Create an Order and one Booking per line item, all in a single transaction.

    Validation performed here (raises ValueError on failure):
      - Every ticket_type_id must exist and belong to order_data.event_id
      - Every ticket_type must be active
      - quantity must not exceed quantity_available for that ticket type
      - quantity must not exceed that ticket type's max_per_booking cap

    NOTE: both the availability and max_per_booking checks are evaluated
    per line item, not aggregated across multiple line items referencing
    the same ticket_type_id within one order. In practice the frontend
    never sends duplicate ticket_type_id line items in a single order, so
    this hasn't been an issue — flagging it here rather than silently
    changing existing validation behavior.

    Pricing is computed entirely server-side from TicketType.price —
    the client never supplies a price. No processing fee is applied;
    total_price is simply the sum of (ticket_type.price * quantity)
    across all line items.
    """
    async with get_async_session() as session:
        line_items = []  # (ticket_type, quantity, line_total)
        subtotal = 0

        for item in order_data.items:
            ticket_type = await session.get(TicketType, item.ticket_type_id)
            if not ticket_type:
                raise ValueError(f"TicketType {item.ticket_type_id} not found")
            if ticket_type.event_id != order_data.event_id:
                raise ValueError(
                    f"TicketType {item.ticket_type_id} does not belong to event {order_data.event_id}"
                )
            if not ticket_type.is_active:
                raise ValueError(f"TicketType {item.ticket_type_id} is not active")

            available = ticket_type.total_quantity - ticket_type.quantity_sold
            if item.quantity > available:
                raise ValueError(
                    f"Only {available} ticket(s) available for '{ticket_type.name}', "
                    f"requested {item.quantity}"
                )

            if item.quantity > ticket_type.max_per_booking:
                raise ValueError(
                    f"'{ticket_type.name}' is limited to {ticket_type.max_per_booking} "
                    f"per booking, requested {item.quantity}"
                )

            line_total = ticket_type.price * item.quantity
            subtotal += line_total
            line_items.append((ticket_type, item.quantity, line_total))

        # Create the Order — total_price is the plain subtotal, no fee
        new_order = Order(
            user_id=user_id,
            event_id=order_data.event_id,
            total_price=subtotal,
            status="pending",
        )
        session.add(new_order)
        await session.flush()  # assigns new_order.id without committing yet

        # Create one Booking per line item
        new_bookings = []
        for ticket_type, quantity, line_total in line_items:
            booking = Booking(
                order_id=new_order.id,
                user_id=user_id,
                event_id=order_data.event_id,
                ticket_type_id=ticket_type.id,
                quantity=quantity,
                total_price=line_total,
                status="pending",
            )
            session.add(booking)
            new_bookings.append(booking)

        await session.commit()
        for b in new_bookings:
            await session.refresh(b)
        await session.refresh(new_order)

        return OrderOut(
            id=new_order.id,
            user_id=new_order.user_id,
            event_id=new_order.event_id,
            total_price=new_order.total_price,
            status=new_order.status,
            created_at=new_order.created_at,
            updated_at=new_order.updated_at,
            bookings=[BookingOut.model_validate(b) for b in new_bookings],
        )


async def get_order_by_id_repo(order_id: int) -> Optional[OrderOut]:
    """Retrieve an order with its bookings."""
    async with get_async_session() as session:
        order = await session.get(Order, order_id)
        if not order:
            return None
        result = await session.execute(
            select(Booking).where(Booking.order_id == order_id)
        )
        bookings = result.scalars().all()
        return OrderOut(
            id=order.id,
            user_id=order.user_id,
            event_id=order.event_id,
            total_price=order.total_price,
            status=order.status,
            created_at=order.created_at,
            updated_at=order.updated_at,
            bookings=[BookingOut.model_validate(b) for b in bookings],
        )


async def list_orders_by_user_repo(user_id: int) -> list[OrderOut]:
    """List all orders for a user, each with its bookings."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc())
        )
        orders = result.scalars().all()

        out = []
        for order in orders:
            b_result = await session.execute(
                select(Booking).where(Booking.order_id == order.id)
            )
            bookings = b_result.scalars().all()
            out.append(OrderOut(
                id=order.id,
                user_id=order.user_id,
                event_id=order.event_id,
                total_price=order.total_price,
                status=order.status,
                created_at=order.created_at,
                updated_at=order.updated_at,
                bookings=[BookingOut.model_validate(b) for b in bookings],
            ))
        return out


async def update_order_status_repo(order_id: int, status: str) -> None:
    """Update the Order status and cascade to all its Bookings."""
    async with get_async_session() as session:
        order = await session.get(Order, order_id)
        if not order:
            return
        order.status = status

        result = await session.execute(
            select(Booking).where(Booking.order_id == order_id)
        )
        for booking in result.scalars().all():
            booking.status = status

        await session.commit()


async def get_order_bookings_repo(order_id: int) -> list[BookingOut]:
    """Get all booking line items for an order — used by the payment callback
    to know which ticket types/quantities to issue instances for."""
    async with get_async_session() as session:
        result = await session.execute(
            select(Booking).where(Booking.order_id == order_id)
        )
        return [BookingOut.model_validate(b) for b in result.scalars().all()]
    

async def count_orders_by_event_id_repo(event_id: int) -> int:
    async with get_async_session() as session:
        result = await session.execute(
            select(func.count(Order.id)).where(Order.event_id == event_id)
        )
        return result.scalar()


async def list_orders_enriched_admin_app_repo() -> list[OrderEnrichedOut]:
    """List all orders with customer, event, payment, and line-item details.
    Used by GET /admin/orders."""
    from app.db.models.user import User
    from app.db.models.event import Event
    from app.db.models.payment import Payment
    from app.db.models.ticket_type import TicketType

    async with get_async_session() as session:
        result = await session.execute(
            select(Order, User.name, User.email, Event.title, Payment)
            .join(User, Order.user_id == User.id)
            .join(Event, Order.event_id == Event.id)
            .outerjoin(Payment, Payment.order_id == Order.id)
            .order_by(Order.created_at.desc())
        )
        rows = result.all()

        orders_out = []
        for order, customer_name, customer_email, event_title, payment in rows:
            b_result = await session.execute(
                select(Booking, TicketType.name)
                .join(TicketType, Booking.ticket_type_id == TicketType.id)
                .where(Booking.order_id == order.id)
            )
            bookings = [
                OrderBookingLineOut(
                    id=booking.id,
                    ticket_type_id=booking.ticket_type_id,
                    ticket_type_name=ticket_type_name,
                    quantity=booking.quantity,
                    total_price=booking.total_price,
                    status=booking.status,
                )
                for booking, ticket_type_name in b_result.all()
            ]

            orders_out.append(OrderEnrichedOut(
                id=order.id,
                user_id=order.user_id,
                customer_name=customer_name,
                customer_email=customer_email,
                event_id=order.event_id,
                event_title=event_title,
                total_price=order.total_price,
                status=order.status,
                created_at=order.created_at,
                updated_at=order.updated_at,
                payment_id=payment.id if payment else None,
                payment_method=payment.method if payment else None,
                payment_status=payment.status if payment else None,
                mpesa_ref=payment.mpesa_ref if payment else None,
                mpesa_phone=payment.mpesa_phone if payment else None,
                bookings=bookings,
            ))

        return orders_out


async def list_orders_enriched_user_app_repo(user_id: int) -> list[OrderEnrichedOut]:
    """List a single user's orders with event, payment, and line-item details.
    Scoped version of list_orders_enriched_repo() above — identical join
    shape and field mapping, with one added filter: Order.user_id == user_id.
    Used by GET /users/me/orders/enriched (Dashboard, My Tickets) so a user
    only ever sees their own orders, never the full platform list."""
    from app.db.models.user import User
    from app.db.models.event import Event
    from app.db.models.payment import Payment
    from app.db.models.ticket_type import TicketType

    async with get_async_session() as session:
        result = await session.execute(
            select(Order, User.name, User.email, Event.title, Payment)
            .join(User, Order.user_id == User.id)
            .join(Event, Order.event_id == Event.id)
            .outerjoin(Payment, Payment.order_id == Order.id)
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
        )
        rows = result.all()

        orders_out = []
        for order, customer_name, customer_email, event_title, payment in rows:
            b_result = await session.execute(
                select(Booking, TicketType.name)
                .join(TicketType, Booking.ticket_type_id == TicketType.id)
                .where(Booking.order_id == order.id)
            )
            bookings = [
                OrderBookingLineOut(
                    id=booking.id,
                    ticket_type_id=booking.ticket_type_id,
                    ticket_type_name=ticket_type_name,
                    quantity=booking.quantity,
                    total_price=booking.total_price,
                    status=booking.status,
                )
                for booking, ticket_type_name in b_result.all()
            ]

            orders_out.append(OrderEnrichedOut(
                id=order.id,
                user_id=order.user_id,
                customer_name=customer_name,
                customer_email=customer_email,
                event_id=order.event_id,
                event_title=event_title,
                total_price=order.total_price,
                status=order.status,
                created_at=order.created_at,
                updated_at=order.updated_at,
                payment_id=payment.id if payment else None,
                payment_method=payment.method if payment else None,
                payment_status=payment.status if payment else None,
                mpesa_ref=payment.mpesa_ref if payment else None,
                mpesa_phone=payment.mpesa_phone if payment else None,
                bookings=bookings,
            ))

        return orders_out


async def delete_order_repo(order_id: int) -> bool:
    """
    Delete an Order and its Bookings/Payment, cascading.

    Refuses to delete (returns False) if any Booking under this order has
    issued TicketInstances — i.e. the order was confirmed and tickets are
    already in customers' hands. In that case the order should be cancelled
    via status update instead, not deleted.
    """
    from app.db.models.payment import Payment
    from app.db.models.ticket_instance import TicketInstance

    async with get_async_session() as session:
        order = await session.get(Order, order_id)
        if not order:
            return False

        b_result = await session.execute(
            select(Booking).where(Booking.order_id == order_id)
        )
        bookings = b_result.scalars().all()

        for booking in bookings:
            ti_result = await session.execute(
                select(TicketInstance).where(TicketInstance.booking_id == booking.id)
            )
            if ti_result.scalars().first():
                raise ValueError(
                    f"Order {order_id} has issued ticket instances and cannot be "
                    f"deleted. Cancel the order instead to preserve audit history."
                )

        # No issued instances — safe to cascade delete
        p_result = await session.execute(
            select(Payment).where(Payment.order_id == order_id)
        )
        payment = p_result.scalars().first()
        if payment:
            await session.delete(payment)

        for booking in bookings:
            await session.delete(booking)

        await session.delete(order)
        await session.commit()
        return True