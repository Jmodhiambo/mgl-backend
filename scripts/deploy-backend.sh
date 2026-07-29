#!/bin/bash
set -e  # Exit immediately if any command fails (up until the "point of no return" below)

BACKEND_DIR="/var/www/mgltickets/mgl-backend"
SERVICE_NAME="mgltickets"
HEALTH_URL="http://127.0.0.1:8000/health"
MAX_ATTEMPTS=15
SLEEP_SECONDS=2

# Path to the migrations folder, relative to BACKEND_DIR.
# Used only to detect whether THIS deploy introduces new migrations, so we
# know whether to warn loudly if we have to roll back later.
# Double-check this matches your actual alembic layout.
MIGRATIONS_DIR="alembic/versions"

cd "$BACKEND_DIR"

echo "=== Starting backend deployment ==="

# --- Guard against a second deploy starting while one is already running ---
# Matters because a hung step (e.g. pre-flight import) combined with a
# dropped SSH session can leave a deploy running invisibly in the background.
# Without this, a second run could start mid-migration or mid-reload of the
# first and the two would collide.
LOCK_FILE="/tmp/mgltickets_deploy.lock"
if [ -e "$LOCK_FILE" ]; then
    LOCK_PID=$(cat "$LOCK_FILE" 2>/dev/null)
    if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
        echo "ERROR: A deploy is already in progress (PID $LOCK_PID, lock file $LOCK_FILE)."
        echo "Check 'ps -eo pid,lstart,etime,cmd | grep $LOCK_PID' before doing anything else."
        echo "If you're certain that process is dead despite this check, remove the lock"
        echo "file manually and retry: rm $LOCK_FILE"
        exit 1
    else
        echo "Found a stale lock file (PID $LOCK_PID is not running). Removing it."
        rm -f "$LOCK_FILE"
    fi
fi
echo $$ > "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

# --- Helper: ask the running service what commit AND schema revision it's
# actually serving. One curl call, two fields extracted from the same
# response - avoids double-hitting the health endpoint in every poll.
get_running_state() {
    local response
    response=$(curl --silent --max-time 3 "$HEALTH_URL" 2>/dev/null)
    local sha rev
    sha=$(echo "$response" | grep -o '"commit":"[^"]*"' | cut -d'"' -f4)
    rev=$(echo "$response" | grep -o '"alembic_revision":"[^"]*"' | cut -d'"' -f4)
    echo "${sha}|${rev}"
}

# --- Capture the rollback target BEFORE we change anything ---
# Deliberately NOT "git rev-parse HEAD". Local git state can lag behind or
# be ahead of what's actually running (exactly what happened here: code had
# already been pulled and migrated, but the service was never reloaded to
# pick it up, so git HEAD said one thing while the live workers said
# another). Asking the service itself via /health is the only source of
# truth for "what's actually live right now" — that's what we compare
# against and what we roll back to.
echo "Checking what commit is currently being served..."
STATE_BEFORE=$(get_running_state)
RUNNING_SHA_BEFORE="${STATE_BEFORE%%|*}"
if [ -z "$RUNNING_SHA_BEFORE" ]; then
    echo "WARNING: Could not reach $HEALTH_URL to confirm the running commit."
    echo "Falling back to local git HEAD — less reliable, won't catch a"
    echo "'code pulled but never reloaded' situation the way /health would."
    RUNNING_SHA_BEFORE=$(git rev-parse HEAD)
fi
echo "Currently serving commit: $RUNNING_SHA_BEFORE"

echo "Pulling latest changes from main..."
git pull origin main

EXPECTED_SHA=$(git rev-parse HEAD)
echo "Target commit: $EXPECTED_SHA"

if [ "$RUNNING_SHA_BEFORE" = "$EXPECTED_SHA" ]; then
    echo "Service is already serving commit $EXPECTED_SHA. Nothing to deploy."
    exit 0
fi

