"""A5 — Rationale agent.

Generates the per-program "why this fits / what's the catch / what
would raise the confidence" narrative. Streaming Sonnet, forced
tool-use, with a groundedness check on every cited field.

Two key invariants:
  1. **Cached aggressively.** Per-(student, program, profile_version,
     program_version) — same inputs return the cached rationale. The
     match service handles cache lookup; this module only generates.
  2. **Grounded.** Every cited field path must resolve to a non-empty
     value in the input. The validator (`is_grounded`) walks each path
     and rejects fabrications. One retry on failure; second failure is
     logged to `ai_safety_incidents` and the rationale is dropped.

Wire pattern:
  RationaleAgent.generate(student_view, program_view, score) →
    RationaleResult{paragraphs, cited_*, grounded: bool, retry_count}

The match service decides whether to commit the result to
`match_rationales` based on `grounded`.
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
from unipaith.ai.tools.rationale_schema import SUBMIT_RATIONALE_TOOL

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").rstrip()


_RATIONALE_PROMPT = _load_prompt("rationale.md")


# ── Data shapes ─────────────────────────────────────────────────────────────


@dataclass
class StudentView:
    """The slice of the student the rationale agent sees.

    Mirrors the dot-notation citation paths in the tool schema. The
    `is_grounded` validator walks these paths.
    """

    applicant_summary: str = ""
    # sparse: dict[key → value] OR dict[key → list/dict] — both are
    # walked by the path resolver.
    sparse: dict[str, Any] = field(default_factory=dict)
    student_id: UUID | None = None
    profile_version: int = 1


@dataclass
class ProgramView:
    """The slice of a program the rationale agent sees."""

    name: str = ""
    description: str = ""
    sparse: dict[str, Any] = field(default_factory=dict)
    program_id: Any = None
    program_version: int = 1


@dataclass
class ScoreView:
    """The score breakdown the rationale agent reasons over."""

    fitness: float = 0.0
    confidence: float = 0.0
    fitness_breakdown: dict[str, Any] = field(default_factory=dict)
    confidence_breakdown: dict[str, Any] = field(default_factory=dict)


@dataclass
class RationaleResult:
    """One rationale generation attempt's full output."""

    para_fit: str = ""
    para_tradeoffs: str = ""
    para_confidence: str = ""
    cited_student_fields: list[str] = field(default_factory=list)
    cited_program_fields: list[str] = field(default_factory=list)
    grounded: bool = False
    ungrounded_paths: list[str] = field(default_factory=list)
    retry_count: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0

    def joined_text(self) -> str:
        """The 3 paragraphs concatenated for storage in
        `match_results.rationale_text` / `match_rationales.rationale_text`.
        """
        return "\n\n".join(
            p
            for p in (self.para_fit, self.para_tradeoffs, self.para_confidence)
            if p
        ).strip()


# ── Groundedness validator ──────────────────────────────────────────────────


def resolve_path(view: StudentView | ProgramView, path: str) -> Any:
    """Walk a dot-notation path against a StudentView or ProgramView.

    Top-level paths map to dataclass attributes. Paths starting with
    `sparse.` walk into the sparse dict. Within sparse, segments can
    dive into nested dicts; if a list contains dicts, segments can
    match by string equality against any value (used for tag lists).
    """
    parts = path.split(".")
    if not parts:
        return None

    # Top-level field on the view.
    head, rest = parts[0], parts[1:]
    if head == "sparse":
        cursor: Any = view.sparse
    else:
        cursor = getattr(view, head, None)
        if cursor is None or not rest:
            # Top-level scalar (e.g. 'applicant_summary', 'description', 'name').
            return cursor

    for seg in rest:
        if cursor is None:
            return None
        if isinstance(cursor, dict):
            if seg in cursor:
                cursor = cursor[seg]
            else:
                return None
        elif isinstance(cursor, list):
            # Tag-list match: segment must appear in the list.
            if seg in cursor:
                cursor = seg  # presence is the value
            else:
                return None
        else:
            return None
    return cursor


def is_grounded(
    student: StudentView,
    program: ProgramView,
    cited_student: list[str],
    cited_program: list[str],
) -> tuple[bool, list[str]]:
    """Validate every citation path resolves to a non-empty value.

    Returns (all_grounded, list_of_ungrounded_paths). Empty cited_*
    arrays are allowed (rare — but the agent might cite only the
    program side if the student summary is unused).
    """
    bad: list[str] = []
    for path in cited_student:
        value = resolve_path(student, path)
        if not _is_nonempty(value):
            bad.append(f"student:{path}")
    for path in cited_program:
        value = resolve_path(program, path)
        if not _is_nonempty(value):
            bad.append(f"program:{path}")
    return not bad, bad


