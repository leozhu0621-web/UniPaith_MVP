"""
Review pipeline service — rubric management, reviewer assignment,
scoring, AI-assisted review summaries, and pipeline analytics.
"""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.ai.llm_client import get_llm_client
from unipaith.config import settings
from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.application import (
    AIPacketSummary,
    Application,
    ApplicationScore,
    ReviewAssignment,
    Rubric,
)
from unipaith.models.institution import Program, Reviewer
from unipaith.models.student import StudentProfile

logger = logging.getLogger(__name__)


class ReviewPipelineService:
    """Manages the admissions review pipeline for an institution."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def get_reviewer_by_user(self, user_id: UUID, institution_id: UUID) -> Reviewer:
        """Look up a Reviewer record by the user's account ID."""
        result = await self.db.execute(
            select(Reviewer).where(
                Reviewer.user_id == user_id,
                Reviewer.institution_id == institution_id,
            )
        )
        reviewer = result.scalar_one_or_none()
        if reviewer is None:
            raise NotFoundException("Reviewer profile not found for this user")
        return reviewer

    # ------------------------------------------------------------------
    # Rubric management
    # ------------------------------------------------------------------

    async def create_rubric(
        self,
        institution_id: UUID,
        rubric_name: str,
        criteria: list[dict],
        program_id: UUID | None = None,
    ) -> Rubric:
        """Create a scoring rubric for an institution.

        Args:
            institution_id: Owning institution.
            rubric_name: Human-readable rubric name.
            criteria: List of criterion dicts, each containing ``name``,
                ``weight``, ``max_score``, and optionally ``description``.
            program_id: Optional program scope.  ``None`` means institution-wide.

        Returns:
            The newly created :class:`Rubric`.

        Raises:
            BadRequestException: If criteria weights do not sum to 1.0 (within
                a tolerance of 0.01).
        """
        total_weight = sum(c.get("weight", 0) for c in criteria)
        if abs(total_weight - 1.0) > 0.01:
            raise BadRequestException(f"Criteria weights must sum to 1.0 (got {total_weight:.3f})")

        rubric = Rubric(
            institution_id=institution_id,
            program_id=program_id,
            rubric_name=rubric_name,
            criteria=criteria,
            is_active=True,
        )
        self.db.add(rubric)
        await self.db.flush()
        return rubric

    async def list_rubrics(
        self, institution_id: UUID, program_id: UUID | None = None
    ) -> list[Rubric]:
        """List active rubrics for an institution, optionally filtered by program.

        Returns institution-wide rubrics (``program_id IS NULL``) plus any
        rubrics scoped to *program_id* when provided.
        """
        stmt = select(Rubric).where(
            Rubric.institution_id == institution_id,
            Rubric.is_active.is_(True),
        )
        if program_id is not None:
            stmt = stmt.where((Rubric.program_id == program_id) | (Rubric.program_id.is_(None)))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Reviewer assignment
    # ------------------------------------------------------------------

    async def assign_reviewers(
        self, application_id: UUID, institution_id: UUID
    ) -> list[ReviewAssignment]:
        """Auto-assign reviewers to an application.

        Selects up to ``settings.review_max_reviewers`` reviewers from the
        institution who have remaining capacity (``current_workload <
        max_workload``), ordered by lowest workload first.

        Creates :class:`ReviewAssignment` records and increments each
        reviewer's ``current_workload``.  Transitions the application status to
        ``under_review`` if at least one reviewer is assigned.

        Returns:
            A list of created :class:`ReviewAssignment` instances.

        Raises:
            NotFoundException: If the application does not exist or does not
                belong to the institution.
            BadRequestException: If no reviewers are available.
        """
        # Verify application belongs to institution
        app_result = await self.db.execute(
            select(Application)
            .join(Program, Application.program_id == Program.id)
            .where(
                Application.id == application_id,
                Program.institution_id == institution_id,
            )
        )
        app = app_result.scalar_one_or_none()
        if not app:
            raise NotFoundException("Application not found for this institution")

        if app.status not in ("submitted", "under_review"):
            raise BadRequestException(
                "Only submitted or under-review applications can be assigned reviewers"
            )

        # Find available reviewers ordered by lowest workload
        reviewer_result = await self.db.execute(
            select(Reviewer)
            .where(
                Reviewer.institution_id == institution_id,
                Reviewer.current_workload < Reviewer.max_workload,
            )
            .order_by(Reviewer.current_workload.asc())
            .limit(settings.review_max_reviewers)
        )
        reviewers = list(reviewer_result.scalars().all())

        if not reviewers:
            raise BadRequestException("No reviewers available with remaining capacity")

        due_date = date.today() + timedelta(days=settings.review_default_due_days)
        assignments: list[ReviewAssignment] = []

        for reviewer in reviewers:
            assignment = ReviewAssignment(
                application_id=application_id,
                reviewer_id=reviewer.id,
                status="assigned",
                due_date=due_date,
            )
            self.db.add(assignment)
            reviewer.current_workload += 1
            assignments.append(assignment)

        # Transition application status
        app.status = "under_review"
        await self.db.flush()
        return assignments

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    async def score_application(
        self,
        reviewer_id: UUID,
        application_id: UUID,
        rubric_id: UUID,
        criterion_scores: dict,
        reviewer_notes: str | None = None,
    ) -> ApplicationScore:
        """Record a human reviewer's scores for an application.

        Args:
            reviewer_id: The reviewer submitting scores.
            application_id: Target application.
            rubric_id: The rubric used for scoring.
            criterion_scores: Mapping of criterion name to numeric score.
            reviewer_notes: Optional free-text notes.

        Returns:
            The created :class:`ApplicationScore`.

        Raises:
            NotFoundException: If the rubric does not exist or is inactive.
        """
        # Load rubric to compute weighted total
        rubric_result = await self.db.execute(
            select(Rubric).where(Rubric.id == rubric_id, Rubric.is_active.is_(True))
        )
        rubric = rubric_result.scalar_one_or_none()
        if not rubric:
            raise NotFoundException("Rubric not found or inactive")

        # Build weight lookup from rubric criteria
        weight_map: dict[str, float] = {c["name"]: c["weight"] for c in (rubric.criteria or [])}

        total_weighted: Decimal = Decimal("0")
        for criterion_name, score_value in criterion_scores.items():
            weight = weight_map.get(criterion_name, 0)
            total_weighted += Decimal(str(score_value)) * Decimal(str(weight))

        app_score = ApplicationScore(
            application_id=application_id,
            reviewer_id=reviewer_id,
            rubric_id=rubric_id,
            criterion_scores=criterion_scores,
            total_weighted_score=total_weighted,
            reviewer_notes=reviewer_notes,
            scored_by_type="human",
        )
        self.db.add(app_score)
        await self.db.flush()
        return app_score

    async def get_application_scores(self, application_id: UUID) -> list[ApplicationScore]:
        """Return all scores recorded for an application."""
        result = await self.db.execute(
            select(ApplicationScore).where(ApplicationScore.application_id == application_id)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # AI-assisted review
    # ------------------------------------------------------------------

    async def generate_ai_review_summary(self, application_id: UUID) -> dict:
        """Generate an AI-powered review summary for an application.

        Loads the student profile, their academic records, test scores,
        activities, and the target program requirements, then asks the LLM to
        produce a structured review summary.

        Returns:
            A dict with keys ``summary``, ``strengths``, ``concerns``,
            ``recommended_score_range``, and
            ``comparable_admitted_profiles``.

        Raises:
            NotFoundException: If the application or student profile cannot be
                found.
        """
        # Load application + program
        app_result = await self.db.execute(
            select(Application).where(Application.id == application_id)
        )
        app = app_result.scalar_one_or_none()
        if not app:
            raise NotFoundException("Application not found")

        program_result = await self.db.execute(select(Program).where(Program.id == app.program_id))
        program = program_result.scalar_one_or_none()
        if not program:
            raise NotFoundException("Program not found")

        # Load student profile with relationships
        profile_result = await self.db.execute(
            select(StudentProfile)
            .where(StudentProfile.id == app.student_id)
            .options(
                selectinload(StudentProfile.academic_records),
                selectinload(StudentProfile.test_scores),
                selectinload(StudentProfile.activities),
            )
        )
        profile = profile_result.scalar_one_or_none()
        if not profile:
            raise NotFoundException("Student profile not found")

        # Build student summary for prompt
        student_summary = {
            "name": f"{profile.first_name} {profile.last_name}",
            "nationality": profile.nationality,
            "bio": profile.bio_text,
            "goals": profile.goals_text,
            "academics": [
                {
                    "institution": r.institution_name,
                    "degree": r.degree_type,
                    "field": r.field_of_study,
                    "gpa": str(r.gpa) if r.gpa else None,
                }
                for r in profile.academic_records
            ],
            "test_scores": [
                {
                    "type": s.test_type,
                    "total": str(s.total_score) if s.total_score else None,
                }
                for s in profile.test_scores
            ],
            "activities": [
                {
                    "type": a.activity_type,
                    "title": a.title,
                    "organization": a.organization,
                }
                for a in profile.activities
            ],
        }

        program_summary = {
            "name": program.program_name,
            "degree_type": program.degree_type,
            "department": program.department,
            "requirements": program.requirements,
            "description": program.description_text,
        }

        system_prompt = (
            "You are an admissions review assistant. Given a student profile "
            "and program requirements, provide a structured review summary. "
            "Respond in valid JSON with keys: summary (string), strengths "
            "(list of strings), concerns (list of strings), "
            "recommended_score_range (object with min and max, each 0-10), "
            "comparable_admitted_profiles (string describing the type of "
            "students typically admitted to similar programs)."
        )

        user_content = (
            f"Student Profile:\n{json.dumps(student_summary, indent=2)}\n\n"
            f"Program:\n{json.dumps(program_summary, indent=2)}"
        )

        llm = get_llm_client()
        raw_response = await llm.generate_reasoning(system_prompt, user_content)

        # Parse LLM response — gracefully handle non-JSON
        try:
            review_data = json.loads(raw_response)
        except (json.JSONDecodeError, TypeError):
            logger.warning(
                "AI review response was not valid JSON for application %s",
                application_id,
            )
            review_data = {
                "summary": raw_response,
                "strengths": [],
                "concerns": [],
                "recommended_score_range": {"min": 0, "max": 10},
                "comparable_admitted_profiles": "Unable to determine.",
            }

        return review_data

    # ------------------------------------------------------------------
    # AI Packet Summary (rubric-aligned with evidence)
    # ------------------------------------------------------------------

    async def get_or_generate_packet_summary(
        self,
        institution_id: UUID,
        application_id: UUID,
        rubric_id: UUID | None = None,
        force_regenerate: bool = False,
    ) -> dict:
        """Get cached AI packet summary or generate a new one."""
        from datetime import UTC, datetime

        # Check cache
        if not force_regenerate:
            cached = await self.db.execute(
                select(AIPacketSummary).where(
                    AIPacketSummary.application_id == application_id,
                )
            )
            existing = cached.scalar_one_or_none()
            if existing:
                return self._packet_to_dict(existing)

        # Load application + program + rubric
        app_r = await self.db.execute(
            select(Application).where(Application.id == application_id)
        )
        app = app_r.scalar_one_or_none()
        if not app:
            raise NotFoundException("Application not found")

        prog_r = await self.db.execute(
            select(Program).where(Program.id == app.program_id)
        )
        program = prog_r.scalar_one_or_none()
        if not program:
            raise NotFoundException("Program not found")

        # Load student
        profile_r = await self.db.execute(
            select(StudentProfile)
            .where(StudentProfile.id == app.student_id)
            .options(
                selectinload(StudentProfile.academic_records),
                selectinload(StudentProfile.test_scores),
                selectinload(StudentProfile.activities),
            )
        )
        profile = profile_r.scalar_one_or_none()

        # Load rubric if provided
        rubric_criteria = []
        if rubric_id:
            rub_r = await self.db.execute(
                select(Rubric).where(Rubric.id == rubric_id)
            )
            rubric = rub_r.scalar_one_or_none()
            if rubric and rubric.criteria:
                rubric_criteria = (
                    rubric.criteria
                    if isinstance(rubric.criteria, list)
                    else []
                )

        # Build context
        student_data = self._build_student_context(profile)
        program_data = {
            "name": program.program_name,
            "degree_type": program.degree_type,
            "department": program.department,
            "requirements": program.requirements,
            "description": program.description_text,
        }

        # Build prompt
        rubric_section = ""
        if rubric_criteria:
            criteria_list = "\n".join(
                f"- {c.get('name', 'Unknown')}"
                f" (weight: {c.get('weight', 1)})"
                f": {c.get('description', '')}"
                for c in rubric_criteria
            )
            rubric_section = (
                f"\n\nRubric Criteria:\n{criteria_list}\n\n"
                "For each criterion, provide a score (0-10), "
                "an assessment, and cite specific evidence "
                "from the application."
            )

        system_prompt = (
            "You are an expert admissions reviewer. Generate a "
            "comprehensive applicant packet summary. Respond in "
            "valid JSON with these keys:\n"
            '- "overall_summary": string (2-3 paragraph narrative)\n'
            '- "strengths": list of objects with keys "text", '
            '"evidence" (specific data point), "source_field" '
            "(which part of the application)\n"
            '- "concerns": same structure as strengths\n'
            '- "criterion_assessments": list of objects with keys '
            '"criterion_name", "score" (0-10), "assessment" '
            '(string), "evidence" (list of objects with "field", '
            '"value", "citation")\n'
            '- "recommended_score": number (0-10)\n'
            '- "confidence_level": "high" | "medium" | "low"\n\n'
            "IMPORTANT: Cite specific evidence from the applicant's "
            "profile for every claim. Reference exact GPA, test "
            "scores, activity titles, and organization names."
            f"{rubric_section}"
        )

        user_content = (
            f"Student Profile:\n{json.dumps(student_data, indent=2)}"
            f"\n\nProgram:\n{json.dumps(program_data, indent=2)}"
        )

        llm = get_llm_client()
        raw = await llm.generate_reasoning(system_prompt, user_content)

        # Parse response
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            data = {
                "overall_summary": raw or "Summary generation failed",
                "strengths": [],
                "concerns": [],
                "criterion_assessments": [],
                "recommended_score": None,
                "confidence_level": "low",
            }

        # Upsert to database
        existing_r = await self.db.execute(
            select(AIPacketSummary).where(
                AIPacketSummary.application_id == application_id,
            )
        )
        existing = existing_r.scalar_one_or_none()

        model_name = getattr(settings, "llm_reasoning_model", "unknown")

        if existing:
            existing.rubric_id = rubric_id
            existing.overall_summary = data.get(
                "overall_summary", "",
            )
            existing.strengths = data.get("strengths")
            existing.concerns = data.get("concerns")
            existing.criterion_assessments = data.get(
                "criterion_assessments",
            )
            existing.recommended_score = (
                Decimal(str(data["recommended_score"]))
                if data.get("recommended_score")
                else None
            )
            existing.confidence_level = data.get("confidence_level")
            existing.model_used = model_name
            existing.generated_at = datetime.now(UTC)
            await self.db.flush()
            await self.db.refresh(existing)
            return self._packet_to_dict(existing)

        summary = AIPacketSummary(
            application_id=application_id,
            institution_id=institution_id,
            rubric_id=rubric_id,
            overall_summary=data.get("overall_summary", ""),
            strengths=data.get("strengths"),
            concerns=data.get("concerns"),
            criterion_assessments=data.get(
                "criterion_assessments",
            ),
            recommended_score=(
                Decimal(str(data["recommended_score"]))
                if data.get("recommended_score")
                else None
            ),
            confidence_level=data.get("confidence_level"),
            model_used=model_name,
            generated_at=datetime.now(UTC),
        )
        self.db.add(summary)
        await self.db.flush()
        await self.db.refresh(summary)
        return self._packet_to_dict(summary)

    def _build_student_context(self, profile) -> dict:
        """Build student data dict for LLM prompt."""
        if not profile:
            return {"name": "Unknown", "academics": [], "test_scores": [], "activities": []}
        return {
            "name": f"{profile.first_name or ''} {profile.last_name or ''}".strip(),
            "nationality": getattr(profile, "nationality", None),
            "bio": getattr(profile, "bio_text", None),
            "goals": getattr(profile, "goals_text", None),
            "academics": [
                {
                    "institution": r.institution_name,
                    "degree": r.degree_type,
                    "field": r.field_of_study,
                    "gpa": str(r.gpa) if r.gpa else None,
                }
                for r in (profile.academic_records or [])
            ],
            "test_scores": [
                {
                    "type": s.test_type,
                    "total": str(s.total_score) if s.total_score else None,
                }
                for s in (profile.test_scores or [])
            ],
            "activities": [
                {
                    "type": a.activity_type,
                    "title": a.title,
                    "organization": a.organization,
                }
                for a in (profile.activities or [])
            ],
        }

    @staticmethod
    def _packet_to_dict(s: AIPacketSummary) -> dict:
        return {
            "id": str(s.id),
            "application_id": str(s.application_id),
            "rubric_id": str(s.rubric_id) if s.rubric_id else None,
            "overall_summary": s.overall_summary,
            "strengths": s.strengths,
            "concerns": s.concerns,
            "criterion_assessments": s.criterion_assessments,
            "recommended_score": (
                float(s.recommended_score)
                if s.recommended_score
                else None
            ),
            "confidence_level": s.confidence_level,
            "model_used": s.model_used,
            "generated_at": (
                s.generated_at.isoformat()
                if s.generated_at
                else None
            ),
        }

    # ------------------------------------------------------------------
    # AI Anomaly & Integrity Signals
    # ------------------------------------------------------------------

    async def scan_integrity(
        self,
        institution_id: UUID,
        application_id: UUID,
    ) -> list[dict]:
        """AI-powered integrity scan — flag anomalies and inconsistencies."""
        from datetime import UTC, datetime

        from unipaith.models.application import IntegritySignal

        # Load application + student
        app_r = await self.db.execute(
            select(Application).where(Application.id == application_id)
        )
        app = app_r.scalar_one_or_none()
        if not app:
            raise NotFoundException("Application not found")

        profile_r = await self.db.execute(
            select(StudentProfile)
            .where(StudentProfile.id == app.student_id)
            .options(
                selectinload(StudentProfile.academic_records),
                selectinload(StudentProfile.test_scores),
                selectinload(StudentProfile.activities),
            )
        )
        profile = profile_r.scalar_one_or_none()
        if not profile:
            return []

        signals: list[dict] = []

        # Rule-based checks first (fast, no LLM needed)

        # 1. Duplicate application check
        dup_r = await self.db.execute(
            select(func.count(Application.id)).where(
                Application.student_id == app.student_id,
                Application.program_id == app.program_id,
                Application.id != application_id,
            )
        )
        if (dup_r.scalar() or 0) > 0:
            signals.append({
                "signal_type": "duplicate_submission",
                "severity": "high",
                "title": "Duplicate application detected",
                "description": (
                    "This student has another application "
                    "to the same program."
                ),
                "evidence": {
                    "student_id": str(app.student_id),
                    "program_id": str(app.program_id),
                },
            })

        # 2. GPA consistency check
        for rec in (profile.academic_records or []):
            if rec.gpa and float(rec.gpa) > 4.0:
                signals.append({
                    "signal_type": "credential_mismatch",
                    "severity": "medium",
                    "title": f"Unusual GPA: {rec.gpa}",
                    "description": (
                        f"GPA of {rec.gpa} at {rec.institution_name} "
                        "exceeds typical 4.0 scale. Verify grading system."
                    ),
                    "evidence": {
                        "institution": rec.institution_name,
                        "gpa": str(rec.gpa),
                        "scale_note": "Exceeds 4.0 scale",
                    },
                })

        # 3. Test score range check
        score_ranges = {
            "SAT": (400, 1600),
            "ACT": (1, 36),
            "GRE": (260, 340),
            "GMAT": (200, 800),
            "TOEFL": (0, 120),
            "IELTS": (0, 9),
        }
        for ts in (profile.test_scores or []):
            if ts.total_score and ts.test_type:
                tt = ts.test_type.upper()
                for key, (lo, hi) in score_ranges.items():
                    if key in tt:
                        score_val = float(ts.total_score)
                        if score_val < lo or score_val > hi:
                            signals.append({
                                "signal_type": "credential_mismatch",
                                "severity": "high",
                                "title": (
                                    f"Out-of-range {ts.test_type} score"
                                ),
                                "description": (
                                    f"{ts.test_type} score of "
                                    f"{ts.total_score} is outside "
                                    f"valid range ({lo}-{hi})."
                                ),
                                "evidence": {
                                    "test_type": ts.test_type,
                                    "score": str(ts.total_score),
                                    "valid_range": f"{lo}-{hi}",
                                },
                            })
                        break

        # 4. Missing critical fields
        if not profile.first_name or not profile.last_name:
            signals.append({
                "signal_type": "incomplete_profile",
                "severity": "low",
                "title": "Missing name fields",
                "description": "Student profile missing first or last name.",
                "evidence": {
                    "first_name": profile.first_name,
                    "last_name": profile.last_name,
                },
            })

        # 5. LLM-powered deeper analysis (if enabled)
        if not settings.ai_mock_mode:
            try:
                student_data = self._build_student_context(profile)
                system_prompt = (
                    "You are an admissions integrity analyst. "
                    "Review the applicant profile for inconsistencies, "
                    "red flags, or unusual patterns. Respond in JSON: "
                    '{"flags": [{"type": string, "severity": '
                    '"high"|"medium"|"low", "title": string, '
                    '"description": string, "evidence": object}]}'
                )
                llm = get_llm_client()
                raw = await llm.generate_reasoning(
                    system_prompt,
                    f"Profile:\n{json.dumps(student_data, indent=2)}",
                )
                try:
                    ai_data = json.loads(raw)
                    for flag in ai_data.get("flags", []):
                        signals.append({
                            "signal_type": flag.get(
                                "type", "ai_detected",
                            ),
                            "severity": flag.get("severity", "medium"),
                            "title": flag.get("title", "AI-detected"),
                            "description": flag.get(
                                "description", "",
                            ),
                            "evidence": flag.get("evidence"),
                        })
                except (json.JSONDecodeError, TypeError):
                    pass
            except Exception:
                pass  # LLM failure is non-fatal

        # Persist signals
        now = datetime.now(UTC)
        persisted: list[dict] = []
        for sig in signals:
            entry = IntegritySignal(
                application_id=application_id,
                institution_id=institution_id,
                signal_type=sig["signal_type"],
                severity=sig["severity"],
                title=sig["title"],
                description=sig["description"],
                evidence=sig.get("evidence"),
            )
            self.db.add(entry)
            persisted.append({
                **sig,
                "status": "open",
                "created_at": now.isoformat(),
            })

        if persisted:
            await self.db.flush()

        return persisted

    async def list_integrity_signals(
        self,
        institution_id: UUID,
        application_id: UUID | None = None,
        status_filter: str | None = None,
    ) -> list[dict]:
        from unipaith.models.application import IntegritySignal

        stmt = (
            select(IntegritySignal)
            .where(IntegritySignal.institution_id == institution_id)
            .order_by(IntegritySignal.created_at.desc())
        )
        if application_id:
            stmt = stmt.where(
                IntegritySignal.application_id == application_id,
            )
        if status_filter:
            stmt = stmt.where(IntegritySignal.status == status_filter)
        result = await self.db.execute(stmt)
        return [
            {
                "id": str(s.id),
                "application_id": str(s.application_id),
                "signal_type": s.signal_type,
                "severity": s.severity,
                "title": s.title,
                "description": s.description,
                "evidence": s.evidence,
                "status": s.status,
                "resolved_by": (
                    str(s.resolved_by) if s.resolved_by else None
                ),
                "resolved_at": (
                    s.resolved_at.isoformat()
                    if s.resolved_at
                    else None
                ),
                "resolution_notes": s.resolution_notes,
                "created_at": s.created_at.isoformat(),
            }
            for s in result.scalars().all()
        ]

    async def resolve_integrity_signal(
        self,
        institution_id: UUID,
        signal_id: UUID,
        user_id: UUID,
        notes: str | None = None,
    ) -> dict:
        from datetime import UTC, datetime

        from unipaith.models.application import IntegritySignal

        result = await self.db.execute(
            select(IntegritySignal).where(
                IntegritySignal.id == signal_id,
                IntegritySignal.institution_id == institution_id,
            )
        )
        sig = result.scalar_one_or_none()
        if not sig:
            raise NotFoundException("Signal not found")
        sig.status = "resolved"
        sig.resolved_by = user_id
        sig.resolved_at = datetime.now(UTC)
        sig.resolution_notes = notes
        await self.db.flush()
        return {
            "id": str(sig.id),
            "status": sig.status,
            "resolved_at": sig.resolved_at.isoformat(),
        }

    # ------------------------------------------------------------------
    # AI Queue Prioritization
    # ------------------------------------------------------------------

    async def calculate_review_priorities(
        self,
        institution_id: UUID,
        program_id: UUID | None = None,
    ) -> list[dict]:
        """Score and rank applications by review priority."""
        from datetime import UTC, datetime

        from unipaith.models.institution import IntakeRound

        # Load applications needing review
        stmt = (
            select(Application)
            .join(Program, Application.program_id == Program.id)
            .where(
                Program.institution_id == institution_id,
                Application.status.in_(["submitted", "under_review"]),
            )
        )
        if program_id:
            stmt = stmt.where(Application.program_id == program_id)
        result = await self.db.execute(stmt)
        apps = list(result.scalars().all())

        if not apps:
            return []

        # Load programs for deadlines
        prog_ids = list({a.program_id for a in apps})
        prog_r = await self.db.execute(
            select(Program).where(Program.id.in_(prog_ids))
        )
        programs = {p.id: p for p in prog_r.scalars().all()}

        # Load intake round deadlines
        intake_r = await self.db.execute(
            select(IntakeRound).where(
                IntakeRound.program_id.in_(prog_ids),
                IntakeRound.is_active.is_(True),
            )
        )
        intake_deadlines: dict[UUID, date | None] = {}
        for ir in intake_r.scalars().all():
            existing = intake_deadlines.get(ir.program_id)
            if ir.application_deadline:
                if not existing or ir.application_deadline < existing:
                    intake_deadlines[ir.program_id] = (
                        ir.application_deadline
                    )

        # Load reviewer workload counts
        assign_r = await self.db.execute(
            select(
                ReviewAssignment.reviewer_id,
                func.count(ReviewAssignment.id),
            )
            .where(
                ReviewAssignment.status.in_(["pending", "in_progress"]),
            )
            .group_by(ReviewAssignment.reviewer_id)
        )
        reviewer_load = dict(assign_r.all())

        # Load assignments per application
        app_ids = [a.id for a in apps]
        app_assign_r = await self.db.execute(
            select(ReviewAssignment).where(
                ReviewAssignment.application_id.in_(app_ids),
            )
        )
        app_assignments: dict[UUID, list] = {}
        for ra in app_assign_r.scalars().all():
            app_assignments.setdefault(ra.application_id, []).append(ra)

        now = datetime.now(UTC).date()
        prioritized = []

        for app in apps:
            score = 0.0
            reasons: list[str] = []
            deadline_days: int | None = None

            # 1. Deadline urgency (40 points max)
            prog = programs.get(app.program_id)
            deadline = None
            if app.program_id in intake_deadlines:
                deadline = intake_deadlines[app.program_id]
            elif prog and prog.application_deadline:
                deadline = prog.application_deadline

            if deadline:
                days = (deadline - now).days
                deadline_days = days
                if days <= 0:
                    score += 40
                    reasons.append("Past deadline")
                elif days <= 7:
                    score += 35
                    reasons.append(f"Deadline in {days}d")
                elif days <= 14:
                    score += 25
                    reasons.append(f"Deadline in {days}d")
                elif days <= 30:
                    score += 15
                    reasons.append(f"Deadline in {days}d")
                else:
                    score += 5

            # 2. Completeness (20 points max)
            cs = app.completeness_status
            if cs == "complete":
                score += 20
                reasons.append("Complete application")
            elif cs == "incomplete":
                score += 5
                reasons.append("Incomplete — missing items")
            else:
                score += 10

            # 3. Match score (20 points max)
            if app.match_score:
                ms = float(app.match_score)
                match_pts = min(20, ms * 20)
                score += match_pts
                if ms >= 0.8:
                    reasons.append(f"High match ({ms:.0%})")
                elif ms >= 0.6:
                    reasons.append(f"Good match ({ms:.0%})")

            # 4. Reviewer workload (20 points max)
            assignments = app_assignments.get(app.id, [])
            if not assignments:
                score += 20
                reasons.append("Unassigned")
            else:
                # Lower priority if assigned to overloaded reviewer
                avg_load = sum(
                    reviewer_load.get(ra.reviewer_id, 0)
                    for ra in assignments
                ) / len(assignments)
                if avg_load <= 5:
                    score += 15
                elif avg_load <= 10:
                    score += 10
                else:
                    score += 5
                    reasons.append("Reviewer overloaded")

            prioritized.append({
                "application_id": str(app.id),
                "student_id": str(app.student_id),
                "program_id": str(app.program_id),
                "program_name": (
                    prog.program_name if prog else "Unknown"
                ),
                "status": app.status,
                "match_score": (
                    float(app.match_score)
                    if app.match_score
                    else None
                ),
                "completeness_status": app.completeness_status,
                "submitted_at": (
                    app.submitted_at.isoformat()
                    if app.submitted_at
                    else None
                ),
                "priority_score": round(score, 1),
                "priority_reasons": reasons,
                "deadline_days": deadline_days,
                "assigned_count": len(assignments),
            })

        prioritized.sort(key=lambda x: x["priority_score"], reverse=True)
        return prioritized

    # ------------------------------------------------------------------
    # Pipeline analytics
    # ------------------------------------------------------------------

    async def get_program_pipeline(self, institution_id: UUID, program_id: UUID) -> dict:
        """Return pipeline analytics for a program.

        Counts applications grouped by status and includes a list of
        application IDs in each stage.

        Returns:
            A dict with ``program_id``, ``total``, and per-status keys
            (``draft``, ``submitted``, ``under_review``, ``interview``,
            ``decision_made``) each containing ``count`` and ``application_ids``.
        """
        # Verify program belongs to institution
        prog_result = await self.db.execute(
            select(Program).where(
                Program.id == program_id,
                Program.institution_id == institution_id,
            )
        )
        if not prog_result.scalar_one_or_none():
            raise NotFoundException("Program not found for this institution")

        result = await self.db.execute(
            select(Application.id, Application.status).where(Application.program_id == program_id)
        )
        rows = result.all()

        statuses = ["draft", "submitted", "under_review", "interview", "decision_made"]
        pipeline: dict = {
            "program_id": str(program_id),
            "total": len(rows),
        }

        for status in statuses:
            matching = [str(r.id) for r in rows if r.status == status]
            pipeline[status] = {
                "count": len(matching),
                "application_ids": matching,
            }

        return pipeline
