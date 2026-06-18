"""Claim service (AI Structure, Spec 2) — an institution admin claims its
school/program profiles. A claimed profile is first-party: the enrichment
routine must not overwrite it (the guard lives in the enrich-profile skill, and
`is_claimed` is the flag it reads)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.institution import Program, School
from unipaith.services.institution_service import InstitutionService


class ClaimService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def claim(
        self,
        user_id: UUID,
        *,
        program_ids: list[UUID] | None = None,
        school_ids: list[UUID] | None = None,
    ) -> dict:
        # The caller must own an institution; only its own programs/schools are claimable.
        inst = await InstitutionService(self.db)._get_institution_for_user(user_id)
        now = datetime.now(UTC)
        result = {"programs": 0, "schools": 0}

        if program_ids:
            rows = (
                (
                    await self.db.execute(
                        select(Program).where(
                            Program.id.in_(program_ids),
                            Program.institution_id == inst.id,
                        )
                    )
                )
                .scalars()
                .all()
            )
            for p in rows:
                p.is_claimed = True
                p.claimed_at = now
                p.claimed_by_user_id = user_id
            result["programs"] = len(rows)

        if school_ids:
            rows = (
                (
                    await self.db.execute(
                        select(School).where(
                            School.id.in_(school_ids),
                            School.institution_id == inst.id,
                        )
                    )
                )
                .scalars()
                .all()
            )
            for s in rows:
                s.is_claimed = True
                s.claimed_at = now
                s.claimed_by_user_id = user_id
            result["schools"] = len(rows)

        await self.db.flush()
        return {"claimed": result}
