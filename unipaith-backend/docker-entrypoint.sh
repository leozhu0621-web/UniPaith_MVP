#!/bin/bash
set -e

echo "=== UniPaith Backend Starting ==="
echo "Environment: ${ENVIRONMENT:-development}"

# Run database migrations
echo "Running Alembic migrations..."
if alembic upgrade head; then
  echo "Migrations complete."
else
  exit_code=$?
  echo "ERROR: Alembic migration failed (exit $exit_code). Aborting startup."
  exit $exit_code
fi

# Execute the main command (uvicorn)
exec "$@"
