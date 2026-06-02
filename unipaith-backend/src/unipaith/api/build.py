"""Specs 48–53 — public build-transparency endpoints.

Back the ``/goal`` hub and its pages. Like ``/ai/agents`` (spec 45): read-only,
DB-free and unauthenticated — they expose only build *architecture* (phases,
feature coverage, the live route map, the live table map, the UX interaction
bar, the acceptance gates), never any user data. The api-contract, data-model
and per-surface UX route-backing maps are derived from the running route table
and the running SQLAlchemy metadata, so the surface can never claim something
the deployed app doesn't have.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from unipaith.ai.catalog import build_catalog
from unipaith.config import settings
from unipaith.transparency.acceptance import build_acceptance
from unipaith.transparency.api_contract import build_api_contract
from unipaith.transparency.data_model import build_data_model
from unipaith.transparency.features import build_features
from unipaith.transparency.roadmap import build_roadmap
from unipaith.transparency.ux_benchmark import build_ux_benchmark

router = APIRouter(prefix="/build", tags=["build-transparency"])


@router.get("/overview", summary="Headline build-transparency stats (specs 48–53)")
async def get_overview(request: Request) -> dict:
    """The hub summary: roadmap, feature-coverage, route / table / agent counts, the
    UX bar and the acceptance readiness — everything the ``/goal`` landing needs in
    one cheap, public call."""
    roadmap = build_roadmap()["summary"]
    features = build_features()["summary"]
    contract = build_api_contract(request.app.routes)["summary"]
    agents = build_catalog()["summary"]
    data_model = build_data_model()["summary"]
    acceptance = build_acceptance(request.app.routes)["summary"]
    blockers_stat = f"{acceptance['launch_blockers_cleared']}/{acceptance['launch_blockers_total']}"
    ux = build_ux_benchmark(request.app.routes)["summary"]
    return {
        "roadmap": roadmap,
        "features": features,
        "api": contract,
        "agents": agents,
        "data_model": data_model,
        "acceptance": acceptance,
        "provider": settings.ai_provider_default,
        "surfaces": [
            {
                "key": "claude-api",
                "title": "AI agents",
                "spec": "45",
                "blurb": "Every assistive feature, powered by Claude — the live agent fleet.",
                "path": "/goal/claude-api",
                "stat": agents["agent_count"],
                "stat_label": "AI agents",
            },
            {
                "key": "roadmap",
                "title": "Build roadmap",
                "spec": "48",
                "blurb": "The phased path from MVP to the master-paper spec.",
                "path": "/goal/roadmap",
                "stat": f"{roadmap['shipped']}/{roadmap['phase_count']}",
                "stat_label": "phases shipped",
            },
            {
                "key": "features",
                "title": "Feature coverage",
                "spec": "49",
                "blurb": "Every feature on the founder's list, mapped and classified.",
                "path": "/goal/features",
                "stat": features["feature_count"],
                "stat_label": "features mapped",
            },
            {
                "key": "api",
                "title": "API contract",
                "spec": "50",
                "blurb": "The front↔back handshake, read live from the running routes.",
                "path": "/goal/api",
                "stat": contract["route_count"],
                "stat_label": "live routes",
            },
            {
                "key": "data-model",
                "title": "Data model",
                "spec": "51",
                "blurb": "The persisted schema, introspected live from the running models.",
                "path": "/goal/data-model",
                "stat": data_model["table_count"],
                "stat_label": "live tables",
            },
            {
                "key": "acceptance",
                "title": "Acceptance & runbook",
                "spec": "52",
                "blurb": "The definition of done — readiness read from the running system.",
                "path": "/goal/acceptance",
                "stat": blockers_stat,
                "stat_label": "launch blockers cleared",
            },
            {
                "key": "experience",
                "title": "Experience standards",
                "spec": "53",
                "blurb": "The interaction bar — every surface benchmarked vs LinkedIn / Handshake.",
                "path": "/goal/experience",
                "stat": ux["surface_count"],
                "stat_label": "benchmarked surfaces",
            },
        ],
    }


@router.get("/roadmap", summary="The phased build roadmap (spec 48)")
async def get_roadmap() -> dict:
    return build_roadmap()


@router.get("/features", summary="The Feature-List V1 coverage map (spec 49)")
async def get_features() -> dict:
    return build_features()


@router.get("/api-contract", summary="The live front↔back API contract (spec 50)")
async def get_api_contract(request: Request) -> dict:
    """The router map is built from ``request.app.routes`` — the running route
    table — so it is the machine source of truth spec 50 §5 points at."""
    return build_api_contract(request.app.routes)


@router.get("/data-model", summary="The live persisted data model (spec 51)")
async def get_data_model() -> dict:
    """The table map is introspected from the running SQLAlchemy metadata — the
    same schema the app and Alembic build against — so it can't drift (spec 51)."""
    return build_data_model()


@router.get("/acceptance", summary="The MVP acceptance & runbook readiness (spec 52)")
async def get_acceptance(request: Request) -> dict:
    """Readiness is read from the running system (routes, agents, schema, feature
    coverage); the launch-blocker statuses are evidence-backed (spec 52)."""
    return build_acceptance(request.app.routes)


@router.get("/ux-benchmark", summary="The UX benchmark & interaction standards (spec 53)")
async def get_ux_benchmark(request: Request) -> dict:
    """Spec 53's experience bar: each surface's benchmark + build contract, the
    interaction standards, and — resolved live from ``request.app.routes`` — the
    count of endpoints backing each surface, so the page can't claim a surface
    the deployed app doesn't serve."""
    return build_ux_benchmark(request.app.routes)
