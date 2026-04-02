"""Admin API for the knowledge engine.

Endpoints for controlling and monitoring the perpetual knowledge engine:
- Engine status and stats
- RPM throttle control
- Steering directives (topic/geo/entity priorities)
- Bias controls (source diversity, credibility weighting)
- Manual triggers
- Live activity feed
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_admin
from unipaith.models.knowledge import (
    CrawlFrontier,
    EngineDirective,
    KnowledgeDocument,
)
from unipaith.models.user import User
from unipaith.services.engine_loop import EngineLoop, get_engine_state

router = APIRouter(prefix="/admin/knowledge", tags=["admin-knowledge"])


class ThrottleRequest(BaseModel):
    rpm: int


class DirectiveRequest(BaseModel):
    directive_type: str
    directive_key: str
    directive_value: dict[str, Any] = {}
    description: str | None = None
    priority: int = 50


class DirectiveUpdateRequest(BaseModel):
    directive_value: dict[str, Any] | None = None
    is_active: bool | None = None
    priority: int | None = None
    description: str | None = None


@router.get("/status")
async def engine_status(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    loop = EngineLoop(db)
    return await loop.get_stats()


@router.post("/throttle")
async def set_throttle(
    body: ThrottleRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    rpm = max(1, min(100, body.rpm))
    state = get_engine_state()
    state.rpm = rpm

    existing = await db.execute(
        select(EngineDirective).where(
            EngineDirective.directive_type == "throttle",
            EngineDirective.directive_key == "rpm",
        )
    )
    directive = existing.scalar_one_or_none()
    if directive:
        directive.directive_value = {"rpm": rpm}
        directive.is_active = True
    else:
        db.add(
            EngineDirective(
                directive_type="throttle",
                directive_key="rpm",
                directive_value={"rpm": rpm},
                description=f"RPM set to {rpm} by admin",
                created_by=admin.id,
            )
        )
    await db.flush()
    return {"rpm": rpm, "status": "applied"}


@router.post("/pause")
async def pause_engine(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    state = get_engine_state()
    state.paused = True
    return {"status": "paused"}


@router.post("/resume")
async def resume_engine(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    state = get_engine_state()
    state.paused = False
    return {"status": "resumed"}


@router.post("/trigger-tick")
async def trigger_tick(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    loop = EngineLoop(db)
    result = await loop.run_tick()
    await db.commit()
    return result


@router.post("/trigger-discovery")
async def trigger_discovery(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from unipaith.crawler.source_discoverer import SourceDiscoverer

    discoverer = SourceDiscoverer(db)
    result = await discoverer.run_discovery_cycle(max_new_urls=50)
    await db.commit()
    return result


@router.get("/directives")
async def list_directives(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EngineDirective).order_by(
            EngineDirective.is_active.desc(),
            EngineDirective.priority.desc(),
        )
    )
    directives = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "directive_type": d.directive_type,
            "directive_key": d.directive_key,
            "directive_value": d.directive_value,
            "description": d.description,
            "priority": d.priority,
            "is_active": d.is_active,
            "expires_at": d.expires_at.isoformat() if d.expires_at else None,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in directives
    ]


@router.post("/directives")
async def create_directive(
    body: DirectiveRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    directive = EngineDirective(
        directive_type=body.directive_type,
        directive_key=body.directive_key,
        directive_value=body.directive_value,
        description=body.description,
        priority=body.priority,
        created_by=admin.id,
    )
    db.add(directive)
    await db.flush()
    return {"id": str(directive.id), "status": "created"}


@router.patch("/directives/{directive_id}")
async def update_directive(
    directive_id: UUID,
    body: DirectiveUpdateRequest,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(EngineDirective).where(EngineDirective.id == directive_id))
    directive = result.scalar_one_or_none()
    if not directive:
        from unipaith.core.exceptions import NotFoundException

        raise NotFoundException("Directive not found")

    if body.directive_value is not None:
        directive.directive_value = body.directive_value
    if body.is_active is not None:
        directive.is_active = body.is_active
    if body.priority is not None:
        directive.priority = body.priority
    if body.description is not None:
        directive.description = body.description

    await db.flush()
    return {"id": str(directive.id), "status": "updated"}


@router.get("/documents/recent")
async def recent_documents(
    limit: int = 20,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc()).limit(limit)
    )
    docs = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "title": d.title,
            "source_url": d.source_url,
            "source_domain": d.source_domain,
            "content_format": d.content_format,
            "content_type": d.content_type,
            "quality_score": d.quality_score,
            "processing_status": d.processing_status,
            "word_count": d.word_count,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in docs
    ]


@router.get("/frontier")
async def frontier_status(
    status: str | None = None,
    limit: int = 20,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(CrawlFrontier)
        .order_by(
            CrawlFrontier.priority.desc(),
            CrawlFrontier.created_at.desc(),
        )
        .limit(limit)
    )
    if status:
        query = query.where(CrawlFrontier.status == status)

    result = await db.execute(query)
    items = result.scalars().all()
    return [
        {
            "id": str(f.id),
            "url": f.url,
            "domain": f.domain,
            "priority": f.priority,
            "status": f.status,
            "crawl_count": f.crawl_count,
            "discovery_method": f.discovery_method,
            "last_crawled_at": f.last_crawled_at.isoformat() if f.last_crawled_at else None,
            "consecutive_failures": f.consecutive_failures,
        }
        for f in items
    ]


@router.post("/frontier/add")
async def add_to_frontier(
    url: str,
    priority: int = 50,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from unipaith.crawler.source_discoverer import SourceDiscoverer

    discoverer = SourceDiscoverer(db)
    item = await discoverer.add_to_frontier(
        url=url,
        priority=priority,
        discovery_method="admin_manual",
    )
    if not item:
        return {"status": "skipped", "reason": "duplicate or excluded"}
    await db.flush()
    return {"id": str(item.id), "status": "added"}


# ─── Advisor Persona ───


class PersonaUpdateRequest(BaseModel):
    warmth: int | None = None
    directness: int | None = None
    formality: int | None = None
    challenge_level: int | None = None
    data_reference_frequency: int | None = None
    humor: int | None = None
    proactivity: int | None = None
    empathy_depth: int | None = None
    custom_instructions: str | None = None
    base_persona_prompt: str | None = None


@router.get("/persona")
async def get_persona(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from unipaith.models.knowledge import AdvisorPersona

    result = await db.execute(
        select(AdvisorPersona).where(AdvisorPersona.is_active.is_(True)).limit(1)
    )
    persona = result.scalar_one_or_none()
    if not persona:
        return {"status": "no_active_persona"}
    return {
        "id": str(persona.id),
        "name": persona.name,
        "warmth": persona.warmth,
        "directness": persona.directness,
        "formality": persona.formality,
        "challenge_level": persona.challenge_level,
        "data_reference_frequency": persona.data_reference_frequency,
        "humor": persona.humor,
        "proactivity": persona.proactivity,
        "empathy_depth": persona.empathy_depth,
        "custom_instructions": persona.custom_instructions,
        "base_persona_prompt": persona.base_persona_prompt,
    }


@router.put("/persona")
async def update_persona(
    body: PersonaUpdateRequest,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from unipaith.models.knowledge import AdvisorPersona

    result = await db.execute(
        select(AdvisorPersona).where(AdvisorPersona.is_active.is_(True)).limit(1)
    )
    persona = result.scalar_one_or_none()
    if not persona:
        from unipaith.core.exceptions import NotFoundException
        raise NotFoundException("No active persona found")

    for field_name in [
        "warmth", "directness", "formality", "challenge_level",
        "data_reference_frequency", "humor", "proactivity", "empathy_depth",
        "custom_instructions", "base_persona_prompt",
    ]:
        val = getattr(body, field_name, None)
        if val is not None:
            if isinstance(val, int):
                val = max(0, min(100, val))
            setattr(persona, field_name, val)

    await db.flush()
    return {"status": "updated", "id": str(persona.id)}


@router.get("/insights/{user_id}")
async def get_person_insights(
    user_id: UUID,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    from unipaith.models.knowledge import PersonInsight

    result = await db.execute(
        select(PersonInsight)
        .where(PersonInsight.user_id == user_id, PersonInsight.is_active.is_(True))
        .order_by(PersonInsight.confidence.desc())
        .limit(30)
    )
    insights = result.scalars().all()
    return [
        {
            "id": str(i.id),
            "insight_type": i.insight_type,
            "insight_text": i.insight_text,
            "confidence": i.confidence,
            "source": i.source,
            "created_at": i.created_at.isoformat() if i.created_at else None,
        }
        for i in insights
    ]
