"""Pipeline admin API.

Endpoints for monitoring and controlling the continuous pipeline:
- Status (per-stage snapshots, queue depths, budget)
- Toggle (on/off)
- Throttle (budget $/hr)
- Config (live-editable key-value pairs)
- Force actions (discovery, train, flush failed)
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_admin
from unipaith.models.knowledge import CrawlFrontier, KnowledgeDocument
from unipaith.models.ml_loop import OutcomeRecord
from unipaith.models.pipeline import PipelineConfig, PipelineStageSnapshot

router = APIRouter(prefix="/admin/pipeline", tags=["pipeline"])


class ToggleRequest(BaseModel):
    enabled: bool


class ThrottleRequest(BaseModel):
    budget_per_hour: float


class ConfigPatch(BaseModel):
    updates: dict[str, Any]


class ForceRequest(BaseModel):
    action: str


@router.get("/status")
async def pipeline_status(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
) -> dict:
    stages: dict[str, Any] = {}
    for stage_name in ("crawl", "extract", "ml"):
        snap = await db.get(PipelineStageSnapshot, stage_name)
        if snap:
            stages[stage_name] = {
                "status": snap.status,
                "last_activity_at": (
                    snap.last_activity_at.isoformat() if snap.last_activity_at else None
                ),
                "items_processed_total": snap.items_processed_total,
                "items_processed_hour": snap.items_processed_hour,
                "queue_depth": snap.queue_depth,
                "last_error": snap.last_error,
                "extra": snap.extra_json,
                "worker_heartbeat_at": (
                    snap.worker_heartbeat_at.isoformat() if snap.worker_heartbeat_at else None
                ),
                "worker_hostname": snap.worker_hostname,
                "budget_spent_this_hour": snap.budget_spent_this_hour,
                "budget_per_hour": snap.budget_per_hour,
            }
        else:
            stages[stage_name] = {"status": "not_started"}

    raw_count = (
        await db.scalar(
            select(func.count())
            .select_from(KnowledgeDocument)
            .where(KnowledgeDocument.processing_status == "raw")
        )
        or 0
    )

    completed_count = (
        await db.scalar(
            select(func.count())
            .select_from(KnowledgeDocument)
            .where(KnowledgeDocument.processing_status == "completed")
        )
        or 0
    )

    frontier_pending = (
        await db.scalar(
            select(func.count()).select_from(CrawlFrontier).where(CrawlFrontier.status == "pending")
        )
        or 0
    )

    outcome_count = await db.scalar(select(func.count()).select_from(OutcomeRecord)) or 0

    from unipaith.services.pipeline import get_pipeline

    pipeline = get_pipeline()

    return {
        "enabled": pipeline.enabled,
        "stages": stages,
        "totals": {
            "raw_docs_queued": raw_count,
            "docs_completed": completed_count,
            "frontier_pending": frontier_pending,
            "outcome_count": outcome_count,
        },
        "budget": {
            "per_hour": pipeline.budget_gate.budget_per_hour,
            "spent_this_hour": pipeline.budget_gate.spent_this_hour,
        },
    }


@router.post("/toggle")
async def pipeline_toggle(
    body: ToggleRequest,
    _=Depends(require_admin),
) -> dict:
    from unipaith.services.pipeline import get_pipeline

    pipeline = get_pipeline()
    pipeline.enabled = body.enabled
    return {"enabled": pipeline.enabled}


@router.post("/throttle")
async def pipeline_throttle(
    body: ThrottleRequest,
    _=Depends(require_admin),
) -> dict:
    from unipaith.services.pipeline import get_pipeline

    pipeline = get_pipeline()
    pipeline.budget_gate.budget_per_hour = body.budget_per_hour
    return {"budget_per_hour": pipeline.budget_gate.budget_per_hour}


@router.get("/config")
async def pipeline_config_get(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
) -> dict:
    result = await db.execute(select(PipelineConfig))
    rows = result.scalars().all()
    return {
        "config": {
            row.key: {
                "value": row.value_json,
                "description": row.description,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                "updated_by": row.updated_by,
            }
            for row in rows
        }
    }


@router.patch("/config")
async def pipeline_config_patch(
    body: ConfigPatch,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
) -> dict:
    updated = []
    for key, value in body.updates.items():
        row = await db.get(PipelineConfig, key)
        if row is None:
            row = PipelineConfig(key=key)
            db.add(row)
        row.value_json = value if isinstance(value, dict) else {"value": value}
        row.updated_by = "admin"
        updated.append(key)
    await db.flush()
    return {"updated": updated}


@router.post("/force")
async def pipeline_force(
    body: ForceRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
) -> dict:
    action = body.action

    if action == "discover":
        from unipaith.crawler.source_discoverer import SourceDiscoverer

        discoverer = SourceDiscoverer(db)
        result = await discoverer.run_discovery_cycle(max_new_urls=50)
        return {"action": "discover", "result": result}

    if action == "train":
        from unipaith.ml.orchestrator import MLOrchestrator

        orch = MLOrchestrator(db)
        result = await orch.run_full_cycle(triggered_by="admin_force")
        return {"action": "train", "result": result}

    if action == "flush_failed":
        from sqlalchemy import update

        count = await db.execute(
            update(KnowledgeDocument)
            .where(KnowledgeDocument.processing_status == "failed")
            .values(processing_status="raw")
        )
        return {"action": "flush_failed", "reset_count": count.rowcount}

    return {"error": f"Unknown action: {action}"}
