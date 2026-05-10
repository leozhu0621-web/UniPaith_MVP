"""Phase A — Identity service (deepest profile layer).

Single row per student. Upsert is the only write path; partial updates
PRESERVE existing field values (only fields explicitly set on the request body
are applied). This avoids the naive-upsert footgun where omitting a field
would clobber the existing list.

`regenerate_summary` is a Plan 2 contract — Phase A returns a stub summary
tagged so Plan 2 can detect it.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import NotFoundException
from unipaith.models.identity import StudentIdentity
from unipaith.models.student import StudentProfile
from unipaith.schemas.identity import UpsertIdentityRequest

STUB_IDENTITY_SUMMARY = "[stub — identity LLM summary not yet wired]"


class IdentityService:
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

    async def _get_or_create(self, student_id: UUID) -> StudentIdentity:
        result = await self.db.execute(
            select(StudentIdentity).where(StudentIdentity.student_id == student_id)
        )
        identity = result.scalar_one_or_none()
        if identity is None:
            identity = StudentIdentity(student_id=student_id)
            self.db.add(identity)
            await self.db.flush()
            await self.db.refresh(identity)
        return identity

    async def get(self, user_id: UUID) -> StudentIdentity:
        student_id = await self._student_id(user_id)
        return await self._get_or_create(student_id)

    async def upsert(self, user_id: UUID, body: UpsertIdentityRequest) -> StudentIdentity:
        student_id = await self._student_id(user_id)
        identity = await self._get_or_create(student_id)

        # exclude_unset filters omitted keys; an explicit `[]` clears the
        # list (intentional). mode='json' coerces Decimal/UUID/datetime into
        # JSON-compatible primitives so the JSONB writer doesn't choke.
        data = body.model_dump(exclude_unset=True, mode="json")
        for key, value in data.items():
            setattr(identity, key, value)
        await self.db.flush()
        await self.db.refresh(identity)
        return identity

    async def regenerate_summary(self, user_id: UUID) -> StudentIdentity:
        """Synthesize a paragraph summarizing the student's identity layer.

        With `settings.ai_identity_v2_enabled=True`, calls Plan 2's
        IdentitySummaryAgent. On failure (or when the flag is off),
        falls back to STUB_IDENTITY_SUMMARY — but only if the row has
        no prior real summary. Once a real summary exists, we don't
        clobber it with the stub on a flag-off retry.
        """
        from unipaith.config import settings as _cfg

        student_id = await self._student_id(user_id)
        identity = await self._get_or_create(student_id)

        new_summary: str | None = None
        if _cfg.ai_identity_v2_enabled:
            new_summary = await self._try_identity_agent(student_id, identity)

        if new_summary is None:
            if not identity.identity_summary:
                identity.identity_summary = STUB_IDENTITY_SUMMARY
        else:
            identity.identity_summary = new_summary

        await self.db.flush()
        await self.db.refresh(identity)
        return identity

    async def _try_identity_agent(self, student_id: UUID, identity: StudentIdentity) -> str | None:
        try:
            from unipaith.ai.identity import (
                IdentityInput,
                get_identity_summary_agent,
            )
        except Exception as e:  # noqa: BLE001
            import logging

            logging.getLogger(__name__).warning("identity agent import failed: %s", e)
            return None

        view = IdentityInput(
            student_id=student_id,
            core_values=list(identity.core_values or []),
            worldview=list(identity.worldview or []),
            self_awareness=list(identity.self_awareness or []),
        )
        try:
            agent = get_identity_summary_agent()
            result = await agent.synthesize(input_view=view, db=self.db)
        except Exception as e:  # noqa: BLE001
            import logging

            logging.getLogger(__name__).warning("identity agent call failed: %s", e)
            return None
        return result.summary if result else None
