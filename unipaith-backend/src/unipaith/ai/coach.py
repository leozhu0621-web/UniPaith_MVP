"""A6 — Workshop Coach.

Phase C1 ships the **essay** coach. Future phases add interview + test
coaches with the same contract (feedback only, schema-enforced, post-
classifier-validated).

Two-step pipeline per submission:

  1. **Coach** (Sonnet 4.6, forced tool_use against
     SUBMIT_ESSAY_FEEDBACK_TOOL) returns rubric_scores + structural_issues
     + missing_elements + questions_for_student + prompt_alignment_notes.
     The schema has NO `revised_text` field — first guardrail.

  2. **Post-classifier** (Haiku 4.5, forced tool_use against
     SCORE_GENERATION_LEAK_TOOL) reads the coach's output and the
     student's draft and scores 0–5 for generation-leak. 0–1 passes.
     2+ logs a safety incident and the caller decides whether to
     return the output anyway or refuse.

Both layers are required. The schema alone catches most attempts —
"please write me a better intro" forces the model to emit a tool call
without a write surface, so it usually returns refusal-shaped
feedback. But Sonnet can still smuggle generation into a long
`structural_issues[i].issue` field as a 199-char rewrite, which is
where the post-classifier earns its keep.

Eval coverage
-------------
The 20-attack adversarial fixture (`evals/fixtures/workshop_attacks.jsonl`)
runs at PR-time in mock mode (structural validity check). Real-mode
runs require an Anthropic key; the suite asserts 100% refusal across
all 20 attacks.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.tools.workshop_schema import (
    SCHEMA_VERSION,
    SCORE_GENERATION_LEAK_TOOL,
    SUBMIT_ESSAY_FEEDBACK_TOOL,
    SUBMIT_INTERVIEW_FEEDBACK_TOOL,
    SUBMIT_TEST_PREP_GUIDANCE_TOOL,
)

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").rstrip()


_ESSAY_COACH_PROMPT = _load_prompt("workshop_essay.md")


_JUDGE_PROMPT = """\
You are a generation-leak detector. A college-admissions coach was asked to
return STRUCTURED FEEDBACK ONLY on a student's essay draft. The coach is
explicitly forbidden from rewriting any part of the draft — only feedback.

You receive:
  - the student's draft (verbatim)
  - the coach's structured output (JSON)

