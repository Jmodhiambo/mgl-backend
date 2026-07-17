#!/usr/bin/env python3
"""
Admin CLI — platform settings.

    python -m app.cli settings --help

ASSUMPTION FLAGGED: _FIELD_CASTERS below mirrors the columns on
app/db/models/platform_settings.py. I don't have app/schemas/settings.py
(PlatformSettingsUpdate) in front of me, so `set` assumes that schema
exposes these same field names as optional. If a field name doesn't match,
Pydantic will raise a clear validation error rather than silently doing
the wrong thing — but if that happens, send me the schema and I'll adjust.
"""

import typer
from fastapi import HTTPException

import app.services.audit_log_services as audit_log_services
import app.services.settings_services as settings_services
from app.cli.utils import echo_error_and_exit, echo_success, resolve_admin, run_async

app = typer.Typer(help="View and update platform-wide settings.")


def _to_bool(v: str) -> bool:
    if v.lower() not in ("1", "0", "true", "false", "yes", "no"):
        raise ValueError(f"'{v}' is not a boolean-like value")
    return v.lower() in ("1", "true", "yes")


_FIELD_CASTERS = {
    "platform_name": str,
    "platform_email": str,
    "support_email": str,
    "default_currency": str,
    "timezone": str,
    "platform_fee_percent": float,
    "require_event_approval": _to_bool,
    "allow_user_registration": _to_bool,
    "allow_organizer_signup": _to_bool,
    "enable_refunds": _to_bool,
    "max_tickets_per_booking": int,
    "session_timeout_hours": int,
    "maintenance_mode": _to_bool,
}


@app.command("show")
@run_async
async def show():
    """Print current platform settings."""
    try:
        settings_out = await settings_services.get_platform_settings_service()
    except HTTPException as exc:
        echo_error_and_exit(exc.detail)
        return

    for field in _FIELD_CASTERS:
        typer.echo(f"{field:<28}{getattr(settings_out, field)}")
    typer.echo(f"{'updated_at':<28}{settings_out.updated_at}")


@app.command("set")
@run_async
async def set_setting(
    key: str,
    value: str,
    as_admin: str = typer.Option(..., "--as"),
):
    """
    Set a single platform setting.
    KEY must be one of the fields printed by `settings show`.
    """
    if key not in _FIELD_CASTERS:
        echo_error_and_exit(
            f"Unknown setting '{key}'. Valid keys: {', '.join(_FIELD_CASTERS)}"
        )
        return

    try:
        admin_id, admin_name = await resolve_admin(as_admin)
    except HTTPException as exc:
        echo_error_and_exit(exc.detail)
        return

    try:
        casted_value = _FIELD_CASTERS[key](value)
    except (ValueError, TypeError):
        echo_error_and_exit(f"Could not parse '{value}' for setting '{key}'.")
        return

    from app.schemas.settings import PlatformSettingsUpdate  # deferred — only needed here

    payload = PlatformSettingsUpdate(**{key: casted_value})

    try:
        updated = await settings_services.update_platform_settings_service(
            payload, admin_id
        )
    except HTTPException as exc:
        echo_error_and_exit(exc.detail)
        return

    # update_platform_settings_service already stamps settings.updated_by_user_id
    # itself, but "settings_updated" is a recognised action in the audit log's
    # own action list (see audit_log_services.py docstring) — logging it here
    # too keeps this change visible in the Audit Logs page, not just on the
    # settings row.
    await audit_log_services.log_admin_action_service(
        admin_id=admin_id,
        admin_name=admin_name,
        action="settings_updated",
        target_type="settings",
        target_id=None,
        details={"key": key, "new_value": casted_value, "via": "cli"},
    )
    echo_success(f"{key} = {getattr(updated, key)}")