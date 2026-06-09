"""Ops endpoint to refresh channel-sourced Events/Updates from public feeds.

System-guarded (``X-Ops-Token``, like the crawler/feedback ops APIs). A daily
scheduler can hit this; ops can trigger an ad-hoc / single-institution refresh.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_system
from unipaith.models.institution import Institution
from unipaith.services.content_ingest import ContentIngestService

router = APIRouter(prefix="/admin/content-ingest", tags=["content-ingest"])


@router.post("/refresh")
async def refresh_channel_content(
    _: bool = Depends(require_system),
    institution_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Pull configured news/events feeds into Events/Updates. One school or all."""
    svc = ContentIngestService(db)
    if institution_id is not None:
        inst = await db.scalar(select(Institution).where(Institution.id == institution_id))
        if inst is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found"
            )
        counts = await svc.ingest_institution(inst)
        await db.commit()
        return {"institution_id": str(institution_id), **counts}
    totals = await svc.ingest_all()
    await db.commit()
    return totals
