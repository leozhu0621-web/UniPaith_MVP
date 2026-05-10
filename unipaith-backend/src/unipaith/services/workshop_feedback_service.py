"""Workshop feedback service (feedback-only).

Two paths per domain (essay / interview / test):

  - LLM path:  WorkshopCoach (A6 + C2) when settings.ai_workshops_v2_enabled
               AND coach output is well-formed AND judge passes
  - Stub path: deterministic rule-based heuristic when the flag is off OR
               the coach fails / trips the guardrail

Why fallback rather than fail loud: workshops are coaching, not auth — a
graceful stub is more useful than a 500. The LLM path is logged via the
AIClient (cost / latency / cache hit) so eval can compare quality over
time.

Heuristics used in stubs:
  essay     — length, paragraph count, presence of intro/conclusion words,
              first-person count, presence of structural transition words
  interview — pulls 5+ canned questions from a typed bank by interview_type
  test      — gap analysis from current_score → target_score
"""

from __future__ import annotations

import logging
import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.exceptions import NotFoundException
from unipaith.models.student import StudentProfile
from unipaith.models.workshops import WorkshopFeedbackRun
from unipaith.schemas.workshop_feedback import (
    EssayFeedbackRequest,
    InterviewPracticeRequest,
    TestGuidanceRequest,
)

logger = logging.getLogger(__name__)

# ── Canned interview question banks (Phase A stubs) ───────────────────────

_BEHAVIORAL_QUESTIONS = [
    (
        "Tell me about a time you led a team through a difficult decision.",
        "Probes leadership + conflict resolution under uncertainty.",
    ),
    (
        "Describe a project that didn't go as planned. What did you learn?",
        "Looks for self-awareness + iteration mindset.",
    ),
    (
        "Walk me through a moment when you changed someone's mind.",
        "Tests persuasion + listening — both essential in cohort settings.",
    ),
    (
        "Give an example of working with someone whose values differed from yours.",
        "Programs care about cohort cohesion across diverse perspectives.",
    ),
    (
        "What's the toughest feedback you've received and how did you act on it?",
        "Shows growth orientation.",
    ),
    (
        "Describe a time you had to choose between two good options.",
        "Reveals decision frameworks under ambiguity.",
    ),
]

_TECHNICAL_QUESTIONS = [
    (
        "Walk me through a technical project end-to-end — design through deployment.",
        "Probes depth across the full lifecycle.",
    ),
    (
        "What tradeoff did you make in your most recent technical decision?",
        "Engineering maturity is about tradeoffs, not 'best practices.'",
    ),
    (
        "How would you approach a problem you've never seen before?",
        "Methodology > memorized answers.",
    ),
    (
        "Describe a bug that taught you something fundamental.",
        "Look for curiosity + root-cause reasoning.",
    ),
    (
        "What would you do differently if you started your last project today?",
        "Tests reflective practice.",
    ),
]

_GENERAL_QUESTIONS = [
    (
        "Why this program specifically — beyond rankings?",
        "Programs sniff out generic answers fast.",
    ),
    (
        "Where do you see yourself five years post-graduation?",
        "Tests goal clarity + alignment with program outcomes.",
    ),
    (
        "What would you contribute to the cohort that's hard to find elsewhere?",
        "Forces self-differentiation.",
    ),
    (
        "What's one assumption you held a year ago that you've since revised?",
        "Reveals intellectual humility.",
    ),
    (
        "Tell me about a non-academic interest you'd bring to campus.",
        "Cohort fit signals — programs want people, not transcripts.",
    ),
]

# ── Test-prep gap-analysis bands ───────────────────────────────────────────

_TEST_GAP_BANDS = {
    "small": (1, 50),  # tighten weak sub-sections
    "medium": (51, 150),  # structured prep, 4-8 weeks
    "large": (151, 1000),  # foundation work, 8+ weeks
}


