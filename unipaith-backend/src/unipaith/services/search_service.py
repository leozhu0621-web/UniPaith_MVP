"""Spec 10 — Discovery type-first program search service.

Two responsibilities:
  - `interpret()` — turn a free-text query into structured constraint chips,
    via the DiscoveryQueryInterpreter LLM agent (behind the
    `ai_discovery_query_v2_enabled` flag) with a deterministic rule-based
    fallback (`services/query_parser.py`). Never raises for a normal query.
  - `search()` — translate chips + panel filters + sort into kwargs for the
    proven FTS engine (`InstitutionService.search_programs`) and return
    programs-only results.

The chip → kwargs translation is the heart of this module: each constraint
category maps onto the (additive) filter params on `search_programs`.
"""

from __future__ import annotations

import logging
import math
import re

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.query_interpreter import get_query_interpreter
from unipaith.config import settings
from unipaith.schemas.search import (
    ConstraintCategory,
    ConstraintChip,
    FilterState,
    InterpretResponse,
    SearchRequest,
    SearchResponse,
    SortOption,
)
from unipaith.services.institution_service import InstitutionService
from unipaith.services.query_parser import interpretation_text, parse_query

logger = logging.getLogger(__name__)

# Cap rows fetched for the in-Python fitness/confidence re-sort (match-based
# ordering isn't expressible in the FTS query). Beyond this the ordering is
# best-effort over the first N relevance-ranked programs.
_MATCH_SORT_CAP = 200

# Constraint value → DB-token sets. A single chip can match several DB
# synonyms (e.g. format "in_person" should also catch "on_campus").
_DEGREE_MAP: dict[str, list[str]] = {
    "bachelor": ["bachelors"],
    "bachelors": ["bachelors"],
    "bachelor's": ["bachelors"],
    "bs": ["bachelors"],
    "ba": ["bachelors"],
    "undergraduate": ["bachelors"],
    "undergrad": ["bachelors"],
    "master": ["masters"],
    "masters": ["masters"],
    "master's": ["masters"],
    "ms": ["masters"],
    "ma": ["masters"],
    "mba": ["masters"],
    "meng": ["masters"],
    "graduate": ["masters"],
    "doctorate": ["phd", "doctorate"],
    "doctoral": ["phd", "doctorate"],
    "phd": ["phd", "doctorate"],
    "doctor": ["phd", "doctorate"],
    "certificate": ["certificate"],
    "cert": ["certificate"],
    "associate": ["associate"],
    "associates": ["associate"],
    "associate's": ["associate"],
    "professional": ["professional"],
}
_FORMAT_MAP: dict[str, list[str]] = {
    "in_person": ["in_person", "on_campus"],
    "on_campus": ["on_campus", "in_person"],
    "on-campus": ["on_campus", "in_person"],
    "in-person": ["in_person", "on_campus"],
    "campus": ["on_campus", "in_person"],
    "online": ["online"],
    "remote": ["online"],
    "distance": ["online"],
    "hybrid": ["hybrid"],
    "blended": ["hybrid"],
}
# Selectivity band → (min_acceptance_rate, max_acceptance_rate), 0..1.
# Low selectivity == high acceptance rate.
_SELECTIVITY_BANDS: dict[str, tuple[float | None, float | None]] = {
    "low": (0.6, None),
    "medium": (0.3, 0.6),
    "high": (0.1, 0.3),
    "very_high": (None, 0.1),
}

_SORT_MAP: dict[SortOption, str] = {
    SortOption.relevance: "relevance",
    SortOption.tuition_asc: "tuition_asc",
    SortOption.tuition_desc: "tuition_desc",
    SortOption.acceptance_asc: "acceptance_asc",
    SortOption.acceptance_desc: "acceptance_desc",
    SortOption.deadline: "deadline",
    SortOption.recently_added: "recently_added",
}


def _parse_range(value: str) -> tuple[int | None, int | None]:
    """Parse a numeric constraint value into (min, max). Handles `<=N`, `>=N`,
    `N-M`, `<N`, `>N`, and a bare `N` (treated as a ceiling)."""
    v = re.sub(r"[,$\s]", "", value or "")
    if m := re.match(r"^<=?(\d+)$", v):
        return (None, int(m.group(1)))
    if m := re.match(r"^>=?(\d+)$", v):
        return (int(m.group(1)), None)
    if m := re.match(r"^(\d+)[-–](\d+)$", v):
        a, b = int(m.group(1)), int(m.group(2))
        return (min(a, b), max(a, b))
    if m := re.match(r"^(\d+)$", v):
        return (None, int(m.group(1)))
    return (None, None)


def _extract_year(value: str) -> int | None:
    m = re.search(r"(20\d{2})", value or "")
    return int(m.group(1)) if m else None


