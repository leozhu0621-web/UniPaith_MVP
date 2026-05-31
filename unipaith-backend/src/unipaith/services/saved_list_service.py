"""
Saved-list service — manage a student's saved/bookmarked programs (Spec 13).

Owns curation (priority + tags + notes), the derived per-row status and
reach/target/safer band, one-click conversion to an application, and the
multi-program compare matrix (dual fitness/confidence scores).
"""

from __future__ import annotations

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.core.exceptions import BadRequestException, ConflictException, NotFoundException
from unipaith.models.application import Application
from unipaith.models.engagement import SavedList, SavedListItem
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import MatchResult

logger = logging.getLogger(__name__)

VALID_PRIORITIES = ("considering", "planning_to_apply", "applied", "dropped")


class SavedListService:
    """CRUD for saved-program lists plus curation, conversion, and comparison."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _get_or_create_default_list(self, student_id: UUID) -> SavedList:
        """Return the student's default saved list, creating one if needed."""
        result = await self.db.execute(
            select(SavedList)
            .where(SavedList.student_id == student_id)
            .options(selectinload(SavedList.items))
        )
        saved_list = result.scalar_one_or_none()
        if saved_list is None:
            saved_list = SavedList(student_id=student_id, list_name="My List")
            self.db.add(saved_list)
            await self.db.flush()
        return saved_list

    async def _get_item(self, saved_list: SavedList, program_id: UUID) -> SavedListItem:
        """Fetch a single item from the list or raise 404."""
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

    @staticmethod
    def _num(value: Decimal | float | int | None) -> float | None:
        return float(value) if value is not None else None

    @staticmethod
    def _band_of(match: MatchResult | None) -> str | None:
        """Reach / target / safer for a saved program (Spec 13 §7 / Spec 09 §6).

        Prefers the persisted tier; falls back to fitness thresholds — the same
        mapping the Match surface uses (high fitness ⇒ safer bet).
        """
        if match is None:
            return None
        tier = match.match_tier
        if tier == 1:
            return "reach"
        if tier == 2:
            return "target"
        if tier == 3:
            return "safer"
        raw = match.fitness_score if match.fitness_score is not None else match.match_score
        if raw is None:
            return None
        f = float(raw)
        if f >= 0.75:
            return "safer"
        if f >= 0.60:
            return "target"
        return "reach"

    @staticmethod
    def _derive_status(priority: str | None, app: Application | None) -> str:
        """Spec 13 §4.4 — status derived from application existence.

        considering | application_started | submitted | accepted | rejected |
        waitlisted | dropped. `dropped` priority wins (the student parked it).
        """
        if priority == "dropped":
            return "dropped"
        if app is None:
            return "considering"
        decision = (app.decision or "").lower()
        if decision == "admitted":
            return "accepted"
        if decision == "rejected":
            return "rejected"
        if decision in ("waitlisted", "deferred"):
            return "waitlisted"
        status = (app.status or "").lower()
        if status in ("submitted", "under_review", "interview", "decision_made"):
            return "submitted"
        return "application_started"

    @classmethod
    def _serialize(
        cls,
        item: SavedListItem,
        prog: Program | None,
        inst: Institution | None,
        match: MatchResult | None,
        app: Application | None,
    ) -> dict:
        program_dict = None
        if prog is not None:
            program_dict = {
                "id": str(prog.id),
                "institution_id": str(prog.institution_id),
                "program_name": prog.program_name,
                "degree_type": prog.degree_type,
                "department": prog.department,
                "tuition": cls._num(prog.tuition),
                "duration_months": prog.duration_months,
                "delivery_format": prog.delivery_format,
                "acceptance_rate": cls._num(prog.acceptance_rate),
                "application_deadline": str(prog.application_deadline)
                if prog.application_deadline
                else None,
                "institution_name": inst.name if inst else None,
                "institution_country": inst.country if inst else None,
                "institution_city": inst.city if inst else None,
                "institution_logo_url": inst.logo_url if inst else None,
            }
        return {
            "id": item.id,
            "list_id": item.list_id,
            "program_id": item.program_id,
            "notes": item.notes,
            "added_at": item.added_at,
            "priority": item.priority or "considering",
            "tags": list(item.tags or []),
            "status": cls._derive_status(item.priority, app),
            "band_label": cls._band_of(match),
            "fitness_score": cls._num(match.fitness_score) if match else None,
            "confidence_score": cls._num(match.confidence_score) if match else None,
            "program_name": prog.program_name if prog else None,
            "institution_id": prog.institution_id if prog else None,
            "institution_name": inst.name if inst else None,
            "institution_country": inst.country if inst else None,
            "institution_city": inst.city if inst else None,
            "degree_type": prog.degree_type if prog else None,
            "tuition": cls._num(prog.tuition) if prog else None,
            "application_deadline": str(prog.application_deadline)
            if prog and prog.application_deadline
            else None,
            "acceptance_rate": cls._num(prog.acceptance_rate) if prog else None,
            "duration_months": prog.duration_months if prog else None,
            "program": program_dict,
        }

    async def _load_context(
        self, student_id: UUID, program_ids: list[UUID]
    ) -> tuple[dict, dict, dict]:
        """Bulk-load program+institution, match, and application maps."""
        prog_map: dict[UUID, tuple[Program, Institution]] = {}
        match_map: dict[UUID, MatchResult] = {}
        app_map: dict[UUID, Application] = {}
        if not program_ids:
            return prog_map, match_map, app_map

        prog_result = await self.db.execute(
            select(Program, Institution)
            .join(Institution, Program.institution_id == Institution.id)
            .where(Program.id.in_(program_ids))
        )
        for prog, inst in prog_result.all():
            prog_map[prog.id] = (prog, inst)

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
        return prog_map, match_map, app_map

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def list_saved(self, student_id: UUID) -> list[SavedListItem]:
        """Raw saved items (back-compat; the API uses :meth:`list_saved_enriched`)."""
        saved_list = await self._get_or_create_default_list(student_id)
        result = await self.db.execute(
            select(SavedListItem)
            .where(SavedListItem.list_id == saved_list.id)
            .order_by(SavedListItem.added_at.desc())
        )
        return list(result.scalars().all())

    async def list_saved_enriched(self, student_id: UUID) -> list[dict]:
        """All saved programs with curation + derived status/band/scores (Spec 13 §7)."""
        items = await self.list_saved(student_id)
        if not items:
            return []
        program_ids = [it.program_id for it in items]
        prog_map, match_map, app_map = await self._load_context(student_id, program_ids)
        out: list[dict] = []
        for it in items:
            prog, inst = prog_map.get(it.program_id, (None, None))
            match = match_map.get(it.program_id)
            app = app_map.get(it.program_id)
            out.append(self._serialize(it, prog, inst, match, app))
        return out

    async def get_one_enriched(self, student_id: UUID, program_id: UUID) -> dict:
        """Single enriched saved program (used by PATCH to return fresh derived data)."""
        saved_list = await self._get_or_create_default_list(student_id)
        item = await self._get_item(saved_list, program_id)
        prog_map, match_map, app_map = await self._load_context(student_id, [program_id])
        prog, inst = prog_map.get(program_id, (None, None))
        return self._serialize(item, prog, inst, match_map.get(program_id), app_map.get(program_id))

    async def save_program(
        self,
        student_id: UUID,
        program_id: UUID,
        notes: str | None = None,
    ) -> SavedListItem:
        """Add a program to the student's saved list."""
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
        )
        self.db.add(item)
        await self.db.flush()
        return item

    async def unsave_program(self, student_id: UUID, program_id: UUID) -> None:
        """Remove a program from the saved list."""
        saved_list = await self._get_or_create_default_list(student_id)
        item = await self._get_item(saved_list, program_id)
        await self.db.delete(item)
        await self.db.flush()

    async def update_notes(self, student_id: UUID, program_id: UUID, notes: str) -> SavedListItem:
        """Update only the notes (legacy PUT /{program_id}/notes path)."""
        return await self.update_saved(student_id, program_id, notes=notes)

    async def update_saved(
        self,
        student_id: UUID,
        program_id: UUID,
        *,
        priority: str | None = None,
        notes: str | None = None,
        tags: list[str] | None = None,
    ) -> SavedListItem:
        """Partial curation update (Spec 13 §4.2 / §4.3)."""
        saved_list = await self._get_or_create_default_list(student_id)
        item = await self._get_item(saved_list, program_id)
        if priority is not None:
            if priority not in VALID_PRIORITIES:
                raise BadRequestException(f"Invalid priority: {priority}")
            item.priority = priority
        if notes is not None:
            item.notes = notes
        if tags is not None:
            item.tags = list(tags)
        await self.db.flush()
        return item

    async def start_application(self, student_id: UUID, program_id: UUID) -> dict:
        """Spec 13 §6 — one-click conversion of a saved program to an application.

        Idempotent: if an application for this program already exists it is
        reused (so a double-click never 409s). The saved row's derived status
        becomes ``application_started`` once an application exists.
        """
        saved_list = await self._get_or_create_default_list(student_id)
        item = await self._get_item(saved_list, program_id)  # 404 if not saved

        existing = await self.db.execute(
            select(Application).where(
                Application.student_id == student_id,
                Application.program_id == program_id,
            )
        )
        app = existing.scalar_one_or_none()
        created = False
        if app is None:
            # Imported lazily to avoid a circular import at module load.
            from unipaith.services.application_service import ApplicationService

            app = await ApplicationService(self.db).create_application(student_id, program_id)
            created = True

        await self.db.flush()
        return {
            "app_id": app.id,
            "program_id": program_id,
            "status": self._derive_status(item.priority, app),
            "created": created,
        }

    async def compare_programs(self, student_id: UUID, program_ids: list[UUID]) -> dict:
        """Build a compare matrix for 2–4 saved programs (Spec 13 §5).

        Each program carries dual ``fitness_score`` + ``confidence_score`` and a
        ``band_label`` (the legacy single ``match_score`` is kept only for
        back-compat).
        """
        if len(program_ids) < 2 or len(program_ids) > 4:
            raise BadRequestException("Provide between 2 and 4 programs for comparison")

        result = await self.db.execute(
            select(Program)
            .where(Program.id.in_(program_ids))
            .options(selectinload(Program.institution))
        )
        by_id = {p.id: p for p in result.scalars().all()}
        if len(by_id) != len(set(program_ids)):
            raise NotFoundException("One or more programs not found")
        # Preserve the caller's selection order so table columns are stable.
        programs = [by_id[pid] for pid in program_ids if pid in by_id]

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
            # Spec 10 §8 — program-level outcomes feed the "outcomes + employer
            # signals" comparison dimension. Match displayed salary coalescing.
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
                    "tuition": self._num(prog.tuition),
                    "delivery_format": prog.delivery_format,
                    "acceptance_rate": self._num(prog.acceptance_rate),
                    "application_deadline": str(prog.application_deadline)
                    if prog.application_deadline
                    else None,
                    "requirements": prog.requirements,
                    # Spec 10 §8 — outcomes + employer signals dimension.
                    "median_salary": salary,
                    "employment_rate": employment,
                    "payback_months": payback,
                    # Spec 13 §5 / §11 — dual scores + band (best-value highlighted client-side).
                    "fitness_score": self._num(match.fitness_score) if match else None,
                    "confidence_score": self._num(match.confidence_score) if match else None,
                    "band_label": self._band_of(match),
                    # Legacy — kept for back-compat during the Phase E transition.
                    "match_score": self._num(match.match_score)
                    if match and match.match_score is not None
                    else None,
                    "match_tier": match.match_tier if match else None,
                }
            )

        return {"programs": comparison_data, "ai_analysis": None}
