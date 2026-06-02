"""Spec 45 — public AI-agent catalog endpoint.

Backs the ``/goal/claude-api`` transparency page. Read-only, DB-free, and
unauthenticated (like ``/health``): it exposes only the agent *architecture*
(tiers, consent levers, fallback contracts) — never any student or institution
data. The payload is assembled live from the registry by ``ai.catalog`` so it
can never drift from what's actually wired.
"""

from __future__ import annotations

from fastapi import APIRouter

from unipaith.ai.catalog import build_catalog

router = APIRouter(prefix="/ai", tags=["ai-agents"])


@router.get("/agents", summary="The live AI agent catalog (spec 45)")
async def get_ai_agents() -> dict:
    """Return the full agent inventory: tiers + per-agent metadata + the
    consent / cache / fallback / validation contracts. Public and cacheable."""
    return build_catalog()
