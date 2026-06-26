"""
Saved-list service — manage a student's saved/bookmarked programs and
provide program comparison (Spec 13).
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.core.exceptions import BadRequestException, ConflictException, NotFoundException
from unipaith.models.application import Application
from unipaith.models.engagement import SavedList, SavedListItem
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentPreference
from unipaith.schemas.saved_list import SavedProgramCard, SavedProgramResponse, SavedStatus
from unipaith.services.application_service import ApplicationService
from unipaith.services.match_banding import band_for_acceptance

logger = logging.getLogger(__name__)

VALID_PRIORITIES = frozenset({"considering", "planning_to_apply", "applied", "dropped"})
VALID_STATUSES = frozenset(
    {
        "considering",
        "application_started",
        "submitted",
        "accepted",
        "rejected",
        "waitlisted",
        "dropped",
    }
)

_APP_TO_SAVED_STATUS: dict[str, SavedStatus] = {
    "draft": "application_started",
    "submitted": "submitted",
    "under_review": "submitted",
    "interview": "submitted",
    "decision_made": "submitted",
    "accepted": "accepted",
    "rejected": "rejected",
    "waitlisted": "waitlisted",
    "withdrawn": "dropped",
}


def _status_from_application(app) -> SavedStatus | None:
    if app is None:
        return None
    status = app.status
    if status == "decision_made":
        # The real admit / reject / waitlist outcome lives on decision /
        # student_decision, not on status (which stays "decision_made") — so the
        # status-only map collapsed every outcome to "submitted".
        decision = (app.decision or "").strip().lower()
        student_decision = (app.student_decision or "").strip().lower()
        if "accept" in student_decision or decision in (
            "admitted",
            "accepted",
            "conditional_admission",
        ):
            return "accepted"
        if decision in ("rejected", "denied"):
            return "rejected"
        if decision in ("waitlisted", "waitlist"):
            return "waitlisted"
        return "submitted"
    return _APP_TO_SAVED_STATUS.get(status)


def _program_card(prog: Program, inst: Institution | None) -> SavedProgramCard:
    outcomes = prog.outcomes_data or {}
    salary = next(
        (
            outcomes[k]
            for k in ("median_salary", "earnings_4yr_median", "earnings_1yr_median")
            if isinstance(outcomes.get(k), (int, float))
        ),
        None,
    )
    employment = outcomes.get("employment_rate")
    employment = float(employment) if isinstance(employment, (int, float)) else None
    acceptance = float(prog.acceptance_rate) if prog.acceptance_rate is not None else None
    return SavedProgramCard(
        id=prog.id,
        institution_id=prog.institution_id,
        program_name=prog.program_name,
        degree_type=prog.degree_type,
        department=prog.department,
        tuition=prog.tuition,
        duration_months=prog.duration_months,
        delivery_format=prog.delivery_format,
        acceptance_rate=acceptance,
        application_deadline=prog.application_deadline,
        institution_name=inst.name if inst else None,
        institution_country=inst.country if inst else None,
        institution_city=inst.city if inst else None,
        median_salary=int(salary) if salary is not None else None,
        employment_rate=employment,
        description_text=prog.description_text,
    )


class SavedListService:
    """CRUD for saved-program lists plus comparison."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_or_create_default_list(self, student_id: UUID) -> SavedList:
        # A student may end up with more than one list (legacy data, a create
        # race). Treat the oldest as the canonical default and take it
        # deterministically — scalar_one_or_none() would 500 on duplicates and
        # take the whole Saved page down with it.
        result = await self.db.execute(
            select(SavedList)
            .where(SavedList.student_id == student_id)
            .options(selectinload(SavedList.items))
            .order_by(SavedList.created_at.asc())
            .limit(1)
        )
        saved_list = result.scalars().first()
        if saved_list is None:
            saved_list = SavedList(student_id=student_id, list_name="My List")
            self.db.add(saved_list)
            await self.db.flush()
        return saved_list

    async def _get_item(self, saved_list: SavedList, program_id: UUID) -> SavedListItem:
        result = await self.db.execute(
            select(SavedListItem).where(
                SavedListItem.list_id == saved_list.id,
                SavedListItem.program_id == program_id,
            )
        )
        item = result.scalar_one_or_none()
        if item is None:
            raise NotFoundException("Program is not in the saved list")
        return item

    async def _weight_ranking(self, student_id: UUID) -> int | None:
        result = await self.db.execute(
            select(StudentPreference.weight_ranking).where(
                StudentPreference.student_id == student_id
            )
        )
        row = result.scalar_one_or_none()
        return row

    async def list_saved_enriched(self, student_id: UUID) -> list[SavedProgramResponse]:
        saved_list = await self._get_or_create_default_list(student_id)
        result = await self.db.execute(
            select(SavedListItem)
            .where(SavedListItem.list_id == saved_list.id)
            .order_by(SavedListItem.added_at.desc())
        )
        items = list(result.scalars().all())
        if not items:
            return []

        program_ids = [i.program_id for i in items]
        prog_result = await self.db.execute(
            select(Program)
            .where(Program.id.in_(program_ids))
            .options(selectinload(Program.institution))
        )
        prog_map = {p.id: p for p in prog_result.scalars().all()}

        match_result = await self.db.execute(
            select(MatchResult).where(
                MatchResult.student_id == student_id,
                MatchResult.program_id.in_(program_ids),
            )
        )
        match_map = {m.program_id: m for m in match_result.scalars().all()}

        app_result = await self.db.execute(
            select(Application).where(
                Application.student_id == student_id,
                Application.program_id.in_(program_ids),
            )
        )
        app_map = {a.program_id: a for a in app_result.scalars().all()}

        weight_ranking = await self._weight_ranking(student_id)
        out: list[SavedProgramResponse] = []
        for item in items:
            prog = prog_map.get(item.program_id)
            inst = prog.institution if prog else None
            match = match_map.get(item.program_id)
            app = app_map.get(item.program_id)

            fitness = float(match.fitness_score) if match else None
            confidence = float(match.confidence_score) if match else None
            band: str | None = None
            if fitness is not None and prog:
                band = band_for_acceptance(
                    fitness=fitness,
                    acceptance_rate=float(prog.acceptance_rate)
                    if prog.acceptance_rate is not None
                    else None,
                    weight_ranking=weight_ranking,
                )

            derived = _status_from_application(app)
            row_status = item.status if item.status in VALID_STATUSES else "considering"
            # A withdrawn / deleted application leaves the saved row stranded at
            # "application_started" with no app behind it — clamp back to
            # "considering" so the "Start application" CTA returns instead of a
            # dead "Application started" badge.
            if app is None and row_status == "application_started":
                row_status = "considering"
            status: SavedStatus = derived or row_status  # type: ignore[assignment]

            tags = item.tags if isinstance(item.tags, list) else []
            priority = item.priority if item.priority in VALID_PRIORITIES else "considering"

            out.append(
                SavedProgramResponse(
                    id=item.id,
                    list_id=item.list_id,
                    program_id=item.program_id,
                    notes=item.notes,
                    added_at=item.added_at,
                    priority=priority,  # type: ignore[arg-type]
                    status=status,
                    tags=[str(t) for t in tags],
                    program_name=prog.program_name if prog else None,
                    institution_name=inst.name if inst else None,
                    program=_program_card(prog, inst) if prog else None,
                    fitness_score=fitness,
                    confidence_score=confidence,
                    band_label=band,  # type: ignore[arg-type]
                )
            )
        return out

    async def list_saved(self, student_id: UUID) -> list[SavedListItem]:
        saved_list = await self._get_or_create_default_list(student_id)
        result = await self.db.execute(
            select(SavedListItem)
            .where(SavedListItem.list_id == saved_list.id)
            .order_by(SavedListItem.added_at.desc())
        )
        return list(result.scalars().all())

    async def save_program(
        self,
        student_id: UUID,
        program_id: UUID,
        notes: str | None = None,
    ) -> SavedListItem:
        prog = await self.db.execute(select(Program).where(Program.id == program_id))
        if prog.scalar_one_or_none() is None:
            raise NotFoundException("Program not found")

        saved_list = await self._get_or_create_default_list(student_id)

        existing = await self.db.execute(
            select(SavedListItem).where(
                SavedListItem.list_id == saved_list.id,
                SavedListItem.program_id == program_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictException("Program is already saved")

        item = SavedListItem(
            list_id=saved_list.id,
            program_id=program_id,
            notes=notes,
            priority="considering",
            status="considering",
            tags=[],
        )
        self.db.add(item)
        await self.db.flush()

        # Spec 20 §2 — saving a program auto-follows its institution so its
        # updates appear in the Connect feed. Best-effort; never blocks the save.
        from unipaith.services.follow_service import FollowService

        await FollowService(self.db).auto_follow_for_program(student_id, program_id, source="saved")
        return item

    async def unsave_program(self, student_id: UUID, program_id: UUID) -> None:
        saved_list = await self._get_or_create_default_list(student_id)
        item = await self._get_item(saved_list, program_id)
        await self.db.delete(item)
        await self.db.flush()

    async def update_notes(self, student_id: UUID, program_id: UUID, notes: str) -> SavedListItem:
        saved_list = await self._get_or_create_default_list(student_id)
        item = await self._get_item(saved_list, program_id)
        item.notes = notes
        await self.db.flush()
        return item

    async def patch_saved(
        self,
        student_id: UUID,
        program_id: UUID,
        *,
        priority: str | None = None,
        notes: str | None = None,
        tags: list[str] | None = None,
    ) -> SavedListItem:
        if priority is not None and priority not in VALID_PRIORITIES:
            raise BadRequestException(f"Invalid priority: {priority}")
        saved_list = await self._get_or_create_default_list(student_id)
        item = await self._get_item(saved_list, program_id)
        if priority is not None:
            item.priority = priority
        if notes is not None:
            item.notes = notes
        if tags is not None:
            item.tags = [t.strip() for t in tags if t and t.strip()]
        await self.db.flush()
        return item

    async def start_application(self, student_id: UUID, program_id: UUID) -> UUID:
        saved_list = await self._get_or_create_default_list(student_id)
        item = await self._get_item(saved_list, program_id)
        app_svc = ApplicationService(self.db)
        existing = await self.db.execute(
            select(Application).where(
                Application.student_id == student_id,
                Application.program_id == program_id,
            )
        )
        app = existing.scalar_one_or_none()
        if app is None:
            app = await app_svc.create_application(student_id, program_id)
        item.status = "application_started"
        if item.priority == "considering":
            item.priority = "planning_to_apply"
        await self.db.flush()
        return app.id

    async def compare_programs(self, student_id: UUID, program_ids: list[UUID]) -> dict:
        if len(program_ids) < 2 or len(program_ids) > 4:
            raise BadRequestException("Provide between 2 and 4 programs for comparison")

        result = await self.db.execute(
            select(Program)
            .where(Program.id.in_(program_ids))
            .options(selectinload(Program.institution))
        )
        programs = list(result.scalars().all())
        if len(programs) != len(program_ids):
            raise NotFoundException("One or more programs not found")

        match_result = await self.db.execute(
            select(MatchResult).where(
                MatchResult.student_id == student_id,
                MatchResult.program_id.in_(program_ids),
            )
        )
        match_map: dict[UUID, MatchResult] = {m.program_id: m for m in match_result.scalars().all()}

        comparison_data: list[dict] = []
        for prog in programs:
            inst: Institution = prog.institution
            match = match_map.get(prog.id)
            outcomes = prog.outcomes_data or {}
            salary = next(
                (
                    outcomes[k]
                    for k in ("median_salary", "earnings_4yr_median", "earnings_1yr_median")
                    if isinstance(outcomes.get(k), (int, float))
                ),
                None,
            )
            employment = outcomes.get("employment_rate")
            employment = employment if isinstance(employment, (int, float)) else None
            payback = outcomes.get("payback_months")
            payback = payback if isinstance(payback, (int, float)) else None
            comparison_data.append(
                {
                    "id": str(prog.id),
                    "institution_id": str(prog.institution_id),
                    "program_name": prog.program_name,
                    "institution_name": inst.name if inst else None,
                    "institution_country": inst.country if inst else None,
                    "institution_city": inst.city if inst else None,
                    "campus_setting": prog.campus_setting,
                    "degree_type": prog.degree_type,
                    "department": prog.department,
                    "duration_months": prog.duration_months,
                    "tuition": prog.tuition,
                    "delivery_format": prog.delivery_format,
                    "acceptance_rate": float(prog.acceptance_rate)
                    if prog.acceptance_rate
                    else None,
                    "application_deadline": str(prog.application_deadline)
                    if prog.application_deadline
                    else None,
                    "requirements": prog.requirements,
                    "median_salary": salary,
                    "employment_rate": employment,
                    "payback_months": payback,
                    "fitness_score": float(match.fitness_score)
                    if match and match.fitness_score is not None
                    else None,
                    "confidence_score": float(match.confidence_score)
                    if match and match.confidence_score is not None
                    else None,
                    "match_score": float(match.match_score)
                    if match and match.match_score
                    else None,
                    "match_tier": match.match_tier if match else None,
                    "match_reasoning": match.reasoning_text if match else None,
                }
            )

        return {
            "programs": comparison_data,
            "ai_analysis": "AI analysis unavailable.",
        }

    async def collect_tag_suggestions(self, student_id: UUID) -> list[str]:
        saved_list = await self._get_or_create_default_list(student_id)
        result = await self.db.execute(
            select(SavedListItem.tags).where(SavedListItem.list_id == saved_list.id)
        )
        counts: dict[str, int] = {}
        for (tags,) in result.all():
            if not isinstance(tags, list):
                continue
            for t in tags:
                s = str(t).strip()
                if s:
                    counts[s] = counts.get(s, 0) + 1
        return [k for k, _ in sorted(counts.items(), key=lambda x: (-x[1], x[0]))]
