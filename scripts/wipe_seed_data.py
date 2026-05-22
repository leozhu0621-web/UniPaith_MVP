"""Wipe seeded program-library inventory (institutions + programs, cascade).

The program crawler + the NYU seed set were removed; the program library is
now sourced from institution Data Upload / direct creation. Run this against
any database you want to reset to an empty library ("start clean").

It TRUNCATEs `institutions` and `programs` with CASCADE, which also removes
everything that hangs off them (schools, intake rounds, posts, events,
campaigns, applications, match results, saved-list items, reviews, etc.).
Student accounts and profiles are NOT touched.

Usage (from repo root):
    # show the target DB without changing anything
    unipaith-backend/.venv/bin/python scripts/wipe_seed_data.py
    # actually wipe
    unipaith-backend/.venv/bin/python scripts/wipe_seed_data.py --confirm

The target database comes from the app config (DATABASE_URL). To clean prod,
point DATABASE_URL at prod (e.g. via a one-off ECS task or an authorized
tunnel) and re-run with --confirm.
"""

from __future__ import annotations

import argparse
import asyncio

from sqlalchemy import text

from unipaith.config import settings
from unipaith.database import async_session


async def _wipe() -> None:
    async with async_session() as db:
        await db.execute(text("TRUNCATE institutions, programs RESTART IDENTITY CASCADE"))
        await db.commit()
    print("Done. Program library is now empty (institutions + programs wiped, cascade).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Wipe program-library inventory.")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required to actually wipe. Without it, prints the target DB and exits.",
    )
    args = parser.parse_args()

    try:
        host = settings.database_url.rsplit("@", 1)[-1]
    except Exception:
        host = "(from app config)"
    print(f"Target database: {host}")

    if not args.confirm:
        print("Dry run — pass --confirm to actually wipe institutions + programs.")
        return

    asyncio.run(_wipe())


if __name__ == "__main__":
    main()
