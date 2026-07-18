#!/usr/bin/env python3
# app/services/event_services.py
"""Event services for MGLTickets."""

import asyncio
from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.core.config import FRONTEND_URL
from app.core.logging_config import logger
from app.emails.email_manager import email_manager
from app.schemas.event import EventCreateWithFlyer, EventDetails, EventStats, EventUpdate
import app.db.repositories.booking_repo as booking_repo
import app.db.repositories.event_repo as event_repo
import app.db.repositories.order_repo as order_repo
import app.db.repositories.settings_repo as settings_repo
import app.db.repositories.ticket_type_repo as tt_repo
import app.db.repositories.user_repo as user_repo


# ── Email background helper ───────────────────────────────────────────────────

def _bg_email(coro) -> None:
    """
    Schedule an email coroutine as a background task.
    Falls back to direct await if no running event loop exists (tests, CLI).
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        asyncio.run(coro)


async def _notify_attendees_of_cancellation(event_id: int, event_title: str, organizer_name: str, cancellation_reason: str) -> None:
    """
    Fan out organizer.cancellation to every attendee with a booking on this
    event. Reuses the same enriched-booking source and variable shape as
    the manual bulk-send path in organizer_emails_services.py, so a
    cancellation notice looks identical whether it was triggered
    automatically (here) or sent manually by the organizer.
    Never raises — a notification failure must not affect the status change
    that already succeeded.
    """
    try:
        bookings = await booking_repo.list_event_bookings_enriched_repo(event_id)
        sent = 0
        for booking in bookings:
            if not booking.customer_email:
                continue
            _bg_email(email_manager.send_from_template(
                template_id="organizer.cancellation",
                to_email=booking.customer_email,
                variables={
                    "customer_name": booking.customer_name or "Valued Customer",
                    "event_title": event_title,
                    "ticket_type": booking.ticket_type_name or "General",
                    "quantity": str(booking.quantity),
                    "order_id": str(booking.order_id or booking.id),
                    "total_price": f"{booking.total_price:,.0f}" if booking.total_price else "0",
                    "cancellation_reason": cancellation_reason or "The event has been cancelled by the organizer.",
                    "organizer_name": organizer_name,
                },
            ))
            sent += 1
        logger.info(f"Dispatched cancellation email to {sent} attendee(s) for event {event_id}")
    except Exception as exc:
        logger.warning(f"Could not schedule cancellation emails for event {event_id}: {exc}")


# ── URL helpers ───────────────────────────────────────────────────────────────

def _organizer_dashboard_url() -> str:
    return f"organizer.{FRONTEND_URL}/dashboard"


def _event_public_url(slug: str) -> str:
    return f"{FRONTEND_URL}/events/{slug}"


# ── Creation ──────────────────────────────────────────────────────────────────

async def create_event_service(event_data: EventCreateWithFlyer):
    """Create a new event, lock commission rate, notify organizer in background."""
    logger.info(f"Creating event: {event_data.title!r}")

    try:
        platform_settings = await settings_repo.get_platform_settings_repo()
        if platform_settings is not None:
            event_data = event_data.model_copy(update={
                "commission_rate": float(platform_settings.platform_fee_percent),
                "commission_source": "platform_default",
            })
    except Exception as exc:
        logger.warning(f"Could not fetch platform settings for commission: {exc}")

    base = await event_repo.create_event_repo(event_data)
    full = await event_repo.get_event_by_id_admin_repo(base.id)
    if not full:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Event created but could not be retrieved.")

    try:
        organizer = await user_repo.get_user_by_id_repo(full.organizer_id)
        if organizer:
            _bg_email(email_manager.send_from_template(
                template_id="organizer.event_created",
                to_email=organizer.email,
                variables={
                    "organizer_name": organizer.name,
                    "event_title": full.title,
                    "venue": full.venue or "TBA",
                    "event_date": full.start_date.strftime("%d %b %Y") if full.start_date else "TBA",
                    "dashboard_url": _organizer_dashboard_url(),
                },
            ))
    except Exception as exc:
        logger.warning(f"Could not schedule event_created email for event {full.id}: {exc}")

    return full


# ── Basic CRUD ────────────────────────────────────────────────────────────────

async def get_event_by_id_service(event_id: int):
    event = await event_repo.get_event_by_id_repo(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


async def get_event_by_slug_service(slug: str):
    return await event_repo.get_event_by_slug_repo(slug)


async def update_event_service(event_id: int, event_data: EventUpdate):
    updated = await event_repo.update_event_repo(event_id, event_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Event not found")
    return await event_repo.get_event_by_id_organizer_repo(updated.id)


async def delete_event_service(event_id: int):
    logger.info(f"Deleting event {event_id}")
    deleted = await event_repo.delete_event_repo(event_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Event not found")
    return deleted


async def update_event_status_service(event_id: int, new_status: str, cancellation_reason: str = ""):
    """
    Update event status. Redirects delete requests to pending_deletion
    when unresolved bookings exist, and notifies the organizer in background.
    When new_status is 'cancelled', every attendee with a booking on the
    event is notified via organizer.cancellation in background (the same
    template organizers can also send manually via the bulk-email tool).
    """
    valid = ["upcoming", "ongoing", "completed", "cancelled", "deleted", "pending_deletion"]
    if new_status not in valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status.")

    if new_status == "deleted":
        unresolved = await booking_repo.count_unresolved_bookings_by_event_repo(event_id)
        if unresolved > 0:
            logger.info(f"Event {event_id} has {unresolved} unresolved booking(s) — redirecting to pending_deletion.")
            result = await event_repo.update_event_status_repo(event_id, "pending_deletion")
            try:
                event = await event_repo.get_event_by_id_repo(event_id)
                if event:
                    organizer = await user_repo.get_user_by_id_repo(event.organizer_id)
                    if organizer:
                        _bg_email(email_manager.send_from_template(
                            template_id="organizer.event_pending_deletion",
                            to_email=organizer.email,
                            variables={
                                "organizer_name": organizer.name,
                                "event_title": event.title,
                                "unresolved_count": str(unresolved),
                            },
                        ))
            except Exception as exc:
                logger.warning(f"Could not schedule pending_deletion email for event {event_id}: {exc}")
            return result

    result = await event_repo.update_event_status_repo(event_id, new_status)

    if new_status == "cancelled":
        try:
            event = await event_repo.get_event_by_id_repo(event_id)
            if event:
                organizer = await user_repo.get_user_by_id_repo(event.organizer_id)
                await _notify_attendees_of_cancellation(
                    event_id=event_id,
                    event_title=event.title,
                    organizer_name=organizer.name if organizer else "Your Organizer",
                    cancellation_reason=cancellation_reason,
                )
        except Exception as exc:
            logger.warning(f"Could not schedule cancellation emails for event {event_id}: {exc}")

    return result


async def confirm_event_deletion_ready_service(event_id: int):
    """pending_deletion → deleted once all refunds are done. Notifies organizer in background."""
    event = await event_repo.get_event_by_id_repo(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found.")
    if event.status != "pending_deletion":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Event is not pending deletion.")

    unresolved = await booking_repo.count_unresolved_bookings_by_event_repo(event_id)
    if unresolved > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Event still has {unresolved} unresolved booking(s). Process all refunds before confirming deletion.",
        )

    result = await event_repo.update_event_status_repo(event_id, "deleted")

    try:
        organizer = await user_repo.get_user_by_id_repo(event.organizer_id)
        if organizer:
            total_bookings = await booking_repo.count_bookings_by_event_repo(event_id)
            _bg_email(email_manager.send_from_template(
                template_id="organizer.event_deletion_confirmed",
                to_email=organizer.email,
                variables={
                    "organizer_name": organizer.name,
                    "event_title": event.title,
                    "deleted_at": datetime.now(timezone.utc).strftime("%d %b %Y at %H:%M UTC"),
                    "refund_count": str(total_bookings),
                    "dashboard_url": _organizer_dashboard_url(),
                },
            ))
    except Exception as exc:
        logger.warning(f"Could not schedule event_deletion_confirmed email for event {event_id}: {exc}")

    return result


async def get_approved_events_service():
    return await event_repo.get_approved_events_repo()


# ── Approval ──────────────────────────────────────────────────────────────────

async def approve_event_service(event_id: int, admin_name: str):
    """Approve an event and notify the organizer in background."""
    result = await event_repo.approve_event_repo(event_id)

    try:
        event = await event_repo.get_event_by_id_repo(event_id)
        if event:
            organizer = await user_repo.get_user_by_id_repo(event.organizer_id)
            if organizer:
                _bg_email(email_manager.send_from_template(
                    template_id="organizer.event_approved",
                    to_email=organizer.email,
                    variables={
                        "organizer_name": organizer.name,
                        "event_title": event.title,
                        "venue": event.venue or "TBA",
                        "event_date": event.start_date.strftime("%d %b %Y") if event.start_date else "TBA",
                        "admin_name": admin_name,
                        "event_url": _event_public_url(event.slug),
                    },
                ))
    except Exception as exc:
        logger.warning(f"Could not schedule event_approved email for event {event_id}: {exc}")

    return result


async def reject_event_service(event_id: int, admin_name: str, reason: str = ""):
    """Reject an event and notify the organizer in background."""
    result = await event_repo.reject_event_repo(event_id)

    try:
        event = await event_repo.get_event_by_id_repo(event_id)
        if event:
            organizer = await user_repo.get_user_by_id_repo(event.organizer_id)
            if organizer:
                variables = {
                    "organizer_name": organizer.name,
                    "event_title": event.title,
                    "admin_name": admin_name,
                    "dashboard_url": _organizer_dashboard_url(),
                }
                if reason:
                    variables["rejection_reason"] = reason
                _bg_email(email_manager.send_from_template(
                    template_id="organizer.event_rejected",
                    to_email=organizer.email,
                    variables=variables,
                ))
    except Exception as exc:
        logger.warning(f"Could not schedule event_rejected email for event {event_id}: {exc}")

    return result


# ── Admin list queries ────────────────────────────────────────────────────────

async def get_event_by_id_admin_service(event_id: int):
    event = await event_repo.get_event_by_id_admin_repo(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

async def get_event_by_slug_admin_service(slug: str):
    event = await event_repo.get_event_by_slug_repo(slug)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return await event_repo.get_event_by_id_admin_repo(event.id)

async def get_events_by_organizer_admin_service(organizer_id: int):
    return await event_repo.get_events_by_organizer_admin_repo(organizer_id)

async def get_approved_events_admin_service():
    return await event_repo.get_approved_events_admin_repo()

async def get_unapproved_events_admin_service():
    return await event_repo.get_unapproved_events_admin_repo()

async def get_all_events_service():
    return await event_repo.get_all_events_admin_repo()


# ── Organizer list queries ────────────────────────────────────────────────────

async def get_event_by_id_organizer_service(event_id: int):
    event = await event_repo.get_event_by_id_organizer_repo(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

async def get_events_by_organizer_service(organizer_id: int):
    return await event_repo.get_events_by_organizer_with_stats_repo(organizer_id)


# ── Counts ────────────────────────────────────────────────────────────────────

async def count_events_by_organizer_service(organizer_id: int) -> int:
    return await event_repo.count_events_by_organizer_repo(organizer_id)

async def count_events_service() -> int:
    return await event_repo.count_events_repo()


# ── Public / search ───────────────────────────────────────────────────────────

async def get_latest_events_service(limit: int = 5):
    return await event_repo.get_latest_events_repo(limit)

async def get_events_by_status_service(new_status: str):
    return await event_repo.get_events_by_status_repo(new_status)

async def search_events_by_title_service(title: str):
    return await event_repo.search_events_by_title_repo(title)

async def search_events_by_venue_service(venue: str):
    return await event_repo.search_events_by_venue_repo(venue)

async def get_events_by_country_service(country: str):
    return await event_repo.get_events_by_country_repo(country)

async def get_events_in_date_range_service(start_date: datetime, end_date: datetime):
    return await event_repo.get_events_in_date_range_repo(start_date, end_date)

async def get_events_sorted_by_start_time_service(ascending: bool = True):
    return await event_repo.get_events_sorted_by_start_time_repo(ascending)

async def get_events_sorted_by_end_time_service(ascending: bool = True):
    return await event_repo.get_events_sorted_by_end_time_repo(ascending)

async def get_events_created_after_service(date: datetime):
    return await event_repo.get_events_created_after_repo(date)

async def get_events_created_before_service(date: datetime):
    return await event_repo.get_events_created_before_repo(date)

async def get_events_updated_after_service(date: datetime):
    return await event_repo.get_events_updated_after_repo(date)

async def get_events_updated_before_service(date: datetime):
    return await event_repo.get_events_updated_before_repo(date)


# ── Organizer detail / stats ──────────────────────────────────────────────────

async def get_event_stats_service(event_id: int) -> EventStats:
    logger.info(f"Getting event stats for event_id={event_id}")
    try:
        (
            total_bookings,
            total_revenue,
            tickets_sold,
            total_available,
            total_sold,
        ) = await asyncio.gather(
            booking_repo.count_bookings_by_event_repo(event_id),
            booking_repo.get_total_revenue_by_event_id_repo(event_id),
            booking_repo.count_tickets_sold_by_event_id_repo(event_id),
            tt_repo.count_available_tickets_by_event_repo(event_id),
            tt_repo.count_tickets_sold_by_event_id_repo(event_id),
        )
        tickets_remaining = total_available - total_sold
        event = await event_repo.get_event_by_id_organizer_repo(event_id)
        commission_rate = float(event.commission_rate) if event else 7.0
        platform_cut = round(total_revenue * commission_rate / 100, 2)
        organizer_net = round(total_revenue - platform_cut, 2)

        return EventStats(
            total_bookings=total_bookings,
            total_revenue=total_revenue,
            tickets_sold=tickets_sold,
            tickets_remaining=tickets_remaining,
            commission_rate=commission_rate,
            platform_cut=platform_cut,
            organizer_net=organizer_net,
        )
    except Exception as e:
        logger.error(f"Error fetching event stats for event_id={event_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching event stats")


async def get_event_recent_bookings_service(event_id: int, limit: int = 5):
    return await booking_repo.list_recent_bookings_by_event_repo(event_id, limit)


async def get_event_details_service(event_id: int) -> EventDetails:
    event = await event_repo.get_event_by_id_organizer_repo(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return await _build_event_details(event)


async def get_event_details_by_slug_service(slug: str) -> EventDetails:
    event = await event_repo.get_event_by_slug_organizer_repo(slug)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return await _build_event_details(event)


async def _build_event_details(event) -> EventDetails:
    try:
        event_stats, ticket_types, recent_bookings = await asyncio.gather(
            get_event_stats_service(event.id),
            tt_repo.list_all_ticket_types_by_event_id_repo(event.id),
            get_event_recent_bookings_service(event.id),
        )
        return EventDetails(event=event, stats=event_stats, ticket_types=ticket_types, recent_bookings=recent_bookings)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building EventDetails for event_id={event.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error fetching event details")


async def get_top_events_by_organizer_service(organizer_id: int, limit: int = 5):
    return await event_repo.get_top_events_by_organizer_repo(organizer_id, limit)