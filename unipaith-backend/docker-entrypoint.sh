#!/bin/bash
set -e

echo "=== UniPaith Backend Starting ==="
echo "Environment: ${ENVIRONMENT:-development}"

# Run database migrations
echo "Running Alembic migrations..."
alembic upgrade head
echo "Migrations complete."

# Execute the main command (uvicorn)
exec "$@"
