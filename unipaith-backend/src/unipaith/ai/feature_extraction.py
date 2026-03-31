"""
Hybrid feature extraction pipeline.
- Structured features: computed directly from DB fields (fast, deterministic)
- LLM features: extracted from free-text via LLM (rich, semantic)
Combined into a single feature_data JSON stored in student_features / institution_features tables.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.ai.llm_client import get_llm_client
from unipaith.models.institution import Program
from unipaith.models.matching import InstitutionFeature, StudentFeature
from unipaith.models.student import (
    StudentProfile,
)

STUDENT_FEATURE_PROMPT = """You are a feature extraction engine for a university admissions matching system.
Analyze the student's profile text and extract the following features as a JSON object.
Return ONLY valid JSON, no other text.

Required fields:
{
    "academic_strength": <float 0-1, overall academic capability signal>,
    "research_experience": <float 0-1, depth and quality of research>,
    "leadership_signal": <float 0-1, leadership and initiative>,
    "international_perspective": <float 0-1, cross-cultural experience and global thinking>,
    "career_clarity": <float 0-1, how clear and specific their career goals are>,
    "technical_depth": <float 0-1, depth of technical/domain expertise>,
    "communication_quality": <float 0-1, writing quality and self-expression>,
    "key_themes": [<list of 3-7 topic/interest keywords>],
    "notable_strengths": [<list of 2-4 standout qualities>],
    "potential_gaps": [<list of 0-3 areas that could be improved>],
    "extracted_interests": [<list of 3-8 specific academic/career interests>],
    "motivation_type": <"career_advancement" | "intellectual_curiosity" | "social_impact" | "mixed">,
    "readiness_level": <"strong" | "moderate" | "developing">
}

Be calibrated: 0.5 means average, 0.8+ means exceptional, below 0.3 means very weak."""

PROGRAM_FEATURE_PROMPT = """You are a feature extraction engine for a university admissions matching system.
Analyze the program description and extract the following features as a JSON object.
Return ONLY valid JSON, no other text.

