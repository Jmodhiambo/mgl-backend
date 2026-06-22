#!/usr/bin/env python3
"""
Repository layer for organizer-scoped analytics.

All queries are read-only aggregations scoped to a single organizer_id.
Modelled on admin_analytics_repo.py — same patterns, narrower scope.

Place at: app/db/repositories/organizer_repo.py
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from sqlalchemy import func, select, and_

from app.db.models.booking import Booking
from app.db.models.event import Event
from app.db.models.order import Order
from app.db.models.payment import Payment
from app.db.models.ticket_type import TicketType
from app.db.models.user import User
from app.db.session import get_async_session
from app.schemas.organizer import DashboardStats, OrganizerOrderOut, OrganizerOrderBookingLine


# ─── Dashboard Stats ──────────────────────────────────────────────────────────

async def get_organizer_dashboard_stats_repo(organizer_id: int) -> DashboardStats:
    """
    Single-session aggregation for the organizer dashboard KPI cards.

    Revenue figures are based on CONFIRMED bookings only.
    monthly_growth = % change in events created this month vs last month
                     (0.0 when last month had zero events to avoid div/zero).
    platform_cut / organizer_net are computed from each event's own
    commission_rate so negotiated rates are honoured correctly.
    """
    async with get_async_session() as session:
        now = datetime.now(timezone.utc)

        # ── Month boundaries ───────────────────────────────────────────────
        first_of_current = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        last_of_previous  = first_of_current - timedelta(days=1)
        first_of_previous = datetime(
            last_of_previous.year, last_of_previous.month, 1, tzinfo=timezone.utc
        )

        # ── Event counts ───────────────────────────────────────────────────
        total_events = await session.scalar(
            select(func.count()).select_from(Event)
            .where(Event.organizer_id == organizer_id)
            .where(Event.status != "deleted")
        ) or 0

        active_events = await session.scalar(
            select(func.count()).select_from(Event)
            .where(Event.organizer_id == organizer_id)
            .where(Event.start_time <= now)
            .where(Event.end_time   >= now)
            .where(Event.status != "deleted")
        ) or 0

        upcoming_events = await session.scalar(
            select(func.count()).select_from(Event)
            .where(Event.organizer_id == organizer_id)
            .where(Event.status == "upcoming")
        ) or 0

        completed_events = await session.scalar(
            select(func.count()).select_from(Event)
            .where(Event.organizer_id == organizer_id)
            .where(Event.status == "completed")
        ) or 0

        events_this_month = await session.scalar(
            select(func.count()).select_from(Event)
            .where(Event.organizer_id == organizer_id)
            .where(Event.created_at  >= first_of_current)
            .where(Event.status != "deleted")
        ) or 0

        events_last_month = await session.scalar(
            select(func.count()).select_from(Event)
            .where(Event.organizer_id == organizer_id)
            .where(Event.created_at  >= first_of_previous)
            .where(Event.created_at  <  first_of_current)
            .where(Event.status != "deleted")
        ) or 0

        if events_last_month > 0:
            monthly_growth = round(
                (events_this_month - events_last_month) / events_last_month * 100, 1
            )
        elif events_this_month > 0:
            monthly_growth = 100.0
        else:
            monthly_growth = 0.0

        # ── Booking / ticket counts ────────────────────────────────────────
        # Join through Event so we only count bookings on THIS organizer's events
        total_bookings = await session.scalar(
            select(func.count(Booking.id))
            .join(Event, Booking.event_id == Event.id)
            .where(Event.organizer_id == organizer_id)
            .where(Booking.status == "confirmed")
        ) or 0

        tickets_sold = await session.scalar(
            select(func.coalesce(func.sum(Booking.quantity), 0))
            .join(Event, Booking.event_id == Event.id)
            .where(Event.organizer_id == organizer_id)
            .where(Booking.status == "confirmed")
        ) or 0

        # ── Revenue split ──────────────────────────────────────────────────
        # We compute SUM(booking.total_price) and
        # SUM(booking.total_price * event.commission_rate / 100) in one query
        # so negotiated rates per event are correctly applied.
        revenue_row = (await session.execute(
            select(
                func.coalesce(func.sum(Booking.total_price), 0).label("gross"),
                func.coalesce(
                    func.sum(
                        Booking.total_price * Event.commission_rate / 100
                    ), 0
                ).label("platform_cut"),
            )
            .join(Event, Booking.event_id == Event.id)
            .where(Event.organizer_id == organizer_id)
            .where(Booking.status == "confirmed")
        )).one()

        gross        = float(revenue_row.gross)
        platform_cut = float(revenue_row.platform_cut)
        organizer_net = gross - platform_cut

        return DashboardStats(
            total_events=total_events,
            active_events=active_events,
            upcoming_events=upcoming_events,
            completed_events=completed_events,
            monthly_growth=monthly_growth,
            total_bookings=total_bookings,
            tickets_sold=int(tickets_sold),
            total_revenue=gross,
            platform_cut=round(platform_cut, 2),
            organizer_net=round(organizer_net, 2),
        )


# ─── Orders (organizer-scoped) ────────────────────────────────────────────────

async def list_orders_by_organizer_repo(organizer_id: int) -> list[OrganizerOrderOut]:
    """
    All orders (with nested booking line items) for events owned by
    organizer_id, newest first.

    Used by GET /organizers/me/orders (BookingsView — Orders tab).
    """
    async with get_async_session() as session:
        # Pull Orders joined to Event (ownership check) + User (customer) + Payment
        from app.db.models.payment import Payment  # local to avoid circular at module level

        rows = (await session.execute(
            select(Order, User, Event, Payment)
            .join(Event, Order.event_id == Event.id)
            .join(User,  Order.user_id  == User.id)
            .outerjoin(Payment, Payment.order_id == Order.id)
            .where(Event.organizer_id == organizer_id)
            .order_by(Order.created_at.desc())
        )).all()

        if not rows:
            return []

        # Collect order IDs so we can batch-fetch bookings
        order_ids = [row.Order.id for row in rows]

        booking_rows = (await session.execute(
            select(Booking, TicketType.name.label("tt_name"))
            .join(TicketType, Booking.ticket_type_id == TicketType.id)
            .where(Booking.order_id.in_(order_ids))
            .order_by(Booking.order_id, Booking.id)
        )).all()

        # Group bookings by order_id
        from collections import defaultdict
        bookings_by_order: dict[int, list[OrganizerOrderBookingLine]] = defaultdict(list)
        for b_row in booking_rows:
            bookings_by_order[b_row.Booking.order_id].append(
                OrganizerOrderBookingLine(
                    id=b_row.Booking.id,
                    ticket_type_id=b_row.Booking.ticket_type_id,
                    ticket_type_name=b_row.tt_name,
                    quantity=b_row.Booking.quantity,
                    total_price=b_row.Booking.total_price,
                    status=b_row.Booking.status,
                )
            )

        result: list[OrganizerOrderOut] = []
        for row in rows:
            order   = row.Order
            user    = row.User
            event   = row.Event
            payment = row.Payment  # may be None

            commission_rate = float(event.commission_rate)
            platform_cut    = round(order.total_price * commission_rate / 100, 2)
            organizer_net   = round(order.total_price - platform_cut, 2)

            result.append(OrganizerOrderOut(
                id=order.id,
                user_id=order.user_id,
                customer_name=user.name,
                customer_email=user.email,
                event_id=event.id,
                event_title=event.title,
                event_slug=event.slug,
                total_price=order.total_price,
                status=order.status,
                created_at=order.created_at,
                updated_at=order.updated_at,
                payment_id=payment.id       if payment else None,
                payment_status=payment.status if payment else None,
                mpesa_ref=payment.mpesa_ref  if payment else None,
                mpesa_phone=getattr(payment, "phone_number", None) if payment else None,
                commission_rate=commission_rate,
                platform_cut=platform_cut,
                organizer_net=organizer_net,
                bookings=bookings_by_order.get(order.id, []),
            ))

        return result


async def get_recent_orders_by_organizer_repo(
    organizer_id: int, limit: int = 10
) -> list[OrganizerOrderOut]:
    """
    Most recent N orders for the organizer's events.
    Used by the dashboard recent-activity widget.
    """
    all_orders = await list_orders_by_organizer_repo(organizer_id)
    return all_orders[:limit]