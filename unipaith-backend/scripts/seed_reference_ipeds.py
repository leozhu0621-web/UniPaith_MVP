#!/usr/bin/env python3
"""Idempotent loader: merge IPEDS admissions into ref_institutions.extra.

    cd unipaith-backend
    PYTHONPATH=src python -m scripts.seed_reference_ipeds

Run AFTER ref_institutions is seeded. Reads the committed seed and merges the ipeds_admissions
object into each matching institution's extra JSONB (unmatched unitids skipped). Idempotent.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os

from unipaith.database import async_session
from unipaith.services.reference_ipeds_ingest import upsert_ipeds_admissions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_reference_ipeds")

SEED = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "reference",
    "ref_ipeds_admissions.jsonl",
)


async def seed() -> None:
    if not os.path.exists(SEED):
        logger.error("seed file not found: %s", SEED)
        return
    with open(SEED, encoding="utf-8") as fh:
        records = [json.loads(line) for line in fh if line.strip()]
    async with async_session() as db:
        linked = await upsert_ipeds_admissions(db, records)
    logger.info("enriched %d institutions with IPEDS admissions", linked)


if __name__ == "__main__":
    asyncio.run(seed())
