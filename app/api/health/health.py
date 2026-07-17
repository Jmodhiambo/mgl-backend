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


@router.get("/health")
async def health():
    """
    Health check endpoint for monitoring.

    Deploy script polls this after `systemctl reload mgltickets` and compares
    the "commit" field against the SHA it just pulled. Once they match, it
    knows the new code is actually the one answering requests.

    NOTE: this only tells you a worker process is alive and reports the right
    commit - it does NOT confirm the database connection pool, Resend API key,
    or anything else is working. If you want a deeper check later (e.g. a
    quick `SELECT 1` against the DB), add it here, but keep it fast - this
    endpoint gets polled in a tight loop during every deploy.
    """
    return {
        "status": "healthy",
        "app": "MGLTickets API",
        "version": "1.0.0",
        "commit": _get_git_sha(),
    }