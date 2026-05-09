"""Phase A — Discovery service.

Owns lifecycle for `discovery_sessions` and `discovery_messages`. When the
`AI_DISCOVERY_V2_ENABLED` flag is on (Phase A2+), `append_message` runs the
real LLM pipeline:

  1. Persist the student message.
  2. Run the extractor (A2) on the student turn → structured signals.
  3. Persist signals to typed tables via `unipaith.ai.artifacts`.
  4. Build a StudentSnapshot and run the validator → LayerVerdict.
  5. Update session.completion_pct from the verdict.
  6. Run the orchestrator (A1) with the verdict in context → assistant turn.
  7. Persist the assistant message and return both.

When the flag is off (default), the original stub assistant reply is
returned. Cross-tenant isolation is enforced as before — every method that
takes a session_id verifies the session belongs to the calling student.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.config import settings
from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.discovery import DiscoveryMessage, DiscoverySession
from unipaith.models.student import StudentProfile

logger = logging.getLogger(__name__)

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
        """Append a message and (when role='student') generate an assistant reply.

        With `AI_DISCOVERY_V2_ENABLED=true` the assistant reply comes from the
        Plan-2 orchestrator with extractor-driven artifact persistence. When
        the flag is off, returns the Phase-A stub reply unchanged.

        Returns (student_or_other_message, assistant_or_None).
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

        if role != "student":
            return msg, None

        if settings.ai_discovery_v2_enabled:
            assistant = await self._run_v2_turn(
                session=session,
                student_id=student_id,
                student_message=msg,
            )
        else:
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

    # ── Phase A2: real LLM pipeline ────────────────────────────────────────

    async def _run_v2_turn(
        self,
        *,
        session: DiscoverySession,
        student_id: UUID,
        student_message: DiscoveryMessage,
    ) -> DiscoveryMessage:
        """One full turn through the LLM pipeline.

        Order matters: extract first (so the orchestrator sees fresh signal
        in its state header), persist artifacts, build snapshot, validate,
        then orchestrate. If anything raises, we still write a fallback
        assistant message so the conversation doesn't dead-end.
        """
        # Local imports — keep the module load cheap when the flag is off.
        from unipaith.ai.artifacts import (
            persist_extraction,
            snapshot_from_extracted_signals_history,
        )
        from unipaith.ai.extractor import get_extractor
        from unipaith.ai.orchestrator import TurnContext, get_orchestrator
        from unipaith.ai.validator import default_validator

        try:
            # 1. Extract from the just-arrived student turn.
            extraction = await get_extractor().extract(
                student_turn=student_message.content,
                student_id=student_id,
                discovery_message_id=student_message.id,
                db=self.db,
            )

            # Stamp the audit trail on the student message.
            if extraction.raw_response is not None:
                student_message.extracted_signals = extraction.raw_response
                await self.db.flush()

            # 2. Persist typed artifacts (goals/needs/identity).
            await persist_extraction(
                db=self.db,
                student_id=student_id,
                session_id=session.id,
                extraction=extraction,
            )

            # 3. Build snapshot from the session's accumulated extractions.
            history = await self._load_extracted_signals_for_session(session.id)
            snapshot = snapshot_from_extracted_signals_history(history)

            # 4. Validate the current layer (BASIC only in A2).
            verdict = None
            if session.track == "profile" and session.layer == "basic":
                verdict = default_validator.validate(layer="basic", snapshot=snapshot)
                session.completion_pct = verdict.completion_pct

            # 5. Orchestrate — generate the assistant turn.
            history_msgs = await self._load_message_history(session.id)
            ctx = TurnContext(
                track=session.track,  # type: ignore[arg-type]
                layer=session.layer,  # type: ignore[arg-type]
                completion_pct=float(session.completion_pct or 0),
                verdict=verdict,
                known_profile_summary=_summarize_snapshot(snapshot),
                recent_signals_summary=_summarize_extraction(extraction),
                history=history_msgs,
            )
            orch_response = await get_orchestrator().respond(
                ctx=ctx,
                student_id=student_id,
                db=self.db,
            )

            assistant_text = orch_response.text or "(empty response)"
            assistant_signals = {
                "_phase": "A2",
                "requested_layer_advance": orch_response.requested_layer_advance,
                "advance_rationale": orch_response.advance_rationale,
                "record_artifact_calls": orch_response.record_artifact_calls,
            }
        except Exception as exc:  # pragma: no cover — degraded path
            logger.exception(
                "Discovery v2 turn failed for session=%s; falling back to soft stub",
                session.id,
            )
            assistant_text = (
                "Sorry — I hit a snag generating that reply. Could you try "
                "rephrasing your last message?"
            )
            assistant_signals = {"_phase": "A2_error", "error": str(exc)[:240]}

        assistant = DiscoveryMessage(
            session_id=session.id,
            role="assistant",
            content=assistant_text,
            extracted_signals=assistant_signals,
        )
        self.db.add(assistant)
        await self.db.flush()
        await self.db.refresh(assistant)
        return assistant

    async def _load_extracted_signals_for_session(self, session_id: UUID) -> list[dict | None]:
        """All extracted_signals for a session, in chronological order."""
        result = await self.db.execute(
            select(DiscoveryMessage.extracted_signals)
            .where(DiscoveryMessage.session_id == session_id)
            .order_by(DiscoveryMessage.created_at)
        )
        return [row[0] for row in result.all()]

    async def _load_message_history(
        self, session_id: UUID, *, limit: int = 24
    ) -> list[dict[str, str]]:
        """Recent (role, content) pairs in Anthropic-message format.

        Returns the last `limit` messages — enough context for natural
        conversation, small enough to stay outside the prompt cache where
        churn is expected.
        """
        result = await self.db.execute(
            select(DiscoveryMessage.role, DiscoveryMessage.content)
            .where(DiscoveryMessage.session_id == session_id)
            .order_by(DiscoveryMessage.created_at.desc())
            .limit(limit)
        )
        rows = list(reversed(result.all()))
        out: list[dict[str, str]] = []
        for role, content in rows:
            # Anthropic accepts role ∈ {user, assistant} only. Map our
            # 'student' → 'user'; drop 'system' (system prompt handles it).
            if role == "student":
                out.append({"role": "user", "content": content})
            elif role == "assistant":
                out.append({"role": "assistant", "content": content})
        return out

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


