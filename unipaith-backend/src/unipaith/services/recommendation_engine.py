"""Guided discovery recommendation engine.

Recommendations are not a list of schools with scores. They are a guided
journey of discovery, surfaced through the advisor conversation.

Each recommendation includes:
- Why THIS program for THIS student (not generic reasons)
- Honest acknowledgment of concerns or tradeoffs
- Connection to things the student has actually said/expressed
- A calibrated sense of chances (woven in naturally, not as a number)
"""
from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.knowledge_retriever import KnowledgeRetriever, format_knowledge_for_prompt
from unipaith.ai.llm_client import get_llm_client
from unipaith.models.institution import Program
from unipaith.models.knowledge import PersonInsight
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentPreference, StudentProfile
from unipaith.services.student_service import StudentService

logger = logging.getLogger("unipaith.recommendation_engine")

RECOMMENDATION_PROMPT = """You are generating personalized program recommendations
for a student. You know this student deeply. Write warm, specific reasoning for
each program -- explain WHY this program suits WHO THEY ARE, not just their numbers.

Rules:
- Reference the student's specific stated priorities and constraints (listed under
  "Student's Stated Priorities") — tie each recommendation back to what THEY said matters
- Acknowledge concerns or tradeoffs honestly
- Frame chances naturally ("I've seen students like you thrive here") not as percentages
- One recommendation should be familiar (on their radar), one should surprise them,
  one should be a "hidden gem" they wouldn't have found
- Keep reasoning to 3-5 sentences; fit_summary to ONE sentence
- Never lead with ranking or statistics
- For priority_matches: list 2-5 of the student's stated priorities that this program
  satisfies, phrased as short confirmations (e.g. "Within your $40k budget",
  "US-based as requested", "Strong CS program matching your interest")
- For tradeoffs: list 1-3 honest tradeoffs where this program is strong on one
  dimension but requires compromise on another. Format each as
  "Strong: <strength> — But: <tradeoff>" (e.g. "Strong: top-10 CS ranking —
  But: tuition $15k above your stated budget"). Use empty array if no tradeoffs.

Return a JSON array of objects:
[{
  "program_id": "<uuid>",
  "program_name": "<name>",
  "institution_name": "<name>",
  "reasoning": "<warm, personal reasoning referencing their stated priorities>",
  "category": "<on_your_radar|might_surprise_you|hidden_gem>",
  "fit_summary": "<one-line summary of why this fits THEM>",
  "priority_matches": ["<short confirmation of met priority>", ...],
  "tradeoffs": ["Strong: <x> — But: <y>", ...]
}]

Return ONLY valid JSON."""


