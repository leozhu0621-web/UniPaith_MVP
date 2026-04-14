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
from pydantic import BaseModel, Field
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


class PersonaChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


@router.post("/persona/chat")
async def chat_tune_persona(
    body: PersonaChatRequest,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Chat-based persona tuning. Send a natural language instruction like
    'be more direct and less warm' and the LLM translates it into slider changes."""
    import json as _json

    from unipaith.ai.llm_client import get_llm_client
    from unipaith.config import settings
    from unipaith.models.knowledge import AdvisorPersona

    result = await db.execute(
        select(AdvisorPersona).where(AdvisorPersona.is_active.is_(True)).limit(1)
    )
    persona = result.scalar_one_or_none()
    if not persona:
        from unipaith.core.exceptions import NotFoundException
        raise NotFoundException("No active persona found")

    current = {
        "warmth": persona.warmth,
        "directness": persona.directness,
        "formality": persona.formality,
        "challenge_level": persona.challenge_level,
        "data_reference_frequency": persona.data_reference_frequency,
        "humor": persona.humor,
        "proactivity": persona.proactivity,
        "empathy_depth": persona.empathy_depth,
        "custom_instructions": persona.custom_instructions or "",
    }

    system = (
        "You are a persona tuning assistant. The admin describes how they want "
        "the AI counselor to behave. "
        "You translate their instruction into specific slider changes.\n\n"
        "Current persona settings (each 0-100):\n"
        f"{_json.dumps(current, indent=2)}\n\n"
        "Available sliders:\n"
        "- warmth: 0=cold/professional, 100=very warm/friendly\n"
        "- directness: 0=gentle/indirect, 100=blunt/direct\n"
        "- formality: 0=casual, 100=formal/polished\n"
        "- challenge_level: 0=always supportive, 100=pushes back hard\n"
        "- data_reference_frequency: 0=never cites numbers, 100=data-heavy\n"
        "- humor: 0=serious, 100=playful\n"
        "- proactivity: 0=only answers when asked, 100=brings up topics unprompted\n"
        "- empathy_depth: 0=surface acknowledgment, 100=deep emotional engagement\n"
        "- custom_instructions: free text rules appended to the system prompt\n\n"
        "Return JSON with:\n"
        '- "changes": dict of slider_name: new_value (only sliders that should change)\n'
        '- "custom_instructions": new custom instructions text (or null to keep current)\n'
        '- "explanation": one sentence explaining what you changed and why\n'
        "Return ONLY valid JSON."
    )

    if settings.ai_mock_mode:
        return {
            "changes": {},
            "explanation": "AI mock mode is on. Changes would be applied in production.",
            "current": current,
        }

    llm = get_llm_client()
    raw = await llm.extract_features(system, body.message)
    try:
        parsed = _json.loads(raw)
    except Exception:
        return {
            "changes": {},
            "explanation": "Could not parse LLM response. Try rephrasing.",
            "current": current,
        }

    changes = parsed.get("changes", {})
    new_instructions = parsed.get("custom_instructions")
    explanation = parsed.get("explanation", "")

    # Apply changes
    applied = {}
    for key, val in changes.items():
        if key in current and isinstance(val, int):
            clamped = max(0, min(100, val))
            setattr(persona, key, clamped)
            applied[key] = clamped

    if new_instructions is not None and isinstance(new_instructions, str):
        persona.custom_instructions = new_instructions
        applied["custom_instructions"] = new_instructions

    if applied:
        await db.flush()

    updated = {
        "warmth": persona.warmth,
        "directness": persona.directness,
        "formality": persona.formality,
        "challenge_level": persona.challenge_level,
        "data_reference_frequency": persona.data_reference_frequency,
        "humor": persona.humor,
        "proactivity": persona.proactivity,
        "empathy_depth": persona.empathy_depth,
        "custom_instructions": persona.custom_instructions or "",
    }

    return {
        "changes": applied,
        "explanation": explanation,
        "current": updated,
    }


@router.post("/seed-from-programs")
async def seed_knowledge_from_programs(
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Seed knowledge documents from all published programs and their institutions.

    Creates one KnowledgeDocument per program, with entity links and embeddings.
    This grounds the advisor and recommendation engine in real program data.
    """
    from datetime import UTC, datetime

    from sqlalchemy.orm import selectinload

    from unipaith.ai.embedding_client import get_embedding_client
    from unipaith.models.institution import Program

    result = await db.execute(
        select(Program)
        .where(Program.is_published.is_(True))
        .options(selectinload(Program.institution))
    )
    programs = result.scalars().all()

    embedding_client = get_embedding_client()
    created = 0
    skipped = 0
    errors: list[dict[str, str]] = []

    for program in programs:
        # Check if knowledge doc already exists for this program
        existing = await db.execute(
            select(KnowledgeDocument).where(
                KnowledgeDocument.source_url == f"internal://program/{program.id}",
            )
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        inst = program.institution
        inst_name = inst.name if inst else "Unknown University"
        inst_country = inst.country if inst else ""
        inst_city = inst.city if inst else ""

        # Build rich text from program data
        parts = [
            f"{program.program_name} — {program.degree_type} program at {inst_name}.",
        ]
        if inst_city and inst_country:
            parts.append(f"Located in {inst_city}, {inst_country}.")
        if program.description_text:
            parts.append(program.description_text)
        if program.department:
            parts.append(f"Department: {program.department}.")
        if program.tuition is not None:
            parts.append(f"Annual tuition: ${program.tuition:,}.")
        if program.duration_months:
            parts.append(f"Duration: {program.duration_months} months.")
        if program.acceptance_rate is not None:
            parts.append(f"Acceptance rate: {float(program.acceptance_rate) * 100:.0f}%.")
        if program.highlights:
            parts.append("Highlights: " + ", ".join(program.highlights[:5]) + ".")
        if program.who_its_for:
            parts.append(f"Who it's for: {program.who_its_for}")
        if program.application_deadline:
            parts.append(f"Application deadline: {program.application_deadline}.")
        if inst and inst.description_text:
            parts.append(f"About {inst_name}: {inst.description_text}")

        full_text = "\n".join(parts)
        summary = parts[0]
        if len(parts) > 1:
            summary += " " + parts[1]

        try:
            emb = await embedding_client.embed_text(full_text[:4000])
        except Exception as e:
            errors.append({"program_id": str(program.id), "error": str(e)})
            continue

        doc = KnowledgeDocument(
            source_url=f"internal://program/{program.id}",
            source_domain="internal",
            content_format="program_profile",
            content_type="program",
            title=f"{program.program_name} at {inst_name}",
            raw_text=full_text,
            extracted_text=full_text,
            summary=summary,
            embedding=emb,
            quality_score=0.9,
            credibility_score=1.0,
            relevance_score=0.8,
            language="en",
            word_count=len(full_text.split()),
            ingested_at=datetime.now(UTC),
            is_active=True,
            processing_status="completed",
        )
        db.add(doc)
        await db.flush()

        # Create entity links
        from unipaith.models.knowledge import KnowledgeLink

        db.add(KnowledgeLink(
            document_id=doc.id,
            entity_type="program",
            entity_id=program.id,
            entity_name=program.program_name,
            relationship_type="describes",
            confidence=1.0,
        ))
        if inst:
            db.add(KnowledgeLink(
                document_id=doc.id,
                entity_type="institution",
                entity_id=inst.id,
                entity_name=inst.name,
                relationship_type="belongs_to",
                confidence=1.0,
            ))

        created += 1

    await db.commit()
    return {
        "status": "completed",
        "programs_total": len(programs),
        "documents_created": created,
        "documents_skipped": skipped,
        "errors": errors,
    }


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
