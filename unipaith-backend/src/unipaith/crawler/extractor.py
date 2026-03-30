"""LLM-based structured data extractor for crawled HTML."""
from __future__ import annotations

import json
import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.llm_client import get_llm_client
from unipaith.config import settings
from unipaith.core.exceptions import NotFoundException
from unipaith.crawler.engine import CrawlerEngine
from unipaith.models.crawler import CrawlJob, ExtractedProgram
from unipaith.models.matching import RawIngestedData

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """\
You are a data extraction assistant. Given the text content of a university web page,
extract all graduate program information you can find. Return a JSON array where each
element is an object with these fields (use null for missing data):

{
  "institution_name": "string",
  "institution_country": "string",
  "institution_city": "string",
  "institution_type": "string (university/college/institute)",
  "institution_website": "string",
  "program_name": "string",
  "degree_type": "string (PhD/Masters/MBA/MFA/JD/MD/etc.)",
  "department": "string",
  "duration_months": number,
  "tuition": number (annual, USD),
  "tuition_currency": "string (USD/EUR/GBP/etc.)",
  "acceptance_rate": number (0.0 to 1.0),
  "requirements": {"gpa_min": number, "gre_required": boolean, "toefl_min": number, ...},
  "description_text": "string",
  "application_deadline": "YYYY-MM-DD",
  "program_start_date": "YYYY-MM-DD",
  "highlights": ["string", ...],
  "faculty_contacts": [{"name": "string", "email": "string", "role": "string"}, ...],
  "rankings": {"qs": number, "us_news": number, ...},
  "financial_aid_info": {"scholarships_available": boolean, "avg_award": number, ...},
  "admission_stats": {"avg_gpa": number, "avg_gre": number, "applicants": number, "enrolled": number}
}

Return ONLY the JSON array. If no programs are found, return an empty array [].
"""


