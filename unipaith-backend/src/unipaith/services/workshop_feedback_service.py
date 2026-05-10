"""Phase A — Workshop feedback service (feedback-only).

Deterministic stub generators for essay / interview / test. Plan 2 will
replace the generator bodies with LLM calls — but the response shape is
fixed at the schema layer, so even Plan 2 can't slip in `revised_text`.

Heuristics used in stubs:
  essay     — length, paragraph count, presence of intro/conclusion words,
              first-person count, presence of structural transition words
  interview — pulls 5+ canned questions from a typed bank by interview_type
  test      — gap analysis from current_score → target_score
"""

from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import NotFoundException
from unipaith.models.student import StudentProfile
from unipaith.models.workshops import WorkshopFeedbackRun
from unipaith.schemas.workshop_feedback import (
    EssayFeedbackRequest,
    InterviewPracticeRequest,
    TestGuidanceRequest,
)

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

    # ── Interview ────────────────────────────────────────────────────────
    async def request_interview_practice(
        self, user_id: UUID, body: InterviewPracticeRequest
    ) -> WorkshopFeedbackRun:
        student_id = await self._student_id(user_id)
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
