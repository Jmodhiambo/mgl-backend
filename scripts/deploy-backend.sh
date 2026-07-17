#!/bin/bash
set -e  # Exit immediately if any command fails

echo "Starting backend deployment..."
cd /var/www/mgltickets/mgl-backend

echo "Pulling latest changes from main..."
git pull origin main

# SHA stands for Secure Hash Algorithm — but in this context we're using it (git),
# it just means "the unique ID git gives to a commit."
EXPECTED_SHA=$(git rev-parse HEAD)
echo "Deploying commit: $EXPECTED_SHA"

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt --quiet

echo "Running database migrations..."
alembic upgrade head

echo "Reloading service (hot-swap, zero downtime)..."
sudo systemctl reload mgltickets

echo "Waiting for service to serve commit $EXPECTED_SHA..."
HEALTH_URL="http://127.0.0.1:8000/health"
MAX_ATTEMPTS=15
SLEEP_SECONDS=2
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
    echo "Old workers may still be serving requests, or the new workers failed to start."
    echo "Recent logs:"
    sudo journalctl -u mgltickets -n 50 --no-pager
    exit 1
fi

echo "Checking service status..."
sudo systemctl status mgltickets --no-pager

echo "Backend deployment complete."