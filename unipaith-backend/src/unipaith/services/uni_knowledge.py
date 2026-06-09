"""Uni knowledge grounding — retrieve real programs (+ scholarships) relevant to
the student's emerging profile so the orchestrator can reference our catalog
our-knowledge-first. Deterministic; reuses InstitutionService.search_programs.

Counselor-paced: returns an empty bundle until the student has captured a real
interest (a goal). Never raises to the caller — on any failure the bundle is
empty and Uni simply counsels generally (the ungrounded fallback).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.state import StudentSnapshot


@dataclass
class ProgramFact:
    program_id: str
    name: str
    school: str | None = None
    degree_type: str | None = None
    tuition: int | None = None
    acceptance_rate: float | None = None
    median_salary: int | None = None


@dataclass
class ReferenceFact:
    kind: str
    label: str
    detail: str


@dataclass
class ProgramQuery:
    query: str
    location: str | None = None


@dataclass
class KnowledgeBundle:
    programs: list[ProgramFact] = field(default_factory=list)
    references: list[ReferenceFact] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not self.programs and not self.references

    def render(self) -> str:
        if self.is_empty():
            return ""
        lines = [
            "## From your knowledge base (real options — prefer these when "
            "naming specific schools/programs/costs)"
        ]
        for p in self.programs:
            bits = [p.name]
            if p.school:
                bits.append(f"at {p.school}")
            if p.tuition is not None:
                bits.append(f"~${p.tuition:,}/yr tuition")
            if p.median_salary:
                bits.append(f"${p.median_salary:,} median salary")
            if p.acceptance_rate is not None:
                bits.append(f"{round(p.acceptance_rate * 100)}% admit")
            lines.append("- " + " · ".join(bits))
        for r in self.references:
            lines.append(f"- {r.label}: {r.detail}")
        return "\n".join(lines)


# Discovery captures ISO-3166 location codes (e.g. "US-MA", "CA-ON", "GB"), but
# search_programs filters on human-readable institution country/region/city. Map
# the country lead to its name so the filter narrows instead of silently zeroing
# the grounded catalog; drop an untranslatable code rather than over-filter.
_ISO_COUNTRY_NAMES = {
    "US": "United States",
    "GB": "United Kingdom",
    "UK": "United Kingdom",
    "CA": "Canada",
}
_ISO_CODE_RE = re.compile(r"^[A-Za-z]{2}(?:-[A-Za-z0-9]{1,3})?$")


def _normalize_location(pref: str | None) -> str | None:
    if not (pref and pref.strip()):
        return None
    pref = pref.strip()
    if _ISO_CODE_RE.match(pref):
        return _ISO_COUNTRY_NAMES.get(pref.split("-", 1)[0].upper())
    return pref


def build_query(snapshot: StudentSnapshot) -> ProgramQuery | None:
    """Counselor-paced gate: only build a query once a real interest (goal) exists."""
    interests = [g.specific.strip() for g in snapshot.goals if (g.specific or "").strip()]
    if not interests:
        return None
    location = _normalize_location(snapshot.location_prefs[0]) if snapshot.location_prefs else None
    return ProgramQuery(query=" ".join(interests[:3]), location=location)


async def _scholarship_facts(snapshot: StudentSnapshot, db: AsyncSession) -> list[ReferenceFact]:
    """Best-effort: a couple of scholarships when the table has rows. Silent otherwise."""
    try:
        from sqlalchemy import select

        from unipaith.models.reference import Scholarship

        rows = (
            await db.execute(
                select(Scholarship)
                .where(Scholarship.status.notin_(("superseded", "archived")))
                .limit(2)
            )
        ).scalars().all()
        out: list[ReferenceFact] = []
        for s in rows:
            amt = f"up to ${int(s.amount_max):,}" if s.amount_max else "varies"
            out.append(
                ReferenceFact(
                    kind="scholarship",
                    label=s.name,
                    detail=f"{s.scholarship_type}, {amt}",
                )
            )
        return out
    except Exception:
        return []


class UniKnowledgeRetriever:
    """Snapshot → a small, cited KnowledgeBundle. Never raises to the caller."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def retrieve(self, snapshot: StudentSnapshot, *, limit: int = 4) -> KnowledgeBundle:
        q = build_query(snapshot)
        if q is None:
            return KnowledgeBundle()
        programs: list[ProgramFact] = []
        try:
            from unipaith.services.institution_service import InstitutionService

            page = await InstitutionService(self.db).search_programs(
                query=q.query, location=q.location, page_size=limit
            )
            for p in page.items[:limit]:
                programs.append(
                    ProgramFact(
                        program_id=str(p.id),
                        name=p.program_name,
                        school=p.institution_name,
                        degree_type=p.degree_type,
                        tuition=p.tuition,
                        acceptance_rate=p.acceptance_rate,
                        median_salary=p.median_salary,
                    )
                )
        except Exception:
            programs = []
        refs = await _scholarship_facts(snapshot, self.db)
        return KnowledgeBundle(programs=programs, references=refs)
