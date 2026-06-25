"""Scholarship service — Spec 2026-06-14 (Resources › Financial).

Read-only search + a "for your level" matches list over the external
CareerOneStop catalog (``models/scholarship.py::Scholarship``, table
``external_scholarships``). A simple ``ilike`` is enough at 9.5k rows — no
trigram/GIN index needed (spec §Slice 2).

``matches_for_student`` derives the student's coarse study level from real
profile signals (active strategy target degree → preference target level →
academic records) and filters ``level_of_study ILIKE %level%``. If no level is
derivable it falls back to a general first page — never a fabricated match
(spec §Slice 2).
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.scholarship import Scholarship
from unipaith.models.strategy import StudentStrategy
from unipaith.models.student import AcademicRecord, StudentPreference, StudentProfile

logger = logging.getLogger(__name__)

# Coarse level → the substring CareerOneStop uses in ``level_of_study``
# (e.g. "Bachelor's Degree Graduate Degree High School"). Keyed terms are
# matched against the student's free-text degree signal, longest first so
# "high school" wins before "school" etc.
_LEVEL_RULES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("high school", "secondary", "highschool"), "High School"),
    (("phd", "ph.d", "doctora", "doctoral", "master", "graduate", "msc", "m.s", "mba"), "Graduate"),
    (("associate", "associate's", "two-year", "community college"), "Associate"),
    (("bachelor", "undergrad", "bs", "ba", "b.s", "b.a", "four-year"), "Bachelor"),
    (("vocational", "trade", "certificate", "diploma"), "Vocational"),
)


def _coarse_level(raw: str | None) -> str | None:
    """Map a free-text degree string to a CareerOneStop ``level_of_study``
    substring, or ``None`` when nothing recognizable is present."""
    if not raw:
        return None
    text = raw.strip().lower()
    for terms, level in _LEVEL_RULES:
        if any(term in text for term in terms):
            return level
    return None


# Canonical field token (match.field_canon vocab) → the ILIKE terms that actually
# appear in CareerOneStop scholarship name/purpose text. Used to build a
# field-relevant "suggested for you" list so a CS student stops seeing
# hydroponics / CPAP / caregiver awards. A field absent here falls back to its
# own token words — never a fabricated keyword.
_FIELD_KEYWORDS: dict[str, list[str]] = {
    "computer_science": [
        "computer",
        "software",
        "data scien",
        "information tech",
        "cybersecur",
        "artificial intellig",
        "STEM",
        "technolog",
        "informatics",
    ],
    "data_science": ["data scien", "data analyt", "statistic", "machine learning", "STEM"],
    "statistics": ["statistic", "data scien", "actuarial", "mathematic", "STEM"],
    "engineering": ["engineering", "STEM", "technolog"],
    "mathematics": ["mathematic", "STEM", "actuarial"],
    "physics": ["physics", "STEM", "astronom"],
    "chemistry": ["chemistr", "STEM"],
    "biology": ["biolog", "life scien", "STEM", "biomedical"],
    "neuroscience": ["neuroscien", "biolog", "STEM"],
    "public_health": ["public health", "nursing", "health", "medical", "pre-med"],
    "psychology": ["psycholog", "behavioral", "mental health"],
    "economics": ["economic", "business", "finance"],
    "business": ["business", "management", "entrepreneur", "marketing", "MBA"],
    "finance": ["finance", "accounting", "business", "financ"],
    "political_science": ["political scien", "public policy", "law", "government", "international"],
    "history": ["history", "humanities"],
    "art_history": ["art history", "art", "humanities"],
    "english": ["english", "writing", "literature", "humanities", "journalism"],
}


class ScholarshipService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(
        self,
        *,
        q: str | None = None,
        level: str | None = None,
        award_type: str | None = None,
        keywords: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """Paginated search. ``q`` matches name OR organization OR purpose
        (case-insensitive); ``level`` is a ``level_of_study`` substring;
        ``award_type`` is an exact match; ``keywords`` (any-of) match
        name/purpose/organization so a field-relevant list can be built.
        Ordered by name. Returns ``{"items": [...ORM rows...], "total": int}``."""
        conditions = []
        if q:
            term = f"%{q.strip()}%"
            conditions.append(
                or_(
                    Scholarship.name.ilike(term),
                    Scholarship.organization.ilike(term),
                    Scholarship.purpose.ilike(term),
                )
            )
        if level:
            conditions.append(Scholarship.level_of_study.ilike(f"%{level.strip()}%"))
        if award_type:
            conditions.append(Scholarship.award_type == award_type)
        kw_terms = [k.strip() for k in (keywords or []) if k and k.strip()]
        if kw_terms:
            conditions.append(
                or_(
                    *[
                        col.ilike(f"%{kw}%")
                        for kw in kw_terms
                        for col in (
                            Scholarship.name,
                            Scholarship.purpose,
                            Scholarship.organization,
                        )
                    ]
                )
            )

        count_stmt = select(func.count()).select_from(Scholarship)
        list_stmt = select(Scholarship).order_by(Scholarship.name)
        for cond in conditions:
            count_stmt = count_stmt.where(cond)
            list_stmt = list_stmt.where(cond)

        total = await self.db.scalar(count_stmt) or 0
        rows = (await self.db.scalars(list_stmt.limit(limit).offset(offset))).all()
        return {"items": list(rows), "total": int(total)}

    async def matches_for_student(self, student_id: UUID, *, limit: int = 20) -> list:
        """A "suggested for you" list. Prefers scholarships relevant to the
        student's FIELD of study (so a CS student stops seeing hydroponics / CPAP
        / caregiver awards), then falls back to their coarse study level, then a
        general first page — never a fabricated match. ``student_id`` is the
        ``user_id`` of the authenticated student."""
        level = await self._derive_level(student_id)
        keywords = await self._derive_field_keywords(student_id)

        # 1. Field-relevant at the student's level (the tightest real match),
        #    then field-relevant at any level.
        if keywords:
            if level:
                result = await self.search(keywords=keywords, level=level, limit=limit)
                if result["items"]:
                    return result["items"]
            result = await self.search(keywords=keywords, limit=limit)
            if result["items"]:
                return result["items"]
        # 2. Level-only (real level, any field) before falling all the way back.
        if level:
            result = await self.search(level=level, limit=limit)
            if result["items"]:
                return result["items"]
        # 3. No derivable signal → general first page.
        return (await self.search(limit=limit))["items"]

    async def _derive_field_keywords(self, user_id: UUID) -> list[str]:
        """ILIKE keywords for the student's field of study, or [] when unknown.

        Resolves a canonical field token from the current AcademicRecord field
        or the onboarding interest track (the same vocab the matcher uses), then
        expands it to the search terms that actually appear in scholarship
        name/purpose text. Fail-soft: any miss returns [] (→ no field filter)."""
        try:
            from unipaith.services.match.field_canon import (
                canonical_field,
                interest_track_to_field,
            )

            profile_id = await self.db.scalar(
                select(StudentProfile.id).where(StudentProfile.user_id == user_id)
            )
            if profile_id is None:
                return []
            token: str | None = None
            field_text = await self.db.scalar(
                select(AcademicRecord.field_of_study)
                .where(AcademicRecord.student_id == profile_id)
                .order_by(
                    AcademicRecord.is_current.desc(), AcademicRecord.end_date.desc().nullslast()
                )
            )
            token = canonical_field(field_text)
            if token is None:
                profile = await self.db.scalar(
                    select(StudentProfile).where(StudentProfile.id == profile_id)
                )
                answers = ((profile.onboarding_state or {}).get("answers") or {}) if profile else {}
                for interest in answers.get("interests") or []:
                    token = interest_track_to_field(interest)
                    if token:
                        break
            if token is None:
                return []
            return _FIELD_KEYWORDS.get(token, [token.replace("_", " ")])
        except Exception:  # pragma: no cover — degraded path → no field filter
            return []

    async def _derive_level(self, user_id: UUID) -> str | None:
        """Coarse study level from (in priority): active strategy target degree
        → preference target level → most recent academic record degree type."""
        profile_id = await self.db.scalar(
            select(StudentProfile.id).where(StudentProfile.user_id == user_id)
        )
        if profile_id is None:
            return None

        # 1. Active strategy's target degree (the strongest forward signal).
        target_degree = await self.db.scalar(
            select(StudentStrategy.target_degree)
            .where(
                StudentStrategy.student_id == profile_id,
                StudentStrategy.status == "active",
            )
            .order_by(StudentStrategy.version.desc())
        )
        level = _coarse_level(target_degree)
        if level:
            return level

        # 2. Stated preference target level.
        pref_level = await self.db.scalar(
            select(StudentPreference.target_degree_level).where(
                StudentPreference.student_id == profile_id
            )
        )
        level = _coarse_level(pref_level)
        if level:
            return level

        # 3. Current (else most recent) academic record degree type.
        degree_type = await self.db.scalar(
            select(AcademicRecord.degree_type)
            .where(AcademicRecord.student_id == profile_id)
            .order_by(AcademicRecord.is_current.desc(), AcademicRecord.end_date.desc().nullslast())
        )
        return _coarse_level(degree_type)
