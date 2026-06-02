"""Spec 48/49/50 — public build-transparency endpoints.

Back the ``/goal`` hub and its roadmap / features / api pages. Like
``/ai/agents`` (spec 45): read-only, DB-free and unauthenticated — they expose
only build *architecture* (phases, feature coverage, the live route map), never
any user data. The api-contract map is derived from the running route table, so
the surface can never claim something the deployed app doesn't have.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from unipaith.ai.catalog import build_catalog
from unipaith.config import settings
from unipaith.transparency.api_contract import build_api_contract
from unipaith.transparency.features import build_features
from unipaith.transparency.roadmap import build_roadmap

router = APIRouter(prefix="/build", tags=["build-transparency"])


@router.get("/overview", summary="Headline build-transparency stats (specs 48/49/50)")
async def get_overview(request: Request) -> dict:
    """The hub summary: roadmap, feature-coverage, route and agent counts —
    everything the ``/goal`` landing needs in one cheap, public call."""
    roadmap = build_roadmap()["summary"]
    features = build_features()["summary"]
    contract = build_api_contract(request.app.routes)["summary"]
    agents = build_catalog()["summary"]
    return {
        "roadmap": roadmap,
        "features": features,
        "api": contract,
        "agents": agents,
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
