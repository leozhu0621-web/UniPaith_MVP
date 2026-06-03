"""Spec 68 — outcomes ingestion (the prod path) + a curated dev generator.

``OutcomesLoader`` ingests structured records into the typed tables via
``OutcomesService`` (idempotent upserts, §3 bias guard). This is the path a real
**IPEDS / U.S. College Scorecard** adapter feeds — that HTTP adapter is a
clearly-scoped follow-up (§7 / spec open question); this module is the seam it
writes through. For local dev, ``curated_program_records`` produces realistic,
**deterministic** figures (never ``random.uniform`` — the §6 fabrication smell)
so the seed has real-looking outcomes without fabricated per-applicant rows.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.services.outcomes_service import OutcomesService


@dataclass
class OutcomeRecord:
    metric: str
    reference_period: str
    source: str = "licensed"
    value_numeric: float | None = None
    value_json: dict | None = None
    cohort_n: int | None = None
    confidence: float = 0.85


@dataclass
class AdmissionsRecord:
    cycle_year: int
    source: str = "reported"
    applicants: int | None = None
    admits: int | None = None
    enrolled: int | None = None
    admit_rate: float | None = None
    yield_rate: float | None = None
    class_profile: dict | None = None
    selectivity_band: str | None = None
    confidence: float = 0.8


class OutcomesLoader:
    """Idempotent ingestion of typed outcomes / admissions records (§7).

    The bulk path: a sourced adapter (IPEDS/Scorecard/partner feed) builds the
    record lists and calls these; resolution + provenance live in the service.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.svc = OutcomesService(db)

    async def load_program_outcomes(self, program_id: UUID, records: list[OutcomeRecord]) -> int:
        for r in records:
            await self.svc.upsert_program_outcome(
                program_id,
                r.metric,
                r.reference_period,
                source=r.source,
                value_numeric=r.value_numeric,
                value_json=r.value_json,
                cohort_n=r.cohort_n,
                confidence=r.confidence,
                status="live",
            )
        return len(records)

    async def load_program_admissions(
        self, program_id: UUID, records: list[AdmissionsRecord]
    ) -> int:
        for r in records:
            await self.svc.upsert_program_admissions(
                program_id,
                r.cycle_year,
                source=r.source,
                applicants=r.applicants,
                admits=r.admits,
                enrolled=r.enrolled,
                admit_rate=r.admit_rate,
                yield_rate=r.yield_rate,
                class_profile=r.class_profile,
                selectivity_band=r.selectivity_band,
                confidence=r.confidence,
                status="live",
            )
        return len(records)


# Realistic figures by degree type (deterministic — NOT random, §6). A real
# IPEDS/Scorecard adapter replaces this curated table with sourced data.
_BY_DEGREE: dict[str, dict] = {
    "masters": dict(
        salary=108000, emp=0.93, payback=28, admit=0.22, yld=0.46, gpa=3.7, sel="highly_selective"
    ),
    "mba": dict(
        salary=152000, emp=0.94, payback=34, admit=0.25, yld=0.50, gpa=3.6, sel="highly_selective"
    ),
    "doctoral": dict(
        salary=92000, emp=0.96, payback=18, admit=0.11, yld=0.55, gpa=3.8, sel="most_selective"
    ),
    "phd": dict(
        salary=92000, emp=0.96, payback=18, admit=0.11, yld=0.55, gpa=3.8, sel="most_selective"
    ),
    "bachelors": dict(
        salary=72000, emp=0.88, payback=40, admit=0.30, yld=0.40, gpa=3.5, sel="selective"
    ),
    "professional": dict(
        salary=125000, emp=0.95, payback=30, admit=0.18, yld=0.52, gpa=3.7, sel="highly_selective"
    ),
}


def curated_program_records(
    degree_type: str,
    *,
    index: int = 0,
    periods: tuple[str, ...] = ("2024",),
    cycles: tuple[int, ...] = (2024, 2025),
) -> tuple[list[OutcomeRecord], list[AdmissionsRecord]]:
    """Realistic, deterministic records for one program — varied a few percent by
    ``index`` so a catalog of the same degree type isn't perfectly flat. Sources
    are ``licensed`` (outcomes) / ``reported`` (admissions); ``class_profile`` is
    academic-only (the §3 guard would reject anything else)."""
    base = _BY_DEGREE.get((degree_type or "").lower(), _BY_DEGREE["masters"])
    d = (index % 5) - 2  # -2..+2 deterministic offset
    salary = int(base["salary"] * (1 + 0.03 * d))
    emp = round(min(0.99, max(0.50, base["emp"] + 0.01 * d)), 4)
    payback = max(6, base["payback"] - d)
    applicants = 1000 + index * 37
    admit_rate = round(min(0.95, max(0.03, base["admit"] + 0.01 * d)), 4)
    admits = int(applicants * admit_rate)
    enrolled = int(admits * base["yld"])

    outcomes: list[OutcomeRecord] = []
    for p in periods:
        outcomes += [
            OutcomeRecord("salary_median", p, value_numeric=salary),
            OutcomeRecord(
                "salary_band",
                p,
                value_json={
                    "p25": int(salary * 0.8),
                    "p50": salary,
                    "p75": int(salary * 1.25),
                    "currency": "USD",
                },
            ),
            OutcomeRecord("employment_rate", p, value_numeric=emp),
            OutcomeRecord("payback_period_months", p, value_numeric=payback),
        ]
    admissions = [
        AdmissionsRecord(
            cycle_year=cy,
            applicants=applicants,
            admits=admits,
            enrolled=enrolled,
            admit_rate=admit_rate,
            yield_rate=base["yld"],
            class_profile={"gpa_p50": base["gpa"], "cohort_size": enrolled},
            selectivity_band=base["sel"],
        )
        for cy in cycles
    ]
    return outcomes, admissions
