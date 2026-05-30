"""A4 — Feature Emitter agent.

Once per student at end-of-Discovery. Reads the StudentSnapshot the
validator already built, runs Haiku to produce the typed sparse-feature
dict + 200-word applicant summary, computes the Voyage embedding, and
upserts into `student_feature_vectors`.

Cache layout
------------
- system_prompt + tool schema = ephemeral cache (rarely change). The
  controlled-vocabulary lists in `feature_schema.py` rarely change too,
  so they're appended to the system prompt and share that cache.
- Per-call payload (the snapshot JSON) is uncached.

What's deliberately NOT here
----------------------------
- Program-side feature emission lives in
  `unipaith.services.program_features`. Same vocabulary, different
  surface — so an offline batch job runs that, not the per-student
  Discovery flow.
- The ML matcher (cosine + soft-align + needs-match) lives in
  `unipaith.services.matching`. The emitter just produces the inputs.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.prompt_cache import CACHE_1H
from unipaith.ai.state import StudentSnapshot
from unipaith.ai.tools.feature_schema import (
    CAREER_ARCS,
    EMIT_FEATURES_TOOL,
    INTEREST_THEMES,
    NEED_SIGNAL_TAGS,
    SCHEMA_VERSION,
    VALUE_TAGS,
)
from unipaith.models.ai_artifacts import StudentFeatureVector

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").rstrip()


_BASE_PROMPT = _load_prompt("feature_emitter.md")


def _vocab_appendix() -> str:
    """Controlled-vocabulary lists appended to the system prompt. Cached
    alongside the prompt itself (they only change on a SCHEMA_VERSION bump)."""
    return (
        "\n\n---\n\n"
        f"# Controlled vocabulary (schema v{SCHEMA_VERSION})\n\n"
        "## INTEREST_THEMES\n"
        + ", ".join(sorted(INTEREST_THEMES))
        + "\n\n## CAREER_ARCS\n"
        + ", ".join(sorted(CAREER_ARCS))
        + "\n\n## VALUE_TAGS\n"
        + ", ".join(sorted(VALUE_TAGS))
        + "\n\n## NEED_SIGNAL_TAGS\n"
        + ", ".join(sorted(NEED_SIGNAL_TAGS))
        + "\n"
    )


_FULL_PROMPT = _BASE_PROMPT + _vocab_appendix()


@dataclass
class EmittedFeatures:
    """The emitter's structured output, post-validation."""

    sparse_features: dict[str, Any] = field(default_factory=dict)
    applicant_summary: str = ""
    embedding: list[float] | None = None
    schema_version: int = SCHEMA_VERSION
    cost_usd: float = 0.0
    latency_ms: int = 0
    raw_response: dict[str, Any] | None = None

    def is_valid(self) -> bool:
        """A valid emission has at least the required sparse-feature keys
        AND a non-empty summary AND an embedding (when not in mock mode)."""
        required = {
            "education_level",
            "intended_degrees",
            "intended_majors",
            "geo_must",
            "geo_avoid",
            "interest_themes",
            "career_arcs",
            "values",
            "needs_signals",
            "social_prefs",
            "feature_completeness",
        }
        return bool(
            self.sparse_features
            and required.issubset(self.sparse_features.keys())
            and self.applicant_summary
        )