Required fields:
{
    "program_focus_areas": [<list of 3-7 academic focus areas>],
    "teaching_style": <"research_heavy" | "coursework_heavy" | "balanced" | "practicum_based">,
    "industry_connection": <float 0-1, how connected to industry/employment>,
    "research_intensity": <float 0-1, emphasis on research>,
    "diversity_emphasis": <float 0-1, emphasis on diverse student body>,
    "innovation_focus": <float 0-1, emphasis on cutting-edge/novel work>,
    "career_support": <float 0-1, career services and placement emphasis>,
    "has_coop_or_internship": <boolean>,
    "ideal_candidate_profile": <string, 1-2 sentences describing who this program seeks>,
    "key_differentiators": [<list of 2-4 things that make this program unique>],
    "target_student_background": [<list of 2-5 backgrounds this program attracts>]
}"""


class FeatureExtractor:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_client()

    # ========================================================================
    # STUDENT FEATURE EXTRACTION
    # ========================================================================

    async def extract_student_features(self, student_id: UUID) -> dict:
        """Extract all features for a student. Stores result in student_features table."""
        student = await self._load_student(student_id)
        if not student:
            raise ValueError(f"Student {student_id} not found")

        structured = self._extract_structured_student_features(student)
        llm_features = await self._extract_llm_student_features(student)

        feature_data = {
            "structured": structured,
            "llm_extracted": llm_features,
            "version": "1.0",
        }

        await self._save_student_features(student_id, feature_data)
        return feature_data

    def _extract_structured_student_features(self, student: StudentProfile) -> dict:
        """Compute numerical/categorical features directly from database fields."""
        academics = student.academic_records or []
        scores = student.test_scores or []
        activities = student.activities or []
        prefs = student.preferences

        degree_rank = {
            "high_school": 1,
            "associate": 2,
            "diploma": 2,
            "bachelors": 3,
            "masters": 4,
            "phd": 5,
        }
        highest_degree = max((degree_rank.get(a.degree_type, 0) for a in academics), default=0)

        normalized_gpas = []
        for a in academics:
            if a.gpa and a.gpa_scale:
                normalized = self._normalize_gpa(float(a.gpa), a.gpa_scale)
                if normalized is not None:
                    normalized_gpas.append(normalized)
        avg_gpa = sum(normalized_gpas) / len(normalized_gpas) if normalized_gpas else None

        test_scores_normalized = {}
        for s in scores:
            norm = self._normalize_test_score(s.test_type, s.total_score)
            if norm is not None:
                test_scores_normalized[s.test_type.lower()] = norm

        work_experiences = [a for a in activities if a.activity_type == "work_experience"]
        research_count = sum(1 for a in activities if a.activity_type == "research")
        leadership_count = sum(1 for a in activities if a.activity_type == "leadership")
        award_count = sum(1 for a in activities if a.activity_type == "awards")
        publication_count = sum(1 for a in activities if a.activity_type == "publications")

        work_years = 0.0
        for w in work_experiences:
            if w.start_date:
                end = w.end_date or date.today()
                work_years += (end - w.start_date).days / 365.25

        budget_flexibility = "unknown"
        if prefs:
            if prefs.funding_requirement == "self_funded":
                budget_flexibility = "high"
            elif prefs.funding_requirement == "flexible":
                budget_flexibility = "medium"
            elif prefs.funding_requirement == "partial":
                budget_flexibility = "low"
            elif prefs.funding_requirement == "full_scholarship":
                budget_flexibility = "none"

        return {
            "highest_degree_level": highest_degree,
            "normalized_gpa": round(avg_gpa, 4) if avg_gpa else None,
            "test_scores": test_scores_normalized,
            "work_experience_years": round(work_years, 1),
            "research_count": research_count,
            "leadership_count": leadership_count,
            "award_count": award_count,
            "publication_count": publication_count,
            "total_activities": len(activities),
            "nationality": student.nationality,
            "is_international": True,
            "budget_flexibility": budget_flexibility,
            "budget_max": prefs.budget_max if prefs else None,
            "preferred_countries": prefs.preferred_countries if prefs else [],
            "funding_requirement": prefs.funding_requirement if prefs else None,
        }

    async def _extract_llm_student_features(self, student: StudentProfile) -> dict:
        """Use LLM to extract semantic features from free-text fields."""
        text_parts = []
        if student.bio_text:
            text_parts.append(f"## Student Bio\n{student.bio_text}")
        if student.goals_text:
            text_parts.append(f"## Goals\n{student.goals_text}")
        for activity in student.activities or []:
            if activity.description:
                text_parts.append(
                    f"## Activity: {activity.title} ({activity.activity_type})\n"
                    f"{activity.description}"
                )
            if activity.impact_description:
                text_parts.append(f"Impact: {activity.impact_description}")
        if student.preferences and student.preferences.goals_text:
            text_parts.append(f"## Detailed Goals\n{student.preferences.goals_text}")

        if not text_parts:
            return {"error": "no_text_available"}

        user_content = "\n\n".join(text_parts)
        raw_response = await self.llm.extract_features(STUDENT_FEATURE_PROMPT, user_content)
        return self._parse_json_response(raw_response)

    # ========================================================================
    # PROGRAM FEATURE EXTRACTION
    # ========================================================================

    async def extract_program_features(self, program_id: UUID) -> dict:
        """Extract features for a program. Stores in institution_features table."""
        program = await self._load_program(program_id)
        if not program:
            raise ValueError(f"Program {program_id} not found")

        structured = self._extract_structured_program_features(program)
        llm_features = await self._extract_llm_program_features(program)

        feature_data = {
            "structured": structured,
            "llm_extracted": llm_features,
            "version": "1.0",
        }

        await self._save_program_features(program_id, feature_data)
        return feature_data

    def _extract_structured_program_features(self, program: Program) -> dict:
        institution = program.institution
        reqs = program.requirements or {}
        degree_rank = {"certificate": 1, "diploma": 1, "bachelors": 2, "masters": 3, "phd": 4}

        return {
            "degree_level": degree_rank.get(program.degree_type, 0),
            "degree_type": program.degree_type,
            "tuition_annual": program.tuition,
            "duration_months": program.duration_months,
            "acceptance_rate": float(program.acceptance_rate) if program.acceptance_rate else None,
            "min_gpa_required": reqs.get("min_gpa"),
            "gre_required": reqs.get("gre_required", False),
            "toefl_min": reqs.get("toefl_min"),
            "ielts_min": reqs.get("ielts_min"),
            "institution_name": institution.name if institution else None,
            "institution_country": institution.country if institution else None,
            "institution_region": institution.region if institution else None,
            "institution_city": institution.city if institution else None,
            "institution_type": institution.type if institution else None,
            "ranking_qs": (institution.ranking_data or {}).get("qs") if institution else None,
            "ranking_us_news": (institution.ranking_data or {}).get("us_news")
            if institution
            else None,
            "is_funded": program.tuition == 0 or program.degree_type == "phd",
            "department": program.department,
            "highlights": program.highlights or [],
        }

    async def _extract_llm_program_features(self, program: Program) -> dict:
        text_parts = []
        if program.description_text:
            text_parts.append(f"## Program Description\n{program.description_text}")
        if program.current_preferences_text:
            text_parts.append(
                f"## Current Admission Preferences\n{program.current_preferences_text}"
            )
        if program.highlights:
            text_parts.append(
                "## Program Highlights\n" + "\n".join(f"- {h}" for h in program.highlights)
            )
        institution = program.institution
        if institution and institution.description_text:
            text_parts.append(f"## Institution Description\n{institution.description_text}")

        if not text_parts:
            return {"error": "no_text_available"}

        user_content = "\n\n".join(text_parts)
        raw_response = await self.llm.extract_features(PROGRAM_FEATURE_PROMPT, user_content)
        return self._parse_json_response(raw_response)

    # ========================================================================
    # NORMALIZATION HELPERS
    # ========================================================================

    def _normalize_gpa(self, gpa: float, scale: str) -> float | None:
        scale = scale.lower().strip()
        scales = {
            "4.0": 4.0,
            "percentage": 100.0,
            "100": 100.0,
            "10.0": 10.0,
            "5.0": 5.0,
            "ib": 45.0,
            "7.0": 7.0,
        }
        max_val = scales.get(scale)
        return min(gpa / max_val, 1.0) if max_val else None

    def _normalize_test_score(self, test_type: str, score: int | None) -> float | None:
        if score is None:
            return None
        max_scores = {
            "SAT": 1600,
            "GRE": 340,
            "GMAT": 800,
            "TOEFL": 120,
            "IELTS": 9,
            "ACT": 36,
            "LSAT": 180,
            "MCAT": 528,
            "DUOLINGO": 160,
            "AP": 5,
            "IB": 45,
        }
        max_score = max_scores.get(test_type.upper())
        return min(score / max_score, 1.0) if max_score else None

    # ========================================================================
    # DATA LOADING & PERSISTENCE
    # ========================================================================

    def _parse_json_response(self, raw_response: str) -> dict:
        try:
            cleaned = raw_response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                cleaned = cleaned.rsplit("```", 1)[0]
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {"error": "parse_failed", "raw": raw_response[:500]}

    async def _load_student(self, student_id: UUID) -> StudentProfile | None:
        result = await self.db.execute(
            select(StudentProfile)
            .where(StudentProfile.id == student_id)
            .options(
                selectinload(StudentProfile.academic_records),
                selectinload(StudentProfile.test_scores),
                selectinload(StudentProfile.activities),
                selectinload(StudentProfile.preferences),
            )
        )
        return result.scalar_one_or_none()

    async def _load_program(self, program_id: UUID) -> Program | None:
        result = await self.db.execute(
            select(Program)
            .where(Program.id == program_id)
            .options(selectinload(Program.institution))
        )
        return result.scalar_one_or_none()

    async def _save_student_features(self, student_id: UUID, feature_data: dict) -> None:
        result = await self.db.execute(
            select(StudentFeature).where(StudentFeature.student_id == student_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.feature_data = feature_data
            existing.updated_at = datetime.now(UTC)
        else:
            self.db.add(
                StudentFeature(
                    student_id=student_id,
                    feature_data=feature_data,
                    updated_at=datetime.now(UTC),
                )
            )
        await self.db.flush()

    async def _save_program_features(self, program_id: UUID, feature_data: dict) -> None:
        result = await self.db.execute(
            select(InstitutionFeature).where(InstitutionFeature.program_id == program_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.feature_data = feature_data
            existing.updated_at = datetime.now(UTC)
        else:
            self.db.add(
                InstitutionFeature(
                    program_id=program_id,
                    feature_data=feature_data,
                    updated_at=datetime.now(UTC),
                )
            )
        await self.db.flush()
