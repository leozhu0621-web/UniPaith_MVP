"""Ops endpoint: POST /ops/airtable/sync

System-guarded (``X-Ops-Token``, same guard as the crawler/content-ingest ops
APIs). Pulls Prompt Library prompts + Session Templates from the configured
Airtable base and upserts them into the DB.

Safe/inert when Airtable credentials are not configured — returns
``{"skipped": "airtable not configured"}`` without writing anything.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.database import get_db
from unipaith.dependencies import require_system
from unipaith.services.airtable.client import AirtableClient
from unipaith.services.airtable.sync_service import AirtableSyncService

router = APIRouter(prefix="/ops/airtable", tags=["ops-airtable"])


@router.post("/sync")
async def airtable_sync(
    _: bool = Depends(require_system),
    db: AsyncSession = Depends(get_db),
):
    """Pull Prompt Library + Session Templates from Airtable and upsert.

    Returns a summary of what was upserted / rejected.  Safe to call when
    Airtable credentials are absent — returns a ``skipped`` marker.
    """
    client = AirtableClient(
        api_key=settings.airtable_api_key,
        base_id=settings.airtable_base_id,
    )
    async with client:
        result = await AirtableSyncService(db, client).sync_all()

    await db.commit()
    return result
