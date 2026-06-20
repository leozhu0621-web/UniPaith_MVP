"""Program-preference service (AI Structure, Spec 2/3) — a claimed school edits
its program's target-applicant preferences. Edits are first-party
(`source="claimed"`, full confidence) and ownership-scoped: a program is only
editable through its owning institution."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import NotFoundException
from unipaith.models.institution import Program, ProgramPreference

_EDITABLE = {
    "pref_min_gpa",
    "pref_test_bands",
    "pref_fields",
    "pref_levels",
    "pref_countries",
    "weight_academic",
    "weight_field_fit",
    "weight_outcomes_alignment",
    "weight_funding_need",
    "weight_geographic",
    "target_profile",
    "preference_weights",
    "provenance",
}


class ProgramPreferenceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _owned_program(self, institution_id: UUID, program_id: UUID) -> Program:
        prog = await self.db.scalar(
            select(Program).where(
                Program.id == program_id, Program.institution_id == institution_id
            )
        )
        if prog is None:
            raise NotFoundException("Program not found")
        return prog

    async def get(self, institution_id: UUID, program_id: UUID) -> ProgramPreference | None:
        await self._owned_program(institution_id, program_id)
        return await self.db.scalar(
            select(ProgramPreference).where(ProgramPreference.program_id == program_id)
        )

    async def upsert(
        self, institution_id: UUID, program_id: UUID, data: dict[str, Any]
    ) -> ProgramPreference:
        await self._owned_program(institution_id, program_id)
        pref = await self.db.scalar(
            select(ProgramPreference).where(ProgramPreference.program_id == program_id)
        )
        if pref is None:
            pref = ProgramPreference(program_id=program_id)
            self.db.add(pref)
        for key, value in data.items():
            if key in _EDITABLE:
                if key == "target_profile" and value is not None:
                    from unipaith.schemas.profile_intelligence import validate_target_profile

                    value = validate_target_profile(value)
                setattr(pref, key, value)
        # A school user setting this is first-party — never overwritten by the routine.
        pref.source = "claimed"
        pref.confidence = Decimal("1.00")
        pref.standard_version = 1
        await self.db.flush()
        return pref
