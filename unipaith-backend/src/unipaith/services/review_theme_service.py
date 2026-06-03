"""Spec 68 §5 — review theme-summarisation over the existing review tables.

The review tables (``student_program_reviews`` / ``employer_feedback``) and the
``func.avg`` dimension roll-ups already exist; this builds only the top-of-
Insights theme block — "what students/employers consistently say" + common
tradeoffs (Business Methodology:191) — into ``review_theme_summaries``.

Deterministic by default (rule-based: rank the dimensions, ground each theme in
the reviews that drive it). The LLM / Qwen display-synth path (63 §2.5) is gated
behind ``ai_review_themes_v2_enabled`` and **falls back** to the deterministic
result on flag-off or any failure — the card never 5xxes. Source-grounded:
every theme cites the ``supporting_review_ids`` that back it.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.models.institution import EmployerFeedback, StudentProgramReview
from unipaith.models.outcomes import ReviewThemeSummary

_STUDENT_DIMS: list[tuple[str, str]] = [
    ("rating_teaching", "Teaching quality"),
    ("rating_workload", "Workload"),
    ("rating_career_support", "Career support"),
    ("rating_internship_access", "Internship access"),
    ("rating_community_culture", "Community & culture"),
    ("rating_roi", "Perceived ROI"),
]
_EMPLOYER_DIMS: list[tuple[str, str]] = [
    ("rating_technical", "Technical fundamentals"),
    ("rating_practical", "Practical skills"),
    ("rating_communication", "Communication"),
    ("rating_teamwork", "Teamwork"),
    ("rating_reliability", "Reliability"),
]
_MODEL_VERSION_RULE = "review-themes-rule-v1"


def _avg(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 3) if values else None


def _build_themes(rows: list, dims: list[tuple[str, str]]) -> tuple[list, list, dict]:
    """Deterministic, grounded themes: the top dimensions are 'what they
    consistently say'; the lowest dimension is a common tradeoff. Each theme
    cites the review ids that drive it (no theme without backing reviews)."""
    dim_stats = []
    rollup: dict[str, float | None] = {}
    for key, label in dims:
        vals = [(r.id, getattr(r, key)) for r in rows if getattr(r, key) is not None]
        a = _avg([v for _i, v in vals])
        rollup[key] = a
        if a is not None:
            dim_stats.append((key, label, a, vals))
    if rows and hasattr(rows[0], "rating_overall"):
        rollup["rating_overall"] = _avg(
            [r.rating_overall for r in rows if r.rating_overall is not None]
        )

    themes: list[dict] = []
    tradeoffs: list[dict] = []
    if dim_stats:
        ranked = sorted(dim_stats, key=lambda t: t[2], reverse=True)
        for _key, label, a, vals in ranked[:2]:
            supporting = [str(i) for i, v in vals if v >= a]
            themes.append(
                {
                    "label": label,
                    "sentiment": "positive",
                    "avg": a,
                    "n": len(supporting),
                    "supporting_review_ids": supporting,
                }
            )
        low_key, low_label, low_avg, low_vals = ranked[-1]
        if len(ranked) >= 3 and low_avg < ranked[0][2]:
            supporting = [str(i) for i, v in low_vals if v <= low_avg]
            tradeoffs.append(
                {
                    "label": low_label,
                    "sentiment": "tradeoff",
                    "avg": low_avg,
                    "n": len(supporting),
                    "supporting_review_ids": supporting,
                }
            )
    return themes, tradeoffs, rollup


class ReviewThemeService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_or_build_program_summary(
        self, program_id: UUID, audience: str = "student", *, refresh: bool = False
    ) -> ReviewThemeSummary:
        """Cached on the review count: rebuild only when reviews changed (§5)."""
        existing = await self._existing("program", program_id, audience)
        rows = await self._reviews(program_id, audience)
        n = len(rows)
        if existing is not None and not refresh and existing.n_reviews == n:
            return existing  # no review-count delta → serve the cached card

        themes, tradeoffs, rollup = _build_themes(
            rows, _STUDENT_DIMS if audience == "student" else _EMPLOYER_DIMS
        )
        model_version = _MODEL_VERSION_RULE
        # Qwen display-synth seam (63 §2.5) — flag-gated; falls back to the
        # deterministic result on flag-off or failure (never 5xx).
        if settings.ai_review_themes_v2_enabled:
            enriched = await self._maybe_llm_synthesize(rows, themes, tradeoffs)
            if enriched is not None:
                themes, tradeoffs, model_version = enriched

        if existing is None:
            existing = ReviewThemeSummary(
                target_type="program",
                target_id=program_id,
                audience=audience,
                source="system",
            )
            self.db.add(existing)
        existing.themes = themes
        existing.tradeoffs = tradeoffs
        existing.dimension_rollup = rollup
        existing.n_reviews = n
        existing.model_version = model_version
        existing.generated_at = datetime.now(UTC)
        existing.status = "live"
        existing.confidence = round(min(1.0, n / 10.0), 3)
        await self.db.flush()
        return existing

    async def _existing(
        self, target_type: str, target_id: UUID, audience: str
    ) -> ReviewThemeSummary | None:
        res = await self.db.execute(
            select(ReviewThemeSummary).where(
                ReviewThemeSummary.target_type == target_type,
                ReviewThemeSummary.target_id == target_id,
                ReviewThemeSummary.audience == audience,
            )
        )
        return res.scalar_one_or_none()

    async def _reviews(self, program_id: UUID, audience: str) -> list:
        if audience == "student":
            res = await self.db.execute(
                select(StudentProgramReview)
                .where(
                    StudentProgramReview.program_id == program_id,
                    StudentProgramReview.is_published.is_(True),
                )
                .limit(500)
            )
        else:
            res = await self.db.execute(
                select(EmployerFeedback)
                .where(
                    EmployerFeedback.program_id == program_id,
                    EmployerFeedback.is_published.is_(True),
                )
                .limit(500)
            )
        return list(res.scalars().all())

    async def _maybe_llm_synthesize(
        self, rows: list, themes: list, tradeoffs: list
    ) -> tuple[list, list, str] | None:
        """Qwen display-synth seam (63 §2.5). Not wired to a live Qwen call yet —
        returns ``None`` so the deterministic, source-grounded result stands. When
        Qwen serving lands, synthesise richer prose here grounded in ``rows`` and
        eval-gated (62); any failure must return ``None`` so we fall back."""
        return None
