#!/bin/bash
set -e

echo "=== UniPaith Backend Starting ==="
echo "Environment: ${ENVIRONMENT:-development}"

# Build DATABASE_URL at runtime from secrets (avoids plaintext password in task definition)
if [ -n "$DB_PASSWORD" ] && [ -n "$DB_HOST" ] && [ -z "$DATABASE_URL" ]; then
  export DATABASE_URL="postgresql+asyncpg://${DB_USER:-unipaith}:${DB_PASSWORD}@${DB_HOST}/${DB_NAME:-unipaith}?ssl=require"
  echo "DATABASE_URL constructed from DB_* components."
fi

# Run database migrations
echo "Running Alembic migrations..."
if alembic upgrade head; then
  echo "Migrations complete."
else
  echo "WARNING: Alembic migration failed (exit $?). Attempting stamp head and retry..."
  alembic stamp head
  echo "Stamped head. Proceeding with startup (some columns may be missing)."
fi

# Execute the main command (uvicorn)
exec "$@"
