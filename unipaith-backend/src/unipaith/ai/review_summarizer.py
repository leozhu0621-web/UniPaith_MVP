"""DraftSummarizerForReview (`45` §14) — institution review packet summary.

Spec 06 §2 names this as the one **Opus (flagship)** agent: a single
high-stakes call per applicant that produces the rubric-aligned packet
summary institution reviewers read (spec 32 §2). Before this it was a stub
that returned "AI review is temporarily unavailable (engine being rebuilt)"
and recorded Sonnet, never Opus — spec 32 gap G-AI5.

Contract guarantees (matches the rest of the L2 stack):
  * **Flagship/Opus** model tier is actually requested.
  * Forced tool-use (`submit_review_summary`); output validated.
  * On ANY failure — provider down, parse error, consent denial, or mock
    mode — falls back to a deterministic rule-based summary built from the
    structured packet. The reviewer surface never 5xxes and never shows
    "unavailable"; it shows a usable (if rule-based) summary.

The output shape maps 1:1 to `AIPacketSummary` + the review-workspace UI.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.prompt_cache import CACHE_1H
from unipaith.ai.tools.review_summary_schema import SUBMIT_REVIEW_SUMMARY_TOOL

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    path = PROMPTS_DIR / name
    if path.exists():
        return path.read_text(encoding="utf-8").rstrip()
    return _DEFAULT_PROMPT


_DEFAULT_PROMPT = (
    "You are an admissions review assistant. Given an applicant packet, a "
    "target program, and a scoring rubric, produce a rubric-aligned summary "
    "using the submit_review_summary tool. Rules: cite only fields present in "
    "the packet (never invent credentials); be balanced (strengths AND "
    "concerns); test-optional non-submission is never a penalty; you produce "
    "feedback, never a final admit/deny decision — the human reviewer "
    "decides. Keep the overall summary to 3-6 sentences."
)


@dataclass
class ReviewSummaryResult:
    overall_summary: str = ""
    strengths: list[dict[str, Any]] = field(default_factory=list)
    concerns: list[dict[str, Any]] = field(default_factory=list)
    criterion_assessments: list[dict[str, Any]] = field(default_factory=list)
    recommended_score: float | None = None
    confidence_level: str = "low"
    is_stub: bool = True
    cost_usd: float = 0.0

    def to_packet_data(self) -> dict[str, Any]:
        return {
            "overall_summary": self.overall_summary,
            "strengths": self.strengths,
            "concerns": self.concerns,
            "criterion_assessments": self.criterion_assessments,
            "recommended_score": self.recommended_score,
            "confidence_level": self.confidence_level,
        }


class DraftSummarizerForReview:
    """`45` §14 — Opus single-shot review summarizer with rule-based fallback."""

    AGENT_NAME = "review_summarizer"

    def __init__(
        self,
        client: AIClient | None = None,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 1800,
        temperature: float = 0.3,
    ):
        self.client = client or get_client()
        self.system_prompt = system_prompt or _load_prompt("review_summary.md")
        self.max_tokens = max_tokens
        self.temperature = temperature

    async def generate(
        self,
        *,
        student_context: dict[str, Any],
        program_context: dict[str, Any],
        rubric_criteria: list[dict[str, Any]] | None = None,
        student_id: UUID | None = None,
        db: AsyncSession | None = None,
    ) -> ReviewSummaryResult:
        """Generate the packet summary. Returns a rule-based fallback (never
        raises) on any provider/parse/consent failure or in mock mode."""
        rubric_criteria = rubric_criteria or []
        try:
            payload = json.dumps(
                {
                    "applicant": student_context,
                    "program": program_context,
                    "rubric_criteria": rubric_criteria,
                },
                ensure_ascii=False,
                default=str,
            )
            response = await self.client.message(
                agent=self.AGENT_NAME,
                model="flagship",  # Spec 06 §2 — Opus, the only flagship caller.
                system=[{"type": "text", "text": self.system_prompt, "cache_control": CACHE_1H}],
                messages=[{"role": "user", "content": payload}],
                tools=[{**SUBMIT_REVIEW_SUMMARY_TOOL, "cache_control": CACHE_1H}],
                tool_choice={"type": "tool", "name": "submit_review_summary"},
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                student_id=student_id,
                surface="review_summary",
                db=db,
            )
            parsed = self._parse(response.content_blocks)
            if parsed is not None and parsed.overall_summary.strip():
                parsed.cost_usd = float(response.cost_usd)
                parsed.is_stub = False
                return parsed
        except Exception as exc:  # noqa: BLE001 — never break the reviewer surface
            logger.info("review_summarizer falling back to rule-based: %s", exc)

        return _rule_based_summary(student_context, program_context, rubric_criteria)

    @staticmethod
    def _parse(blocks: list[dict[str, Any]]) -> ReviewSummaryResult | None:
        for b in blocks:
            if b.get("type") == "tool_use" and b.get("name") == "submit_review_summary":
                inp = b.get("input") or {}
                return ReviewSummaryResult(
                    overall_summary=inp.get("overall_summary", "") or "",
                    strengths=list(inp.get("strengths") or []),
                    concerns=list(inp.get("concerns") or []),
                    criterion_assessments=list(inp.get("criterion_assessments") or []),
                    recommended_score=inp.get("recommended_score"),
                    confidence_level=inp.get("confidence_level", "low") or "low",
                )
        return None


# ── Rule-based fallback ──────────────────────────────────────────────────────


def _rule_based_summary(
    student: dict[str, Any],
    program: dict[str, Any],
    rubric_criteria: list[dict[str, Any]],
) -> ReviewSummaryResult:
    """Deterministic summary from the structured packet. This is what tests
    (mock mode) and any environment without Opus see — it must be genuinely
    useful, not a placeholder."""
    name = student.get("name") or "This applicant"
    academics = student.get("academics") or []
    test_scores = student.get("test_scores") or []
    activities = student.get("activities") or []
    program_name = program.get("name") or "the program"

    best_gpa: float | None = None
    gpa_inst: str | None = None
    for rec in academics:
        try:
            g = float(rec.get("gpa")) if rec.get("gpa") not in (None, "") else None
        except (TypeError, ValueError):
            g = None
        if g is not None and (best_gpa is None or g > best_gpa):
            best_gpa, gpa_inst = g, rec.get("institution")

    strengths: list[dict[str, Any]] = []
    concerns: list[dict[str, Any]] = []

    if best_gpa is not None:
        strengths.append(
            {
                "text": f"Strong academic record (GPA {best_gpa}).",
                "source_field": "academics.gpa",
                "evidence": f"GPA {best_gpa}" + (f" at {gpa_inst}" if gpa_inst else ""),
            }
        )
    if test_scores:
        ts = test_scores[0]
        strengths.append(
            {
                "text": f"Submitted standardized testing ({ts.get('type', 'test')}).",
                "source_field": "test_scores",
                "evidence": f"{ts.get('type', 'test')}: {ts.get('total', 'n/a')}",
            }
        )
    if activities:
        strengths.append(
            {
                "text": f"Engaged beyond academics ({len(activities)} activities).",
                "source_field": "activities",
                "evidence": ", ".join(a.get("title", "") for a in activities[:3] if a.get("title"))
                or f"{len(activities)} activities",
            }
        )

    if not test_scores:
        concerns.append(
            {
                "text": (
                    "No standardized test scores on file (treat per test-optional "
                    "policy — never a penalty)."
                ),
                "source_field": "test_scores",
                "evidence": "No test_scores records.",
            }
        )
    if not activities:
        concerns.append(
            {
                "text": "Limited extracurricular signal on file.",
                "source_field": "activities",
                "evidence": "No activities records.",
            }
        )

    criterion_assessments: list[dict[str, Any]] = []
    for c in rubric_criteria:
        cname = c.get("name") or "Criterion"
        criterion_assessments.append(
            {
                "criterion_name": cname,
                "score": None,
                "assessment": (
                    f"Rule-based placeholder for {cname}; reviewer to score. "
                    "Full AI assessment available when the review model is enabled."
                ),
                "evidence": [],
            }
        )

    parts = [f"{name} applied to {program_name}."]
    if best_gpa is not None:
        parts.append(f"Academic record shows a GPA of {best_gpa}.")
    if activities:
        parts.append(f"They list {len(activities)} extracurricular activities.")
    parts.append(
        "Showing a rule-based summary (enable the review model for the full Opus summary)."
    )
    overall = " ".join(parts)

    # Coarse heuristic recommendation, only when there's enough signal.
    rec_score: float | None = None
    if best_gpa is not None:
        rec_score = round(min(10.0, max(0.0, (best_gpa / 4.0) * 7 + len(activities) * 0.5)), 1)

    completeness = sum(bool(x) for x in (academics, test_scores, activities))
    confidence = "high" if completeness == 3 else "medium" if completeness == 2 else "low"

    return ReviewSummaryResult(
        overall_summary=overall,
        strengths=strengths,
        concerns=concerns,
        criterion_assessments=criterion_assessments,
        recommended_score=rec_score,
        confidence_level=confidence,
        is_stub=True,
    )


# ── Singleton ───────────────────────────────────────────────────────────────

_default: DraftSummarizerForReview | None = None


def get_review_summarizer() -> DraftSummarizerForReview:
    global _default
    if _default is None:
        _default = DraftSummarizerForReview()
    return _default


def reset_review_summarizer() -> None:
    """Test helper."""
    global _default
    _default = None