class LLMExtractor:
    """Extracts structured program data from raw HTML using an LLM."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = get_llm_client()

    async def extract_from_raw(
        self,
        raw_data_id: UUID,
        crawl_job_id: UUID,
        prompt_override: str | None = None,
    ) -> list[ExtractedProgram]:
        """Extract program records from a single RawIngestedData row."""
        raw = await self.db.get(RawIngestedData, raw_data_id)
        if not raw:
            raise NotFoundException(f"Raw data {raw_data_id} not found")

        job = await self.db.get(CrawlJob, crawl_job_id)
        if not job:
            raise NotFoundException(f"Crawl job {crawl_job_id} not found")

        # Clean HTML for LLM
        cleaned = CrawlerEngine.clean_html(raw.raw_content or "")
        if not cleaned.strip():
            raw.processed = True
            raw.processing_result = {"status": "empty_content"}
            await self.db.flush()
            return []

        # Call LLM
        prompt = prompt_override or EXTRACTION_PROMPT
        try:
            response_text = await self.llm.extract_features(prompt, cleaned)
        except Exception as exc:
            logger.error("LLM extraction failed for raw %s: %s", raw_data_id, exc)
            raw.processed = True
            raw.processing_result = {"status": "llm_error", "error": str(exc)}
            await self.db.flush()
            return []

        # Parse JSON response
        programs_data = self._parse_response(response_text)
        if not programs_data:
            raw.processed = True
            raw.processing_result = {"status": "no_programs_found"}
            await self.db.flush()
            return []

        # Create ExtractedProgram records
        extracted: list[ExtractedProgram] = []
        for prog_data in programs_data:
            confidence, field_confs = self._compute_confidence(prog_data)
            ep = ExtractedProgram(
                crawl_job_id=crawl_job_id,
                source_id=raw.source_id,
                raw_data_id=raw_data_id,
                institution_name=prog_data.get("institution_name"),
                institution_country=prog_data.get("institution_country"),
                institution_city=prog_data.get("institution_city"),
                institution_type=prog_data.get("institution_type"),
                institution_website=prog_data.get("institution_website"),
                program_name=prog_data.get("program_name"),
                degree_type=self._normalize_degree_type(prog_data.get("degree_type")),
                department=prog_data.get("department"),
                duration_months=prog_data.get("duration_months"),
                tuition=prog_data.get("tuition"),
                tuition_currency=prog_data.get("tuition_currency", "USD"),
                acceptance_rate=prog_data.get("acceptance_rate"),
                requirements=prog_data.get("requirements"),
                description_text=prog_data.get("description_text"),
                application_deadline=prog_data.get("application_deadline"),
                program_start_date=prog_data.get("program_start_date"),
                highlights=prog_data.get("highlights"),
                faculty_contacts=prog_data.get("faculty_contacts"),
                rankings=prog_data.get("rankings"),
                financial_aid_info=prog_data.get("financial_aid_info"),
                extraction_confidence=confidence,
                field_confidences=field_confs,
                extraction_model=settings.crawler_extraction_model,
                raw_extracted_json=prog_data,
                review_status="pending",
            )
            self.db.add(ep)
            extracted.append(ep)

        # Update job counters
        job.items_extracted += len(extracted)

        # Mark raw data as processed
        raw.processed = True
        raw.processing_result = {
            "status": "extracted",
            "programs_found": len(extracted),
        }
        await self.db.flush()

        logger.info(
            "Extracted %d programs from raw %s (job %s)",
            len(extracted), raw_data_id, crawl_job_id,
        )
        return extracted

    async def process_unprocessed(
        self,
        crawl_job_id: UUID,
        limit: int = 100,
    ) -> int:
        """Process all unprocessed RawIngestedData for a crawl job."""
        job = await self.db.get(CrawlJob, crawl_job_id)
        if not job:
            raise NotFoundException(f"Crawl job {crawl_job_id} not found")

        stmt = (
            select(RawIngestedData)
            .where(
                RawIngestedData.source_id == job.source_id,
                RawIngestedData.processed.is_(False),
            )
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        raw_rows = list(result.scalars().all())

        total = 0
        for raw in raw_rows:
            extracted = await self.extract_from_raw(raw.id, crawl_job_id)
            total += len(extracted)

        logger.info("Processed %d raw records, extracted %d programs", len(raw_rows), total)
        return total

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_response(text: str) -> list[dict]:
        """Attempt to parse LLM JSON response. Robust to markdown fences."""
        if not text:
            return []

        # Strip markdown code fences
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines)

        try:
            data = json.loads(cleaned)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return [data]
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM JSON response: %.100s...", cleaned)
        return []

    @staticmethod
    def _compute_confidence(prog_data: dict) -> tuple[Decimal, dict]:
        """Compute extraction confidence from field presence.

        Weights: required fields = 3, high-value = 2, optional = 1.
        Returns (overall_confidence, per_field_confidences).
        """
        field_weights = {
            # Required (weight 3)
            "institution_name": 3,
            "program_name": 3,
            "degree_type": 3,
            # High-value (weight 2)
            "department": 2,
            "tuition": 2,
            "application_deadline": 2,
            "description_text": 2,
            "requirements": 2,
            # Optional (weight 1)
            "institution_country": 1,
            "institution_city": 1,
            "duration_months": 1,
            "acceptance_rate": 1,
            "highlights": 1,
            "faculty_contacts": 1,
            "rankings": 1,
            "financial_aid_info": 1,
        }

        total_weight = sum(field_weights.values())
        earned = 0
        field_confs: dict[str, float] = {}

        for field, weight in field_weights.items():
            value = prog_data.get(field)
            present = value is not None and value != "" and value != []
            field_confs[field] = 1.0 if present else 0.0
            if present:
                earned += weight

        overall = Decimal(str(round(earned / total_weight, 2)))
        return overall, field_confs

    @staticmethod
    def _normalize_degree_type(degree: str | None) -> str | None:
        """Normalize degree type strings to canonical forms."""
        if not degree:
            return None
        mapping = {
            "phd": "PhD",
            "ph.d.": "PhD",
            "ph.d": "PhD",
            "doctorate": "PhD",
            "masters": "Masters",
            "master": "Masters",
            "master's": "Masters",
            "ms": "Masters",
            "m.s.": "Masters",
            "ma": "Masters",
            "m.a.": "Masters",
            "msc": "Masters",
            "m.sc.": "Masters",
            "meng": "Masters",
            "m.eng.": "Masters",
            "mba": "MBA",
            "m.b.a.": "MBA",
            "mfa": "MFA",
            "m.f.a.": "MFA",
            "jd": "JD",
            "j.d.": "JD",
            "md": "MD",
            "m.d.": "MD",
            "edd": "EdD",
            "ed.d.": "EdD",
            "llm": "LLM",
            "l.l.m.": "LLM",
        }
        normalized = mapping.get(degree.lower().strip())
        return normalized if normalized else degree.strip()
