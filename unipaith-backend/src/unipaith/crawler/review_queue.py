"""Review queue — human review workflow for extracted program records."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.crawler.ingestor import AutoIngestor
from unipaith.models.crawler import CrawlJob, ExtractedProgram

logger = logging.getLogger(__name__)


class ReviewQueue:
    """Manages the human review workflow for low-confidence extracted records."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_pending_count(self) -> int:
        """Return the number of extracted records awaiting review."""
        result = await self.db.execute(
            select(func.count(ExtractedProgram.id)).where(
                ExtractedProgram.review_status == "pending"
            )
        )
        return result.scalar() or 0

    async def list_pending(
        self,
        limit: int = 50,
        offset: int = 0,
        source_id: UUID | None = None,
    ) -> list[ExtractedProgram]:
        """List extracted programs awaiting review."""
        stmt = (
            select(ExtractedProgram)
            .where(ExtractedProgram.review_status == "pending")
            .order_by(ExtractedProgram.extraction_confidence.desc())
            .offset(offset)
            .limit(limit)
        )
        if source_id:
            stmt = stmt.where(ExtractedProgram.source_id == source_id)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def approve(
        self,
        extracted_id: UUID,
        reviewer_id: UUID,
        edits: dict | None = None,
        notes: str | None = None,
    ) -> dict:
        """Approve an extracted record, optionally applying edits, then ingest.

        Args:
            extracted_id: The record to approve.
            reviewer_id: Who approved it.
            edits: Optional dict of field overrides to apply before ingestion.
            notes: Optional reviewer notes.

        Returns:
            Ingestion result dict.
        """
        ep = await self.db.get(ExtractedProgram, extracted_id)
        if not ep:
            raise NotFoundException(f"Extracted program {extracted_id} not found")
        if ep.review_status != "pending":
            raise BadRequestException(
                f"Record is not pending review (status={ep.review_status})"
            )

        # Apply edits
        if edits:
            editable_fields = {
                "institution_name", "institution_country", "institution_city",
                "institution_type", "institution_website",
                "program_name", "degree_type", "department",
                "duration_months", "tuition", "tuition_currency",
                "acceptance_rate", "requirements", "description_text",
                "application_deadline", "program_start_date",
                "highlights", "faculty_contacts", "rankings",
                "financial_aid_info",
            }
            for field, value in edits.items():
                if field in editable_fields:
                    setattr(ep, field, value)

        ep.review_status = "approved"
        ep.reviewed_by = reviewer_id
        ep.reviewed_at = datetime.now(timezone.utc)
        ep.review_notes = notes
        await self.db.flush()

        # Run ingestion
        ingestor = AutoIngestor(self.db)
        # Force ingestion by temporarily raising confidence
        original_confidence = ep.extraction_confidence
        from decimal import Decimal
        ep.extraction_confidence = Decimal("0.99")
        result = await ingestor.process_extracted(extracted_id)
        ep.extraction_confidence = original_confidence
        await self.db.flush()

        logger.info("Approved and ingested EP %s by reviewer %s", extracted_id, reviewer_id)
        return result

    async def reject(
        self,
        extracted_id: UUID,
        reviewer_id: UUID,
        reason: str | None = None,
    ) -> dict:
        """Reject an extracted record."""
        ep = await self.db.get(ExtractedProgram, extracted_id)
        if not ep:
            raise NotFoundException(f"Extracted program {extracted_id} not found")
        if ep.review_status != "pending":
            raise BadRequestException(
                f"Record is not pending review (status={ep.review_status})"
            )

        ep.review_status = "rejected"
        ep.reviewed_by = reviewer_id
        ep.reviewed_at = datetime.now(timezone.utc)
        ep.review_notes = reason
        await self.db.flush()

        logger.info("Rejected EP %s by reviewer %s: %s", extracted_id, reviewer_id, reason)
        return {
            "action": "rejected",
            "extracted_id": str(extracted_id),
            "reason": reason,
        }

    async def get_review_stats(self) -> dict:
        """Return aggregate review statistics."""
        stmt = select(
            ExtractedProgram.review_status,
            func.count(ExtractedProgram.id),
        ).group_by(ExtractedProgram.review_status)

        result = await self.db.execute(stmt)
        rows = result.all()

        stats = {"pending": 0, "approved": 0, "rejected": 0, "auto_ingested": 0}
        for status, count in rows:
            stats[status] = count

        return stats
