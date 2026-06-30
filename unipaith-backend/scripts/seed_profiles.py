#!/usr/bin/env python3
"""Idempotently seed university profiles into the database — the canonical data path.

Run this instead of writing a per-university Alembic *data* migration. Profiles use
a **sync** SQLAlchemy ``Session`` (that is how they are called from migrations), so
we bridge through the project's async engine exactly like ``alembic/env.py`` does
(``conn.run_sync(...)``) — no separate sync driver required.

Usage:
    python -m scripts.seed_profiles                # all profiles
    python -m scripts.seed_profiles mit yale ucla  # a subset

Idempotent: each profile UPSERTs its own university, so re-running is safe.
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy.orm import Session

from unipaith.data.profiles import seed_all
from unipaith.database import engine


async def _run(slugs: list[str] | None) -> dict[str, bool]:
    # Mirror alembic/env.py: open the async engine, bridge to a sync Session via
    # run_sync, and let the surrounding transaction commit on success.
    async with engine.begin() as conn:
        return await conn.run_sync(lambda sync_conn: seed_all(Session(bind=sync_conn), slugs=slugs))


def main(argv: list[str]) -> int:
    slugs = argv or None
    results = asyncio.run(_run(slugs))
    changed = [s for s, c in results.items() if c]
    print(
        f"Seeded {len(results)} profile(s); {len(changed)} changed: {', '.join(changed) or 'none'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
