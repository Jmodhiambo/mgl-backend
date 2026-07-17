#!/usr/bin/env python3
"""
Admin CLI — event moderation.

    python -m app.cli events --help
"""

from typing import Optional

import typer
from fastapi import HTTPException

import app.services.audit_log_services as audit_log_services
import app.services.event_services as event_services
import app.services.notification_services as notification_services
from app.cli.utils import echo_error_and_exit, echo_success, resolve_admin, run_async

app = typer.Typer(help="Moderate events: approve, reject, change status.")

VALID_STATUSES = {
    "upcoming", "ongoing", "completed", "cancelled", "deleted", "pending_deletion"
}


def _print_events(events) -> None:
    if not events:
        typer.echo("No events found.")
        return
    typer.echo(
        f"{'ID':<6}{'Title':<35}{'Organizer':<20}{'Status':<16}"
        f"{'Approved':<9}{'Bookings':<9}"
    )
    typer.echo("-" * 95)
    for e in events:
        organizer = getattr(e, "organizer_name", None) or ""
        typer.echo(
            f"{e.id:<6}{e.title[:34]:<35}{organizer[:19]:<20}{e.status:<16}"
            f"{str(e.is_approved):<9}{e.total_bookings:<9}"
        )


@app.command("pending")
@run_async
async def pending():
    """List events awaiting approval."""
    events = await event_services.get_unapproved_events_admin_service()
    _print_events(events)


@app.command("list")
@run_async
async def list_events(organizer_id: Optional[int] = typer.Option(None)):
    """List all events, optionally scoped to one organizer."""
    events = (
        await event_services.get_events_by_organizer_admin_service(organizer_id)
        if organizer_id
        else await event_services.get_all_events_service()
    )
    _print_events(events)


@app.command("show")
@run_async
async def show(event_id: int):
    """Show full detail for one event, including revenue/commission breakdown."""
    try:
        event = await event_services.get_event_by_id_admin_service(event_id)
    except HTTPException as exc:
        echo_error_and_exit(exc.detail)
        return

    typer.echo(f"ID:               {event.id}")
    typer.echo(f"Title:            {event.title}")
    typer.echo(f"Slug:             {event.slug}")
    typer.echo(f"Organizer:        {event.organizer_name} (#{event.organizer_id})")
    typer.echo(f"Status:           {event.status}")
    typer.echo(f"Approved:         {event.is_approved}")
    typer.echo(f"Venue:            {event.venue}, {event.city}, {event.country}")
    typer.echo(f"Start / End:      {event.start_time} \u2192 {event.end_time}")
    typer.echo(f"Bookings:         {event.total_bookings}")
    typer.echo(f"Revenue:          KES {event.total_revenue:,.2f}")
    typer.echo(
        f"Commission rate:  {event.commission_rate}% ({event.commission_source})"
    )
    typer.echo(f"Platform cut:     KES {event.platform_cut:,.2f}")
    typer.echo(f"Organizer net:    KES {event.organizer_net:,.2f}")
    typer.echo(
        f"Unresolved bookings (blocks hard-delete): {event.unresolved_bookings_count}"
    )


@app.command("approve")
@run_async
async def approve(event_id: int, as_admin: str = typer.Option(..., "--as")):
    """Approve a pending event."""
    try:
        admin_id, admin_name = await resolve_admin(as_admin)
    except HTTPException as exc:
        echo_error_and_exit(exc.detail)
        return

    event = await event_services.approve_event_service(event_id)
    if not event:
        echo_error_and_exit(f"Event {event_id} not found.")
        return

    await audit_log_services.log_admin_action_service(
        admin_id=admin_id,
        admin_name=admin_name,
        action="event_approved",
        target_type="event",
        target_id=event.id,
        details={"approved_event": event.title, "via": "cli"},
    )
    await notification_services.notify_event_approved(
        event.id, event.title, event.slug, admin_name, event.organizer_id
    )
    echo_success(f"Approved '{event.title}' (#{event.id}).")


