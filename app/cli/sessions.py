#!/usr/bin/env python3
"""
Admin CLI — session management.

    python -m app.cli sessions --help
"""

import typer
from fastapi import HTTPException

import app.services.ref_session_services as ref_session_services
import app.services.user_services as user_services
from app.cli.utils import echo_error_and_exit, echo_success, run_async

app = typer.Typer(help="Inspect and clean up login sessions.")


@app.command("cleanup")
@run_async
async def cleanup(
    hours: int = typer.Option(
        24, help="Delete expired/revoked sessions older than this many hours."
    ),
):
    """Purge expired and revoked refresh sessions (safe to run repeatedly)."""
    result = await ref_session_services.cleanup_expired_and_revoked_sessions_service(
        hours
    )
    echo_success(
        f"Deleted {result['deleted_count']} stale session(s). "
        f"{result['active_sessions']} active session(s) remain."
    )


@app.command("list-active")
@run_async
async def list_active(email: str):
    """List a user's currently active sessions."""
    try:
        user = await user_services.get_user_by_email_service(email)
    except HTTPException as exc:
        echo_error_and_exit(exc.detail)
        return

    active_sessions = await ref_session_services.get_my_sessions_service(user.id)
    if not active_sessions:
        typer.echo(f"No active sessions for {email}.")
        return

    for s in active_sessions:
        typer.echo(
            f"{s.session_id[:12]}...  device={s.device_info}  "
            f"ip={s.ip_address}  expires={s.expires_at}"
        )


@app.command("force-logout")
@run_async
async def force_logout(email: str):
    """Revoke ALL sessions for a user — forces them to log in again everywhere."""
    try:
        user = await user_services.get_user_by_email_service(email)
    except HTTPException as exc:
        echo_error_and_exit(exc.detail)
        return

    result = await ref_session_services.cleanup_user_sessions_service(user.id)
    echo_success(f"{result['deleted_count']} session(s) revoked for {email}.")