"""Institution intelligence -- narrative insight partner.

This is NOT a dashboard with charts. It's an intelligence partner that helps
admission staff understand their applicants and their own patterns deeply.

Insight delivery formats:
- Weekly narrative digest: what's happening in their applicant pool
- Application context cards: deep context for individual applicants
- Demand forecasting: predict application trends
- Competitive analysis: how the school compares from applicants' perspective
- Yield risk alerts: admits showing signals of choosing elsewhere
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.knowledge_retriever import KnowledgeRetriever, format_knowledge_for_prompt
from unipaith.ai.llm_client import get_llm_client
from unipaith.models.application import Application, HistoricalOutcome
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import MatchResult, PredictionLog
from unipaith.models.student import StudentProfile

logger = logging.getLogger("unipaith.institution_intelligence")

NARRATIVE_DIGEST_PROMPT = """You are an intelligence analyst for a university admissions office.
Write a concise but insightful narrative digest about this institution's applicant landscape.

Rules:
- Write in natural language, not bullet points
- Highlight patterns and trends, not just numbers
- Compare implicit vs explicit preferences (what they say they want vs what they admit)
- Note shifts in demand and emerging opportunities
- Be honest about weaknesses and risks
- Frame insights as actionable ("you might consider..." not just "data shows...")
- Keep to 3-4 paragraphs

Focus on what would genuinely help an admissions director make better decisions."""

APPLICANT_CONTEXT_PROMPT = """You are providing deep context for an admissions officer reviewing
a specific applicant. Help them understand this person beyond their numbers.

