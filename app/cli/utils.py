#!/usr/bin/env python3
"""
Shared helpers for the MGLTickets admin CLI.

Design principle: the CLI never talks to repositories directly. Every
command calls the exact same app/services/*.py functions the FastAPI
routers call, so business rules (validation, idempotency guards,
commission locking, etc.) only ever live in one place. The CLI is a
second, unauthenticated "front door" onto the service layer — not a
bypass of it.
"""

import asyncio
import functools
from typing import Any, Callable, Coroutine

import typer
from fastapi import HTTPException


def run_async(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable[..., Any]:
    """
    Adapt an `async def` Typer command into the sync callable Typer/Click expects.

    functools.wraps sets __wrapped__ on the returned function, and
    inspect.signature() follows __wrapped__ automatically — so Typer still
    builds its CLI interface (arguments, options, types, help text) from the
    original async function's signature, even though what actually executes
    is this sync wrapper via asyncio.run().
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return asyncio.run(func(*args, **kwargs))

    return wrapper


def echo_error_and_exit(message: str, code: int = 1) -> None:
    """Print a red error message and exit with a non-zero status."""
    typer.secho(f"\u2717 {message}", fg=typer.colors.RED)
    raise typer.Exit(code=code)


def echo_success(message: str) -> None:
    """Print a green success message."""
    typer.secho(f"\u2713 {message}", fg=typer.colors.GREEN)


async def resolve_admin(email: str) -> tuple[int, str]:
    """
    Look up a user by email and confirm they currently hold the 'admin' role.

    Used to attribute CLI-driven mutations to a real admin in the audit log —
    the same (admin_id, admin_name) pairing every router endpoint already
    writes via audit_log_services.log_admin_action_service(). This is what
    makes `--as <admin-email>` meaningful instead of just decorative.

    Raises:
        HTTPException(404) — propagated from get_user_by_email_service if the
            email doesn't exist.
        HTTPException(403) — if the account exists but isn't an admin.

    Callers should wrap this in try/except HTTPException and route the
    message through echo_error_and_exit().
    """
    from app.services.user_services import get_user_by_email_service

    user = await get_user_by_email_service(email)
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail=f"{email} is not an admin (current role: '{user.role}').",
        )
    return user.id, user.name