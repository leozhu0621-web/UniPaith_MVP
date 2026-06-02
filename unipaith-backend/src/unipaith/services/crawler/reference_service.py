"""Spec 60 §4 / §12 — read the reference projection, provenance-first.

Every row returned carries its provenance envelope (source + url + domain +
confidence + freshness), so the consuming surface can render "sourced from
<domain> · updated N days ago" (§4) and mark a fact provisional until it's
confidence-gated or institution-confirmed. Public, read-only; only ``live`` /
``provisional`` rows surface (review / superseded / archived stay internal).
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.reference import (
    RefAccreditation,
    RefGeoCost,
    RefMajor,
    RefOccupation,
    RefRanking,
    RefTest,
    RefVisa,
    Scholarship,
)

_PUBLIC_STATUSES = ("live", "provisional")


def _days_ago(when: datetime | None) -> int | None:
    if when is None:
        return None
    now = datetime.now(UTC)
    ref = when if when.tzinfo else when.replace(tzinfo=UTC)
    return max(0, (now - ref).days)


def provenance(row) -> dict:
    """The §4 provenance block attached to every reference fact."""
    fetched = getattr(row, "fetched_at", None) or getattr(row, "updated_at", None)
    return {
        "source": getattr(row, "source", None),
        "source_url": getattr(row, "source_url", None),
        "source_domain": getattr(row, "source_domain", None),
        "confidence": getattr(row, "confidence", None),
        "status": getattr(row, "status", None),
        "updated_days_ago": _days_ago(fetched),
        "provisional": getattr(row, "status", None) == "provisional",
    }


class ReferenceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _fetch(self, model, *conds, order=None, limit: int = 100) -> list:
        stmt = select(model).where(model.status.in_(_PUBLIC_STATUSES))
        for c in conds:
            stmt = stmt.where(c)
        if order is not None:
            stmt = stmt.order_by(order)
        stmt = stmt.limit(limit)
        return list((await self.db.execute(stmt)).scalars().all())

    async def occupations(self, q: str | None = None, limit: int = 100) -> list[dict]:
        conds = [RefOccupation.title.ilike(f"%{q}%")] if q else []
        rows = await self._fetch(RefOccupation, *conds, order=RefOccupation.title, limit=limit)
        return [
            {
                "soc_code": r.soc_code,
                "title": r.title,
                "description": r.description,
                "median_salary": float(r.median_salary) if r.median_salary is not None else None,
                "salary_currency": r.salary_currency,
                "projected_growth_pct": r.projected_growth_pct,
                "outlook": r.outlook,
                "education_typical": r.education_typical,
                "related_majors": r.related_majors,
                "provenance": provenance(r),
            }
            for r in rows
        ]

    async def tests(self, limit: int = 100) -> list[dict]:
        rows = await self._fetch(RefTest, order=RefTest.name, limit=limit)
        return [
            {
                "code": r.code,
                "name": r.name,
                "category": r.category,
                "sections": r.sections,
                "score_min": r.score_min,
                "score_max": r.score_max,
                "validity_years": r.validity_years,
                "superscore_allowed": r.superscore_allowed,
                "provenance": provenance(r),
            }
            for r in rows
        ]

    async def visas(self, country: str | None = None, limit: int = 100) -> list[dict]:
        conds = [RefVisa.country.ilike(f"%{country}%")] if country else []
        rows = await self._fetch(RefVisa, *conds, order=RefVisa.country, limit=limit)
        return [
            {
                "country": r.country,
                "code": r.code,
                "name": r.name,
                "requirements": r.requirements,
                "work_rights": r.work_rights,
                "duration": r.duration,
                "financial_proof_required": r.financial_proof_required,
                "provenance": provenance(r),
            }
            for r in rows
        ]

    async def geo_cost(self, country: str | None = None, limit: int = 100) -> list[dict]:
        conds = [RefGeoCost.country.ilike(f"%{country}%")] if country else []
        rows = await self._fetch(RefGeoCost, *conds, order=RefGeoCost.locale, limit=limit)
        return [
            {
                "locale": r.locale,
                "country": r.country,
                "cost_of_living_index": r.cost_of_living_index,
                "rent_index": r.rent_index,
                "monthly_estimate": float(r.monthly_estimate)
                if r.monthly_estimate is not None
                else None,
                "currency": r.currency,
                "provenance": provenance(r),
            }
            for r in rows
        ]

    async def majors(self, q: str | None = None, limit: int = 100) -> list[dict]:
        conds = [RefMajor.title.ilike(f"%{q}%")] if q else []
        rows = await self._fetch(RefMajor, *conds, order=RefMajor.title, limit=limit)
        return [
            {
                "cip_code": r.cip_code,
                "title": r.title,
                "description": r.description,
                "typical_curriculum": r.typical_curriculum,
                "prerequisites": r.prerequisites,
                "related_occupations": r.related_occupations,
                "provenance": provenance(r),
            }
            for r in rows
        ]

    async def rankings(self, entity: str | None = None, limit: int = 100) -> list[dict]:
        conds = [RefRanking.entity_name.ilike(f"%{entity}%")] if entity else []
        rows = await self._fetch(RefRanking, *conds, order=RefRanking.rank, limit=limit)
        return [
            {
                "ranker": r.ranker,
                "entity_name": r.entity_name,
                "entity_type": r.entity_type,
                "scope": r.scope,
                "rank": r.rank,
                "year": r.year,
                "provenance": provenance(r),
            }
            for r in rows
        ]

    async def accreditation(self, entity: str | None = None, limit: int = 100) -> list[dict]:
        conds = [RefAccreditation.entity_name.ilike(f"%{entity}%")] if entity else []
        rows = await self._fetch(
            RefAccreditation, *conds, order=RefAccreditation.entity_name, limit=limit
        )
        return [
            {
                "body": r.body,
                "body_type": r.body_type,
                "entity_name": r.entity_name,
                "accreditation_status": r.accreditation_status,
                "scope": r.scope,
                "valid_through": r.valid_through.isoformat() if r.valid_through else None,
                "provenance": provenance(r),
            }
            for r in rows
        ]

    async def scholarships(
        self, scholarship_type: str | None = None, q: str | None = None, limit: int = 100
    ) -> list[dict]:
        conds = []
        if scholarship_type:
            conds.append(Scholarship.scholarship_type == scholarship_type)
        if q:
            conds.append(Scholarship.name.ilike(f"%{q}%"))
        rows = await self._fetch(Scholarship, *conds, order=Scholarship.name, limit=limit)
        return [
            {
                "name": r.name,
                "slug": r.slug,
                "scholarship_type": r.scholarship_type,
                "sponsor": r.sponsor,
                "amount_min": float(r.amount_min) if r.amount_min is not None else None,
                "amount_max": float(r.amount_max) if r.amount_max is not None else None,
                "currency": r.currency,
                "is_renewable": r.is_renewable,
                "eligibility": r.eligibility,
                "deadline": r.deadline.isoformat() if r.deadline else None,
                "application_url": r.application_url,
                "provenance": provenance(r),
            }
            for r in rows
        ]

    async def summary(self) -> dict:
        """Live per-domain counts (live + provisional) for the transparency page."""
        out: dict[str, int] = {}
        for key, model in (
            ("occupations", RefOccupation),
            ("tests", RefTest),
            ("visas", RefVisa),
            ("geo_cost", RefGeoCost),
            ("majors", RefMajor),
            ("rankings", RefRanking),
            ("accreditation", RefAccreditation),
            ("scholarships", Scholarship),
        ):
            n = await self.db.execute(
                select(func.count()).select_from(model).where(model.status.in_(_PUBLIC_STATUSES))
            )
            out[key] = int(n.scalar_one() or 0)
        out["total"] = sum(out.values())
        return out
