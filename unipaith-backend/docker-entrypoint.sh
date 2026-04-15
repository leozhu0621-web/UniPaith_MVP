#!/bin/bash
set -e

echo "=== UniPaith Backend Starting ==="
echo "Environment: ${ENVIRONMENT:-development}"

# Run database migrations
echo "Running Alembic migrations..."
if alembic upgrade heads; then
  echo "Migrations complete."
else
  echo "WARNING: Alembic migration failed (exit $?). Attempting stamp heads and retry..."
  alembic stamp heads
  echo "Stamped heads. Proceeding with startup (some columns may be missing)."
fi

# Execute the main command (uvicorn)
exec "$@"
