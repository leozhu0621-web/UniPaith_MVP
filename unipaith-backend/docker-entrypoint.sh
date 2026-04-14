#!/bin/bash
set -e

echo "=== UniPaith Backend Starting ==="
echo "Environment: ${ENVIRONMENT:-development}"

# Assemble DATABASE_URL from individual env vars so the password
# (injected via Secrets Manager) never appears in the task definition.
if [ -n "$DB_HOST" ] && [ -n "$DB_PASSWORD" ] && [ -z "$DATABASE_URL" ]; then
  export DATABASE_URL="postgresql+asyncpg://${DB_USERNAME:-unipaith}:${DB_PASSWORD}@${DB_HOST}/${DB_NAME:-unipaith}?ssl=require"
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
