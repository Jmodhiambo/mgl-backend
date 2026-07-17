#!/usr/bin/env python3
"""
Admin CLI — user management.

    python -m app.cli users --help

Bootstrap note:
    The very first admin can't be created with `--as <admin-email>` because
    no admin exists yet. Use `--bootstrap` exactly once for that; every
    subsequent role/status change should use `--as` so the audit log
    attributes to a real admin instead of "CLI (bootstrap)".
"""

from typing import Optional

import typer
from fastapi import HTTPException

import app.services.audit_log_services as audit_log_services
import app.services.user_services as user_services
from app.cli.utils import echo_error_and_exit, echo_success, resolve_admin, run_async

app = typer.Typer(help="Manage users: roles, activation, verification.")

VALID_ROLES = {"user", "organizer", "admin"}


# ─── Internal logic (shared by multiple commands) ────────────────────────────

async def _set_role(
    email: str, role: str, as_admin: Optional[str], bootstrap: bool
) -> None:
    if role not in VALID_ROLES:
        echo_error_and_exit(
            f"Invalid role '{role}'. Must be one of: {', '.join(sorted(VALID_ROLES))}"
        )
        return

    try:
        target = await user_services.get_user_by_email_service(email)
    except HTTPException as exc:
        echo_error_and_exit(exc.detail)
        return

    if target.role == role:
        echo_error_and_exit(f"{email} already has role '{role}'.")
        return

    admin_id: Optional[int] = None
    admin_name = "CLI (bootstrap — no admin account existed yet)"

    if as_admin:
        try:
            admin_id, admin_name = await resolve_admin(as_admin)
        except HTTPException as exc:
            echo_error_and_exit(exc.detail)
            return
    elif not bootstrap:
        echo_error_and_exit(
            "Pass --as <admin-email> to attribute this change, or --bootstrap "
            "if this is the very first admin account being created."
        )
        return

    updated = await user_services.update_user_role_service(target.id, role)

    # AuditLog.admin_id is nullable (ondelete=SET NULL), so a None admin_id
    # from --bootstrap is a valid row — it just won't point at a real admin.
    await audit_log_services.log_admin_action_service(
        admin_id=admin_id,
        admin_name=admin_name,
        action="user_role_changed",
        target_type="user",
        target_id=updated.id,
        details={"new_role": role, "previous_role": target.role, "via": "cli"},
    )

    echo_success(f"{email} is now '{role}'.")


# ─── Commands ─────────────────────────────────────────────────────────────────

@app.command("list")
@run_async
async def list_users(
    role: Optional[str] = typer.Option(
        None, help="Filter by role: user | organizer | admin"
    ),
    active_only: bool = typer.Option(False, help="Only show active accounts"),
):
    """List users, optionally filtered by role or active status."""
    if role and role not in VALID_ROLES:
        echo_error_and_exit(
            f"Invalid role '{role}'. Must be one of: {', '.join(sorted(VALID_ROLES))}"
        )
        return

    users = (
        await user_services.list_active_users_service()
        if active_only
        else await user_services.list_all_users_service()
    )

    if role:
        users = [u for u in users if u.role == role]

    if not users:
        typer.echo("No users found.")
        return

    typer.echo(f"{'ID':<6}{'Name':<25}{'Email':<35}{'Role':<12}{'Active':<8}")
    typer.echo("-" * 86)
    for u in users:
        typer.echo(
            f"{u.id:<6}{u.name[:24]:<25}{u.email[:34]:<35}{u.role:<12}{str(u.is_active):<8}"
        )


@app.command("search")
@run_async
async def search_users(name: str):
    """Search users by (partial) name."""
    users = await user_services.search_users_by_name_service(name)
    if not users:
        typer.echo(f"No users matching '{name}'.")
        return
    for u in users:
        typer.echo(f"#{u.id}  {u.name}  <{u.email}>  role={u.role}  active={u.is_active}")


