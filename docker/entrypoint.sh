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

exec "$@"
