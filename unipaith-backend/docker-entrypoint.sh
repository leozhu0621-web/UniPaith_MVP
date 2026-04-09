#!/bin/bash
set -e

echo "=== UniPaith Backend Starting ==="
echo "Environment: ${ENVIRONMENT:-development}"

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
