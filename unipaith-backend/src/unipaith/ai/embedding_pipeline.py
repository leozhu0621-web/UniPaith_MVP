"""
Embedding generation pipeline.
Takes feature_data from student_features/institution_features and generates
768-dim embeddings stored in the embeddings table (pgvector).
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.embedding_client import get_embedding_client
from unipaith.models.matching import Embedding, InstitutionFeature, StudentFeature


class EmbeddingPipeline:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.client = get_embedding_client()

    async def generate_student_embedding(self, student_id: UUID) -> list[float]:
        """Generate embedding for a student from their feature data."""
        result = await self.db.execute(
            select(StudentFeature).where(StudentFeature.student_id == student_id)
        )
        features = result.scalar_one_or_none()
        if not features:
            raise ValueError(
                f"No features found for student {student_id}. Run feature extraction first."
            )

        text = self._build_student_embedding_text(features.feature_data)
        embedding = await self.client.embed_text(text)
        await self._save_embedding("student", student_id, embedding)
        return embedding

    async def generate_program_embedding(self, program_id: UUID) -> list[float]:
        """Generate embedding for a program from its feature data."""
        result = await self.db.execute(
            select(InstitutionFeature).where(InstitutionFeature.program_id == program_id)
        )
        features = result.scalar_one_or_none()
        if not features:
            raise ValueError(
                f"No features found for program {program_id}. Run feature extraction first."
            )

        text = self._build_program_embedding_text(features.feature_data)
        embedding = await self.client.embed_text(text)
        await self._save_embedding("program", program_id, embedding)
        return embedding

    async def generate_all_program_embeddings(self) -> int:
        """Batch generate embeddings for all programs that have features."""
        result = await self.db.execute(select(InstitutionFeature))
        all_features = result.scalars().all()

        count = 0
        for feat in all_features:
            text = self._build_program_embedding_text(feat.feature_data)
            embedding = await self.client.embed_text(text)
            await self._save_embedding("program", feat.program_id, embedding)
            count += 1
        return count

    def _build_student_embedding_text(self, feature_data: dict) -> str:
        """Convert student features into natural language for embedding."""
        parts = []
        structured = feature_data.get("structured", {})
        llm = feature_data.get("llm_extracted", {})

        gpa = structured.get("normalized_gpa")
        if gpa:
            strength = "strong" if gpa > 0.85 else "solid" if gpa > 0.7 else "developing"
            parts.append(f"Student with {strength} academic background (GPA ~{gpa:.2f} normalized).")

        degree = structured.get("highest_degree_level", 0)
        degree_names = {1: "high school", 2: "associate", 3: "bachelor's", 4: "master's", 5: "PhD"}
        if degree:
            parts.append(f"Highest education: {degree_names.get(degree, 'unknown')} level.")

        work_years = structured.get("work_experience_years", 0)
        if work_years > 0:
            parts.append(f"{work_years} years of work experience.")
        research = structured.get("research_count", 0)
        if research > 0:
            parts.append(f"{research} research experience(s).")
        pubs = structured.get("publication_count", 0)
        if pubs > 0:
            parts.append(f"{pubs} publication(s).")

        themes = llm.get("key_themes", [])
        if themes:
            parts.append(f"Interested in: {', '.join(themes)}.")
        interests = llm.get("extracted_interests", [])
        if interests:
            parts.append(f"Specific interests: {', '.join(interests)}.")
        strengths = llm.get("notable_strengths", [])
        if strengths:
            parts.append(f"Strengths: {', '.join(strengths)}.")
        motivation = llm.get("motivation_type")
        if motivation:
            parts.append(f"Motivation: {motivation}.")

        countries = structured.get("preferred_countries", [])
        if countries:
            parts.append(f"Prefers studying in: {', '.join(countries)}.")
        funding = structured.get("funding_requirement")
        if funding:
            parts.append(f"Funding need: {funding}.")

        return " ".join(parts) if parts else "Student profile with limited information."

    def _build_program_embedding_text(self, feature_data: dict) -> str:
        """Convert program features into natural language for embedding."""
        parts = []
        structured = feature_data.get("structured", {})
        llm = feature_data.get("llm_extracted", {})

        name = structured.get("institution_name", "Unknown University")
        degree = structured.get("degree_type", "program")
        dept = structured.get("department", "")
        parts.append(f"{degree.title()} program at {name}.")
        if dept:
            parts.append(f"Department: {dept}.")

        country = structured.get("institution_country")
        city = structured.get("institution_city")
        if city and country:
            parts.append(f"Located in {city}, {country}.")

        rate = structured.get("acceptance_rate")
        if rate:
            selectivity = (
                "highly selective" if rate < 0.1
                else "selective" if rate < 0.25
                else "moderately selective" if rate < 0.5
                else "accessible"
            )
            parts.append(f"Admission is {selectivity} ({rate * 100:.0f}% acceptance rate).")

        tuition = structured.get("tuition_annual")
        if tuition is not None:
            if tuition == 0:
                parts.append("Fully funded (no tuition).")
            else:
                parts.append(f"Annual tuition: ${tuition:,}.")

        focus = llm.get("program_focus_areas", [])
        if focus:
            parts.append(f"Focus areas: {', '.join(focus)}.")
        style = llm.get("teaching_style")
        if style:
            parts.append(f"Teaching style: {style.replace('_', ' ')}.")
        ideal = llm.get("ideal_candidate_profile")
        if ideal:
            parts.append(f"Ideal candidate: {ideal}")
        differentiators = llm.get("key_differentiators", [])
        if differentiators:
            parts.append(f"Unique aspects: {', '.join(differentiators)}.")

        highlights = structured.get("highlights", [])
        if highlights:
            parts.append(f"Highlights: {', '.join(highlights[:5])}.")

        return " ".join(parts) if parts else "Academic program with limited information."

    async def _save_embedding(
        self, entity_type: str, entity_id: UUID, embedding: list[float]
    ) -> None:
        result = await self.db.execute(
            select(Embedding).where(
                Embedding.entity_type == entity_type,
                Embedding.entity_id == entity_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.embedding = embedding
            existing.updated_at = datetime.now(timezone.utc)
        else:
            self.db.add(Embedding(
                entity_type=entity_type,
                entity_id=entity_id,
                embedding=embedding,
                updated_at=datetime.now(timezone.utc),
            ))
        await self.db.flush()
