#!/usr/bin/env python3
"""Idempotent loader: upsert ref_majors from the committed JSONL seed.

    cd unipaith-backend
    PYTHONPATH=src python -m scripts.seed_reference_majors

Reads the committed seed (no raw CSV needed) → runs in any env incl. prod via
``aws ecs run-task``. Safe to re-run (upserts by cip_code).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os

from unipaith.database import async_session
from unipaith.services.reference_majors_ingest import upsert_majors

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_reference_majors")

SEED = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "reference",
    "ref_majors.jsonl",
)


async def seed() -> None:
    if not os.path.exists(SEED):
        logger.error("seed file not found: %s", SEED)
        return
    with open(SEED, encoding="utf-8") as fh:
        records = [json.loads(line) for line in fh if line.strip()]
    async with async_session() as db:
        written = await upsert_majors(db, records)
    logger.info("seeded %d reference majors", written)


if __name__ == "__main__":
    asyncio.run(seed())
