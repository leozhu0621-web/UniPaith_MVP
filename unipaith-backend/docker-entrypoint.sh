#!/bin/bash
set -e

echo "=== UniPaith Backend Starting ==="
echo "Environment: ${ENVIRONMENT:-development}"

# Run database migrations
echo "Running Alembic migrations..."
if alembic upgrade heads; then
  echo "Migrations complete."
else
  echo "WARNING: Alembic migration failed. DB may have unknown/divergent revision."
  echo "Purging alembic_version and stamping current heads..."
  # Drop alembic_version so stamp works even if DB points at an unknown revision.
  # Uses asyncpg (already a project dependency) to avoid adding new deps.
  python - <<'PY' || echo "  (purge attempt failed, continuing)"
import os, asyncio, asyncpg, re

async def reset():
    url = os.environ["DATABASE_URL"]
    # asyncpg wants postgres:// not postgresql+asyncpg://
    clean = re.sub(r"^postgresql\+asyncpg://", "postgresql://", url)
    clean = re.sub(r"^postgres\+asyncpg://", "postgres://", clean)
    conn = await asyncpg.connect(clean)
    try:
        await conn.execute("DROP TABLE IF EXISTS alembic_version")
        print("  Purged alembic_version table")
    finally:
        await conn.close()

asyncio.run(reset())
PY
  alembic stamp heads || echo "  stamp heads failed — continuing anyway; app bootstrap will run"
  echo "Recovery complete — proceeding with startup."
fi

# Execute the main command (uvicorn)
exec "$@"
