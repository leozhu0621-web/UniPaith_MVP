"""Phase A — Discovery service.

Owns lifecycle for `discovery_sessions` and `discovery_messages`. The Discovery
LLM (Plan 2) plugs in at `append_message`: when a student message arrives, the
service today returns a clearly-marked stub assistant reply. Plan 2 will swap
the stub body for a real LLM call without changing the contract.

Cross-tenant isolation: every method that takes a session_id verifies the
session belongs to the calling student before mutating or reading.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.discovery import DiscoveryMessage, DiscoverySession
from unipaith.models.student import StudentProfile

# Marker used by tests and Plan 2 to detect that the assistant reply is a
# Phase A stub rather than a real LLM-generated message.
STUB_ASSISTANT_CONTENT = "[stub — discovery LLM not yet wired]"
STUB_PHASE_MARKER = {"_phase": "A_stub"}


class DiscoveryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Helpers ────────────────────────────────────────────────────────────
    async def _profile_id_for_user(self, user_id: UUID) -> UUID:
        result = await self.db.execute(
            select(StudentProfile.id).where(StudentProfile.user_id == user_id)
        )
        profile_id = result.scalar_one_or_none()
        if profile_id is None:
            raise NotFoundException("Student profile not found")
        return profile_id

    async def _get_session_for_student(
        self, session_id: UUID, student_id: UUID, *, with_messages: bool = False
    ) -> DiscoverySession:
        stmt = select(DiscoverySession).where(
            DiscoverySession.id == session_id,
            DiscoverySession.student_id == student_id,
        )
        if with_messages:
            stmt = stmt.options(selectinload(DiscoverySession.messages))
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()
        if session is None:
            raise NotFoundException("Discovery session not found")
        return session

    # ── Public API ─────────────────────────────────────────────────────────
    async def start_session(
        self, user_id: UUID, *, track: str, layer: str | None
    ) -> DiscoverySession:
        # Cross-field validation: layer is required for 'profile', forbidden
        # for 'goals' / 'needs'. The DB CHECK constraint enforces the second
        # half; we surface a friendly 400 here for both.
        if track == "profile" and layer is None:
            raise BadRequestException("layer is required when track='profile'")
        if track != "profile" and layer is not None:
            raise BadRequestException("layer must be omitted unless track='profile'")

        student_id = await self._profile_id_for_user(user_id)
        session = DiscoverySession(
            student_id=student_id,
            track=track,
            layer=layer,
            status="active",
            completion_pct=Decimal("0"),
        )
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def list_sessions(
        self,
        user_id: UUID,
        *,
        track: str | None = None,
        status: str | None = None,
    ) -> list[DiscoverySession]:
        student_id = await self._profile_id_for_user(user_id)
        stmt = select(DiscoverySession).where(DiscoverySession.student_id == student_id)
        if track is not None:
            stmt = stmt.where(DiscoverySession.track == track)
        if status is not None:
            stmt = stmt.where(DiscoverySession.status == status)
        stmt = stmt.order_by(DiscoverySession.started_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_session(self, user_id: UUID, session_id: UUID) -> DiscoverySession:
        student_id = await self._profile_id_for_user(user_id)
        return await self._get_session_for_student(session_id, student_id, with_messages=True)

    async def update_session(
        self,
        user_id: UUID,
        session_id: UUID,
        *,
        status: str | None = None,
        completion_pct: Decimal | None = None,
        exit_signal: dict | None = None,
    ) -> DiscoverySession:
        student_id = await self._profile_id_for_user(user_id)
        session = await self._get_session_for_student(session_id, student_id)

        if status is not None:
            session.status = status
            if status == "completed" and session.completed_at is None:
                session.completed_at = func.now()  # type: ignore[assignment]
        if completion_pct is not None:
            session.completion_pct = completion_pct
        if exit_signal is not None:
            session.exit_signal = exit_signal

        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def append_message(
        self,
        user_id: UUID,
        session_id: UUID,
        *,
        role: str,
        content: str,
        extracted_signals: dict | None = None,
    ) -> tuple[DiscoveryMessage, DiscoveryMessage | None]:
        """Append a message and, if it was from the student, append a stub
        assistant reply. Returns (student_or_other_message, assistant_or_None).

        Plan 2 will replace the stub-generation block with real LLM calls.
        """
        student_id = await self._profile_id_for_user(user_id)
        session = await self._get_session_for_student(session_id, student_id)
        if session.status != "active":
            raise BadRequestException(
                f"Cannot append messages to a session with status='{session.status}'"
            )

        msg = DiscoveryMessage(
            session_id=session.id,
            role=role,
            content=content,
            extracted_signals=extracted_signals,
        )
        self.db.add(msg)
        await self.db.flush()
        await self.db.refresh(msg)

        assistant: DiscoveryMessage | None = None
        if role == "student":
            assistant = DiscoveryMessage(
                session_id=session.id,
                role="assistant",
                content=STUB_ASSISTANT_CONTENT,
                extracted_signals=STUB_PHASE_MARKER,
            )
            self.db.add(assistant)
            await self.db.flush()
            await self.db.refresh(assistant)

        return msg, assistant

    async def get_completion_map(self, user_id: UUID) -> dict[str, Decimal]:
        """Return per-track completion 0–1 plus a separate 'identity'
        dimension. Per-track value is the max completion_pct across all
        completed sessions for that track (or 0 if none). Identity is the max
        completion_pct of completed sessions with track='profile' AND
        layer='identity'."""
        student_id = await self._profile_id_for_user(user_id)

        result = await self.db.execute(
            select(
                DiscoverySession.track,
                DiscoverySession.layer,
                func.max(DiscoverySession.completion_pct).label("max_pct"),
            )
            .where(
                DiscoverySession.student_id == student_id,
                DiscoverySession.status == "completed",
            )
            .group_by(DiscoverySession.track, DiscoverySession.layer)
        )
        rows = result.all()

        out: dict[str, Decimal] = {
            "profile": Decimal("0"),
            "goals": Decimal("0"),
            "needs": Decimal("0"),
            "identity": Decimal("0"),
        }
        for track, layer, max_pct in rows:
            value = max_pct or Decimal("0")
            if track in out and value > out[track]:
                out[track] = value
            if track == "profile" and layer == "identity" and value > out["identity"]:
                out["identity"] = value
        return out