Rules:
- Start with what makes this applicant unusual or notable
- Connect their profile to historical patterns at this school
- Note any lab/faculty fit signals
- Compare to the school's implicit admit profile
- Mention what other programs they're likely considering
- Be honest about strengths AND gaps
- Keep to 2-3 paragraphs"""


class InstitutionIntelligence:
    """Narrative intelligence partner for admissions staff."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_client()
        self.knowledge = KnowledgeRetriever(db)

    async def generate_narrative_digest(
        self, institution_id: UUID,
    ) -> dict:
        """Generate a weekly narrative digest for the institution."""
        institution = await self._load_institution(institution_id)
        if not institution:
            return {"status": "not_found"}

        programs = await self._load_programs(institution_id)
        app_stats = await self._compute_application_stats(institution_id)
        outcome_patterns = await self._analyze_outcome_patterns(institution_id)
        knowledge_items = await self.knowledge.retrieve(
            query=f"{institution.name} admissions trends applicant patterns",
            entity_type="institution",
            entity_name=institution.name,
            limit=5,
        )

        context = self._build_digest_context(
            institution, programs, app_stats, outcome_patterns, knowledge_items,
        )

        try:
            narrative = await self.llm.generate_reasoning(
                NARRATIVE_DIGEST_PROMPT, context,
            )
        except Exception:
            logger.exception("Narrative digest generation failed")
            narrative = "Narrative digest generation is temporarily unavailable."

        return {
            "institution_id": str(institution_id),
            "institution_name": institution.name,
            "digest": narrative,
            "stats": app_stats,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    async def generate_applicant_context(
        self, institution_id: UUID, student_id: UUID,
    ) -> dict:
        """Generate deep applicant context card for admissions review."""
        institution = await self._load_institution(institution_id)
        student = await self._load_student(student_id)
        if not institution or not student:
            return {"status": "not_found"}

        matches = await self._load_student_matches(student_id, institution_id)
        knowledge_items = await self.knowledge.retrieve_for_program(
            program_name=institution.name,
            institution_name=institution.name,
            limit=3,
        )

        context = self._build_applicant_context(
            institution, student, matches, knowledge_items,
        )

        try:
            narrative = await self.llm.generate_reasoning(
                APPLICANT_CONTEXT_PROMPT, context,
            )
        except Exception:
            logger.exception("Applicant context generation failed")
            narrative = "Applicant context generation is temporarily unavailable."

        return {
            "institution_id": str(institution_id),
            "student_id": str(student_id),
            "student_name": f"{student.first_name or ''} {student.last_name or ''}".strip(),
            "context": narrative,
            "match_data": [
                {
                    "program_id": str(m.program_id),
                    "score": float(m.match_score),
                    "tier": m.match_tier,
                }
                for m in matches
            ],
            "generated_at": datetime.now(UTC).isoformat(),
        }

    async def generate_demand_forecast(
        self, institution_id: UUID,
    ) -> dict:
        """Forecast application demand based on interest signals."""
        institution = await self._load_institution(institution_id)
        if not institution:
            return {"status": "not_found"}

        programs = await self._load_programs(institution_id)

        program_demand = []
        for program in programs:
            match_count = await self.db.scalar(
                select(func.count()).select_from(MatchResult).where(
                    MatchResult.program_id == program.id,
                    MatchResult.is_stale.is_(False),
                )
            ) or 0
            prediction_count = await self.db.scalar(
                select(func.count()).select_from(PredictionLog).where(
                    PredictionLog.program_id == program.id,
                    PredictionLog.predicted_at >= datetime.now(UTC) - timedelta(days=30),
                )
            ) or 0

            program_demand.append({
                "program_id": str(program.id),
                "program_name": program.program_name,
                "degree_type": program.degree_type,
                "active_matches": match_count,
                "recent_predictions": prediction_count,
                "demand_signal": "high" if prediction_count > 10 else "moderate" if prediction_count > 3 else "low",
            })

        program_demand.sort(key=lambda x: x["recent_predictions"], reverse=True)

        return {
            "institution_id": str(institution_id),
            "institution_name": institution.name,
            "programs": program_demand,
            "forecast_period": "next_30_days",
            "generated_at": datetime.now(UTC).isoformat(),
        }

    async def generate_yield_risk_alerts(
        self, institution_id: UUID,
    ) -> dict:
        """Identify admits showing signals of choosing elsewhere."""
        programs = await self._load_programs(institution_id)
        program_ids = [p.id for p in programs]
        if not program_ids:
            return {"alerts": [], "institution_id": str(institution_id)}

        admitted_apps = await self.db.execute(
            select(Application).where(
                Application.program_id.in_(program_ids),
                Application.decision == "admitted",
                Application.status != "enrolled",
            )
        )
        apps = list(admitted_apps.scalars().all())

        alerts = []
        for app in apps[:20]:
            other_matches = await self.db.execute(
                select(func.count()).select_from(MatchResult).where(
                    MatchResult.student_id == app.student_id,
                    MatchResult.program_id.notin_(program_ids),
                    MatchResult.match_score > app.match_score if hasattr(app, "match_score") else True,
                )
            )
            competing_count = other_matches.scalar() or 0

            if competing_count > 2:
                alerts.append({
                    "application_id": str(app.id),
                    "student_id": str(app.student_id),
                    "program_id": str(app.program_id),
                    "risk_level": "high" if competing_count > 5 else "moderate",
                    "competing_programs": competing_count,
                    "reason": f"Student has {competing_count} other strong matches",
                })

        return {
            "institution_id": str(institution_id),
            "alerts": alerts,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    def _build_digest_context(
        self, institution, programs, app_stats, outcome_patterns, knowledge_items,
    ) -> str:
        parts = [
            f"## Institution: {institution.name}",
            f"Country: {institution.country or 'Unknown'}",
            f"Type: {institution.type or 'Unknown'}",
            f"Programs: {len(programs)}",
            f"\n## Application Statistics\n{_dict_to_text(app_stats)}",
        ]
        if outcome_patterns:
            parts.append(f"\n## Outcome Patterns\n{_dict_to_text(outcome_patterns)}")
        if knowledge_items:
            parts.append(format_knowledge_for_prompt(knowledge_items, max_chars=2000))
        return "\n".join(parts)

    def _build_applicant_context(
        self, institution, student, matches, knowledge_items,
    ) -> str:
        parts = [
            f"## Institution: {institution.name}",
            f"## Applicant: {student.first_name or ''} {student.last_name or ''}",
            f"Nationality: {student.nationality or 'Unknown'}",
            f"Goals: {student.goals_text or 'Not specified'}",
            f"Bio: {student.bio_text or 'Not provided'}",
        ]
        if matches:
            parts.append("\n## Match Data")
            for m in matches:
                parts.append(f"- Program {m.program_id}: score={m.match_score}, tier={m.match_tier}")
        if knowledge_items:
            parts.append(format_knowledge_for_prompt(knowledge_items, max_chars=1500))
        return "\n".join(parts)

    async def _load_institution(self, institution_id: UUID) -> Institution | None:
        result = await self.db.execute(
            select(Institution).where(Institution.id == institution_id)
        )
        return result.scalar_one_or_none()

    async def _load_programs(self, institution_id: UUID) -> list[Program]:
        result = await self.db.execute(
            select(Program).where(
                Program.institution_id == institution_id,
                Program.is_published.is_(True),
            )
        )
        return list(result.scalars().all())

    async def _load_student(self, student_id: UUID) -> StudentProfile | None:
        result = await self.db.execute(
            select(StudentProfile).where(StudentProfile.id == student_id)
        )
        return result.scalar_one_or_none()

    async def _load_student_matches(
        self, student_id: UUID, institution_id: UUID,
    ) -> list[MatchResult]:
        programs = await self._load_programs(institution_id)
        if not programs:
            return []
        result = await self.db.execute(
            select(MatchResult).where(
                MatchResult.student_id == student_id,
                MatchResult.program_id.in_([p.id for p in programs]),
            )
        )
        return list(result.scalars().all())

    async def _compute_application_stats(self, institution_id: UUID) -> dict:
        programs = await self._load_programs(institution_id)
        program_ids = [p.id for p in programs]
        if not program_ids:
            return {"total_applications": 0}

        total = await self.db.scalar(
            select(func.count()).select_from(Application).where(
                Application.program_id.in_(program_ids),
            )
        ) or 0

        return {
            "total_applications": total,
            "programs_count": len(programs),
        }

    async def _analyze_outcome_patterns(self, institution_id: UUID) -> dict:
        programs = await self._load_programs(institution_id)
        program_ids = [p.id for p in programs]
        if not program_ids:
            return {}

        outcomes = await self.db.execute(
            select(HistoricalOutcome.outcome, func.count())
            .where(HistoricalOutcome.program_id.in_(program_ids))
            .group_by(HistoricalOutcome.outcome)
        )
        return {row[0]: row[1] for row in outcomes.fetchall()}


def _dict_to_text(d: dict) -> str:
    return "\n".join(f"- {k}: {v}" for k, v in d.items())
