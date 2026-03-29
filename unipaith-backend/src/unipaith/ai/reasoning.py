"""
NL Reasoning Generator.
Produces human-readable match explanations using the reasoning LLM.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.ai.llm_client import get_llm_client
from unipaith.models.institution import Program
from unipaith.models.matching import InstitutionFeature, StudentFeature
from unipaith.models.student import StudentProfile

REASONING_SYSTEM_PROMPT = """You are an admissions advisor generating a personalized match explanation for a student.

Write 3-5 sentences explaining why this program is a good (or reasonable) match for this student.

Rules:
- Be specific: reference the student's actual background and the program's actual features
- Be balanced: mention strengths of the match AND any areas of concern
- Address financial fit if tuition vs budget is relevant
- If it's a Tier 1 match, be encouraging. If Tier 3, be honest about it being a stretch/safety.
- Write in second person ("Your background in..." not "The student's background...")
- Do NOT use bullet points — write flowing prose
- Do NOT start with "This program" — start with something about the student"""


class ReasoningGenerator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_client()

    async def generate_match_reasoning(
        self,
        student_id: UUID,
        program_id: UUID,
        score: float,
        tier: int,
        breakdown: dict,
    ) -> str:
        """Generate a natural-language explanation for why this student matches this program."""
        student = await self._load_student_summary(student_id)
        program = await self._load_program_summary(program_id)

        tier_label = {1: "Strong Match", 2: "Good Match", 3: "Possible Match"}

        user_content = f"""
## Match Context
- Match Score: {score:.2f}/1.00 ({tier_label.get(tier, 'Match')})
- Score Breakdown: {breakdown}

## Student Profile Summary
- Name: {student.get('name', 'Student')}
- Nationality: {student.get('nationality', 'Unknown')}
- Highest Degree: {student.get('highest_degree', 'Unknown')}
- GPA: {student.get('gpa', 'N/A')}
- Work Experience: {student.get('work_years', 0)} years
- Key Interests: {student.get('interests', [])}
- Goals: {student.get('goals', 'Not specified')}
- Budget Max: ${student.get('budget_max', 'N/A')}
- Funding Need: {student.get('funding', 'N/A')}

## Program Summary
- Program: {program.get('name', 'Unknown')}
- Institution: {program.get('institution', 'Unknown')}
- Degree: {program.get('degree_type', 'Unknown')}
- Location: {program.get('location', 'Unknown')}
- Tuition: ${program.get('tuition', 'N/A')}/year
- Acceptance Rate: {program.get('acceptance_rate', 'N/A')}
- Focus Areas: {program.get('focus_areas', [])}
"""
        reasoning = await self.llm.generate_reasoning(REASONING_SYSTEM_PROMPT, user_content)
        return reasoning.strip()

    async def _load_student_summary(self, student_id: UUID) -> dict:
        result = await self.db.execute(
            select(StudentProfile)
            .where(StudentProfile.id == student_id)
            .options(
                selectinload(StudentProfile.academic_records),
                selectinload(StudentProfile.test_scores),
                selectinload(StudentProfile.preferences),
            )
        )
        student = result.scalar_one_or_none()
        if not student:
            return {}

        feat_result = await self.db.execute(
            select(StudentFeature).where(StudentFeature.student_id == student_id)
        )
        features = feat_result.scalar_one_or_none()
        llm_data = (features.feature_data or {}).get("llm_extracted", {}) if features else {}

        highest_degree = "Unknown"
        best_gpa = None
        for a in (student.academic_records or []):
            highest_degree = a.degree_type
            if a.gpa:
                best_gpa = f"{a.gpa} ({a.gpa_scale})"

        return {
            "name": f"{student.first_name or ''} {student.last_name or ''}".strip(),
            "nationality": student.nationality,
            "highest_degree": highest_degree,
            "gpa": best_gpa,
            "work_years": (
                (features.feature_data or {}).get("structured", {}).get("work_experience_years", 0)
                if features else 0
            ),
            "interests": llm_data.get("key_themes", []),
            "goals": student.goals_text[:200] if student.goals_text else "Not specified",
            "budget_max": student.preferences.budget_max if student.preferences else None,
            "funding": student.preferences.funding_requirement if student.preferences else None,
        }

    async def _load_program_summary(self, program_id: UUID) -> dict:
        result = await self.db.execute(
            select(Program)
            .where(Program.id == program_id)
            .options(selectinload(Program.institution))
        )
        program = result.scalar_one_or_none()
        if not program:
            return {}

        feat_result = await self.db.execute(
            select(InstitutionFeature).where(InstitutionFeature.program_id == program_id)
        )
        features = feat_result.scalar_one_or_none()
        llm_data = (features.feature_data or {}).get("llm_extracted", {}) if features else {}

        inst = program.institution
        return {
            "name": program.program_name,
            "institution": inst.name if inst else "Unknown",
            "degree_type": program.degree_type,
            "location": f"{inst.city}, {inst.country}" if inst else "Unknown",
            "tuition": program.tuition,
            "acceptance_rate": (
                f"{float(program.acceptance_rate) * 100:.0f}%"
                if program.acceptance_rate else "N/A"
            ),
            "focus_areas": llm_data.get("program_focus_areas", []),
        }
