#!/bin/bash
# SyncScript Backend Entrypoint Script
# Handles migrations, static files, and server startup

set -e

echo "=== SyncScript Backend Startup ==="

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z ${DB_HOST:-db} ${DB_PORT:-5432}; do
    sleep 1
done
echo "PostgreSQL is ready!"

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! nc -z ${REDIS_HOST:-redis} ${REDIS_PORT:-6379}; do
    sleep 1
done
echo "Redis is ready!"

# Run database migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files (only in production, skip for celery workers)
if [ "$DEBUG" != "True" ] && [[ "$1" != *"celery"* ]]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput --clear || echo "Warning: collectstatic failed, continuing..."
fi

# Create cache table if needed
echo "Ensuring cache table exists..."
python manage.py createcachetable --dry-run 2>/dev/null || python manage.py createcachetable 2>/dev/null || true

echo "=== Starting Server ==="

# Execute the main command
exec "$@"