# --- Detect whether this deploy includes new migrations ---
# Compared against what's actually RUNNING, not just what git last had
# checked out — so this still catches migrations from a previous deploy
# that got interrupted before the reload step.
MIGRATIONS_CHANGED=false
if git diff --name-only "$RUNNING_SHA_BEFORE" "$EXPECTED_SHA" -- "$MIGRATIONS_DIR" | grep -q .; then
    MIGRATIONS_CHANGED=true
    echo "This deploy includes new database migration(s)."
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt --quiet

# --- Determine the target schema revision ---
# This reads what the just-pulled code's migration files declare as HEAD,
# not the database's current state — it's "where we're trying to get to,"
# used later to confirm the running service actually gets there after
# migrations run and it's reloaded.
EXPECTED_ALEMBIC_REV=$(alembic heads 2>/dev/null | head -n1 | awk '{print $1}')
if [ -z "$EXPECTED_ALEMBIC_REV" ]; then
    echo "ERROR: Could not determine target schema revision from 'alembic heads'."
    echo "Aborting rather than risk comparing two empty values as if they matched."
    git reset --hard "$RUNNING_SHA_BEFORE"
    pip install -r requirements.txt --quiet
    exit 1
fi
echo "Target schema revision: $EXPECTED_ALEMBIC_REV"

# --- Pre-flight check: does the new code even import? ---
# Cheapest possible safety net. Catches syntax errors, bad imports, broken
# route registration, etc. Nothing has touched migrations or the live
# service yet at this point, so on failure we can just reset the working
# tree and walk away — no rollback machinery needed, no downtime risked.
#
# Wrapped in `timeout` so a genuine hang (e.g. a blocking DB/network call
# made at module level instead of inside a function) fails loudly in a
# bounded time instead of running silently in the background if this
# script's own session gets disconnected mid-check.
PREFLIGHT_TIMEOUT_SECONDS=20
echo "Running pre-flight import check (max ${PREFLIGHT_TIMEOUT_SECONDS}s)..."
timeout "$PREFLIGHT_TIMEOUT_SECONDS" python -c "import app.main" 2>/tmp/mgltickets_preflight_error.log
PREFLIGHT_STATUS=$?

if [ $PREFLIGHT_STATUS -ne 0 ]; then
    echo "ERROR: New code failed to import. Aborting before touching the live service."
    if [ $PREFLIGHT_STATUS -eq 124 ]; then
        echo "This was a TIMEOUT, not an exception — something blocked during import"
        echo "without raising an error (e.g. a DB connection or network call made at"
        echo "module load time rather than inside a function). Check for module-level"
        echo "side effects in the files this deploy touched."
    fi
    echo "--- Captured output/error ---"
    cat /tmp/mgltickets_preflight_error.log
    echo "------------------------------"
    echo "Resetting working tree back to $RUNNING_SHA_BEFORE (service was never touched)..."
    git reset --hard "$RUNNING_SHA_BEFORE"
    pip install -r requirements.txt --quiet
    exit 1
fi
echo "Pre-flight import check passed."

# From here on we've passed the point where a failure is "free" to walk away
# from — migrations or the live service may already be touched. set -e exiting
# the whole script isn't good enough anymore; we need to actively roll back
# instead. So: turn off exit-on-error and check each risky step explicitly.
set +e

