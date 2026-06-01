"""Spec 37 (AI Extensibility) §5 — per-institution AI configuration.

The single source of truth for which AI-assistive surfaces an institution has
enabled, the per-surface confidence thresholds, and the no-training tier
override (46 §9). Stored on ``Institution.ai_config`` (JSONB, nullable). NULL or
a partial blob is always overlaid on :data:`DEFAULT_AI_CONFIG`, so surfaces
added in code later light up for every tenant without a data migration.

Enforcement contract (consumed by the AI endpoints + ai_surface_service):
- ``is_surface_enabled`` → when False the endpoint returns the rule-based /
  empty result with ``disabled: True``; it never calls the agent and never 5xx.
- ``min_confidence`` → a per-surface floor; e.g. rubric pre-fill values below
  the floor are withheld (Spec 37 §5 "only show AI prefill when confidence ≥ 70").
- ``is_no_training`` → flows into every captured edit-diff event's metadata as
  ``training_eligible: False`` so the future per-tenant tuning corpus excludes it.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.institution import Institution

# ── Canonical surface registry ───────────────────────────────────────────────
# key → (human label, whether a confidence threshold is meaningful). The order
# here is the display order in /i/settings → AI tab.
AI_SURFACES: dict[str, dict] = {
    "packet_summary": {"label": "AI packet summary", "confidence": False},
    "rubric_prefill": {"label": "Rubric pre-fill", "confidence": True},
    "assistant_chat": {"label": "Applicant assistant chat", "confidence": False},
    "message_draft": {"label": "AI message drafts", "confidence": False},
    "authenticity_risk": {"label": "Authenticity risk scoring", "confidence": True},
    "intelligence_digest": {"label": "Intelligence digest", "confidence": False},
    "doc_parse_triage": {"label": "Document parse triage", "confidence": False},
    "campaign_copy": {"label": "Campaign copy suggestions", "confidence": False},
}

# Default per-surface state. Everything on by default (the rule-based fallback
# keeps each surface safe); rubric pre-fill ships with the spec's 70-confidence
# floor (Spec 37 §5 example).
_DEFAULT_THRESHOLDS = {"rubric_prefill": 70}

DEFAULT_AI_CONFIG: dict = {
    "surfaces": {
        key: {"enabled": True, "min_confidence": _DEFAULT_THRESHOLDS.get(key, 0)}
        for key in AI_SURFACES
    },
    "no_training": False,
}


def _clamp_confidence(value: object, fallback: int = 0) -> int:
    try:
        n = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return fallback
    return max(0, min(100, n))


def merge_ai_config(raw: dict | None) -> dict:
    """Overlay a stored (possibly partial / stale) blob onto the defaults.

    Always returns a full config with every known surface present, so callers
    and the settings UI can rely on the shape regardless of what was persisted.
    """
    merged: dict = {
        "surfaces": {key: dict(DEFAULT_AI_CONFIG["surfaces"][key]) for key in AI_SURFACES},
        "no_training": False,
    }
    if not isinstance(raw, dict):
        return merged
    stored_surfaces = raw.get("surfaces")
    if isinstance(stored_surfaces, dict):
        for key in AI_SURFACES:
            s = stored_surfaces.get(key)
            if not isinstance(s, dict):
                continue
            if "enabled" in s:
                merged["surfaces"][key]["enabled"] = bool(s["enabled"])
            if "min_confidence" in s:
                merged["surfaces"][key]["min_confidence"] = _clamp_confidence(
                    s["min_confidence"], merged["surfaces"][key]["min_confidence"]
                )
    merged["no_training"] = bool(raw.get("no_training", False))
    return merged


def apply_update(current_raw: dict | None, patch: dict | None) -> dict:
    """Merge an incoming partial patch onto the current config; return the full
    normalized config to persist. Unknown surfaces are ignored; confidences are
    clamped to [0, 100]."""
    merged = merge_ai_config(current_raw)
    if not isinstance(patch, dict):
        return merged
    patch_surfaces = patch.get("surfaces")
    if isinstance(patch_surfaces, dict):
        for key, s in patch_surfaces.items():
            if key not in AI_SURFACES or not isinstance(s, dict):
                continue
            if "enabled" in s and s["enabled"] is not None:
                merged["surfaces"][key]["enabled"] = bool(s["enabled"])
            if "min_confidence" in s and s["min_confidence"] is not None:
                merged["surfaces"][key]["min_confidence"] = _clamp_confidence(
                    s["min_confidence"], merged["surfaces"][key]["min_confidence"]
                )
    if "no_training" in patch and patch["no_training"] is not None:
        merged["no_training"] = bool(patch["no_training"])
    return merged


def surface_enabled(cfg: dict, surface: str) -> bool:
    return bool(cfg.get("surfaces", {}).get(surface, {}).get("enabled", True))


def surface_min_confidence(cfg: dict, surface: str) -> int:
    return _clamp_confidence(cfg.get("surfaces", {}).get(surface, {}).get("min_confidence", 0))


def no_training(cfg: dict) -> bool:
    return bool(cfg.get("no_training", False))


class AIConfigService:
    """Async accessor that loads + merges an institution's AI config."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_for_institution(self, institution_id: UUID | None) -> dict:
        if institution_id is None:
            return merge_ai_config(None)
        inst = await self.db.get(Institution, institution_id)
        return merge_ai_config(inst.ai_config if inst else None)

    async def is_surface_enabled(self, institution_id: UUID | None, surface: str) -> bool:
        return surface_enabled(await self.get_for_institution(institution_id), surface)

    async def min_confidence(self, institution_id: UUID | None, surface: str) -> int:
        return surface_min_confidence(await self.get_for_institution(institution_id), surface)

    async def is_no_training(self, institution_id: UUID | None) -> bool:
        return no_training(await self.get_for_institution(institution_id))