# ── Module helpers (state-header rendering) ────────────────────────────────


def _summarize_snapshot(snapshot) -> str:  # type: ignore[no-untyped-def]
    """Compact human-readable summary of the StudentSnapshot for the
    orchestrator's state header. Skips nulls; one line per known fact."""
    parts: list[str] = []
    if snapshot.age is not None:
        parts.append(f"- age: {snapshot.age}")
    if snapshot.education_level:
        parts.append(f"- education_level: {snapshot.education_level}")
    if snapshot.gpa is not None:
        parts.append(f"- gpa: {snapshot.gpa}")
    if snapshot.test_scores:
        scores = ", ".join(f"{t['type']}={t['score']}" for t in snapshot.test_scores)
        parts.append(f"- test_scores: {scores}")
    if snapshot.location_prefs:
        parts.append(f"- location_prefs: {', '.join(snapshot.location_prefs)}")
    if snapshot.location_avoid:
        parts.append(f"- location_avoid: {', '.join(snapshot.location_avoid)}")
    if snapshot.first_gen is not None:
        parts.append(f"- first_gen: {snapshot.first_gen}")
    if snapshot.income_band:
        parts.append(f"- income_band: {snapshot.income_band}")
    if snapshot.gender:
        parts.append(f"- gender: {snapshot.gender}")
    return "\n".join(parts) or "(nothing yet)"


def _summarize_extraction(extraction) -> str:  # type: ignore[no-untyped-def]
    """One-line-per-signal summary of the latest extraction. Used in the
    orchestrator's state header so the model knows what was just captured."""
    bits: list[str] = []
    for p in extraction.personality:
        bits.append(f"- personality.{p.get('facet')}: {p.get('value')}")
    for i in extraction.identity:
        bits.append(f"- identity.{i.get('facet')}: {i.get('claim')}")
    for g in extraction.goals:
        spec = g.get("specific") or "(unspecified)"
        bits.append(f"- goal[{g.get('category')}]: {spec[:120]}")
    for n in extraction.needs:
        bits.append(
            f"- need[{n.get('maslow_level')}]: {n.get('signal')} (severity={n.get('severity')})"
        )
    return "\n".join(bits) if bits else "(nothing new this turn)"
