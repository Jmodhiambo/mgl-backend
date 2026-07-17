#!/usr/bin/env python3
"""
MGLTickets admin CLI — root entry point.

    python -m app.cli users --help
    python -m app.cli events --help
    python -m app.cli settings --help
    python -m app.cli audit --help
    python -m app.cli sessions --help

Every command delegates to the same app/services/*.py functions the FastAPI
routers call — the CLI is a second, unauthenticated "front door" onto the
service layer, not a bypass of it. Because commands run outside a request
(no JWT, no logged-in admin), mutating commands take --as <admin-email> so
the change is attributed correctly in the audit log, the same way a router
endpoint attributes it to the admin from the JWT.

Example — the very first admin, then everything after:

    python -m app.cli users promote-admin martin@mgltickets.com --bootstrap
    python -m app.cli events pending
    python -m app.cli events approve 42 --as martin@mgltickets.com
"""

import typer

from app.cli import audit, events, sessions, settings, users

app = typer.Typer(
    help="MGLTickets admin CLI.",
    no_args_is_help=True,
)

app.add_typer(users.app, name="users")
app.add_typer(events.app, name="events")
app.add_typer(settings.app, name="settings")
app.add_typer(audit.app, name="audit")
app.add_typer(sessions.app, name="sessions")


if __name__ == "__main__":
    app()