@app.command("show")
@run_async
async def show_user(email: str):
    """Show full details for a single user by email."""
    try:
        user = await user_services.get_user_by_email_service(email)
    except HTTPException as exc:
        echo_error_and_exit(exc.detail)
        return

    typer.echo(f"ID:              {user.id}")
    typer.echo(f"Name:            {user.name}")
    typer.echo(f"Email:           {user.email}")
    typer.echo(f"Phone:           {user.phone_number}")
    typer.echo(f"Role:            {user.role}")
    typer.echo(f"Active:          {user.is_active}")
    typer.echo(f"Email verified:  {user.email_verified}")
    typer.echo(f"Created:         {user.created_at}")


@app.command("set-role")
@run_async
async def set_role(
    email: str,
    role: str,
    as_admin: Optional[str] = typer.Option(
        None, "--as", help="Admin email, for the audit log."
    ),
    bootstrap: bool = typer.Option(
        False, help="First-ever admin promotion; skips the --as requirement."
    ),
):
    """Change a user's role to one of: user, organizer, admin."""
    await _set_role(email, role, as_admin, bootstrap)


@app.command("promote-admin")
@run_async
async def promote_admin(
    email: str,
    as_admin: Optional[str] = typer.Option(None, "--as"),
    bootstrap: bool = typer.Option(
        False, help="Use for the very first admin account only."
    ),
):
    """Shortcut for `set-role EMAIL admin`."""
    await _set_role(email, "admin", as_admin, bootstrap)


@app.command("demote")
@run_async
async def demote(
    email: str,
    as_admin: str = typer.Option(..., "--as", help="Admin email, for the audit log."),
):
    """Shortcut for `set-role EMAIL user`. Always requires --as — never bootstrap."""
    await _set_role(email, "user", as_admin, bootstrap=False)


@app.command("deactivate")
@run_async
async def deactivate(email: str, as_admin: str = typer.Option(..., "--as")):
    """Deactivate a user account."""
    try:
        admin_id, admin_name = await resolve_admin(as_admin)
        target = await user_services.get_user_by_email_service(email)
    except HTTPException as exc:
        echo_error_and_exit(exc.detail)
        return

    await user_services.deactivate_user_service(target.id)
    await audit_log_services.log_admin_action_service(
        admin_id=admin_id,
        admin_name=admin_name,
        action="user_deactivated",
        target_type="user",
        target_id=target.id,
        details={"via": "cli"},
    )
    echo_success(f"{email} deactivated.")


@app.command("reactivate")
@run_async
async def reactivate(email: str, as_admin: str = typer.Option(..., "--as")):
    """Reactivate a deactivated user account."""
    try:
        admin_id, admin_name = await resolve_admin(as_admin)
    except HTTPException as exc:
        echo_error_and_exit(exc.detail)
        return

    try:
        result = await user_services.reactivate_account_service(email)
    except HTTPException as exc:
        echo_error_and_exit(exc.detail)
        return

    await audit_log_services.log_admin_action_service(
        admin_id=admin_id,
        admin_name=admin_name,
        action="user_activated",
        target_type="user",
        target_id=None,
        details={"email": email, "via": "cli"},
    )
    echo_success(result["message"])


@app.command("force-verify-email")
@run_async
async def force_verify_email(email: str, as_admin: str = typer.Option(..., "--as")):
    """
    Mark a user's email verified without requiring their verification token.
    Useful when the token expired or the email never arrived.

    Depends on user_services.admin_force_verify_email_service — a new,
    small addition (see the updated user_services.py delivered alongside
    this CLI) since no existing service exposed a token-less verify.
    """
    try:
        admin_id, admin_name = await resolve_admin(as_admin)
        target = await user_services.get_user_by_email_service(email)
    except HTTPException as exc:
        echo_error_and_exit(exc.detail)
        return

    await user_services.admin_force_verify_email_service(target.id)
    await audit_log_services.log_admin_action_service(
        admin_id=admin_id,
        admin_name=admin_name,
        action="user_verified",
        target_type="user",
        target_id=target.id,
        details={"via": "cli", "method": "admin_force"},
    )
    echo_success(f"{email} marked as verified.")