def _chips_to_kwargs(chips: list[ConstraintChip]) -> dict:
    """Translate constraint chips into `search_programs` filter kwargs."""
    kwargs: dict = {}
    degree_types: list[str] = []
    delivery_formats: list[str] = []
    for c in chips:
        val = (c.value or "").strip()
        low = val.lower()
        if not val:
            continue
        if c.category == ConstraintCategory.degree_level:
            degree_types += _DEGREE_MAP.get(low, [low])
        elif c.category == ConstraintCategory.format:
            delivery_formats += _FORMAT_MAP.get(low, [low])
        elif c.category == ConstraintCategory.location:
            kwargs["location"] = val
        elif c.category == ConstraintCategory.budget:
            lo, hi = _parse_range(low)
            if lo is not None:
                kwargs["min_tuition"] = lo
            if hi is not None:
                kwargs["max_tuition"] = hi
        elif c.category == ConstraintCategory.duration:
            lo, hi = _parse_range(low)
            if lo is not None:
                kwargs["min_duration_months"] = lo
            if hi is not None:
                kwargs["max_duration_months"] = hi
        elif c.category == ConstraintCategory.selectivity:
            band = _SELECTIVITY_BANDS.get(low)
            if band:
                mn, mx = band
                if mn is not None:
                    kwargs["min_acceptance_rate"] = mn
                if mx is not None:
                    kwargs["max_acceptance_rate"] = mx
        elif c.category == ConstraintCategory.start_term:
            yr = _extract_year(val)
            if yr:
                kwargs["start_year"] = yr
        # major / other → free-text FTS, handled in _build_fts_query
    if degree_types:
        kwargs["degree_types"] = list(dict.fromkeys(degree_types))
    if delivery_formats:
        kwargs["delivery_formats"] = list(dict.fromkeys(delivery_formats))
    return kwargs


def _build_fts_query(chips: list[ConstraintChip], raw_query: str | None) -> str | None:
    """The FTS `q` is built from major/other chips. If there are chips but none
    are free-text, `q` is None (filters fully drive the search — passing the
    raw sentence would wrongly narrow results). With no chips at all, the raw
    query is used directly."""
    terms = [
        c.value for c in chips if c.category in (ConstraintCategory.major, ConstraintCategory.other)
    ]
    if terms:
        return " ".join(terms)
    if not chips:
        return (raw_query or "").strip() or None
    return None


def _merge_filters(kwargs: dict, filters: FilterState | None) -> None:
    """Overlay explicit panel filters; they win on conflict with chip-derived
    values (the panel is the precise control)."""
    if filters is None:
        return
    for fld in (
        "campus_setting",
        "program_name",
        "country",
        "region",
        "city",
        "min_tuition",
        "max_tuition",
        "min_duration_months",
        "max_duration_months",
        "min_acceptance_rate",
        "max_acceptance_rate",
        "start_year",
        "min_median_salary",
        "min_employment_rate",
        "max_payback_months",
    ):
        v = getattr(filters, fld, None)
        if v is not None:
            kwargs[fld] = v
    if filters.degree_types:
        kwargs["degree_types"] = filters.degree_types
    if filters.delivery_formats:
        kwargs["delivery_formats"] = filters.delivery_formats


class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def interpret(
        self,
        query: str,
        *,
        student_id=None,
        profile_summary: str = "",
    ) -> InterpretResponse:
        """NL query → constraint chips. LLM agent behind the flag; deterministic
        rule-based parser as the flag-off default AND the failure fallback."""
        if settings.ai_discovery_query_v2_enabled:
            try:
                result = await get_query_interpreter().interpret(
                    query=query,
                    profile_summary=profile_summary,
                    student_id=student_id,
                    db=self.db,
                )
                return InterpretResponse(
                    chips=result.chips,
                    interpretation=interpretation_text(result.chips),
                    degraded=False,
                )
            except Exception as exc:  # consent / provider / parse — never 5xx
                logger.warning(
                    "query_interpreter failed; falling back to rule-based parser: %s",
                    exc,
                )
                chips = parse_query(query)
                return InterpretResponse(
                    chips=chips, interpretation=interpretation_text(chips), degraded=True
                )
        chips = parse_query(query)
        return InterpretResponse(
            chips=chips, interpretation=interpretation_text(chips), degraded=False
        )

    async def search(
        self,
        req: SearchRequest,
        *,
        student_profile_id=None,
    ) -> SearchResponse:
        kwargs = _chips_to_kwargs(req.chips)
        _merge_filters(kwargs, req.filters)
        q = _build_fts_query(req.chips, req.query)
        inst_svc = InstitutionService(self.db)

        if req.sort in (SortOption.fitness, SortOption.confidence) and student_profile_id:
            match_map = await self._match_map(student_profile_id)
            if match_map:
                wide = await inst_svc.search_programs(
                    query=q, sort_by="relevance", page=1, page_size=_MATCH_SORT_CAP, **kwargs
                )
                idx = 1 if req.sort == SortOption.confidence else 0

                def _key(item):
                    pair = match_map.get(item.id)
                    # Matched programs first (tuple[0]=0), higher score first.
                    return (1, 0.0) if pair is None else (0, -pair[idx])

                ordered = sorted(wide.items, key=_key)
                start = (req.page - 1) * req.page_size
                page_items = ordered[start : start + req.page_size]
                return SearchResponse(
                    results=page_items,
                    total=wide.total,
                    page=req.page,
                    page_size=req.page_size,
                    total_pages=max(1, math.ceil(wide.total / req.page_size)),
                )
            # No matches available → fall through to relevance ordering.

        sort_by = _SORT_MAP.get(req.sort, "relevance")
        resp = await inst_svc.search_programs(
            query=q, sort_by=sort_by, page=req.page, page_size=req.page_size, **kwargs
        )
        return SearchResponse(
            results=resp.items,
            total=resp.total,
            page=resp.page,
            page_size=resp.page_size,
            total_pages=resp.total_pages,
        )

    async def _match_map(self, student_profile_id) -> dict:
        """Best-effort {program_id: (fitness, confidence)} for match-based sort.
        Gated on matching consent inside MatchService; any failure → empty (the
        search degrades to relevance ordering)."""
        try:
            from unipaith.services.match_service import MatchService

            rows = await MatchService(self.db).list_matches(
                student_profile_id, limit=_MATCH_SORT_CAP
            )
            return {r.program_id: (float(r.fitness), float(r.confidence)) for r in rows}
        except Exception:
            return {}
