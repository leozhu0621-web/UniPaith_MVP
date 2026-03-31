"""Historical seeder — create HistoricalOutcome records from extracted data."""

from __future__ import annotations

import json
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.llm_client import get_llm_client
from unipaith.core.exceptions import NotFoundException
from unipaith.crawler.engine import CrawlerEngine
from unipaith.models.application import HistoricalOutcome
from unipaith.models.institution import Program

logger = logging.getLogger(__name__)

HISTORICAL_EXTRACTION_PROMPT = """\
You are a data extraction assistant. Given the text content of a university program page,
extract historical admission statistics for each available year. Return a JSON array where
each element is an object with these fields:

{
  "year": 2024,
  "applicants": number,
  "admitted": number,
  "enrolled": number,
  "avg_gpa": number or null,
  "avg_gre_verbal": number or null,
  "avg_gre_quant": number or null,
  "acceptance_rate": number (0.0 to 1.0) or null,
  "yield_rate": number (0.0 to 1.0) or null
}

Return ONLY the JSON array. If no historical data is found, return [].
"""


class HistoricalSeeder:
    """Seeds HistoricalOutcome records from extracted admissions statistics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def seed_from_extracted(
        self,
        program_id: UUID,
        stats_data: list[dict],
    ) -> int:
        """Create HistoricalOutcome records from structured stats data.

        Args:
            program_id: The program to attach outcomes to.
            stats_data: List of dicts with year, applicants, admitted, enrolled, etc.

        Returns:
            Number of records created.
        """
        program = await self.db.get(Program, program_id)
        if not program:
            raise NotFoundException(f"Program {program_id} not found")

        created = 0
        for stat in stats_data:
            year = stat.get("year")
            if not year:
                continue

            # Check for existing record
            existing = await self.db.execute(
                select(HistoricalOutcome).where(
                    HistoricalOutcome.program_id == program_id,
                    HistoricalOutcome.year == year,
                )
            )
            if existing.scalar_one_or_none():
                continue

            applicants = stat.get("applicants", 0)
            admitted = stat.get("admitted", 0)
            enrolled = stat.get("enrolled", 0)

            profile_summary = {
                "avg_gpa": stat.get("avg_gpa"),
                "avg_gre_verbal": stat.get("avg_gre_verbal"),
                "avg_gre_quant": stat.get("avg_gre_quant"),
                "applicants": applicants,
                "admitted": admitted,
                "acceptance_rate": stat.get("acceptance_rate"),
                "yield_rate": stat.get("yield_rate"),
            }

            outcome = HistoricalOutcome(
                program_id=program_id,
                year=year,
                applicant_profile_summary=profile_summary,
                outcome="admitted" if admitted > 0 else "unknown",
                enrolled=enrolled > 0,
            )
            self.db.add(outcome)
            created += 1

        await self.db.flush()
        logger.info("Seeded %d historical outcomes for program %s", created, program_id)
        return created

    async def extract_and_seed(
        self,
        program_id: UUID,
        raw_html: str,
    ) -> int:
        """Use LLM to extract admission statistics from HTML, then seed.

        Args:
            program_id: The program to attach outcomes to.
            raw_html: Raw HTML containing historical admission stats.

        Returns:
            Number of records created.
        """
        program = await self.db.get(Program, program_id)
        if not program:
            raise NotFoundException(f"Program {program_id} not found")

        cleaned = CrawlerEngine.clean_html(raw_html)
        if not cleaned.strip():
            return 0

        llm = get_llm_client()
        try:
            response_text = await llm.extract_features(HISTORICAL_EXTRACTION_PROMPT, cleaned)
        except Exception as exc:
            logger.error("LLM historical extraction failed: %s", exc)
            return 0

        # Parse response
        stats_data = self._parse_stats(response_text)
        if not stats_data:
            return 0

        return await self.seed_from_extracted(program_id, stats_data)

    @staticmethod
    def _parse_stats(text: str) -> list[dict]:
        """Parse LLM JSON response for historical stats."""
        if not text:
            return []

        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [line for line in lines if not line.strip().startswith("```")]
            cleaned = "\n".join(lines)

        try:
            data = json.loads(cleaned)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            logger.warning("Failed to parse historical stats JSON: %.100s...", cleaned)
        return []
