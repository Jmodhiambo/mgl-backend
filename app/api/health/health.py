#!/usr/bin/env python3
# app/api/health/health.py
#
# WHY THIS FILE EXISTS
# ---------------------
# Our deploy script does a "hot reload" (systemctl reload, not restart) so that
# gunicorn swaps in new worker processes without ever closing the listening
# socket - old workers keep serving in-flight requests while new ones spin up,
# and only get killed once the new ones are ready. No downtime.
#
# The problem: during that swap window, BOTH old and new workers are alive at
# the same time, and requests get load-balanced across whichever workers exist
# at that moment. So if the deploy script just checks "did I get a 200 back
# from /health", that 200 might have come from an OLD worker that hasn't been
# killed yet - not proof that the NEW code is actually up and serving traffic.
#
# The fix: this endpoint reports which git commit the responding worker was
# started from. The deploy script polls /health in a loop and only declares
# success once it sees the SHA of the commit it just deployed. That's a real
# guarantee that new code is live, not just that "a" process responded.
#
# SECOND PROBLEM THIS FILE SOLVES: code matching isn't the same as schema
# matching. We had an incident where code was pulled, migrations ran fine
# against the database, but the running gunicorn workers were never reloaded
# to pick any of it up - `git rev-parse HEAD` on disk said one thing, the
# live workers (still holding old code in memory) said another, and nothing
# caught the gap because commit-matching alone can't see it. So this
# endpoint also reports the database's current alembic revision, read
# directly from the alembic_version table. The deploy script can then
# confirm BOTH the code AND the schema the worker is actually using, instead
# of just one.
#
# HOW A WORKER "KNOWS" ITS OWN COMMIT
# -------------------------------------
# Each gunicorn worker process re-imports the whole app fresh when it starts
# (we don't use gunicorn's --preload flag). So a worker that was forked BEFORE
# the reload is still running the OLD code in memory, and a worker forked
# AFTER the reload is running the NEW code. Both workers, if asked "what
# commit are you", will correctly report whichever version of this exact file
# they loaded - because the answer is computed fresh on every request by
# asking git directly, not cached from when the server first booted.

import subprocess
from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import async_engine

router = APIRouter()

# Absolute path to the repo on the server. Hardcoded because this needs to
# work regardless of what directory gunicorn happens to be started from.
REPO_PATH = "/var/www/mgltickets/mgl-backend"


def _get_git_sha() -> str:
    """
    Ask git, right now, what commit HEAD points to on disk.

    We deliberately do NOT cache this in a variable at import time. If we
    cached it, every worker would report whatever commit was checked out
    at the moment THAT worker's process started - which is actually what we
    want here (see comment above), so caching at import time would technically
    still work. We call it fresh per-request instead just to keep this function
    simple and stateless, and because health-check traffic is low-volume so the
    extra subprocess call per request is cheap. If this endpoint ever gets hit
    by frequent uptime monitors, revisit this (see note below).

    Returns "unknown" instead of raising if anything goes wrong - a health
    endpoint should never itself throw a 500 just because git had a bad day.
    """
    try:
        result = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],  # "give me the current commit hash"
            cwd=REPO_PATH,                  # run it as if we were in the repo dir
            timeout=2,                      # don't hang the health check forever
        )
        return result.decode().strip()      # bytes -> string, drop trailing newline
    except Exception:
        return "unknown"


async def _get_alembic_revision() -> str:
    """
    Ask the DATABASE ITSELF what migration revision it's currently on, by
    reading the alembic_version table directly - not by shelling out to
    `alembic current`.

    Why not just run `alembic current` like a human would? Because that
    command reloads the entire alembic environment (env.py, config, its own
    engine) on every call - slow and overkill for something polled in a
    tight loop during every deploy. Reading the table directly is a single
    lightweight query using the connection pool the app already has open,
    and it's the same table alembic itself writes to - so it's exactly as
    authoritative, just cheaper to ask.

    Returns "unknown" instead of raising if anything goes wrong (DB
    unreachable, table doesn't exist yet on a brand-new database, etc.) -
    same philosophy as _get_git_sha() above: a health endpoint should never
    500 just because one of its checks had a bad day.
    """
    try:
        async with async_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT version_num FROM alembic_version LIMIT 1")
            )
            row = result.first()
            return row[0] if row else "unknown"
    except Exception:
        return "unknown"


@router.get("/health")
async def health():
    """
    Health check endpoint for monitoring.

    Deploy script polls this after `systemctl reload mgltickets` and compares
    both the "commit" field and the "alembic_revision" field against what it
    just deployed and migrated to. Only once BOTH match does it know the new
    code AND the matching schema are actually the ones being served - not
    just that a worker process is alive.

    NOTE: this confirms code + schema are aligned, but does NOT confirm
    things like the Resend API key or Daraja credentials are valid. If you
    want a deeper check later, add it here, but keep it fast - this endpoint
    gets polled in a tight loop during every deploy.
    """
    return {
        "status": "healthy",
        "app": "MGLTickets API",
        "version": "1.0.0",
        "commit": _get_git_sha(),
        "alembic_revision": await _get_alembic_revision(),
    }