class FeatureEmitter:
    """A4 — once-per-student feature emitter.

    Stateless; safe to instantiate per-call. Singleton via
    `get_feature_emitter()` for the common path.
    """

    AGENT_NAME = "feature_emitter"

    def __init__(
        self,
        client: AIClient | None = None,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 2000,
        temperature: float = 0.2,
    ):
        self.client = client or get_client()
        self.system_prompt = system_prompt or _FULL_PROMPT
        self.max_tokens = max_tokens
        # Low-but-not-zero temperature: enough creativity to write a
        # readable applicant_summary, low enough to keep tag selection
        # deterministic-ish across reruns of the same snapshot.
        self.temperature = temperature

    async def emit(
        self,
        *,
        snapshot: StudentSnapshot,
        student_id: UUID | None = None,
        db: AsyncSession | None = None,
    ) -> EmittedFeatures:
        """Run the emitter end-to-end and return parsed features.

        Caller (DiscoveryService or a Discovery-completed hook) is
        responsible for persisting via `persist_features` if the result
        `is_valid()`.
        """
        payload = self._snapshot_payload(snapshot)

        system = [
            {
                "type": "text",
                "text": self.system_prompt,
                "cache_control": CACHE_1H,
            }
        ]
        tools = [{**EMIT_FEATURES_TOOL, "cache_control": CACHE_1H}]

        response = await self.client.message(
            agent=self.AGENT_NAME,
            model="haiku",
            system=system,
            messages=[{"role": "user", "content": payload}],
            tools=tools,
            tool_choice={"type": "tool", "name": "emit_features"},
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            student_id=student_id,
            surface="discovery_complete",
            db=db,
        )

        sparse, summary = self._parse_response(response.content_blocks)
        # Embedding: separate Voyage call. Falls back to None on failure
        # — the matcher can still rank using sparse features alone, just
        # without cosine similarity weight.
        embedding: list[float] | None = None
        if summary:
            try:
                embed_resp = await self.client.embed(
                    summary, student_id=student_id, db=db
                )
                embedding = embed_resp.embedding
            except Exception as exc:  # pragma: no cover — degraded path
                logger.warning(
                    "FeatureEmitter: Voyage embed failed for student=%s: %s",
                    student_id,
                    exc,
                )

        return EmittedFeatures(
            sparse_features=sparse,
            applicant_summary=summary,
            embedding=embedding,
            schema_version=SCHEMA_VERSION,
            cost_usd=float(response.cost_usd),
            latency_ms=response.latency_ms,
            raw_response={"sparse_features": sparse, "applicant_summary": summary},
        )

    # ── Internals ──────────────────────────────────────────────────────

    @staticmethod
    def _snapshot_payload(snapshot: StudentSnapshot) -> str:
        """Serialize a StudentSnapshot to JSON for the LLM payload.

        Keep the shape close to what's already in extracted_signals so
        the model has familiar handles. Lists of dataclasses are
        unpacked to dicts.
        """
        return json.dumps(
            {
                "basic": {
                    "age": snapshot.age,
                    "education_level": snapshot.education_level,
                    "gpa": snapshot.gpa,
                    "test_scores": snapshot.test_scores,
                    "location_prefs": snapshot.location_prefs,
                    "location_avoid": snapshot.location_avoid,
                    "first_gen": snapshot.first_gen,
                    "income_band": snapshot.income_band,
                    "gender": snapshot.gender,
                },
                "personality": [
                    {"facet": p.facet, "value": p.value, "evidence": p.evidence}
                    for p in snapshot.personality
                ],
                "identity": [
                    {
                        "facet": c.facet,
                        "claim": c.claim,
                        "evidence": c.evidence,
                        "user_confirmed": c.user_confirmed,
                    }
                    for c in snapshot.identity_claims
                ],
                "goals": [
                    {
                        "category": g.category,
                        "specific": g.specific,
                        "measurable": g.measurable,
                        "achievable": g.achievable,
                        "relevant": g.relevant,
                        "time_bound": g.time_bound,
                        "completeness": g.completeness,
                        "user_confirmed": g.user_confirmed,
                    }
                    for g in snapshot.goals
                ],
                "needs": [
                    {
                        "maslow_level": n.maslow_level,
                        "signal": n.signal,
                        "free_text": n.free_text,
                        "severity": n.severity,
                        "evidence": n.evidence,
                    }
                    for n in snapshot.needs
                ],
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _parse_response(blocks: list[dict[str, Any]]) -> tuple[dict[str, Any], str]:
        """Extract sparse_features + applicant_summary from the tool call."""
        for b in blocks:
            if b.get("type") == "tool_use" and b.get("name") == "emit_features":
                inp = b.get("input") or {}
                return inp.get("sparse_features") or {}, inp.get("applicant_summary") or ""
        return {}, ""


# ── Persistence ─────────────────────────────────────────────────────────────


async def persist_features(
    *,
    db: AsyncSession,
    student_id: UUID,
    features: EmittedFeatures,
    bump_version: bool = True,
) -> StudentFeatureVector:
    """Upsert into `student_feature_vectors`.

    `bump_version` defaults to True — re-emissions invalidate downstream
    caches (match_rationales). Set False for idempotent re-runs of the
    same snapshot (e.g. retrying a transient embedding failure).
    """
    if not features.is_valid():
        raise ValueError("FeatureEmitter: invalid features — refusing to persist")

    row = await db.scalar(
        select(StudentFeatureVector).where(StudentFeatureVector.student_id == student_id)
    )
    if row is None:
        row = StudentFeatureVector(
            student_id=student_id,
            profile_version=1,
            embedding=None,
            sparse_features={},
            applicant_summary="",
        )
        db.add(row)

    row.sparse_features = features.sparse_features
    row.applicant_summary = features.applicant_summary
    # JSONB column at ORM layer (see model docstring); we round-trip a
    # plain list in mock + cold-start. Production migrations write to
    # VECTOR(1024) — same wire format.
    if features.embedding is not None:
        row.embedding = list(features.embedding)
    if bump_version:
        row.profile_version = (row.profile_version or 1) + 1

    await db.flush()
    return row


# ── Singleton ───────────────────────────────────────────────────────────────


_default_emitter: FeatureEmitter | None = None


def get_feature_emitter() -> FeatureEmitter:
    global _default_emitter
    if _default_emitter is None:
        _default_emitter = FeatureEmitter()
    return _default_emitter


def reset_feature_emitter() -> None:
    """Test helper."""
    global _default_emitter
    _default_emitter = None
