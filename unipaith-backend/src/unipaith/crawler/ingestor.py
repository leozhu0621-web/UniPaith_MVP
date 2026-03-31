"""Auto-ingestor — route extracted programs into the main database."""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.exceptions import NotFoundException
from unipaith.models.crawler import CrawlJob, ExtractedProgram
from unipaith.models.institution import Program

logger = logging.getLogger(__name__)


class AutoIngestor:
    """Ingests extracted programs into the production database.

    Routing logic based on extraction confidence and match type:
    - confidence >= auto_ingest threshold AND (new or update) -> auto-ingest
    - confidence >= review_queue threshold -> queue for review
    - confidence < review_queue threshold -> queue for review with low-confidence flag
    - duplicate -> skip
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_extracted(self, extracted_id: UUID) -> dict:
        """Route a single ExtractedProgram through the ingestion pipeline."""
        ep = await self.db.get(ExtractedProgram, extracted_id)
        if not ep:
            raise NotFoundException(f"Extracted program {extracted_id} not found")

        confidence = float(ep.extraction_confidence or 0)
        auto_threshold = settings.crawler_confidence_auto_ingest
        match_type = ep.match_type or "new"

        # Duplicates are always skipped
        if match_type == "duplicate":
            ep.review_status = "auto_ingested"
            await self.db.flush()
            return {"action": "skipped_duplicate", "extracted_id": str(ep.id)}

        # High confidence + new/update -> auto-ingest
        if confidence >= auto_threshold and match_type in ("new", "update"):
            if match_type == "new":
                result = await self._create_new(ep)
            else:
                result = await self._update_existing(ep)
            ep.review_status = "auto_ingested"
            await self.db.flush()
            return result

        # Anything else -> queue for review
        ep.review_status = "pending"
        await self.db.flush()
        return {
            "action": "queued_for_review",
            "extracted_id": str(ep.id),
            "reason": f"confidence={confidence:.2f}, match_type={match_type}",
        }

    async def process_crawl_job(self, crawl_job_id: UUID) -> dict:
        """Batch process all classified extracted programs for a crawl job."""
        job = await self.db.get(CrawlJob, crawl_job_id)
        if not job:
            raise NotFoundException(f"Crawl job {crawl_job_id} not found")

        stmt = select(ExtractedProgram).where(
            ExtractedProgram.crawl_job_id == crawl_job_id,
            ExtractedProgram.match_type.isnot(None),
            ExtractedProgram.review_status == "pending",
        )
        result = await self.db.execute(stmt)
        eps = list(result.scalars().all())

        counts = {
            "auto_ingested_new": 0,
            "auto_ingested_update": 0,
            "skipped_duplicate": 0,
            "queued_for_review": 0,
        }

        for ep in eps:
            res = await self.process_extracted(ep.id)
            action = res.get("action", "")
            if action == "created_new":
                counts["auto_ingested_new"] += 1
                job.items_ingested += 1
            elif action == "updated_existing":
                counts["auto_ingested_update"] += 1
                job.items_ingested += 1
            elif action == "skipped_duplicate":
                counts["skipped_duplicate"] += 1
                job.items_duplicate += 1
            elif action == "queued_for_review":
                counts["queued_for_review"] += 1
                job.items_queued_for_review += 1

        await self.db.flush()
        logger.info("Ingestion for job %s: %s", crawl_job_id, counts)
        return counts

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _create_new(self, ep: ExtractedProgram) -> dict:
        """Create a new Program (and Institution if needed) from an ExtractedProgram.

        Note: Institution requires admin_user_id (NOT NULL), so crawler-created
        institutions cannot be auto-created. If no existing institution matches,
        the record is queued for review so an admin can manually assign it.
        """
        institution_id = ep.matched_institution_id

        # If no matched institution, we cannot auto-create one because Institution
        # requires a non-null admin_user_id FK. Queue for manual review instead.
        if not institution_id:
            ep.review_status = "pending"
            await self.db.flush()
            return {
                "action": "queued_for_review",
                "extracted_id": str(ep.id),
                "reason": "no_matching_institution",
            }

        program = Program(
            institution_id=institution_id,
            program_name=ep.program_name or "Unknown Program",
            degree_type=ep.degree_type or "Masters",
            department=ep.department,
            duration_months=ep.duration_months,
            tuition=ep.tuition,
            acceptance_rate=ep.acceptance_rate,
            requirements=ep.requirements,
            description_text=ep.description_text,
            application_deadline=ep.application_deadline,
            program_start_date=ep.program_start_date,
            highlights=ep.highlights,
            faculty_contacts=ep.faculty_contacts,
            is_published=False,
        )
        self.db.add(program)
        await self.db.flush()

        ep.matched_program_id = program.id
        logger.info("Created new program %s at institution %s", program.id, institution_id)

        return {
            "action": "created_new",
            "extracted_id": str(ep.id),
            "program_id": str(program.id),
            "institution_id": str(institution_id),
        }

    async def _update_existing(self, ep: ExtractedProgram) -> dict:
        """Update non-null fields on the matched existing Program."""
        if not ep.matched_program_id:
            return {"action": "queued_for_review", "reason": "no_matched_program"}

        program = await self.db.get(Program, ep.matched_program_id)
        if not program:
            return {"action": "queued_for_review", "reason": "program_not_found"}

        # Update only non-null extracted fields
        updatable = [
            ("department", ep.department),
            ("duration_months", ep.duration_months),
            ("tuition", ep.tuition),
            ("acceptance_rate", ep.acceptance_rate),
            ("requirements", ep.requirements),
            ("description_text", ep.description_text),
            ("application_deadline", ep.application_deadline),
            ("program_start_date", ep.program_start_date),
            ("highlights", ep.highlights),
            ("faculty_contacts", ep.faculty_contacts),
        ]

        updated_fields: list[str] = []
        for field_name, new_value in updatable:
            if new_value is not None:
                setattr(program, field_name, new_value)
                updated_fields.append(field_name)

        await self.db.flush()
        logger.info(
            "Updated program %s: fields=%s",
            ep.matched_program_id,
            updated_fields,
        )

        return {
            "action": "updated_existing",
            "extracted_id": str(ep.id),
            "program_id": str(ep.matched_program_id),
            "updated_fields": updated_fields,
        }
