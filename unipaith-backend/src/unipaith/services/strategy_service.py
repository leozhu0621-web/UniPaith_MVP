"""Phase A — Strategy service.

Owns the rule-based strategy generator + lifecycle (versioning, activate,
edit-creates-new-draft). The generator body is intentionally crude template
code — Plan 2 will replace `_rule_based_generate` with an LLM call without
changing the public method signatures or persistence semantics.

Lifecycle rules:
- generate: requires at least one active academic goal (else 400). Creates a
  new draft strategy with version = max(prior versions) + 1.
- activate: archives the previous active strategy (if any), then sets this
  strategy to status='active'. Atomic — same DB transaction.
- update: only allowed on status='draft' or 'active'. Archives the original
  (regardless of which) and creates a NEW draft with the patch applied.
  Does NOT auto-activate; user calls activate explicitly.
"""

from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.goals import StudentGoal
from unipaith.models.needs import StudentNeed
from unipaith.models.strategy import StudentStrategy
from unipaith.models.student import StudentProfile
from unipaith.schemas.strategy import UpdateStrategyRequest

# Hardcoded mapping: lowercased keyword fragments → degree label. First match
# wins. Plan 2 will replace this with an LLM-driven inference.
# Each entry: (regex word-pattern alternations, degree label). Matched with
# re.search using \b so "swe" doesn't accidentally match "sweater".
_DEGREE_KEYWORDS: list[tuple[tuple[str, ...], str]] = [
    (("doctor", "physician", "medical doctor", "medicine", "md"), "MD"),
    (("lawyer", "law school", "attorney", "juris doctor"), "JD"),
    (("mba", "business school", "management consulting"), "MBA"),
    (("phd", "research scientist", "academia", "professor"), "PhD"),
    (
        ("data scientist", "ml", "machine learning", "ai engineer"),
        "Master's in CS / Data Science",
    ),
    (("software engineer", "swe", "developer"), "BS / MS in Computer Science"),
    (("nurse", "nursing"), "BSN / MSN"),
    (("teacher", "education"), "MEd / Teaching credential"),
    (("public health",), "MPH"),
    (("social work",), "MSW"),
]

_NARRATIVE_TEMPLATE = """\
Based on what you've shared, your most active academic goal is: {career_target}

The most likely degree path: **{target_degree}**.

Academic path. We've laid out three concrete steps below — identify program \
type, build profile depth, and structure your application across reach / \
target / safety tiers. The exact options will sharpen as you complete more \
of Discovery.

Financial path. Most students at this stage qualify for some combination of \
need-based, merit-based, and departmental funding (assistantships, \
scholarships). The eligibility specifics depend on programs you target.

Geographic path. {geographic_summary}

Note: this is a template-generated preview. The full LLM-written strategy \
will replace this once Plan 2 is wired.
"""


class StrategyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _student_id(self, user_id: UUID) -> UUID:
        result = await self.db.execute(
            select(StudentProfile.id).where(StudentProfile.user_id == user_id)
        )
        sid = result.scalar_one_or_none()
        if sid is None:
            raise NotFoundException("Student profile not found")
        return sid

    async def _get_strategy(self, strategy_id: UUID, student_id: UUID) -> StudentStrategy:
        result = await self.db.execute(
            select(StudentStrategy).where(
                StudentStrategy.id == strategy_id,
                StudentStrategy.student_id == student_id,
            )
        )
        strategy = result.scalar_one_or_none()
        if strategy is None:
            raise NotFoundException("Strategy not found")
        return strategy

    async def _next_version(self, student_id: UUID) -> int:
        """Per-student monotonic version. Compute as max+1 in the same
        transaction. Concurrent generation by the same student is unlikely in
        practice and would just collide on the unique (student_id, version)
        constraint with a clear IntegrityError."""
        result = await self.db.execute(
            select(StudentStrategy.version)
            .where(StudentStrategy.student_id == student_id)
            .order_by(StudentStrategy.version.desc())
            .limit(1)
        )
        latest = result.scalar_one_or_none()
        return (latest or 0) + 1

    @staticmethod
    def _map_career_to_degree(career_target: str) -> str:
        haystack = career_target.lower()
        for needles, degree in _DEGREE_KEYWORDS:
            pattern = r"\b(" + "|".join(re.escape(n) for n in needles) + r")\b"
            if re.search(pattern, haystack):
                return degree
        return "TBD"

    async def _rule_based_generate(
        self, student_id: UUID
    ) -> tuple[str, str, list[dict], list[dict], list[dict], str, list[UUID]]:
        """Returns (career_target, target_degree, academic_path,
        financial_path, geographic_path, narrative, source_session_ids)."""
        # Pull the most recent active academic goal — that's the anchor.
        result = await self.db.execute(
            select(StudentGoal)
            .where(
                StudentGoal.student_id == student_id,
                StudentGoal.status == "active",
                StudentGoal.category == "academic",
            )
            .order_by(StudentGoal.created_at.desc())
        )
        academic_goals = list(result.scalars().all())
        if not academic_goals:
            raise BadRequestException(
                "Cannot generate strategy without at least one active academic goal."
            )

        anchor = academic_goals[0]
        career_target = anchor.specific.strip()[:500]
        target_degree = self._map_career_to_degree(career_target)

        # Pull active social-tier needs for geographic context.
        result = await self.db.execute(
            select(StudentNeed).where(
                StudentNeed.student_id == student_id,
                StudentNeed.maslow_level == "social",
            )
        )
        social_needs = list(result.scalars().all())

        academic_path: list[dict] = [
            {
                "step": "Identify program type",
                "options": [target_degree] if target_degree != "TBD" else [],
                "rationale": "Anchored to your stated career target.",
            },
            {
                "step": "Build profile depth",
                "options": ["Research labs", "Industry internships", "Capstone projects"],
                "rationale": "Common preparation paths admissions committees look for.",
            },
            {
                "step": "Application strategy",
                "options": ["Reach", "Target", "Safety"],
                "rationale": "Spread risk across tiers.",
            },
        ]

        financial_path: list[dict] = [
            {
                "aid_type": "Need-based aid",
                "eligibility": "Family income relative to program's published ranges.",
                "estimated_value": None,
            },
            {
                "aid_type": "Merit-based scholarships",
                "eligibility": "GPA + standardized test scores at or above program medians.",
                "estimated_value": None,
            },
            {
                "aid_type": "Departmental funding",
                "eligibility": "Research / teaching assistantships; competitive at PhD tier.",
                "estimated_value": None,
            },
        ]

        # Geographic items: one per active social need that mentions a region
        # signal, plus a generic catchall if nothing structured exists.
        geographic_path: list[dict] = []
        for need in social_needs:
            geographic_path.append(
                {
                    "region": need.need_type[:200],
                    "rationale": need.signal[:1000],
                    "constraints": [need.severity],
                }
            )
        if not geographic_path:
            geographic_path.append(
                {
                    "region": "Open",
                    "rationale": (
                        "No geographic preference signal yet — Discovery's "
                        "needs track will sharpen this."
                    ),
                    "constraints": [],
                }
            )

        geographic_summary = (
            f"{len(geographic_path)} region signal(s) collected so far"
            if social_needs
            else (
                "No region preference yet — flesh out Discovery's Needs "
                "track to sharpen this section."
            )
        )
        narrative = _NARRATIVE_TEMPLATE.format(
            career_target=career_target,
            target_degree=target_degree,
            geographic_summary=geographic_summary,
        )

        # Session-id provenance — pull distinct source_session_ids from the
        # goals + needs we used to generate.
        session_ids: set[UUID] = set()
        if anchor.source_session_id is not None:
            session_ids.add(anchor.source_session_id)
        for n in social_needs:
            if n.source_session_id is not None:
                session_ids.add(n.source_session_id)

        return (
            career_target,
            target_degree,
            academic_path,
            financial_path,
            geographic_path,
            narrative,
            sorted(session_ids),
        )

    async def generate(self, user_id: UUID) -> StudentStrategy:
        student_id = await self._student_id(user_id)
        (
            career_target,
            target_degree,
            academic_path,
            financial_path,
            geographic_path,
            narrative,
            session_ids,
        ) = await self._rule_based_generate(student_id)

        version = await self._next_version(student_id)
        strategy = StudentStrategy(
            student_id=student_id,
            version=version,
            status="draft",
            career_target=career_target,
            target_degree=target_degree,
            academic_path=academic_path,
            financial_path=financial_path,
            geographic_path=geographic_path,
            narrative=narrative,
            generated_from_session_ids=session_ids,
            is_stub=True,
        )
        self.db.add(strategy)
        await self.db.flush()
        await self.db.refresh(strategy)
        return strategy

    async def get_active(self, user_id: UUID) -> StudentStrategy | None:
        student_id = await self._student_id(user_id)
        result = await self.db.execute(
            select(StudentStrategy).where(
                StudentStrategy.student_id == student_id,
                StudentStrategy.status == "active",
            )
        )
        return result.scalar_one_or_none()

    async def list_versions(self, user_id: UUID) -> list[StudentStrategy]:
        student_id = await self._student_id(user_id)
        result = await self.db.execute(
            select(StudentStrategy)
            .where(StudentStrategy.student_id == student_id)
            .order_by(StudentStrategy.version.desc())
        )
        return list(result.scalars().all())

    async def get_strategy(self, user_id: UUID, strategy_id: UUID) -> StudentStrategy:
        student_id = await self._student_id(user_id)
        return await self._get_strategy(strategy_id, student_id)

    async def _refresh_profile_strategy_active(self, student_id: UUID) -> None:
        """Recompute student_profiles.strategy_active_id from the current
        active row (or NULL if none). Called after every status mutation so
        the home page can read the active strategy id without joining."""
        result = await self.db.execute(
            select(StudentStrategy.id).where(
                StudentStrategy.student_id == student_id,
                StudentStrategy.status == "active",
            )
        )
        active_id = result.scalar_one_or_none()
        await self.db.execute(
            update(StudentProfile)
            .where(StudentProfile.id == student_id)
            .values(strategy_active_id=active_id)
        )
        await self.db.flush()

    async def activate(self, user_id: UUID, strategy_id: UUID) -> StudentStrategy:
        """Archive previous active (if any), set this to active. Same
        transaction so the partial unique index never sees two active rows."""
        student_id = await self._student_id(user_id)
        target = await self._get_strategy(strategy_id, student_id)
        if target.status == "archived":
            raise BadRequestException(
                "Cannot activate an archived strategy; create a new version instead."
            )
        if target.status == "active":
            return target  # idempotent

        # Archive the existing active row first (separate flush) so the
        # partial unique index never sees two active rows. SQLAlchemy
        # otherwise batches both UPDATEs in PK order, which can fire the
        # new-active write before the archive lands and trip the constraint.
        result = await self.db.execute(
            select(StudentStrategy).where(
                StudentStrategy.student_id == student_id,
                StudentStrategy.status == "active",
            )
        )
        prev_active = result.scalar_one_or_none()
        if prev_active is not None:
            prev_active.status = "archived"
            await self.db.flush()

        target.status = "active"
        await self.db.flush()
        await self.db.refresh(target)

        # Refresh the profile-summary pointer so the home page reads the
        # active strategy id without joining.
        await self._refresh_profile_strategy_active(student_id)
        return target

    async def update(
        self, user_id: UUID, strategy_id: UUID, body: UpdateStrategyRequest
    ) -> StudentStrategy:
        """Manual edit = clone-and-modify. Archives the original (must be
        draft or active) and creates a new draft with the patch applied."""
        student_id = await self._student_id(user_id)
        original = await self._get_strategy(strategy_id, student_id)
        if original.status == "archived":
            raise BadRequestException(
                "Cannot edit an archived strategy. Activate or generate a new one first."
            )

        patch = body.model_dump(exclude_unset=True, mode="json")

        # Inherit values from the original; overlay the patch. JSONB list
        # fields: explicit `[]` clears, omitted preserves.
        merged = {
            "career_target": original.career_target,
            "target_degree": original.target_degree,
            "academic_path": original.academic_path,
            "financial_path": original.financial_path,
            "geographic_path": original.geographic_path,
            "narrative": original.narrative,
        }
        merged.update(patch)

        # Archive the original — service-driven, so we don't trip the partial
        # unique index when the new row is also created as a draft.
        original.status = "archived"

        version = await self._next_version(student_id)
        new_draft = StudentStrategy(
            student_id=student_id,
            version=version,
            status="draft",
            career_target=merged["career_target"],
            target_degree=merged["target_degree"],
            academic_path=merged["academic_path"],
            financial_path=merged["financial_path"],
            geographic_path=merged["geographic_path"],
            narrative=merged["narrative"],
            generated_from_session_ids=list(original.generated_from_session_ids or []),
            is_stub=original.is_stub,
        )
        self.db.add(new_draft)
        await self.db.flush()
        await self.db.refresh(new_draft)

        # If the original was the active strategy, archiving it leaves the
        # student with no active strategy — refresh the pointer so the home
        # page reflects "no active" until the user explicitly activates the
        # new draft.
        await self._refresh_profile_strategy_active(student_id)
        return new_draft
