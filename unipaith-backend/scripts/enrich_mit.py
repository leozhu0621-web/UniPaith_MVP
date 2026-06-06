"""One-off: enrich MIT to the canonical profile. Idempotent.

The Alembic data migration (mitprof1a2b3c) ships this automatically on deploy;
this script is for running the same enrichment by hand against a dev DB or any
environment whose DATABASE_URL is set:

    cd unipaith-backend && set -a && . ./.env && set +a && \
        PYTHONPATH=src .venv/bin/python -m scripts.enrich_mit

Prints a notice and changes nothing if MIT is not present.
"""

import asyncio
import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from unipaith.data import mit_profile


async def _run() -> bool:
    engine = create_async_engine(os.environ["DATABASE_URL"])
    try:
        async with AsyncSession(engine) as session:
            # apply() is sync (shared with the Alembic migration); run it over
            # the async connection via run_sync, then commit.
            changed = await session.run_sync(mit_profile.apply)
            await session.commit()
        return changed
    finally:
        await engine.dispose()


def main() -> None:
    changed = asyncio.run(_run())
    print("MIT enriched." if changed else "MIT not found — no-op.")


if __name__ == "__main__":
    main()