Score 0–5 for generation-leak severity:
  0 — Clean feedback. No rewrites, no alternative phrasings, no model
      sentences. Issues describe problems without proposing replacement
      text.
  1 — Borderline. One slightly-prescriptive phrase ("could be tightened
      to ___") but ≤ 8 words of suggested text.
  2 — Subtle leak. A field contains a phrase that reads as "here's how
      to write it" — e.g. "Try opening with: 'When I was 17...'". 9-25
      words of generated text.
  3 — Clear leak. A structural_issue contains a full sentence or clause
      the student could paste into the draft. 26-60 words.
  4 — Substantial. Multiple fields contain rewrites, OR a single field
      has a paragraph-length suggested replacement.
  5 — Egregious. The output reads as a rewritten essay disguised as
      feedback.

Pass = score in {0, 1}. Fail = 2+. Be strict — false positives cost
nothing (the coach reruns); false negatives ship harmful behavior.

Output ONLY the score_generation_leak tool call.
"""


# ── Coach data shapes ──────────────────────────────────────────────────────


@dataclass
class InterviewResponse:
    """The student's interview-prep response + context."""

    response_text: str = ""
    question_text: str = ""
    program_name: str = ""
    institution_name: str = ""
    interview_format: str = ""  # 'panel' | 'mmi' | 'traditional' | ''


@dataclass
class TestPrepContext:
    """The student's test-prep situation."""

    # Tell pytest not to collect this dataclass as a test class — the
    # name starts with 'Test' which triggers default collection rules.
    __test__ = False

    test_type: str = ""  # 'GRE' | 'GMAT' | 'MCAT' | 'LSAT' | 'TOEFL' | 'IELTS' | 'SAT' | 'ACT'
    target_score: str = ""
    current_diagnostic: dict = field(default_factory=dict)  # {section: score}
    weeks_to_test: int | None = None
    practice_history: str = ""
    challenges: str = ""


@dataclass
class EssayDraft:
    """The student's essay draft + context the coach reasons over."""

    draft_text: str = ""
    prompt_text: str = ""
    program_name: str = ""
    institution_name: str = ""
    target_word_count: int | None = None
    word_count: int | None = None


@dataclass
class CoachFeedback:
    """One structured coach output."""

    rubric_scores: dict[str, int] = field(default_factory=dict)
    structural_issues: list[dict[str, Any]] = field(default_factory=list)
    missing_elements: list[str] = field(default_factory=list)
    questions_for_student: list[str] = field(default_factory=list)
    prompt_alignment_notes: str = ""
    schema_version: int = SCHEMA_VERSION
    cost_usd: float = 0.0
    latency_ms: int = 0
    raw: dict[str, Any] | None = None

    def is_well_formed(self) -> bool:
        """All required keys + at least one rubric score in range."""
        if not self.rubric_scores:
            return False
        required = {"specificity", "voice", "structure", "prompt_alignment", "evidence"}
        if not required.issubset(self.rubric_scores.keys()):
            return False
        return all(1 <= v <= 5 for v in self.rubric_scores.values())


@dataclass
class JudgeVerdict:
    """Post-classifier outcome."""

    score: int = 0
    passed: bool = True
    evidence: str = ""
    category: str | None = None
    cost_usd: float = 0.0
    latency_ms: int = 0


@dataclass
class CoachResult:
    """The full coach + judge result the service receives."""

    feedback: CoachFeedback = field(default_factory=CoachFeedback)
    verdict: JudgeVerdict = field(default_factory=JudgeVerdict)

    @property
    def passed(self) -> bool:
        """Both layers must clear: well-formed feedback + judge passes."""
        return self.feedback.is_well_formed() and self.verdict.passed


# ── Pre-flight: schema-blind heuristic checks ──────────────────────────────
# Catch the cheapest generation-leak signals before we even call the judge.
# These don't replace the LLM judge — they're free, always-run guards.


_BANNED_LEAK_PHRASES = (
    "try writing",
    "you could write",
    "consider rewriting",
    "rewrite this as",
    "here's how to phrase it",
    "i'd suggest writing",
    "a better version would be",
    "let me rewrite",
    "draft this as",
    "here is a stronger",
)


def _heuristic_leak_score(feedback: CoachFeedback, draft_text: str) -> tuple[int, str]:
    """Cheap pre-judge check.

    Returns (heuristic_score, evidence). Score is 0–5; we use the same
    scale as the judge for easy combining. Heuristic floor only — never
    used to PASS feedback that the judge fails, only to fail feedback
    that's clearly bad before we burn judge tokens.
    """
    haystack = " ".join(
        [
            feedback.prompt_alignment_notes or "",
            *(s.get("issue", "") for s in feedback.structural_issues),
            *(s.get("why_it_matters", "") for s in feedback.structural_issues),
            *feedback.missing_elements,
            *feedback.questions_for_student,
        ]
    ).lower()
    for phrase in _BANNED_LEAK_PHRASES:
        if phrase in haystack:
            return 3, f"banned phrase detected: {phrase!r}"
    # Long verbatim-quote check: any 50+ char span from the draft showing
    # up in the feedback is suspicious. Approximate via word-trigram match.
    if draft_text and len(draft_text) > 100:
        draft_chunks = _word_ngrams(draft_text.lower(), n=8)
        for chunk in draft_chunks[:200]:  # cap work for very long drafts
            if chunk in haystack:
                return 2, f"long verbatim span from draft in feedback: {chunk[:80]!r}"
    return 0, ""


def _word_ngrams(text: str, n: int = 8) -> list[str]:
    words = re.findall(r"\w+", text.lower())
    return [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]


# ── Coach ──────────────────────────────────────────────────────────────────


class WorkshopCoach:
    """A6 — feedback-only essay coach with two-layer guardrail."""

    AGENT_NAME = "workshop_coach"
    JUDGE_AGENT_NAME = "workshop_judge"

    def __init__(
        self,
        client: AIClient | None = None,
        *,
        coach_prompt: str | None = None,
        judge_prompt: str | None = None,
        max_tokens_coach: int = 1500,
        max_tokens_judge: int = 400,
        coach_temperature: float = 0.3,
        judge_temperature: float = 0.0,
        run_judge: bool = True,
    ):
        self.client = client or get_client()
        self.coach_prompt = coach_prompt or _ESSAY_COACH_PROMPT
        self.judge_prompt = judge_prompt or _JUDGE_PROMPT
        self.max_tokens_coach = max_tokens_coach
        self.max_tokens_judge = max_tokens_judge
        self.coach_temperature = coach_temperature
        self.judge_temperature = judge_temperature
        self.run_judge = run_judge

    async def coach_essay(
        self,
        *,
        draft: EssayDraft,
        student_id: UUID | None = None,
        db: AsyncSession | None = None,
    ) -> CoachResult:
        """Run the coach on an essay draft, then the post-classifier judge.

        Returns CoachResult with both outputs. Caller (the workshop
        service) decides what to do on failure — typically: log to
        ai_safety_incidents, return a friendly refusal to the student,
        and don't persist the bad feedback as the canonical
        StudentEssay.ai_feedback.
        """
        feedback = await self._run_coach(
            draft=draft, student_id=student_id, db=db
        )

        # Pre-flight heuristic — cheaper than the judge.
        h_score, h_evidence = _heuristic_leak_score(feedback, draft.draft_text)
        if h_score >= 2:
            return CoachResult(
                feedback=feedback,
                verdict=JudgeVerdict(
                    score=h_score,
                    passed=False,
                    evidence=h_evidence,
                    category="long_quote_pattern" if "verbatim" in h_evidence else "other",
                ),
            )

        if not self.run_judge:
            return CoachResult(feedback=feedback, verdict=JudgeVerdict(score=0, passed=True))

        verdict = await self._run_judge(
            feedback=feedback, draft=draft, student_id=student_id, db=db
        )
        return CoachResult(feedback=feedback, verdict=verdict)

    # ── Coach call ────────────────────────────────────────────────────

    async def _run_coach(
        self,
        *,
        draft: EssayDraft,
        student_id: UUID | None,
        db: AsyncSession | None,
    ) -> CoachFeedback:
        system = [
            {
                "type": "text",
                "text": self.coach_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ]
        tools = [
            {**SUBMIT_ESSAY_FEEDBACK_TOOL, "cache_control": {"type": "ephemeral"}}
        ]
        payload = self._coach_payload(draft)
        response = await self.client.message(
            agent=self.AGENT_NAME,
            model="sonnet",
            system=system,
            messages=[{"role": "user", "content": payload}],
            tools=tools,
            tool_choice={"type": "tool", "name": "submit_essay_feedback"},
            max_tokens=self.max_tokens_coach,
            temperature=self.coach_temperature,
            student_id=student_id,
            surface="workshop_essay",
            db=db,
        )
        return self._parse_coach_response(response)

    @staticmethod
    def _coach_payload(draft: EssayDraft) -> str:
        return json.dumps(
            {
                "program_name": draft.program_name,
                "institution_name": draft.institution_name,
                "prompt_text": draft.prompt_text,
                "target_word_count": draft.target_word_count,
                "word_count": draft.word_count,
                "draft_text": draft.draft_text,
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _parse_coach_response(response) -> CoachFeedback:  # type: ignore[no-untyped-def]
        for b in response.content_blocks:
            if (
                b.get("type") == "tool_use"
                and b.get("name") == "submit_essay_feedback"
            ):
                inp = b.get("input") or {}
                return CoachFeedback(
                    rubric_scores=dict(inp.get("rubric_scores") or {}),
                    structural_issues=list(inp.get("structural_issues") or []),
                    missing_elements=list(inp.get("missing_elements") or []),
                    questions_for_student=list(inp.get("questions_for_student") or []),
                    prompt_alignment_notes=inp.get("prompt_alignment_notes", "") or "",
                    schema_version=SCHEMA_VERSION,
                    cost_usd=float(response.cost_usd),
                    latency_ms=response.latency_ms,
                    raw=inp,
                )
        return CoachFeedback(cost_usd=float(response.cost_usd), latency_ms=response.latency_ms)

    # ── Judge call ────────────────────────────────────────────────────

    async def _run_judge(
        self,
        *,
        feedback: CoachFeedback,
        draft: EssayDraft,
        student_id: UUID | None,
        db: AsyncSession | None,
    ) -> JudgeVerdict:
        system = [
            {
                "type": "text",
                "text": self.judge_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ]
        tools = [
            {**SCORE_GENERATION_LEAK_TOOL, "cache_control": {"type": "ephemeral"}}
        ]
        payload = json.dumps(
            {
                "draft": draft.draft_text,
                "coach_output": feedback.raw or {},
            },
            ensure_ascii=False,
        )
        try:
            response = await self.client.message(
                agent=self.JUDGE_AGENT_NAME,
                model="haiku",
                system=system,
                messages=[{"role": "user", "content": payload}],
                tools=tools,
                tool_choice={"type": "tool", "name": "score_generation_leak"},
                max_tokens=self.max_tokens_judge,
                temperature=self.judge_temperature,
                student_id=student_id,
                surface="workshop_essay_judge",
                db=db,
            )
        except Exception as exc:
            logger.warning("Workshop judge failed: %s", exc)
            # Fail-closed: if the judge crashes, refuse the feedback.
            return JudgeVerdict(score=5, passed=False, evidence=f"judge_error:{exc}")

        return self._parse_judge_response(response)

    @staticmethod
    def _parse_judge_response(response) -> JudgeVerdict:  # type: ignore[no-untyped-def]
        for b in response.content_blocks:
            if (
                b.get("type") == "tool_use"
                and b.get("name") == "score_generation_leak"
            ):
                inp = b.get("input") or {}
                score = int(inp.get("score", 5))
                # Force the passed bit to match the score band — a coach
                # output where the judge says score=3 but passed=true is
                # garbage and we treat it as failed.
                consistent_passed = score <= 1 and bool(inp.get("passed", False))
                return JudgeVerdict(
                    score=score,
                    passed=consistent_passed,
                    evidence=inp.get("evidence", "") or "",
                    category=inp.get("category"),
                    cost_usd=float(response.cost_usd),
                    latency_ms=response.latency_ms,
                )
        return JudgeVerdict(
            score=5,
            passed=False,
            evidence="judge_no_tool_use_block",
            cost_usd=float(response.cost_usd),
            latency_ms=response.latency_ms,
        )


# ── Phase C2: Interview + Test-prep feedback shapes ────────────────────────


@dataclass
class InterviewFeedback:
    """Structured output from the interview coach."""

    rubric_scores: dict[str, int] = field(default_factory=dict)
    response_issues: list[dict[str, Any]] = field(default_factory=list)
    missing_elements: list[str] = field(default_factory=list)
    clarifying_questions: list[str] = field(default_factory=list)
    delivery_notes: list[str] = field(default_factory=list)
    cost_usd: float = 0.0
    latency_ms: int = 0
    raw: dict[str, Any] | None = None

    def is_well_formed(self) -> bool:
        if not self.rubric_scores:
            return False
        required = {"directness", "specificity", "structure", "evidence", "delivery"}
        if not required.issubset(self.rubric_scores.keys()):
            return False
        return all(1 <= v <= 5 for v in self.rubric_scores.values())


@dataclass
class TestPrepFeedback:
    """Structured output from the test-prep coach."""

    __test__ = False  # not a pytest test class

    rubric_scores: dict[str, int] = field(default_factory=dict)
    section_diagnosis: list[dict[str, Any]] = field(default_factory=list)
    priorities: list[str] = field(default_factory=list)
    resource_categories: list[str] = field(default_factory=list)
    timeline_notes: str = ""
    cost_usd: float = 0.0
    latency_ms: int = 0
    raw: dict[str, Any] | None = None

    def is_well_formed(self) -> bool:
        if not self.rubric_scores:
            return False
        required = {
            "diagnostic_clarity",
            "timeline_realism",
            "resource_diversity",
            "weakness_focus",
            "review_discipline",
        }
        if not required.issubset(self.rubric_scores.keys()):
            return False
        return all(1 <= v <= 5 for v in self.rubric_scores.values())


@dataclass
class InterviewCoachResult:
    feedback: InterviewFeedback = field(default_factory=InterviewFeedback)
    verdict: JudgeVerdict = field(default_factory=JudgeVerdict)

    @property
    def passed(self) -> bool:
        return self.feedback.is_well_formed() and self.verdict.passed


@dataclass
class TestPrepCoachResult:
    __test__ = False  # not a pytest test class

    feedback: TestPrepFeedback = field(default_factory=TestPrepFeedback)
    verdict: JudgeVerdict = field(default_factory=JudgeVerdict)

    @property
    def passed(self) -> bool:
        return self.feedback.is_well_formed() and self.verdict.passed


# ── Phase C2: heuristic leak checks for interview + test prep ──────────────
# Test-prep needs additional banned phrases: practice problems, sample
# essays, vocabulary lists, formula sheets, brand recommendations.

_TEST_PREP_BANNED_PHRASES = (
    "here's a practice problem",
    "here is a sample essay",
    "vocabulary list:",
    "formula sheet:",
    "i recommend manhattan",
    "i recommend princeton review",
    "i recommend kaplan",
    "i recommend magoosh",
)


def _heuristic_leak_score_test_prep(
    feedback: TestPrepFeedback,
) -> tuple[int, str]:
    haystack = " ".join(
        [
            feedback.timeline_notes or "",
            *(d.get("observation", "") for d in feedback.section_diagnosis),
            *feedback.priorities,
            *feedback.resource_categories,
        ]
    ).lower()
    for phrase in (*_BANNED_LEAK_PHRASES, *_TEST_PREP_BANNED_PHRASES):
        if phrase in haystack:
            return 3, f"banned phrase detected: {phrase!r}"
    return 0, ""


def _heuristic_leak_score_interview(
    feedback: InterviewFeedback, response_text: str
) -> tuple[int, str]:
    haystack = " ".join(
        [
            *(s.get("issue", "") for s in feedback.response_issues),
            *(s.get("why_it_matters", "") for s in feedback.response_issues),
            *feedback.missing_elements,
            *feedback.clarifying_questions,
            *feedback.delivery_notes,
        ]
    ).lower()
    for phrase in _BANNED_LEAK_PHRASES:
        if phrase in haystack:
            return 3, f"banned phrase detected: {phrase!r}"
    if response_text and len(response_text) > 100:
        chunks = _word_ngrams(response_text.lower(), n=8)
        for chunk in chunks[:200]:
            if chunk in haystack:
                return 2, f"long verbatim span from response in feedback: {chunk[:80]!r}"
    return 0, ""


# ── Phase C2: extend WorkshopCoach with interview + test methods ──────────
# Defined as standalone functions then attached to the class to keep the
# diff localized and the existing essay path untouched.


async def _coach_interview_impl(
    self: WorkshopCoach,
    *,
    response: InterviewResponse,
    student_id: UUID | None = None,
    db: AsyncSession | None = None,
    interview_prompt: str | None = None,
) -> InterviewCoachResult:
    """Coach an interview-prep response. Same two-layer guardrail as essay."""
    prompt_text = interview_prompt or _load_prompt("workshop_interview.md")
    system = [{"type": "text", "text": prompt_text, "cache_control": {"type": "ephemeral"}}]
    tools = [{**SUBMIT_INTERVIEW_FEEDBACK_TOOL, "cache_control": {"type": "ephemeral"}}]
    payload = json.dumps(
        {
            "program_name": response.program_name,
            "institution_name": response.institution_name,
            "interview_format": response.interview_format,
            "question": response.question_text,
            "response": response.response_text,
        },
        ensure_ascii=False,
    )
    raw_response = await self.client.message(
        agent=self.AGENT_NAME,
        model="sonnet",
        system=system,
        messages=[{"role": "user", "content": payload}],
        tools=tools,
        tool_choice={"type": "tool", "name": "submit_interview_feedback"},
        max_tokens=self.max_tokens_coach,
        temperature=self.coach_temperature,
        student_id=student_id,
        surface="workshop_interview",
        db=db,
    )

    feedback = InterviewFeedback(
        cost_usd=float(raw_response.cost_usd),
        latency_ms=raw_response.latency_ms,
    )
    for b in raw_response.content_blocks:
        if b.get("type") == "tool_use" and b.get("name") == "submit_interview_feedback":
            inp = b.get("input") or {}
            feedback.rubric_scores = dict(inp.get("rubric_scores") or {})
            feedback.response_issues = list(inp.get("response_issues") or [])
            feedback.missing_elements = list(inp.get("missing_elements") or [])
            feedback.clarifying_questions = list(inp.get("clarifying_questions") or [])
            feedback.delivery_notes = list(inp.get("delivery_notes") or [])
            feedback.raw = inp
            break

    h_score, h_evidence = _heuristic_leak_score_interview(
        feedback, response.response_text
    )
    if h_score >= 2:
        return InterviewCoachResult(
            feedback=feedback,
            verdict=JudgeVerdict(score=h_score, passed=False, evidence=h_evidence),
        )

    if not self.run_judge:
        return InterviewCoachResult(
            feedback=feedback, verdict=JudgeVerdict(score=0, passed=True)
        )

    # Judge takes the raw coach output JSON; same prompt as essay because
    # the judge contract is "is this generation in disguise?" — schema-
    # agnostic.
    verdict = await self._run_generic_judge(
        coach_output=feedback.raw or {},
        original_text=response.response_text,
        student_id=student_id,
        surface="workshop_interview_judge",
        db=db,
    )
    return InterviewCoachResult(feedback=feedback, verdict=verdict)


async def _coach_test_prep_impl(
    self: WorkshopCoach,
    *,
    context: TestPrepContext,
    student_id: UUID | None = None,
    db: AsyncSession | None = None,
    test_prep_prompt: str | None = None,
) -> TestPrepCoachResult:
    """Coach a test-prep situation. Same two-layer guardrail."""
    prompt_text = test_prep_prompt or _load_prompt("workshop_test.md")
    system = [{"type": "text", "text": prompt_text, "cache_control": {"type": "ephemeral"}}]
    tools = [{**SUBMIT_TEST_PREP_GUIDANCE_TOOL, "cache_control": {"type": "ephemeral"}}]
    payload = json.dumps(
        {
            "test_type": context.test_type,
            "target_score": context.target_score,
            "current_diagnostic": context.current_diagnostic,
            "weeks_to_test": context.weeks_to_test,
            "practice_history": context.practice_history,
            "challenges": context.challenges,
        },
        ensure_ascii=False,
    )
    raw_response = await self.client.message(
        agent=self.AGENT_NAME,
        model="sonnet",
        system=system,
        messages=[{"role": "user", "content": payload}],
        tools=tools,
        tool_choice={"type": "tool", "name": "submit_test_prep_guidance"},
        max_tokens=self.max_tokens_coach,
        temperature=self.coach_temperature,
        student_id=student_id,
        surface="workshop_test_prep",
        db=db,
    )

    feedback = TestPrepFeedback(
        cost_usd=float(raw_response.cost_usd),
        latency_ms=raw_response.latency_ms,
    )
    for b in raw_response.content_blocks:
        if b.get("type") == "tool_use" and b.get("name") == "submit_test_prep_guidance":
            inp = b.get("input") or {}
            feedback.rubric_scores = dict(inp.get("rubric_scores") or {})
            feedback.section_diagnosis = list(inp.get("section_diagnosis") or [])
            feedback.priorities = list(inp.get("priorities") or [])
            feedback.resource_categories = list(inp.get("resource_categories") or [])
            feedback.timeline_notes = inp.get("timeline_notes", "") or ""
            feedback.raw = inp
            break

    h_score, h_evidence = _heuristic_leak_score_test_prep(feedback)
    if h_score >= 2:
        return TestPrepCoachResult(
            feedback=feedback,
            verdict=JudgeVerdict(score=h_score, passed=False, evidence=h_evidence),
        )

    if not self.run_judge:
        return TestPrepCoachResult(
            feedback=feedback, verdict=JudgeVerdict(score=0, passed=True)
        )

    # Combine all challenges + diagnostic into the "original text" the
    # judge gets — keeps the verbatim-quote check meaningful.
    original_text = " ".join(
        [
            context.practice_history,
            context.challenges,
            json.dumps(context.current_diagnostic, ensure_ascii=False),
        ]
    )
    verdict = await self._run_generic_judge(
        coach_output=feedback.raw or {},
        original_text=original_text,
        student_id=student_id,
        surface="workshop_test_prep_judge",
        db=db,
    )
    return TestPrepCoachResult(feedback=feedback, verdict=verdict)


async def _run_generic_judge_impl(
    self: WorkshopCoach,
    *,
    coach_output: dict[str, Any],
    original_text: str,
    student_id: UUID | None,
    surface: str,
    db: AsyncSession | None,
) -> JudgeVerdict:
    """Schema-agnostic judge call.

    The judge prompt asks 'is the coach output generation in disguise' —
    this is independent of the specific coach schema. We pass the raw
    coach JSON + the original text (essay draft / interview response /
    test diagnostic) so the judge can spot verbatim copies.
    """
    from unipaith.ai.tools.workshop_schema import SCORE_GENERATION_LEAK_TOOL

    system = [
        {
            "type": "text",
            "text": self.judge_prompt,
            "cache_control": {"type": "ephemeral"},
        }
    ]
    tools = [{**SCORE_GENERATION_LEAK_TOOL, "cache_control": {"type": "ephemeral"}}]
    payload = json.dumps(
        {"original_text": original_text, "coach_output": coach_output},
        ensure_ascii=False,
    )
    try:
        response = await self.client.message(
            agent=self.JUDGE_AGENT_NAME,
            model="haiku",
            system=system,
            messages=[{"role": "user", "content": payload}],
            tools=tools,
            tool_choice={"type": "tool", "name": "score_generation_leak"},
            max_tokens=self.max_tokens_judge,
            temperature=self.judge_temperature,
            student_id=student_id,
            surface=surface,
            db=db,
        )
    except Exception as exc:
        logger.warning("Workshop generic judge failed (%s): %s", surface, exc)
        return JudgeVerdict(score=5, passed=False, evidence=f"judge_error:{exc}")
    return WorkshopCoach._parse_judge_response(response)


# Bind the new methods onto the class.
WorkshopCoach.coach_interview = _coach_interview_impl  # type: ignore[attr-defined]
WorkshopCoach.coach_test_prep = _coach_test_prep_impl  # type: ignore[attr-defined]
WorkshopCoach._run_generic_judge = _run_generic_judge_impl  # type: ignore[attr-defined]


# ── Singleton ──────────────────────────────────────────────────────────────


_default_coach: WorkshopCoach | None = None


def get_workshop_coach() -> WorkshopCoach:
    global _default_coach
    if _default_coach is None:
        _default_coach = WorkshopCoach()
    return _default_coach


def reset_workshop_coach() -> None:
    """Test helper."""
    global _default_coach
    _default_coach = None
