#!/usr/bin/env python3
"""
Admin CLI — audit log viewer.

    python -m app.cli audit --help
"""

from typing import Optional

import typer

import app.services.audit_log_services as audit_log_services
from app.cli.utils import run_async

app = typer.Typer(help="Browse the admin audit log.")


@app.command("list")
@run_async
async def list_logs(
    admin_id: Optional[int] = typer.Option(None),
    action: Optional[str] = typer.Option(None),
    target_type: Optional[str] = typer.Option(None),
    limit: int = typer.Option(50, help="Max rows to show"),
):
    """List audit log entries, newest first, with optional filters."""
    result = await audit_log_services.list_audit_logs_service(
        admin_id=admin_id, action=action, target_type=target_type, limit=limit
    )
    if not result.items:
        typer.echo("No matching audit log entries.")
        return

    typer.echo(f"Showing {len(result.items)} of {result.total} total entries")
    typer.echo("-" * 90)
    for entry in result.items:
        target_id = entry.target_id if entry.target_id is not None else "-"
        typer.echo(
            f"#{entry.id:<6} {entry.created_at.isoformat():<26} "
            f"{entry.admin_name:<20} {entry.action:<22} "
            f"{entry.target_type}#{target_id}"
        )


@app.command("show")
@run_async
async def show(log_id: int):
    """Show one audit log entry, including its full details payload."""
    entry = await audit_log_services.get_audit_log_service(log_id)
    typer.echo(f"ID:          {entry.id}")
    typer.echo(f"When:        {entry.created_at}")
    typer.echo(f"Admin:       {entry.admin_name} (#{entry.admin_id})")
    typer.echo(f"Action:      {entry.action}")
    typer.echo(f"Target:      {entry.target_type}#{entry.target_id}")
    typer.echo(f"Details:     {entry.details}")


@app.command("my-activity")
@run_async
async def my_activity(admin_id: int, limit: int = typer.Option(15)):
    """Show the most recent actions performed by one admin."""
    result = await audit_log_services.list_my_activity_service(admin_id, limit=limit)
    typer.echo(f"{result.total} total lifetime action(s). Showing {len(result.items)}:")
    for entry in result.items:
        target_id = entry.target_id if entry.target_id is not None else "-"
        typer.echo(
            f"#{entry.id:<6} {entry.created_at.isoformat():<26} "
            f"{entry.action:<22} {entry.target_type}#{target_id}"
        )