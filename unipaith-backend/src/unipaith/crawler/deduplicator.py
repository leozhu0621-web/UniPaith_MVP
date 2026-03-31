"""Deduplicator — match extracted programs to existing institutions/programs."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from thefuzz import fuzz

from unipaith.config import settings
from unipaith.core.exceptions import NotFoundException
from unipaith.models.crawler import CrawlJob, ExtractedProgram
from unipaith.models.institution import Institution, Program

logger = logging.getLogger(__name__)


class Deduplicator:
    """Matches extracted records against existing institutions and programs."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def match_and_classify(self, extracted_id: UUID) -> ExtractedProgram:
        """Load an ExtractedProgram, match institution/program, classify type."""
        ep = await self.db.get(ExtractedProgram, extracted_id)
        if not ep:
            raise NotFoundException(f"Extracted program {extracted_id} not found")

        # Step 1: match institution
        institution = await self._match_institution(ep)
        if institution:
            ep.matched_institution_id = institution.id

            # Step 2: match program within institution
            program = await self._match_program(ep, institution.id)
            if program:
                ep.matched_program_id = program.id
                ep.match_type = self._classify_match(ep, program)
            else:
                ep.match_type = "new"
        else:
            ep.match_type = "new"

        await self.db.flush()
        logger.debug(
            "Classified EP %s: match_type=%s, inst=%s, prog=%s",
            ep.id,
            ep.match_type,
            ep.matched_institution_id,
            ep.matched_program_id,
        )
        return ep

    async def deduplicate_batch(self, crawl_job_id: UUID) -> dict:
        """Process all ExtractedPrograms for a crawl job. Return classification counts."""
        job = await self.db.get(CrawlJob, crawl_job_id)
        if not job:
            raise NotFoundException(f"Crawl job {crawl_job_id} not found")

        stmt = select(ExtractedProgram).where(
            ExtractedProgram.crawl_job_id == crawl_job_id,
            ExtractedProgram.match_type.is_(None),
        )
        result = await self.db.execute(stmt)
        eps = list(result.scalars().all())

        counts = {"new": 0, "update": 0, "duplicate": 0, "conflict": 0}
        for ep in eps:
            await self.match_and_classify(ep.id)
            match_type = ep.match_type or "new"
            counts[match_type] = counts.get(match_type, 0) + 1

        await self.db.flush()
        logger.info("Deduplicated %d records for job %s: %s", len(eps), crawl_job_id, counts)
        return counts

    # ------------------------------------------------------------------
    # Matching helpers
    # ------------------------------------------------------------------

    async def _match_institution(self, ep: ExtractedProgram) -> Institution | None:
        """Try exact name match first, then fuzzy match above threshold."""
        if not ep.institution_name:
            return None

        # Exact match
        stmt = select(Institution).where(
            func.lower(Institution.name) == ep.institution_name.lower()
        )
        result = await self.db.execute(stmt)
        exact = result.scalar_one_or_none()
        if exact:
            return exact

        # Fuzzy match
        all_stmt = select(Institution).limit(1000)
        result = await self.db.execute(all_stmt)
        institutions = list(result.scalars().all())

        threshold = settings.crawler_fuzzy_match_threshold
        best_score = 0
        best_match: Institution | None = None

        for inst in institutions:
            score = fuzz.ratio(ep.institution_name.lower(), inst.name.lower())
            if score > best_score and score >= threshold:
                best_score = score
                best_match = inst

        return best_match

    async def _match_program(
        self,
        ep: ExtractedProgram,
        institution_id: UUID,
    ) -> Program | None:
        """Match by program name + degree type within an institution."""
        if not ep.program_name or not ep.degree_type:
            return None

        stmt = select(Program).where(
            Program.institution_id == institution_id,
            func.lower(Program.program_name) == ep.program_name.lower(),
            func.lower(Program.degree_type) == ep.degree_type.lower(),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _classify_match(ep: ExtractedProgram, existing: Program) -> str:
        """Classify as duplicate, update, or conflict based on field differences.

        - duplicate: no meaningful differences
        - update: 1-3 fields differ
        - conflict: 4+ fields differ
        """
        diffs = 0
        comparisons = [
            (ep.department, existing.department),
            (ep.duration_months, existing.duration_months),
            (ep.tuition, existing.tuition),
            (ep.description_text, existing.description_text),
            (
                str(ep.application_deadline) if ep.application_deadline else None,
                str(existing.application_deadline) if existing.application_deadline else None,
            ),
            (ep.acceptance_rate, existing.acceptance_rate),
        ]

        for new_val, old_val in comparisons:
            if new_val is not None and old_val is not None:
                if str(new_val).strip() != str(old_val).strip():
                    diffs += 1
            elif new_val is not None and old_val is None:
                diffs += 1

        if diffs == 0:
            return "duplicate"
        elif diffs <= 3:
            return "update"
        else:
            return "conflict"