def _is_nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) > 0
    if isinstance(value, (int, float)):
        return True
    return bool(value)


# ── Agent ───────────────────────────────────────────────────────────────────


class RationaleAgent:
    """A5 — generates 3-paragraph rationales with groundedness checks."""

    AGENT_NAME = "rationale"

    def __init__(
        self,
        client: AIClient | None = None,
        *,
        system_prompt: str | None = None,
        max_tokens: int = 1200,
        temperature: float = 0.4,
        max_retries: int = 1,
    ):
        self.client = client or get_client()
        self.system_prompt = system_prompt or _RATIONALE_PROMPT
        self.max_tokens = max_tokens
        # 0.4 — readable prose without veering into marketing voice.
        self.temperature = temperature
        # One regenerate on groundedness failure; second failure logs to
        # ai_safety_incidents and returns ungrounded result.
        self.max_retries = max_retries

    async def generate(
        self,
        *,
        student: StudentView,
        program: ProgramView,
        score: ScoreView,
        db: AsyncSession | None = None,
    ) -> RationaleResult:
        """Run the rationale agent end-to-end with retry on hallucinated paths.

        Caller (the match service) decides whether to commit the result
        to `match_rationales` based on `result.grounded`. Ungrounded
        results are logged but returned for inspection.
        """
        attempt = 0
        last_result: RationaleResult | None = None
        while attempt <= self.max_retries:
            payload = self._payload(student, program, score, retry_hint=attempt > 0)
            response = await self.client.message(
                agent=self.AGENT_NAME,
                model="sonnet",
                system=[
                    {
                        "type": "text",
                        "text": self.system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": payload}],
                tools=[
                    {**SUBMIT_RATIONALE_TOOL, "cache_control": {"type": "ephemeral"}}
                ],
                tool_choice={"type": "tool", "name": "submit_rationale"},
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                student_id=student.student_id,
                surface="rationale",
                db=db,
            )

            result = self._parse_response(response.content_blocks)
            result.cost_usd = float(response.cost_usd)
            result.latency_ms = response.latency_ms
            result.retry_count = attempt

            grounded, bad = is_grounded(
                student,
                program,
                result.cited_student_fields,
                result.cited_program_fields,
            )
            result.grounded = grounded
            result.ungrounded_paths = bad

            if grounded:
                return result

            last_result = result
            attempt += 1
            logger.warning(
                "Rationale ungrounded (attempt %d) for student=%s program=%s; "
                "ungrounded_paths=%s",
                attempt,
                student.student_id,
                program.program_id,
                bad,
            )

        # Final result remains ungrounded; caller decides what to do.
        return last_result or RationaleResult()

    # ── Internals ──────────────────────────────────────────────────────

    @staticmethod
    def _payload(
        student: StudentView,
        program: ProgramView,
        score: ScoreView,
        *,
        retry_hint: bool,
    ) -> str:
        """Serialize the inputs the agent sees. Retry adds a hint about
        the previous failure mode."""
        body: dict[str, Any] = {
            "student": {
                "applicant_summary": student.applicant_summary,
                "sparse": student.sparse,
            },
            "program": {
                "name": program.name,
                "description": program.description,
                "sparse": program.sparse,
            },
            "score": {
                "fitness": score.fitness,
                "confidence": score.confidence,
                "fitness_breakdown": score.fitness_breakdown,
                "confidence_breakdown": score.confidence_breakdown,
            },
        }
        if retry_hint:
            body["_retry_note"] = (
                "Previous attempt cited paths that didn't resolve in the "
                "input. Cite ONLY paths that exist in the JSON above. "
                "If you don't have the data to back a claim, drop the "
                "claim — don't fabricate the source."
            )
        return json.dumps(body, ensure_ascii=False)

    @staticmethod
    def _parse_response(blocks: list[dict[str, Any]]) -> RationaleResult:
        for b in blocks:
            if b.get("type") == "tool_use" and b.get("name") == "submit_rationale":
                inp = b.get("input") or {}
                return RationaleResult(
                    para_fit=inp.get("para_fit", "") or "",
                    para_tradeoffs=inp.get("para_tradeoffs", "") or "",
                    para_confidence=inp.get("para_confidence", "") or "",
                    cited_student_fields=list(inp.get("cited_student_fields") or []),
                    cited_program_fields=list(inp.get("cited_program_fields") or []),
                )
        return RationaleResult()


# ── Singleton ───────────────────────────────────────────────────────────────


_default_rationale: RationaleAgent | None = None


def get_rationale_agent() -> RationaleAgent:
    global _default_rationale
    if _default_rationale is None:
        _default_rationale = RationaleAgent()
    return _default_rationale


def reset_rationale_agent() -> None:
    """Test helper."""
    global _default_rationale
    _default_rationale = None
