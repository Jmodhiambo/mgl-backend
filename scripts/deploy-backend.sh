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

# --- Capture the rollback target BEFORE we change anything ---
# This is whatever commit is currently live. If anything downstream fails,
# this is what we reset back to.
PREVIOUS_SHA=$(git rev-parse HEAD)
echo "Currently deployed commit: $PREVIOUS_SHA"

echo "Pulling latest changes from main..."
git pull origin main

EXPECTED_SHA=$(git rev-parse HEAD)
echo "Deploying commit: $EXPECTED_SHA"

if [ "$PREVIOUS_SHA" = "$EXPECTED_SHA" ]; then
    echo "Already up to date. Nothing to deploy."
    exit 0
fi

# --- Detect whether this deploy includes new migrations ---
# We use this later purely to decide how scary the warning message should be
# if we end up rolling back after migrations have already run.
MIGRATIONS_CHANGED=false
if git diff --name-only "$PREVIOUS_SHA" "$EXPECTED_SHA" -- "$MIGRATIONS_DIR" | grep -q .; then
    MIGRATIONS_CHANGED=true
    echo "This deploy includes new database migration(s)."
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt --quiet

# --- Pre-flight check: does the new code even import? ---
# Cheapest possible safety net. Catches syntax errors, bad imports, broken
# route registration, etc. — exactly the class of bug that's broken prod
# twice now. Nothing has touched migrations or the live service yet at this
# point, so on failure we can just reset the working tree and walk away —
# no rollback machinery needed, no downtime risked.
echo "Running pre-flight import check..."
if ! python -c "import app.main" 2>/tmp/mgltickets_preflight_error.log; then
    echo "ERROR: New code failed to import. Aborting before touching the live service."
    echo "--- Import error ---"
    cat /tmp/mgltickets_preflight_error.log
    echo "---------------------"
    echo "Resetting working tree back to $PREVIOUS_SHA (service was never touched)..."
    git reset --hard "$PREVIOUS_SHA"
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
    echo "=== ROLLING BACK code to $PREVIOUS_SHA ==="
    git reset --hard "$PREVIOUS_SHA"
    pip install -r requirements.txt --quiet
    sudo systemctl reload "$SERVICE_NAME"

    echo "Verifying rollback is serving $PREVIOUS_SHA..."
    attempt=1
    while [ $attempt -le $MAX_ATTEMPTS ]; do
        RESPONSE=$(curl --silent --max-time 3 "$HEALTH_URL" || echo "")
        RUNNING_SHA=$(echo "$RESPONSE" | grep -o '"commit":"[^"]*"' | cut -d'"' -f4)
        if [ "$RUNNING_SHA" = "$PREVIOUS_SHA" ]; then
            echo "Rollback confirmed: service is serving $PREVIOUS_SHA again."
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

echo "Waiting for service to serve commit $EXPECTED_SHA..."
attempt=1
success=false
while [ $attempt -le $MAX_ATTEMPTS ]; do
    RESPONSE=$(curl --silent --max-time 3 "$HEALTH_URL" || echo "")
    RUNNING_SHA=$(echo "$RESPONSE" | grep -o '"commit":"[^"]*"' | cut -d'"' -f4)

    if [ "$RUNNING_SHA" = "$EXPECTED_SHA" ]; then
        echo "Health check passed on attempt $attempt: serving $RUNNING_SHA"
        success=true
        break
    fi

    echo "Attempt $attempt/$MAX_ATTEMPTS: got '${RUNNING_SHA:-no response}', want '$EXPECTED_SHA'. Retrying in ${SLEEP_SECONDS}s..."
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