class RecommendationEngine:
    """Generates warm, personalized program recommendations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_client()
        self.knowledge = KnowledgeRetriever(db)
        self.student_service = StudentService(db)

    async def generate_recommendations(
        self,
        student_user_id: UUID,
        count: int = 5,
        conversation_context: str | None = None,
    ) -> list[dict]:
        """Generate personalized recommendations for a student."""
        profile = await self.student_service._get_student_profile(student_user_id)
        preferences = await self._load_preferences(profile.id)
        insights = await self._load_insights(student_user_id)
        matches = await self._load_top_matches(profile.id, limit=count * 2)

        if not matches:
            return []

        programs = await self._load_programs([m.program_id for m in matches])
        knowledge_items = await self.knowledge.retrieve_for_student_context(
            interests=[profile.goals_text or "graduate programs"],
            goals=profile.goals_text,
        )

        student_context = self._build_student_context(profile, preferences, insights)
        program_summaries = self._build_program_summaries(matches, programs)
        knowledge_text = format_knowledge_for_prompt(knowledge_items, max_chars=2000)

        priorities_section = ""
        if conversation_context:
            student_context += f"\n\n## Recent Conversation Context\n{conversation_context[:1000]}"
            ctx = conversation_context[:1500]
            priorities_section = (
                f"\n\n## Student's Stated Priorities\n"
                f"The student explicitly told us these matter:\n{ctx}\n"
                f"Tie every recommendation back to these priorities."
            )

        prompt = (
            f"{student_context}\n\n"
            f"## Available Programs (ranked by prediction model)\n{program_summaries}\n\n"
            f"{knowledge_text}"
            f"{priorities_section}\n\n"
            f"Generate {count} personalized recommendations from the programs above."
        )

        try:
            result = await self.llm.generate_reasoning(RECOMMENDATION_PROMPT, prompt)
            parsed = _safe_json(result)
            if parsed and isinstance(parsed, list):
                for rec in parsed:
                    pid_raw = rec.get("program_id")
                    try:
                        pid = UUID(str(pid_raw)) if pid_raw else None
                    except ValueError:
                        pid = None
                    if pid and pid in programs:
                        p = programs[pid]
                        self._enrich_with_quick_facts(rec, p)
                return parsed[:count]
        except Exception:
            logger.exception("Recommendation generation failed")

        return self._fallback_recommendations(matches, programs, count)

    def _build_student_context(
        self,
        profile: StudentProfile,
        preferences: StudentPreference | None,
        insights: list[PersonInsight],
    ) -> str:
        parts = [
            f"## Student: {profile.first_name or ''} {profile.last_name or ''}",
            f"Goals: {profile.goals_text or 'Not specified'}",
            f"Bio: {profile.bio_text or 'Not provided'}",
        ]
        if preferences:
            if preferences.preferred_countries:
                parts.append(f"Preferred countries: {', '.join(preferences.preferred_countries)}")
            if preferences.budget_max:
                parts.append(f"Budget max: ${preferences.budget_max}")
            if preferences.funding_requirement:
                parts.append(f"Funding need: {preferences.funding_requirement}")

        if insights:
            parts.append("\n## What We Know About This Student")
            for ins in insights[:10]:
                parts.append(f"- [{ins.insight_type}] {ins.insight_text}")

        return "\n".join(parts)

    def _build_program_summaries(
        self, matches: list[MatchResult], programs: dict[UUID, Program],
    ) -> str:
        lines = []
        for i, match in enumerate(matches, 1):
            p = programs.get(match.program_id)
            if not p:
                continue
            inst_name = p.institution.name if p.institution else "Unknown"
            breakdown = match.score_breakdown or {}
            lines.append(
                f"{i}. {p.program_name} at {inst_name} "
                f"(ID: {p.id}, Degree: {p.degree_type}, "
                f"Tuition: ${p.tuition or '?'}, "
                f"P(admitted): {breakdown.get('p_admitted', match.match_score)})"
            )
        return "\n".join(lines)

    @staticmethod
    def _enrich_with_quick_facts(rec: dict, p: Program) -> None:
        """Add standardized quick-fact fields from Program + Institution."""
        rec["degree_type"] = p.degree_type
        rec["tuition"] = p.tuition
        rec["duration_months"] = p.duration_months
        rec["delivery_format"] = p.delivery_format
        rec["acceptance_rate"] = float(p.acceptance_rate) if p.acceptance_rate else None
        rec["application_deadline"] = (
            p.application_deadline.isoformat() if p.application_deadline else None
        )
        rec["institution_country"] = p.institution.country if p.institution else None
        rec["institution_city"] = p.institution.city if p.institution else None
        rec.setdefault("fit_summary", "")
        rec.setdefault("priority_matches", [])
        rec.setdefault("tradeoffs", [])

    def _fallback_recommendations(
        self, matches: list[MatchResult], programs: dict[UUID, Program], count: int,
    ) -> list[dict]:
        recs = []
        categories = ["on_your_radar", "might_surprise_you", "hidden_gem"]
        for i, match in enumerate(matches[:count]):
            p = programs.get(match.program_id)
            if not p:
                continue
            rec = {
                "program_id": str(p.id),
                "program_name": p.program_name,
                "institution_name": p.institution.name if p.institution else "Unknown",
                "reasoning": (
                    match.reasoning_text
                    or "This program aligns well with your profile and interests."
                ),
                "category": categories[i % len(categories)],
                "fit_summary": "Strong match based on your background and goals.",
            }
            self._enrich_with_quick_facts(rec, p)
            recs.append(rec)
        return recs

    async def _load_top_matches(self, student_id: UUID, limit: int) -> list[MatchResult]:
        result = await self.db.execute(
            select(MatchResult)
            .where(MatchResult.student_id == student_id, MatchResult.is_stale.is_(False))
            .order_by(MatchResult.match_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def _load_programs(self, program_ids: list[UUID]) -> dict[UUID, Program]:
        if not program_ids:
            return {}
        from sqlalchemy.orm import selectinload
        result = await self.db.execute(
            select(Program)
            .where(Program.id.in_(program_ids))
            .options(selectinload(Program.institution))
        )
        return {p.id: p for p in result.scalars().all()}

    async def _load_preferences(self, student_id: UUID) -> StudentPreference | None:
        result = await self.db.execute(
            select(StudentPreference).where(StudentPreference.student_id == student_id)
        )
        return result.scalar_one_or_none()

    async def _load_insights(self, user_id: UUID) -> list[PersonInsight]:
        result = await self.db.execute(
            select(PersonInsight).where(
                PersonInsight.user_id == user_id, PersonInsight.is_active.is_(True),
            ).order_by(PersonInsight.confidence.desc()).limit(15)
        )
        return list(result.scalars().all())


def _safe_json(text: str):
    import json
    import re
    if not text:
        return None
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"[\[\{].*[\]\}]", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None
