"""Enrichment pipeline — supplementary data enrichment for institutions and programs."""
from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import NotFoundException
from unipaith.models.crawler import EnrichmentRecord
from unipaith.models.institution import Institution, Program

logger = logging.getLogger(__name__)


class EnrichmentPipeline:
    """Manages supplementary data enrichment records and their application."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def enrich_institution(
        self,
        institution_id: UUID,
        enrichment_type: str,
        source_id: UUID,
        data: dict,
        confidence: float,
        effective_date: date | None = None,
        expires_at: date | None = None,
    ) -> EnrichmentRecord:
        """Create an enrichment record for an institution."""
        institution = await self.db.get(Institution, institution_id)
        if not institution:
            raise NotFoundException(f"Institution {institution_id} not found")

        record = EnrichmentRecord(
            institution_id=institution_id,
            enrichment_type=enrichment_type,
            source_id=source_id,
            data=data,
            confidence=Decimal(str(round(confidence, 2))),
            effective_date=effective_date,
            expires_at=expires_at,
        )
        self.db.add(record)
        await self.db.flush()

        logger.info(
            "Created %s enrichment for institution %s (confidence=%.2f)",
            enrichment_type, institution_id, confidence,
        )
        return record

    async def enrich_program(
        self,
        program_id: UUID,
        enrichment_type: str,
        source_id: UUID,
        data: dict,
        confidence: float,
        effective_date: date | None = None,
        expires_at: date | None = None,
    ) -> EnrichmentRecord:
        """Create an enrichment record for a program."""
        program = await self.db.get(Program, program_id)
        if not program:
            raise NotFoundException(f"Program {program_id} not found")

        record = EnrichmentRecord(
            program_id=program_id,
            enrichment_type=enrichment_type,
            source_id=source_id,
            data=data,
            confidence=Decimal(str(round(confidence, 2))),
            effective_date=effective_date,
            expires_at=expires_at,
        )
        self.db.add(record)
        await self.db.flush()

        logger.info(
            "Created %s enrichment for program %s (confidence=%.2f)",
            enrichment_type, program_id, confidence,
        )
        return record

    async def apply_enrichments(self, program_id: UUID) -> dict:
        """Apply highest-confidence enrichments to a program.

        For each enrichment type, picks the record with the highest confidence
        and merges the data into the program fields.
        """
        program = await self.db.get(Program, program_id)
        if not program:
            raise NotFoundException(f"Program {program_id} not found")

        stmt = (
            select(EnrichmentRecord)
            .where(EnrichmentRecord.program_id == program_id)
            .order_by(EnrichmentRecord.confidence.desc())
        )
        result = await self.db.execute(stmt)
        records = list(result.scalars().all())

        if not records:
            return {"program_id": str(program_id), "applied": 0}

        # Group by type, take highest confidence
        best_by_type: dict[str, EnrichmentRecord] = {}
        for rec in records:
            if rec.enrichment_type not in best_by_type:
                best_by_type[rec.enrichment_type] = rec

        applied_count = 0
        applied_types: list[str] = []

        for etype, rec in best_by_type.items():
            data = rec.data or {}
            if etype == "ranking" and data:
                current = program.ranking_data if hasattr(program, "ranking_data") else None
                # Merge into institution ranking_data via institution
                inst = await self.db.get(Institution, program.institution_id)
                if inst:
                    merged = inst.ranking_data or {}
                    merged.update(data)
                    inst.ranking_data = merged
                    applied_count += 1
                    applied_types.append(etype)

            elif etype == "stats" and data:
                if "acceptance_rate" in data:
                    program.acceptance_rate = Decimal(str(data["acceptance_rate"]))
                    applied_count += 1
                    applied_types.append(etype)

            elif etype == "financial_aid" and data:
                current_highlights = program.highlights or []
                if isinstance(current_highlights, list):
                    aid_summary = data.get("summary")
                    if aid_summary and aid_summary not in current_highlights:
                        current_highlights.append(aid_summary)
                        program.highlights = current_highlights
                        applied_count += 1
                        applied_types.append(etype)

            elif etype == "deadline" and data:
                if "application_deadline" in data:
                    from datetime import date as date_type
                    try:
                        program.application_deadline = date_type.fromisoformat(
                            data["application_deadline"]
                        )
                        applied_count += 1
                        applied_types.append(etype)
                    except (ValueError, TypeError):
                        pass

        await self.db.flush()
        logger.info(
            "Applied %d enrichments to program %s: %s",
            applied_count, program_id, applied_types,
        )
        return {
            "program_id": str(program_id),
            "applied": applied_count,
            "types": applied_types,
        }

    async def apply_all_pending_enrichments(self) -> dict:
        """Apply enrichments to all programs that have pending enrichment records."""
        stmt = (
            select(EnrichmentRecord.program_id)
            .where(EnrichmentRecord.program_id.isnot(None))
            .distinct()
        )
        result = await self.db.execute(stmt)
        program_ids = [row[0] for row in result.all()]

        total_applied = 0
        for pid in program_ids:
            res = await self.apply_enrichments(pid)
            total_applied += res.get("applied", 0)

        logger.info(
            "Applied enrichments to %d programs, %d total enrichments",
            len(program_ids), total_applied,
        )
        return {
            "programs_processed": len(program_ids),
            "total_applied": total_applied,
        }
