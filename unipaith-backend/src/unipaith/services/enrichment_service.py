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
from unipaith.services.enrichment_planner import (
    CATALOG,
    essentials_present,
    plan_next,
)
from unipaith.services.intake.intake_engine_service import IntakeEngineService

_CATALOG_KEYS = {f["key"] for f in CATALOG}


def _unwrap(v: Any) -> Any:
    """Signals store scalars wrapped as ``{"v": ...}`` — unwrap for the planner."""
    if isinstance(v, dict) and set(v.keys()) == {"v"}:
        return v["v"]
    return v


class EnrichmentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

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

    async def next_signals(self, student_id: UUID, *, limit: int = 3) -> dict[str, Any]:
        state = await self.build_signal_state(student_id)
        return {
            "items": plan_next(state, limit=limit),
            "essentials_present": essentials_present(state),
        }

    async def set_value(self, student_id: UUID, field: str, value: Any) -> dict[str, Any]:
        if field not in _CATALOG_KEYS:
            raise BadRequestException(f"Unknown enrichment field '{field}'")
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