class WorkshopFeedbackService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _student_id(self, user_id: UUID) -> UUID:
        result = await self.db.execute(
            select(StudentProfile.id).where(StudentProfile.user_id == user_id)
        )
        sid = result.scalar_one_or_none()
        if sid is None:
            raise NotFoundException("Student profile not found")
        return sid

    # ── Essay ────────────────────────────────────────────────────────────
    @staticmethod
    def _score_essay(essay_text: str) -> tuple[dict, list, list]:
        """Phase A heuristic. Returns (rubric_scores, structural_issues,
        missing_elements). All rubric scores on a 0..5 float scale."""
        text = essay_text.strip()
        word_count = len(text.split())
        paragraphs = [p for p in text.split("\n\n") if p.strip()]
        para_count = len(paragraphs) or 1
        sentences = re.split(r"[.!?]+\s+", text)
        avg_sentence_len = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        first_person_count = sum(1 for w in text.lower().split() if w in {"i", "me", "my", "mine"})
        first_person_rate = first_person_count / max(word_count, 1)

        # Rubric — five dimensions, all 0..5.
        scores = {
            "length_appropriateness": 5.0
            if 250 <= word_count <= 800
            else (3.5 if 150 <= word_count < 250 or 800 < word_count <= 1200 else 2.0),
            "paragraph_structure": 5.0 if para_count >= 3 else (3.5 if para_count == 2 else 2.0),
            "sentence_flow": 5.0
            if 12 <= avg_sentence_len <= 22
            else (3.5 if 8 <= avg_sentence_len < 12 or 22 < avg_sentence_len <= 30 else 2.5),
            "first_person_voice": 5.0
            if 0.02 <= first_person_rate <= 0.08
            else (3.5 if first_person_rate < 0.02 else 2.5),
            "structural_signals": 4.0
            if any(w in text.lower() for w in ("first,", "second,", "however,", "in conclusion"))
            else 2.5,
        }

        # Structural issues — what's *concretely* off the heuristic ideal.
        issues = []
        if word_count < 150:
            issues.append(
                {
                    "issue": (
                        "Essay is much shorter than typical app responses (target 400–650 words)."
                    ),
                    "severity": "major",
                    "location_ref": "overall length",
                }
            )
        if para_count < 3:
            issues.append(
                {
                    "issue": (
                        "Fewer than three paragraphs — admissions readers "
                        "expect intro/body/conclusion structure."
                    ),
                    "severity": "moderate",
                    "location_ref": "paragraph count",
                }
            )
        if avg_sentence_len > 30:
            issues.append(
                {
                    "issue": (
                        "Average sentence length is high — consider splitting compound sentences."
                    ),
                    "severity": "minor",
                    "location_ref": "sentence-level",
                }
            )

        # Missing elements — coaching prompts, not rewrites.
        missing = []
        if not any(w in text.lower() for w in ("learned", "discovered", "realized", "changed")):
            missing.append(
                {
                    "element": (
                        "An explicit reflection / change moment — what did you learn or revise?"
                    ),
                    "importance": "should_have",
                }
            )
        if not any(w in text.lower() for w in ("future", "plan", "next", "after")):
            missing.append(
                {
                    "element": ("A forward-looking sentence connecting the essay to your goals."),
                    "importance": "should_have",
                }
            )
        if first_person_count == 0:
            missing.append(
                {
                    "element": ("First-person voice — make sure 'I' / 'my' anchor the narrative."),
                    "importance": "required",
                }
            )

        return scores, issues, missing

    async def request_essay_feedback(
        self, user_id: UUID, body: EssayFeedbackRequest
    ) -> WorkshopFeedbackRun:
        student_id = await self._student_id(user_id)

        # Plan 2 path — try the LLM coach first when the flag is on. Fall
        # through to the rule-based stub on any failure so the caller
        # always gets feedback.
        if settings.ai_workshops_v2_enabled:
            llm_payload = await self._try_essay_coach(student_id, body)
            if llm_payload is not None:
                rubric, issues, missing, questions = llm_payload
                run = WorkshopFeedbackRun(
                    student_id=student_id,
                    domain="essay",
                    input_artifact_id=str(body.document_id) if body.document_id else None,
                    prompt_text=body.prompt_text,
                    rubric_scores=rubric,
                    structural_issues=issues,
                    missing_elements=missing,
                    suggested_questions=questions,
                    is_stub=False,
                )
                self.db.add(run)
                await self.db.flush()
                await self.db.refresh(run)
                return run

        rubric, issues, missing = self._score_essay(body.essay_text)
        run = WorkshopFeedbackRun(
            student_id=student_id,
            domain="essay",
            input_artifact_id=str(body.document_id) if body.document_id else None,
            prompt_text=body.prompt_text,
            rubric_scores=rubric,
            structural_issues=issues,
            missing_elements=missing,
            suggested_questions=[],
            is_stub=True,
        )
        self.db.add(run)
        await self.db.flush()
        await self.db.refresh(run)
        return run

    # ── LLM helpers (Plan 2 swap-ins) ────────────────────────────────────
    async def _try_essay_coach(
        self, student_id: UUID, body: EssayFeedbackRequest
    ) -> tuple[dict, list, list, list] | None:
        """Run the A6 essay coach. Returns (rubric, issues, missing, questions)
        on success, None on any failure (logged + falls through to stub).

        Maps CoachFeedback (1–5 int rubric, list[str] missing_elements,
        list[str] questions_for_student) into the WorkshopFeedbackRun shape
        (float rubric, dict missing_elements, dict suggested_questions)."""
        try:
            from unipaith.ai.coach import EssayDraft, get_workshop_coach
        except Exception as e:  # noqa: BLE001
            logger.warning("workshop coach import failed; falling back: %s", e)
            return None

        try:
            coach = get_workshop_coach()
            draft = EssayDraft(
                draft_text=body.essay_text,
                prompt_text=body.prompt_text or "",
                word_count=len(body.essay_text.split()),
            )
            result = await coach.coach_essay(draft=draft, student_id=student_id, db=self.db)
        except Exception as e:  # noqa: BLE001
            logger.warning("essay coach call failed; falling back: %s", e)
            return None

        if not result.passed:
            logger.info(
                "essay coach guardrail failed (judge.score=%s, evidence=%s); falling back",
                result.verdict.score,
                result.verdict.evidence[:120],
            )
            return None

        fb = result.feedback
        # 1–5 int → float, structural_issues already dict-shaped (issue/severity/
        # location_ref) per the coach prompt contract — pass through.
        rubric = {k: float(v) for k, v in fb.rubric_scores.items()}
        # Wrap raw strings into the schema's dict shape.
        missing = [{"element": s, "importance": "should_have"} for s in fb.missing_elements]
        questions = [
            {"question": q, "why": fb.prompt_alignment_notes or ""}
            for q in fb.questions_for_student
        ]
        return rubric, fb.structural_issues, missing, questions

    # ── Interview ────────────────────────────────────────────────────────
    async def request_interview_practice(
        self, user_id: UUID, body: InterviewPracticeRequest
    ) -> WorkshopFeedbackRun:
        student_id = await self._student_id(user_id)

        if settings.ai_workshops_v2_enabled:
            llm_payload = await self._try_interview_coach(student_id, body)
            if llm_payload is not None:
                rubric, issues, missing, questions = llm_payload
                run = WorkshopFeedbackRun(
                    student_id=student_id,
                    domain="interview",
                    input_artifact_id=(
                        str(body.target_program_id) if body.target_program_id else None
                    ),
                    prompt_text=body.focus_area,
                    rubric_scores=rubric,
                    structural_issues=issues,
                    missing_elements=missing,
                    suggested_questions=questions,
                    is_stub=False,
                )
                self.db.add(run)
                await self.db.flush()
                await self.db.refresh(run)
                return run

        bank = {
            "behavioral": _BEHAVIORAL_QUESTIONS,
            "technical": _TECHNICAL_QUESTIONS,
            "general": _GENERAL_QUESTIONS,
        }[body.interview_type]
        questions = [{"question": q, "why": w} for q, w in bank[:5]]
        # Minimal "rubric" framing on what to evaluate — keeps the
        # response shape consistent across domains.
        rubric = {
            "specificity": 0.0,
            "structure_STAR": 0.0,
            "ownership": 0.0,
            "reflection": 0.0,
        }
        run = WorkshopFeedbackRun(
            student_id=student_id,
            domain="interview",
            input_artifact_id=str(body.target_program_id) if body.target_program_id else None,
            prompt_text=body.focus_area,
            rubric_scores=rubric,
            structural_issues=[],
            missing_elements=[],
            suggested_questions=questions,
            is_stub=True,
        )
        self.db.add(run)
        await self.db.flush()
        await self.db.refresh(run)
        return run

    async def _try_interview_coach(
        self, student_id: UUID, body: InterviewPracticeRequest
    ) -> tuple[dict, list, list, list] | None:
        """Run the interview coach to score `response_text`. When the
        request body has no response_text, no-ops so the caller falls
        back to the rule-based bank (the user wants prompts, not
        coaching)."""
        if not body.response_text:
            return None
        try:
            from unipaith.ai.coach import InterviewResponse, get_workshop_coach
        except Exception as e:  # noqa: BLE001
            logger.warning("interview coach import failed; falling back: %s", e)
            return None
        try:
            coach = get_workshop_coach()
            resp = InterviewResponse(
                response_text=body.response_text,
                question_text=body.question_text or "",
                program_name="",
                institution_name="",
                interview_format=body.interview_type,
            )
            result = await coach.coach_interview(  # type: ignore[attr-defined]
                response=resp, student_id=student_id, db=self.db
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("interview coach call failed; falling back: %s", e)
            return None

        if not result.passed:
            logger.info("interview coach guardrail failed; falling back to rule-based bank")
            return None

        fb = result.feedback
        rubric = {k: float(v) for k, v in fb.rubric_scores.items()}
        missing = [{"element": s, "importance": "should_have"} for s in fb.missing_elements]
        # clarifying_questions → suggested_questions (Phase A schema). The
        # delivery_notes carry through as structural_issues with severity
        # 'minor' since they're polish, not blockers.
        questions = [
            {"question": q, "why": "Targeted to your response."} for q in fb.clarifying_questions
        ]
        issues = list(fb.response_issues) + [
            {"issue": n, "severity": "minor", "location_ref": "delivery"} for n in fb.delivery_notes
        ]
        return rubric, issues, missing, questions

    # ── Test guidance ────────────────────────────────────────────────────
    @staticmethod
    def _gap_band(gap: float) -> str:
        for band, (lo, hi) in _TEST_GAP_BANDS.items():
            if lo <= gap <= hi:
                return band
        return "large"

    async def request_test_guidance(
        self, user_id: UUID, body: TestGuidanceRequest
    ) -> WorkshopFeedbackRun:
        student_id = await self._student_id(user_id)

        if settings.ai_workshops_v2_enabled:
            llm_payload = await self._try_test_coach(student_id, body)
            if llm_payload is not None:
                rubric, issues, missing, questions = llm_payload
                run = WorkshopFeedbackRun(
                    student_id=student_id,
                    domain="test",
                    input_artifact_id=body.test_type,
                    prompt_text=None,
                    rubric_scores=rubric,
                    structural_issues=issues,
                    missing_elements=missing,
                    suggested_questions=questions,
                    is_stub=False,
                )
                self.db.add(run)
                await self.db.flush()
                await self.db.refresh(run)
                return run

        missing: list[dict] = []
        rubric: dict[str, float] = {}
        if body.current_score is not None and body.target_score is not None:
            gap = body.target_score - body.current_score
            band = self._gap_band(abs(gap))
            rubric = {
                "current_score": float(body.current_score),
                "target_score": float(body.target_score),
                "gap": float(gap),
            }
            if gap <= 0:
                missing.append(
                    {
                        "element": (
                            "You're already at or above target — focus on "
                            "consistency rather than ramp."
                        ),
                        "importance": "nice_to_have",
                    }
                )
            else:
                missing.append(
                    {
                        "element": f"{band.capitalize()} gap — plan for "
                        + (
                            "section-level tightening (1-3 weeks)"
                            if band == "small"
                            else "structured prep (4-8 weeks)"
                            if band == "medium"
                            else "foundation work (8+ weeks)"
                        ),
                        "importance": "required" if band == "large" else "should_have",
                    }
                )
        else:
            missing.append(
                {
                    "element": (
                        "Provide both current_score and target_score for a tailored gap plan."
                    ),
                    "importance": "should_have",
                }
            )

        # Test-type specific guidance (canned).
        run = WorkshopFeedbackRun(
            student_id=student_id,
            domain="test",
            input_artifact_id=body.test_type,
            prompt_text=None,
            rubric_scores=rubric,
            structural_issues=[],
            missing_elements=missing,
            suggested_questions=[],
            is_stub=True,
        )
        self.db.add(run)
        await self.db.flush()
        await self.db.refresh(run)
        return run

    async def _try_test_coach(
        self, student_id: UUID, body: TestGuidanceRequest
    ) -> tuple[dict, list, list, list] | None:
        """Run the test-prep coach. Maps TestPrepFeedback (with
        section_diagnosis / priorities / resource_categories / timeline_notes)
        into the four canonical WorkshopFeedbackRun fields."""
        try:
            from unipaith.ai.coach import TestPrepContext, get_workshop_coach
        except Exception as e:  # noqa: BLE001
            logger.warning("test coach import failed; falling back: %s", e)
            return None
        try:
            coach = get_workshop_coach()
            ctx = TestPrepContext(
                test_type=body.test_type,
                target_score=str(body.target_score) if body.target_score is not None else "",
                current_diagnostic=(
                    {"overall": body.current_score} if body.current_score is not None else {}
                ),
            )
            result = await coach.coach_test_prep(  # type: ignore[attr-defined]
                context=ctx, student_id=student_id, db=self.db
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("test coach call failed; falling back: %s", e)
            return None

        if not result.passed:
            logger.info("test coach guardrail failed; falling back to stub")
            return None

        fb = result.feedback
        rubric = {k: float(v) for k, v in fb.rubric_scores.items()}
        # section_diagnosis is already dict-shaped from the coach prompt;
        # surface it as structural_issues (severity inferred per item).
        issues: list[dict] = []
        for item in fb.section_diagnosis:
            severity = item.get("severity") or "moderate"
            issues.append(
                {
                    "issue": str(item.get("section") or item.get("issue") or "section"),
                    "severity": severity,
                    "location_ref": item.get("location_ref"),
                }
            )
        # priorities → missing_elements (these are the prep moves to make).
        missing = [{"element": p, "importance": "should_have"} for p in fb.priorities]
        # resource_categories surface as suggestions (timeline_notes appended
        # to first if present).
        questions: list[dict] = []
        for cat in fb.resource_categories:
            questions.append({"question": cat, "why": fb.timeline_notes or ""})
        return rubric, issues, missing, questions

    # ── List ──────────────────────────────────────────────────────────────
    async def list_runs(
        self, user_id: UUID, *, domain: str | None = None
    ) -> list[WorkshopFeedbackRun]:
        student_id = await self._student_id(user_id)
        stmt = select(WorkshopFeedbackRun).where(WorkshopFeedbackRun.student_id == student_id)
        if domain is not None:
            stmt = stmt.where(WorkshopFeedbackRun.domain == domain)
        stmt = stmt.order_by(WorkshopFeedbackRun.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