# --- Rollback function ---
# Resets code to the previous commit, reinstalls ITS dependencies, reloads
# the service, and confirms it's actually serving again.
#
# Deliberately does NOT touch the database automatically. Whether an
# `alembic downgrade` is safe depends entirely on what that specific
# migration did (some are trivially reversible, some involve data
# transformations that aren't). That's a judgment call for a human, not
# this script — see the warning printed before rollback is called below.
rollback() {
    echo ""
    echo "=== ROLLING BACK code to $RUNNING_SHA_BEFORE ==="
    git reset --hard "$RUNNING_SHA_BEFORE"
    pip install -r requirements.txt --quiet
    sudo systemctl reload "$SERVICE_NAME"

    echo "Verifying rollback is serving $RUNNING_SHA_BEFORE..."
    attempt=1
    while [ $attempt -le $MAX_ATTEMPTS ]; do
        STATE=$(get_running_state)
        RUNNING_SHA="${STATE%%|*}"
        if [ "$RUNNING_SHA" = "$RUNNING_SHA_BEFORE" ]; then
            echo "Rollback confirmed: service is serving $RUNNING_SHA_BEFORE again."
            return 0
        fi
        sleep $SLEEP_SECONDS
        attempt=$((attempt + 1))
    done

    echo "!!! ROLLBACK DID NOT CONFIRM. Service may still be down. !!!"
    echo "!!! Manual intervention required immediately. !!!"
    echo "Recent logs:"
    sudo journalctl -u "$SERVICE_NAME" -n 50 --no-pager
    return 1
}

echo "Running database migrations..."
alembic upgrade head
MIGRATION_STATUS=$?

if [ $MIGRATION_STATUS -ne 0 ]; then
    echo "ERROR: Migration failed (exit code $MIGRATION_STATUS)."
    if [ "$MIGRATIONS_CHANGED" = true ]; then
        echo "NOTE: Alembic runs each revision in its own transaction, so a clean"
        echo "failure should mean the schema was NOT advanced — but confirm with"
        echo "'alembic current' before assuming that's true here."
    fi
    echo "Rolling back code..."
    rollback
    exit 1
fi

echo "Reloading service (hot-swap, zero downtime)..."
sudo systemctl reload "$SERVICE_NAME"

echo "Waiting for service to serve commit $EXPECTED_SHA at schema revision ${EXPECTED_ALEMBIC_REV:-unknown}..."
attempt=1
success=false
while [ $attempt -le $MAX_ATTEMPTS ]; do
    STATE=$(get_running_state)
    RUNNING_SHA="${STATE%%|*}"
    RUNNING_ALEMBIC_REV="${STATE##*|}"

    if [ "$RUNNING_SHA" = "$EXPECTED_SHA" ] && [ "$RUNNING_ALEMBIC_REV" = "$EXPECTED_ALEMBIC_REV" ]; then
        echo "Health check passed on attempt $attempt: serving $RUNNING_SHA at revision $RUNNING_ALEMBIC_REV"
        success=true
        break
    fi

    echo "Attempt $attempt/$MAX_ATTEMPTS: commit='${RUNNING_SHA:-no response}' (want '$EXPECTED_SHA'), revision='${RUNNING_ALEMBIC_REV:-no response}' (want '$EXPECTED_ALEMBIC_REV'). Retrying in ${SLEEP_SECONDS}s..."
    sleep $SLEEP_SECONDS
    attempt=$((attempt + 1))
done

if [ "$success" = false ]; then
    echo "ERROR: Service did not converge on commit $EXPECTED_SHA after $MAX_ATTEMPTS attempts."
    echo "Recent logs:"
    sudo journalctl -u "$SERVICE_NAME" -n 50 --no-pager

    if [ "$MIGRATIONS_CHANGED" = true ]; then
        echo ""
        echo "!!! WARNING: This deploy included database migrations that HAVE"
        echo "!!! ALREADY BEEN APPLIED against the new schema. Rolling back the"
        echo "!!! CODE now will leave the OLD code running against the NEW"
        echo "!!! schema. That combination may itself be broken (missing columns"
        echo "!!! the old code doesn't expect, renamed tables, etc.)."
        echo "!!!"
        echo "!!! Code rollback will proceed below, but you must manually decide"
        echo "!!! whether 'alembic downgrade -1' is safe for THIS migration, and"
        echo "!!! run it yourself if so. This script will not guess."
    fi

    rollback
    exit 1
fi

echo "Checking service status..."
sudo systemctl status "$SERVICE_NAME" --no-pager
echo "Backend deployment complete: $EXPECTED_SHA"