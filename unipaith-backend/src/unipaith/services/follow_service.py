"""Follow service — Spec 20 §2 following model.

Single source of truth for the Connect following graph:
- auto-follow on save (`saved`) and on start-application (`application`),
- explicit follow from a school/program page (`explicit`),
- mute (keeps the follow, suppresses feed items),
- unfollow, **blocked while an active application exists** at that institution.

Because ``ApplicationService.withdraw_application`` *deletes* the row, the
presence of *any* ``Application`` for a program at an institution means the
relationship is active — that is the unfollow-block condition (Spec 20 §2).
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.application import Application
from unipaith.models.follow import InstitutionFollow
from unipaith.models.institution import Institution, Program
from unipaith.models.student import StudentPreference

logger = logging.getLogger(__name__)

# Strength order so an auto-follow reason is never silently downgraded:
# an explicit follow that later gets an application keeps the stronger source.
_SOURCE_RANK = {"explicit": 0, "saved": 1, "application": 2}


class FollowService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    async def ensure_follow(
        self,
        student_id: UUID,
        institution_id: UUID,
        *,
        program_id: UUID | None = None,
        source: str = "explicit",
    ) -> InstitutionFollow:
        """Idempotently follow an institution.

        If a follow already exists, its ``source`` is upgraded to the stronger
        reason (explicit < saved < application) and a ``program_id`` is filled
        in if it was previously null. Never downgrades or un-mutes.
        """
        existing = await self.db.scalar(
            select(InstitutionFollow).where(
                InstitutionFollow.student_id == student_id,
                InstitutionFollow.institution_id == institution_id,
            )
        )
        if existing is not None:
            if _SOURCE_RANK.get(source, 0) > _SOURCE_RANK.get(existing.source, 0):
                existing.source = source
            if existing.program_id is None and program_id is not None:
                existing.program_id = program_id
            await self.db.flush()
            return existing

        follow = InstitutionFollow(
            student_id=student_id,
            institution_id=institution_id,
            program_id=program_id,
            source=source,
        )
        self.db.add(follow)
        await self.db.flush()
        return follow

    async def auto_follow_for_program(
        self, student_id: UUID, program_id: UUID, *, source: str
    ) -> InstitutionFollow | None:
        """Resolve a program's institution and ensure a follow (Spec 20 §2).

        Used by the save-program and start-application hooks. Defensive: if the
        program or its institution can't be resolved, silently no-ops so the
        primary action (save / apply) is never blocked by follow bookkeeping.

        Respects ``auto_follow_on_save`` for ``source='saved'`` (Settings toggle).
        Application auto-follow is always enforced.
        """
        if source == "saved" and not await self.auto_follow_on_save(student_id):
            return None
        institution_id = await self.db.scalar(
            select(Program.institution_id).where(Program.id == program_id)
        )
        if institution_id is None:
            return None
        return await self.ensure_follow(
            student_id, institution_id, program_id=program_id, source=source
        )

    async def auto_follow_on_save(self, student_id: UUID) -> bool:
        """Whether saving a program should auto-follow its institution (Spec 20 §2)."""
        row = await self.db.scalar(
            select(StudentPreference.auto_follow_on_save).where(
                StudentPreference.student_id == student_id
            )
        )
        return True if row is None else bool(row)

    async def set_muted(
        self, student_id: UUID, institution_id: UUID, muted: bool
    ) -> InstitutionFollow:
        follow = await self.db.scalar(
            select(InstitutionFollow).where(
                InstitutionFollow.student_id == student_id,
                InstitutionFollow.institution_id == institution_id,
            )
        )
        if follow is None:
            raise NotFoundException("Not following this institution")
        follow.muted = muted
        await self.db.flush()
        return follow

    async def unfollow(self, student_id: UUID, institution_id: UUID) -> None:
        """Remove a follow. Blocked while an active application exists (Spec 20 §2).

        Idempotent when not following. Raises ``BadRequestException`` with an
        explanation when an application ties the student to the institution.
        """
        if await self.has_active_application_at(student_id, institution_id):
            raise BadRequestException(
                "You have an active application with this institution, so it stays "
                "in your Connect feed. Withdraw the application first to unfollow."
            )
        await self.db.execute(
            sa_delete(InstitutionFollow).where(
                InstitutionFollow.student_id == student_id,
                InstitutionFollow.institution_id == institution_id,
            )
        )
        await self.db.flush()

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    async def has_active_application_at(self, student_id: UUID, institution_id: UUID) -> bool:
        row = await self.db.scalar(
            select(Application.id)
            .join(Program, Program.id == Application.program_id)
            .where(
                Application.student_id == student_id,
                Program.institution_id == institution_id,
            )
            .limit(1)
        )
        return row is not None

    async def _active_application_institution_ids(self, student_id: UUID) -> set[UUID]:
        rows = await self.db.execute(
            select(Program.institution_id)
            .join(Application, Application.program_id == Program.id)
            .where(Application.student_id == student_id)
            .distinct()
        )
        return {r[0] for r in rows.all() if r[0] is not None}

    async def followed_institution_ids(
        self, student_id: UUID, *, include_muted: bool = True, include_saved: bool = True
    ) -> set[UUID]:
        """Institution ids feeding the Connect feed.

        Unions explicit follows with the institutions of saved programs
        (back-compat — saving implies interest). When ``include_muted`` is
        False, muted *explicit* follows are excluded (their feed items are
        suppressed, per Spec 20 §2).
        """
        q = select(InstitutionFollow.institution_id).where(
            InstitutionFollow.student_id == student_id
        )
        if not include_muted:
            q = q.where(InstitutionFollow.muted.is_(False))
        follow_rows = await self.db.execute(q)
        ids = {r[0] for r in follow_rows.all()}

        if include_saved and await self.auto_follow_on_save(student_id):
            from unipaith.models.engagement import SavedList, SavedListItem

            saved_rows = await self.db.execute(
                select(Program.institution_id)
                .join(SavedListItem, SavedListItem.program_id == Program.id)
                .join(SavedList, SavedList.id == SavedListItem.list_id)
                .where(SavedList.student_id == student_id)
                .distinct()
            )
            ids |= {r[0] for r in saved_rows.all() if r[0] is not None}
        return ids

    async def muted_institution_ids(self, student_id: UUID) -> set[UUID]:
        rows = await self.db.execute(
            select(InstitutionFollow.institution_id).where(
                InstitutionFollow.student_id == student_id,
                InstitutionFollow.muted.is_(True),
            )
        )
        return {r[0] for r in rows.all()}

    async def list_detailed(self, student_id: UUID) -> list[dict]:
        """Followed institutions enriched for the Manage-Following panel.

        Each row carries ``muted``, ``source``, ``can_unfollow`` (false while an
        active application exists), and a published-program count.
        """
        prog_count_sq = (
            select(Program.institution_id, func.count(Program.id).label("pc"))
            .where(Program.is_published.is_(True))
            .group_by(Program.institution_id)
            .subquery()
        )
        result = await self.db.execute(
            select(
                InstitutionFollow.institution_id,
                Institution.name,
                InstitutionFollow.created_at,
                Institution.country,
                Institution.city,
                Institution.logo_url,
                Institution.type,
                InstitutionFollow.source,
                InstitutionFollow.muted,
                func.coalesce(prog_count_sq.c.pc, 0),
            )
            .join(Institution, Institution.id == InstitutionFollow.institution_id)
            .outerjoin(
                prog_count_sq, prog_count_sq.c.institution_id == InstitutionFollow.institution_id
            )
            .where(InstitutionFollow.student_id == student_id)
            .order_by(InstitutionFollow.created_at.desc())
        )
        active_inst = await self._active_application_institution_ids(student_id)
        out: list[dict] = []
        for row in result.all():
            inst_id = row[0]
            out.append(
                {
                    "institution_id": inst_id,
                    "name": row[1],
                    "followed_at": row[2],
                    "country": row[3],
                    "city": row[4],
                    "logo_url": row[5],
                    "type": row[6],
                    "source": row[7],
                    "muted": row[8],
                    "program_count": row[9] or 0,
                    "can_unfollow": inst_id not in active_inst,
                }
            )
        return out
