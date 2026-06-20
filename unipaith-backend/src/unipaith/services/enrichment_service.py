"""Enrichment service (AI Structure, Spec 1) — the thin DB adapter between the
pure planner and the normalized signal store.

`build_signal_state` reads the student's `StudentSignal` rows into the planner's
`{field: {value, confidence}}` shape; `next_signals` runs the planner; `set_value`
writes a confirmed answer back through the intake engine (which normalizes,
versions, and stamps provenance + a change-event).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import BadRequestException
from unipaith.models.intake import StudentSignal
from unipaith.models.student import StudentPreference
from unipaith.services.catalog_service import CatalogService
from unipaith.services.enrichment_planner import (
    CATALOG,
    essentials_present,
    plan_next,
)
from unipaith.services.intake.intake_engine_service import IntakeEngineService


def _unwrap(v: Any) -> Any:
    """Signals store scalars wrapped as ``{"v": ...}`` — unwrap for the planner."""
    if isinstance(v, dict) and set(v.keys()) == {"v"}:
        return v["v"]
    return v


def _coerce_weight_0_5(field: str, value: Any) -> int:
    """Spec 1 §2.4 — an importance weight is asked 0-5. Coerce a numeric value to
    an int in 0..5; reject non-numeric (the old widget submitted a phrase) or
    out-of-range. Returns the 0-5 value (the caller scales to 0-10)."""
    if isinstance(value, bool):
        raise BadRequestException(f"{field}: importance must be a number 0-5")
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        raise BadRequestException(f"{field}: importance must be a number 0-5, got {value!r}")
    if not 0 <= n <= 5:
        raise BadRequestException(f"{field}: importance must be 0-5, got {n}")
    return n


def _validate_taxonomy(field: str, value: Any, options: list[str], *, is_multi: bool) -> None:
    """Spec 1 §8 — a categorical/multi answer must be in the field's CATALOG taxonomy."""
    allowed = set(options)
    if is_multi:
        if not isinstance(value, list):
            raise BadRequestException(f"{field}: expected a list of choices")
        bad = [v for v in value if v not in allowed]
        if bad:
            raise BadRequestException(f"{field}: {bad!r} not in the allowed options")
    elif value not in allowed:
        raise BadRequestException(f"{field}: {value!r} is not one of the allowed options")


class EnrichmentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _catalog(self) -> list[dict[str, Any]]:
        """The data-driven Prompt Library, in the planner's dict shape. Falls
        back to the in-code CATALOG when the table is unseeded (fresh DB / tests),
        so behavior is identical before the startup seed runs."""
        cat = await CatalogService(self.db).load()
        return cat or list(CATALOG)

    async def build_signal_state(self, student_id: UUID) -> dict[str, Any]:
        rows = (
            (
                await self.db.execute(
                    select(StudentSignal).where(StudentSignal.student_id == student_id)
                )
            )
            .scalars()
            .all()
        )
        state: dict[str, Any] = {}
        for s in rows:
            state[s.signal_name] = {
                "value": _unwrap(s.value),
                "confidence": (s.confidence / 100.0) if s.confidence is not None else None,
                "source": s.source,
            }
        return state

    async def next_signals(
        self, student_id: UUID, *, limit: int = 3, section: str | None = None
    ) -> dict[str, Any]:
        state = await self.build_signal_state(student_id)
        cat = await self._catalog()
        return {
            # `section` scopes the planner to one tab's fields; an unknown/None
            # section is unscoped (global next). `essentials_present` is always
            # global — it is the match prerequisite, not a per-tab signal.
            "items": plan_next(state, limit=limit, section=section, catalog=cat),
            "essentials_present": essentials_present(state, catalog=cat),
        }

    async def set_value(self, student_id: UUID, field: str, value: Any) -> dict[str, Any]:
        by_key = {e["key"]: e for e in await self._catalog()}
        entry = by_key.get(field)
        if entry is None:
            raise BadRequestException(f"Unknown enrichment field '{field}'")
        # Type the value per the CATALOG (the Prompt Library) before it reaches the
        # signal store (Spec 1 §2.4 / §8):
        #  - weight: asked 0-5, stored 0-10 on StudentPreference (the column the
        #    matcher reads at match_banding.py); the signal keeps the 0-5 answer.
        #  - categorical/multi with a fixed option set: reject out-of-taxonomy.
        options = entry.get("options")
        if entry["type"] == "weight":
            chosen = _coerce_weight_0_5(field, value)
            await self._project_preference_weight(student_id, field, chosen * 2)
            value = chosen
        elif entry["ask_kind"] in ("choice", "multi") and options:
            _validate_taxonomy(field, value, options, is_multi=entry["type"] == "multi")
        # A confirmed widget/ask answer: student-typed, structured, parse OK → the
        # intake engine stamps it at high confidence and writes a change-event.
        return await IntakeEngineService(self.db).ingest_signal(
            student_id,
            field,
            value,
            channel="form",
            source="student-typed",
            structured=True,
            parse_ok=True,
        )

    async def _project_preference_weight(self, student_id: UUID, column: str, scaled: int) -> None:
        """Write the scaled 0-10 importance weight onto StudentPreference (matcher source)."""
        pref = (
            await self.db.execute(
                select(StudentPreference).where(StudentPreference.student_id == student_id)
            )
        ).scalar_one_or_none()
        if pref is None:
            pref = StudentPreference(student_id=student_id)
            self.db.add(pref)
        setattr(pref, column, scaled)
        await self.db.flush()