@app.command("reject")
@run_async
async def reject(
    event_id: int,
    as_admin: str = typer.Option(..., "--as"),
    reason: str = typer.Option(
        "", help="Optional reason — recorded in the audit log and sent to the organizer."
    ),
):
    """Reject a pending event."""
    try:
        admin_id, admin_name = await resolve_admin(as_admin)
    except HTTPException as exc:
        echo_error_and_exit(exc.detail)
        return

    event = await event_services.reject_event_service(event_id)
    if not event:
        echo_error_and_exit(f"Event {event_id} not found.")
        return

    await audit_log_services.log_admin_action_service(
        admin_id=admin_id,
        admin_name=admin_name,
        action="event_rejected",
        target_type="event",
        target_id=event.id,
        details={"rejected_event": event.title, "reason": reason, "via": "cli"},
    )
    await notification_services.notify_event_rejected(
        event.id, event.title, event.slug, admin_name, event.organizer_id, reason
    )
    echo_success(f"Rejected '{event.title}' (#{event.id}).")


@app.command("set-status")
@run_async
async def set_status(
    event_id: int,
    status: str,
    as_admin: str = typer.Option(..., "--as"),
):
    """
    Set an event's status.
    One of: upcoming, ongoing, completed, cancelled, deleted, pending_deletion.

    Note: passing 'deleted' on an event with unresolved bookings will be
    silently redirected to 'pending_deletion' by event_services — this
    command just reports whatever status comes back.
    """
    if status not in VALID_STATUSES:
        echo_error_and_exit(
            f"Invalid status. Must be one of: {', '.join(sorted(VALID_STATUSES))}"
        )
        return

    try:
        admin_id, admin_name = await resolve_admin(as_admin)
    except HTTPException as exc:
        echo_error_and_exit(exc.detail)
        return

    try:
        event = await event_services.update_event_status_service(event_id, status)
    except HTTPException as exc:
        echo_error_and_exit(exc.detail)
        return

    if not event:
        echo_error_and_exit(f"Event {event_id} not found.")
        return

    # "event_status_changed" is a new action tag not in the existing
    # recognised list in audit_log_services.py. Per the reminder comment
    # already in that file, add it to the frontend filter list in
    # AuditLogs.tsx so it displays/filters correctly in the admin UI.
    action = "event_deleted" if event.status == "deleted" else "event_status_changed"
    await audit_log_services.log_admin_action_service(
        admin_id=admin_id,
        admin_name=admin_name,
        action=action,
        target_type="event",
        target_id=event.id,
        details={"new_status": event.status, "via": "cli"},
    )
    echo_success(f"'{event.title}' (#{event.id}) status is now '{event.status}'.")
    if status == "deleted" and event.status == "pending_deletion":
        typer.secho(
            "  Note: event had unresolved bookings, so it was routed to "
            "'pending_deletion' instead of 'deleted'.",
            fg=typer.colors.YELLOW,
        )


@app.command("confirm-deletion")
@run_async
async def confirm_deletion(event_id: int, as_admin: str = typer.Option(..., "--as")):
    """
    Confirm an event in 'pending_deletion' is ready for a hard delete
    (i.e. all refunds have actually been processed).
    """
    try:
        admin_id, admin_name = await resolve_admin(as_admin)
    except HTTPException as exc:
        echo_error_and_exit(exc.detail)
        return

    try:
        event = await event_services.confirm_event_deletion_ready_service(event_id)
    except HTTPException as exc:
        echo_error_and_exit(exc.detail)
        return

    await audit_log_services.log_admin_action_service(
        admin_id=admin_id,
        admin_name=admin_name,
        action="event_deleted",
        target_type="event",
        target_id=event.id,
        details={"deleted_event": event.title, "via": "cli"},
    )
    echo_success(f"'{event.title}' (#{event.id}) confirmed deleted.")