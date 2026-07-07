#!/bin/sh
# Waits for the database, applies migrations, then runs the CMD.
set -e

echo "Applying database migrations (retrying while the database starts)..."
tries=0
until python manage.py migrate --noinput; do
    tries=$((tries + 1))
    if [ "$tries" -ge 12 ]; then
        echo "Database not reachable after ${tries} attempts; giving up." >&2
        exit 1
    fi
    sleep 5
done

# Optional one-shot demo bootstrap for hosts without a shell (e.g. Render Free).
# Idempotent and run in the background so it never blocks startup or health
# checks; after the first boot it finds everything present and returns fast.
if [ "${SEED_DEMO_DATA:-}" = "true" ]; then
    echo "SEED_DEMO_DATA=true: ensuring demo data in the background..."
    (python manage.py ensure_demo_seed || echo "demo seed failed (continuing)") &
fi

exec "$@"
