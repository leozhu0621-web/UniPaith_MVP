#!/usr/bin/env python3
"""Idempotent linker: write the CIP<->SOC crosswalk onto ref_majors / ref_occupations.

    cd unipaith-backend
    PYTHONPATH=src python -m scripts.seed_reference_crosswalk

Run AFTER ref_majors + ref_occupations are seeded. Reads the committed crosswalk seed and
denormalizes it onto the existing rows (related_occupations / related_majors). Idempotent.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os

from unipaith.database import async_session
from unipaith.services.reference_crosswalk_ingest import link_crosswalk

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_reference_crosswalk")

SEED = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "reference",
    "ref_cip_soc.jsonl",
)


async def seed() -> None:
    if not os.path.exists(SEED):
        logger.error("seed file not found: %s", SEED)
        return
    with open(SEED, encoding="utf-8") as fh:
        pairs = [json.loads(line) for line in fh if line.strip()]
    async with async_session() as db:
        result = await link_crosswalk(db, pairs)
    logger.info(
        "linked crosswalk: %d majors, %d occupations",
        result["majors_linked"],
        result["occupations_linked"],
    )


if __name__ == "__main__":
    asyncio.run(seed())
