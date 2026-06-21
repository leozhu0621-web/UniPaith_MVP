#!/bin/bash
set -e

echo "=== UniPaith Backend Starting ==="
echo "Environment: ${ENVIRONMENT:-development}"

# Schema pre-recovery (runs BEFORE alembic).
# A prior failed deploy can leave a migration "stamped without running" (the
# nuclear recovery below), so its ORM-mapped columns are missing while alembic
# believes they exist — 500-ing every institution/program read. A plain
# `alembic upgrade` cannot self-heal that, and the intervening per-credential
# data migrations `select(Institution)` + backfill, so they FAIL on the missing
# columns before any tail recovery can run. Ensure those columns exist FIRST,
# with pure idempotent `ADD COLUMN IF NOT EXISTS` (shared with the deepintelfix1
# migration). Best-effort: never abort startup if this can't connect.
echo "Ensuring recovery columns exist (pre-migration)..."
python - <<'PY' || echo "  (recovery-column pre-step skipped — continuing)"
import asyncio
import os
import re

import asyncpg

from unipaith.recovery_ddl import RECOVERY_STATEMENTS


async def _run() -> None:
    url = os.environ["DATABASE_URL"]
    clean = re.sub(r"^postgresql\+asyncpg://", "postgresql://", url)
    clean = re.sub(r"^postgres\+asyncpg://", "postgres://", clean)
    conn = await asyncpg.connect(clean)
    try:
        for statement in RECOVERY_STATEMENTS:
            await conn.execute(statement)
        print(f"  Ensured {len(RECOVERY_STATEMENTS)} recovery statements.")
    finally:
        await conn.close()


asyncio.run(_run())
PY

# Run database migrations.
# Retry first: most upgrade failures here are transient — a brief DB blip, or two
# deploys racing migrations (a momentary dual-head). Retrying lets the DB settle
# BEFORE the nuclear drop+stamp recovery below, which marks every migration
# "applied" WITHOUT running it and would silently freeze data-only migrations
# (this exact masking once froze the program catalog).
echo "Running Alembic migrations..."
migrated=""
for attempt in 1 2 3; do
  if alembic upgrade heads; then
    echo "Migrations complete (attempt ${attempt})."
    migrated="yes"
    break
  fi
  echo "Alembic upgrade attempt ${attempt} failed; retrying in 5s..."
  sleep 5
done

if [ -z "${migrated}" ]; then
  echo "WARNING: Alembic migration still failing after retries. DB may have unknown/divergent revision."
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
