"""A3 — Layer Validator.

Phase A2 shipped the BASIC layer (deterministic). Phase A3 adds:

  - PERSONALITY: deterministic count + an LLM-as-judge pass that scores
    the *quality* of evidence quotes (Haiku 4.5, JSON output). The
    deterministic gate must pass before the LLM judge runs — we never burn
    tokens on a clearly-incomplete layer.

  - IDENTITY: deterministic gate (≥3 value/belief claims, ≥1
    self-awareness moment, ≥2 user-confirmed) + the same LLM-as-judge
    pattern. Identity quality matters more than personality, so the
    judge's threshold is stricter.

The LLM judge is gated by `use_llm_judge`. When False, the validator
returns the deterministic verdict alone (cheap, useful for tests and
internal callers that just want a layer-complete check).

Why a judge at all
------------------
Identity-layer evidence is the highest-stakes signal we extract. A
mechanical count of "≥3 claims with quotes" is necessary but not
sufficient — the model can technically satisfy it with surface-level
nodding. The judge reads each claim + its quote and scores depth on a
1–5 rubric. Layer-complete requires the deterministic gate AND average
judge score ≥ a per-layer threshold.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.state import (
    Layer,
    LayerVerdict,
    StudentSnapshot,
    Track,
    evaluate_basic_layer,
    evaluate_goals_track,
    evaluate_identity_layer,
    evaluate_needs_track,
    evaluate_personality_layer,
)

logger = logging.getLogger(__name__)


# Judge thresholds (1–5 rubric mean). Calibrated against the bias-pair +
# golden conversation runs; tighten as fixtures grow.
PERSONALITY_JUDGE_THRESHOLD = 3.0
IDENTITY_JUDGE_THRESHOLD = 3.5


# ── LLM-as-judge tool schemas ───────────────────────────────────────────────
# Forced tool-use; the judge has no other surface to leak into.

_PERSONALITY_JUDGE_TOOL = {
    "name": "score_personality_evidence",
    "description": (
        "Score each personality entry on a 1–5 rubric. Return one entry per "
        "input entry, in the same order. Score depth, specificity, and whether "
        "the evidence quote actually supports the claimed value."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["scores"],
        "properties": {
            "scores": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["facet", "score", "reason"],
                    "properties": {
                        "facet": {"type": "string"},
                        "score": {"type": "integer", "minimum": 1, "maximum": 5},
                        "reason": {"type": "string", "maxLength": 200},
                    },
                },
            },
        },
    },
}

_IDENTITY_JUDGE_TOOL = {
    "name": "score_identity_claims",
    "description": (
        "Score each identity claim on a 1–5 rubric. 5 = a defended belief or "
        "values-rooted claim with a quote that directly supports it. 1 = "
        "casual statement promoted past its weight, or a quote that doesn't "
        "actually support the claim."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["scores"],
        "properties": {
            "scores": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["facet", "score", "reason"],
                    "properties": {
                        "facet": {"type": "string"},
                        "score": {"type": "integer", "minimum": 1, "maximum": 5},
                        "reason": {"type": "string", "maxLength": 200},
                    },
                },
            },
        },
    },
}


_PERSONALITY_JUDGE_PROMPT = """\
You score personality-layer signals from a college admissions Discovery
conversation. Each entry has a facet (e.g. peer_style), a value (a short
descriptor), and an evidence quote (the student's own words).

Rubric (1-5):
  5 - Specific, vivid evidence that directly supports the claimed value.
  4 - Clear evidence; minor gap between quote and value descriptor.
  3 - Plausible but generic evidence. Could fit several values.
  2 - Quote barely supports the value; mostly a leap.
  1 - Quote doesn't support the value, or value is too vague to score.

Be strict - over-scoring leads to bad recommendations downstream. Output ONLY
the score_personality_evidence tool call.
"""


_IDENTITY_JUDGE_PROMPT = """\
You score identity-layer claims from a college admissions Discovery
conversation. Each claim has a facet (value / belief / view / self_awareness)
and an evidence quote.

Rubric (1-5):
  5 - Defended values or beliefs anchored in concrete behavior or experience.
      Self-awareness moments must include a real trigger event.
  4 - Strong claim with credible (if not concrete) evidence.
  3 - Plausible but generic - could be anyone's claim.
  2 - Casual statement promoted past its weight; quote is vague.
  1 - Claim is contradicted by the quote, or quote is filler.

The IDENTITY layer is the deepest tier - it's worth burning a few tokens to
get this right. Output ONLY the score_identity_claims tool call.
"""


@dataclass
class JudgeOutcome:
    """Aggregated LLM-judge result for a layer."""

    mean_score: float
    threshold: float
    passed: bool
    per_entry: list[dict[str, Any]] = field(default_factory=list)
    cost_usd: float = 0.0
    latency_ms: int = 0


class LayerValidator:
    """Layer-by-layer exit-condition checker.

    BASIC: deterministic only.
    PERSONALITY / IDENTITY: deterministic gate + optional LLM-as-judge.
    """

    AGENT_NAME = "validator"

    def __init__(
        self,
        client: AIClient | None = None,
        *,
        use_llm_judge: bool = True,
    ):
        self.client = client or get_client()
        self.use_llm_judge = use_llm_judge

    # ── Sync entrypoint (BASIC, or no-LLM uses) ──────────────────────────

    def validate(
        self,
        *,
        layer: Layer,
        snapshot: StudentSnapshot,
        recent_extractions: list[dict[str, Any]] | None = None,  # noqa: ARG002
    ) -> LayerVerdict:
        """Synchronous, no-LLM verdict. Use for BASIC, or for personality/
        identity when you only need the deterministic gate.

        For the GOALS / NEEDS *tracks* (which don't have layers), use
        `validate_track()`.
        """
        if layer == "basic":
            return evaluate_basic_layer(snapshot)
        if layer == "personality":
            return evaluate_personality_layer(snapshot)
        if layer == "identity":
            return evaluate_identity_layer(snapshot)
        raise ValueError(f"unknown layer: {layer!r}")

    def validate_track(
        self,
        *,
        track: Track,
        snapshot: StudentSnapshot,
    ) -> LayerVerdict:
        """Track-level deterministic verdict for GOALS and NEEDS.

        Profile-track validation goes through `validate(layer=...)` since
        each profile layer has its own evaluator. Goals and needs are
        flat — one evaluator per track.
        """
        if track == "goals":
            return evaluate_goals_track(snapshot)
        if track == "needs":
            return evaluate_needs_track(snapshot)
        raise ValueError(
            f"validate_track: track={track!r} is not flat — "
            "use validate(layer=...) for the profile track."
        )

    # ── Async entrypoint with LLM judge for personality/identity ────────

    async def validate_with_judge(
        self,
        *,
        layer: Layer,
        snapshot: StudentSnapshot,
        db: AsyncSession | None = None,
    ) -> tuple[LayerVerdict, JudgeOutcome | None]:
        """Run the deterministic gate AND (when applicable) the LLM judge.

        Returns (verdict, judge_outcome). The verdict's `layer_complete`
        flag is gated on BOTH the deterministic count AND the judge mean
        score crossing the per-layer threshold. Judge outcome is None for
        BASIC and when `use_llm_judge` is False.
        """
        deterministic = self.validate(layer=layer, snapshot=snapshot)
        if layer == "basic" or not self.use_llm_judge:
            return deterministic, None

        # Skip the judge when the deterministic gate already says incomplete
        # — no point grading evidence we know is missing.
        if not deterministic.layer_complete:
            return deterministic, None

        if layer == "personality":
            outcome = await self._judge_personality(snapshot=snapshot, db=db)
        elif layer == "identity":
            outcome = await self._judge_identity(snapshot=snapshot, db=db)
        else:
            return deterministic, None

        gated_complete = deterministic.layer_complete and outcome.passed
        gated = LayerVerdict(
            layer_complete=gated_complete,
            completion_pct=deterministic.completion_pct,
            missing_signals=(
                deterministic.missing_signals
                if gated_complete
                else deterministic.missing_signals
                + [f"{layer}.judge_score ({outcome.mean_score:.2f}/{outcome.threshold:.2f})"]
            ),
            next_probe_hint=(
                deterministic.next_probe_hint
                if gated_complete
                else _judge_followup_probe(layer)
            ),
            evidence_count={
                **deterministic.evidence_count,
                f"{layer}.judge_score_x100": int(round(outcome.mean_score * 100)),
            },
        )
        return gated, outcome

    # ── Judge internals ────────────────────────────────────────────────

    async def _judge_personality(
        self,
        *,
        snapshot: StudentSnapshot,
        db: AsyncSession | None,
    ) -> JudgeOutcome:
        entries = [
            {"facet": p.facet, "value": p.value, "evidence": p.evidence}
            for p in snapshot.personality
            if p.evidence
        ]
        return await self._run_judge(
            tool=_PERSONALITY_JUDGE_TOOL,
            system_prompt=_PERSONALITY_JUDGE_PROMPT,
            entries=entries,
            threshold=PERSONALITY_JUDGE_THRESHOLD,
            surface="personality",
            db=db,
        )

    async def _judge_identity(
        self,
        *,
        snapshot: StudentSnapshot,
        db: AsyncSession | None,
    ) -> JudgeOutcome:
        entries = [
            {"facet": c.facet, "claim": c.claim, "evidence": c.evidence}
            for c in snapshot.identity_claims
            if c.evidence and c.claim
        ]
        return await self._run_judge(
            tool=_IDENTITY_JUDGE_TOOL,
            system_prompt=_IDENTITY_JUDGE_PROMPT,
            entries=entries,
            threshold=IDENTITY_JUDGE_THRESHOLD,
            surface="identity",
            db=db,
        )

    async def _run_judge(
        self,
        *,
        tool: dict[str, Any],
        system_prompt: str,
        entries: list[dict[str, Any]],
        threshold: float,
        surface: str,
        db: AsyncSession | None,
    ) -> JudgeOutcome:
        if not entries:
            # Defensive: deterministic gate should have caught this; if we
            # got here with no entries, fail closed (judge cannot pass on
            # no evidence).
            return JudgeOutcome(
                mean_score=0.0, threshold=threshold, passed=False, per_entry=[]
            )

        system = [
            {"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}
        ]
        tools = [{**tool, "cache_control": {"type": "ephemeral"}}]
        payload = json.dumps({"entries": entries}, ensure_ascii=False)

        try:
            response = await self.client.message(
                agent=self.AGENT_NAME,
                model="haiku",
                system=system,
                messages=[{"role": "user", "content": payload}],
                tools=tools,
                tool_choice={"type": "tool", "name": tool["name"]},
                max_tokens=800,
                temperature=0.0,
                surface=surface,
                db=db,
            )
        except Exception as exc:
            # Judge failures are not blocking — fall back to deterministic.
            logger.warning("LayerValidator judge failed (%s): %s", surface, exc)
            return JudgeOutcome(
                mean_score=0.0,
                threshold=threshold,
                passed=False,
                per_entry=[],
            )

        scores = self._parse_judge_response(response.content_blocks)
        if not scores:
            return JudgeOutcome(
                mean_score=0.0,
                threshold=threshold,
                passed=False,
                per_entry=[],
                cost_usd=float(response.cost_usd),
                latency_ms=response.latency_ms,
            )

        mean = sum(s["score"] for s in scores) / len(scores)
        return JudgeOutcome(
            mean_score=mean,
            threshold=threshold,
            passed=mean >= threshold,
            per_entry=scores,
            cost_usd=float(response.cost_usd),
            latency_ms=response.latency_ms,
        )

    @staticmethod
    def _parse_judge_response(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for b in blocks:
            if b.get("type") == "tool_use":
                inp = b.get("input") or {}
                scores = inp.get("scores") or []
                if isinstance(scores, list):
                    return [
                        s
                        for s in scores
                        if isinstance(s, dict)
                        and isinstance(s.get("score"), int)
                        and 1 <= s["score"] <= 5
                    ]
        return []


# ── Helpers ─────────────────────────────────────────────────────────────────


def _judge_followup_probe(layer: Layer) -> str:
    """When the LLM judge fails, the orchestrator should probe deeper, not
    advance. Return a layer-specific 'go deeper' nudge."""
    if layer == "personality":
        return (
            "Pick the most surface-level personality answer the student gave "
            "and ask for a concrete example that anchors it."
        )
    if layer == "identity":
        return (
            "The student's identity claims are present but thin. Ask them "
            "for a moment when one of their values was tested — a real "
            "story, not an abstraction."
        )
    return ""


# Module-level convenience: a default instance.
default_validator = LayerValidator()
