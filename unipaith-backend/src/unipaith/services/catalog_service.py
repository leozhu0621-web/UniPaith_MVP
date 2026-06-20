"""CatalogService — load the data-driven Prompt Library and idempotently seed it.

`load` returns the catalog in the exact dict shape the pure planner consumes
(`key, type, tier, ask_kind, question, options`), read from the `prompt_catalog`
table. `ensure_seeded` inserts any *missing* prompts from the in-code `CATALOG`
snapshot (insert-if-absent by `key`), so re-seeding on every boot never clobbers
edits a later Airtable sync writes into the same rows.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.prompt_catalog import PromptCatalog
from unipaith.services.enrichment_planner import CATALOG

# Student-facing section grouping (spec §3.1) for the seed of the existing
# CATALOG keys. The planner does not use `section` (it scopes by SECTION_FIELDS);
# it is for display grouping only.
_SECTION_BY_KEY: dict[str, str] = {
    "gender": "Basics",
    "nationality": "Basics",
    "date_of_birth": "Basics",
    "country_of_residence": "Basics",
    "first_generation": "Basics",
    "current_education_level": "Basics",
    "target_degree_level": "Your direction",
    "field_of_interest": "Your direction",
    "specialization": "Your direction",
    "intended_start": "Your direction",
    "study_mode": "Your direction",
    "gpa": "Academics",
    "gpa_scale": "Academics",
    "test_scores": "Academics",
    "tests_taken": "Academics",
    "english_proficiency": "Academics",
    "strongest_subjects": "Academics",
    "research_experience": "Experience",
    "activities": "Experience",
    "work_experience": "Experience",
    "languages": "Experience",
    "career_goal": "Goals",
    "goal_after_degree": "Goals",
    "goals": "Goals",
    "budget_band": "Money",
    "funding_requirement": "Money",
    "preferred_countries": "Where & how",
    "preferred_setting": "Where & how",
    "school_size": "Where & how",
    "institution_type": "Where & how",
    "climate": "Where & how",
    "distance_from_home": "Where & how",
    "weight_cost": "What matters most",
    "weight_location": "What matters most",
    "weight_outcomes": "What matters most",
    "weight_flexibility": "What matters most",
    "weight_support": "What matters most",
    "weight_time_to_degree": "What matters most",
    "needs": "What matters most",
    "identity": "What matters most",
}
# Free-categorical fields resolve against a reference list, not free text.
_REFERENCE_SOURCE: dict[str, str] = {
    "nationality": "countries",
    "country_of_residence": "countries",
}


class CatalogService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def ensure_seeded(self) -> None:
        """Insert any CATALOG prompts not already present (idempotent by key)."""
        for i, f in enumerate(CATALOG):
            await self.db.execute(
                pg_insert(PromptCatalog)
                .values(
                    key=f["key"],
                    section=_SECTION_BY_KEY.get(f["key"], "Basics"),
                    question=f["question"],
                    ask_kind=f["ask_kind"],
                    value_type=f["type"],
                    options=f.get("options"),
                    tier=f["tier"],
                    saves_to=f["key"],
                    reference_source=_REFERENCE_SOURCE.get(f["key"]),
                    sort_order=i,
                )
                .on_conflict_do_nothing(index_elements=["key"])
            )
        await self.db.flush()

    async def load(self) -> list[dict[str, Any]]:
        """Return the active catalog in the planner's dict shape, ordered."""
        rows = (
            (
                await self.db.execute(
                    select(PromptCatalog)
                    .where(PromptCatalog.active.is_(True))
                    .order_by(PromptCatalog.sort_order, PromptCatalog.key)
                )
            )
            .scalars()
            .all()
        )
        return [
            {
                "key": r.key,
                "type": r.value_type,
                "tier": r.tier,
                "ask_kind": r.ask_kind,
                "question": r.question,
                "options": r.options,
            }
            for r in rows
        ]
