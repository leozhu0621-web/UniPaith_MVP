"""Spec 68 — the one service every consumer reads outcomes through.

The point of the typed layer (§6) is that downstream stops digging into JSONB:
``65`` (program embed + ``data_completeness``), ``67`` (admit-history corpus),
``70`` (net-price / admit-probability), the Featured filters, and ``11``/``12``
detail all call this service, which owns:

- typed CRUD (``upsert_*``) with the §3 bias-avoidance guard on ``class_profile``;
- ``resolve()`` — authority precedence (first-party-wins, §7) then recency, so no
  consumer re-implements precedence;
- ``program_data_completeness()`` — the real coverage fraction that replaces the
  matcher's ``0.5`` cold-start default (``matching.py`` ``data_completeness``).

Absence is first-class (§2): a metric with no row resolves to ``None``; the
caller renders nothing, never a zero.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.outcomes import (
    OUTCOME_METRICS,
    OUTCOME_SOURCE_AUTHORITY,
    ProgramAdmissionsHistory,
    ProgramOutcome,
    ProgramTopEmployer,
    SchoolAdmissionsHistory,
    SchoolOutcome,
    disallowed_class_profile_keys,
)

_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


def _authority_key(row: ProgramOutcome | SchoolOutcome | ProgramAdmissionsHistory):
    """Sort key for §7 resolution: authority desc, then recency desc.

    Higher authority wins (first-party ``reported`` > ``licensed`` > ``crawled``);
    ties broken by the most recent reference window, then the latest write.
    """
    ref = getattr(row, "reference_period", None)
    if ref is None:
        ref = str(getattr(row, "cycle_year", "") or "")
    ts = getattr(row, "updated_at", None) or getattr(row, "created_at", None) or _EPOCH
    return (OUTCOME_SOURCE_AUTHORITY.get(row.source, 0), ref, ts)


class ClassProfileError(ValueError):
    """Raised when an admissions ``class_profile`` carries a non-academic key
    (a protected attribute or demographic proxy) — the §3 / spec 46 §6 guard."""


def _guard_class_profile(class_profile: dict | None) -> None:
    bad = disallowed_class_profile_keys(class_profile)
    if bad:
        raise ClassProfileError(
            "class_profile may carry academic aggregates only (spec 68 §3 / 46 §6); "
            f"disallowed keys: {sorted(bad)}"
        )


class OutcomesService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Program outcomes ────────────────────────────────────────────────────
    async def list_program_outcomes(self, program_id: UUID) -> list[ProgramOutcome]:
        res = await self.db.execute(
            select(ProgramOutcome).where(ProgramOutcome.program_id == program_id)
        )
        return list(res.scalars().all())

    async def resolve_program_outcome(self, program_id: UUID, metric: str) -> ProgramOutcome | None:
        """The §7 winner for one (program, metric): highest authority, newest."""
        res = await self.db.execute(
            select(ProgramOutcome).where(
                ProgramOutcome.program_id == program_id, ProgramOutcome.metric == metric
            )
        )
        rows = list(res.scalars().all())
        return max(rows, key=_authority_key) if rows else None

    async def resolved_program_outcomes(self, program_id: UUID) -> dict[str, ProgramOutcome]:
        """One winner per metric (§7), for the Outcomes section / embed summary."""
        winners: dict[str, ProgramOutcome] = {}
        for row in await self.list_program_outcomes(program_id):
            cur = winners.get(row.metric)
            if cur is None or _authority_key(row) > _authority_key(cur):
                winners[row.metric] = row
        return winners

    async def list_program_top_employers(self, program_id: UUID) -> list[ProgramTopEmployer]:
        res = await self.db.execute(
            select(ProgramTopEmployer)
            .where(ProgramTopEmployer.program_id == program_id)
            .order_by(ProgramTopEmployer.hire_count.desc().nullslast())
        )
        return list(res.scalars().all())

    async def list_program_admissions_history(
        self, program_id: UUID
    ) -> list[ProgramAdmissionsHistory]:
        res = await self.db.execute(
            select(ProgramAdmissionsHistory)
            .where(ProgramAdmissionsHistory.program_id == program_id)
            .order_by(ProgramAdmissionsHistory.cycle_year.desc())
        )
        return list(res.scalars().all())

    async def program_data_completeness(self, program_id: UUID) -> float:
        """Fraction of the outcomes vocabulary + admit-history populated (§6).

        Replaces the matcher's ``data_completeness`` cold-start ``0.5``: a program
        with rich, real data scores high; a thin one scores honestly low, which
        flows into Confidence (``65`` §5).
        """
        outcomes = await self.list_program_outcomes(program_id)
        admits = await self.list_program_admissions_history(program_id)
        present_metrics = {o.metric for o in outcomes}
        present = len(present_metrics & set(OUTCOME_METRICS)) + (1 if admits else 0)
        expected = len(OUTCOME_METRICS) + 1
        return round(present / expected, 4)

    async def upsert_program_outcome(
        self,
        program_id: UUID,
        metric: str,
        reference_period: str,
        *,
        source: str = "reported",
        value_numeric: float | None = None,
        value_json: dict | None = None,
        cohort_n: int | None = None,
        confidence: float = 0.7,
        status: str = "live",
        source_url: str | None = None,
    ) -> ProgramOutcome:
        """Idempotent on the (program, metric, window, source) unique key (§2)."""
        if metric not in OUTCOME_METRICS:
            raise ValueError(f"unknown outcome metric: {metric!r}")
        res = await self.db.execute(
            select(ProgramOutcome).where(
                ProgramOutcome.program_id == program_id,
                ProgramOutcome.metric == metric,
                ProgramOutcome.reference_period == reference_period,
                ProgramOutcome.source == source,
            )
        )
        row = res.scalar_one_or_none()
        if row is None:
            row = ProgramOutcome(
                program_id=program_id,
                metric=metric,
                reference_period=reference_period,
                source=source,
            )
            self.db.add(row)
        row.value_numeric = value_numeric
        row.value_json = value_json
        row.cohort_n = cohort_n
        row.confidence = confidence
        row.status = status
        row.source_url = source_url
        await self.db.flush()
        return row

    async def upsert_program_admissions(
        self,
        program_id: UUID,
        cycle_year: int,
        *,
        source: str = "reported",
        applicants: int | None = None,
        admits: int | None = None,
        enrolled: int | None = None,
        admit_rate: float | None = None,
        yield_rate: float | None = None,
        class_profile: dict | None = None,
        selectivity_band: str | None = None,
        confidence: float = 0.7,
        status: str = "live",
    ) -> ProgramAdmissionsHistory:
        """Idempotent on (program, cycle_year, source). Enforces the §3 academic-
        only ``class_profile`` guard before any write reaches the DB."""
        _guard_class_profile(class_profile)
        res = await self.db.execute(
            select(ProgramAdmissionsHistory).where(
                ProgramAdmissionsHistory.program_id == program_id,
                ProgramAdmissionsHistory.cycle_year == cycle_year,
                ProgramAdmissionsHistory.source == source,
            )
        )
        row = res.scalar_one_or_none()
        if row is None:
            row = ProgramAdmissionsHistory(
                program_id=program_id, cycle_year=cycle_year, source=source
            )
            self.db.add(row)
        row.applicants = applicants
        row.admits = admits
        row.enrolled = enrolled
        row.admit_rate = admit_rate
        row.yield_rate = yield_rate
        row.class_profile = class_profile
        row.selectivity_band = selectivity_band
        row.confidence = confidence
        row.status = status
        await self.db.flush()
        return row

    # ── School outcomes (§4 — distinct grain, never averaged up from programs) ─
    async def list_school_outcomes(self, school_id: UUID) -> list[SchoolOutcome]:
        res = await self.db.execute(
            select(SchoolOutcome).where(SchoolOutcome.school_id == school_id)
        )
        return list(res.scalars().all())

    async def resolve_school_outcome(self, school_id: UUID, metric: str) -> SchoolOutcome | None:
        res = await self.db.execute(
            select(SchoolOutcome).where(
                SchoolOutcome.school_id == school_id, SchoolOutcome.metric == metric
            )
        )
        rows = list(res.scalars().all())
        return max(rows, key=_authority_key) if rows else None

    async def list_school_admissions_history(
        self, school_id: UUID
    ) -> list[SchoolAdmissionsHistory]:
        res = await self.db.execute(
            select(SchoolAdmissionsHistory)
            .where(SchoolAdmissionsHistory.school_id == school_id)
            .order_by(SchoolAdmissionsHistory.cycle_year.desc())
        )
        return list(res.scalars().all())

    # ── Bulk resolution (§6/§7) — for the Featured-filter response build ────
    async def resolve_program_metrics_bulk(
        self, program_ids: list[UUID], metrics: list[str] | None = None
    ) -> dict[tuple[UUID, str], float]:
        """Authority-resolved scalar (``value_numeric``) per (program, metric)
        for a batch of programs in one query (§7). ``DISTINCT ON`` over the
        authority/recency order picks the winner; lets the Featured filters stop
        digging into JSONB per-program (§6). Only scalar metrics are returned."""
        if not program_ids:
            return {}
        metrics = metrics or list(OUTCOME_METRICS)
        auth = case(
            (ProgramOutcome.source == "reported", 3),
            (ProgramOutcome.source == "licensed", 2),
            else_=1,
        )
        stmt = (
            select(
                ProgramOutcome.program_id,
                ProgramOutcome.metric,
                ProgramOutcome.value_numeric,
            )
            .where(
                ProgramOutcome.program_id.in_(program_ids),
                ProgramOutcome.metric.in_(metrics),
                ProgramOutcome.value_numeric.isnot(None),
            )
            .distinct(ProgramOutcome.program_id, ProgramOutcome.metric)
            .order_by(
                ProgramOutcome.program_id,
                ProgramOutcome.metric,
                auth.desc(),
                ProgramOutcome.reference_period.desc(),
                ProgramOutcome.updated_at.desc(),
            )
        )
        res = await self.db.execute(stmt)
        return {(r.program_id, r.metric): float(r.value_numeric) for r in res.all()}
