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

from sqlalchemy import func, select, update
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

# Profile-track depth order. The orchestrator advances basic→personality→
# identity as each layer's exit conditions are met (spec 19 §2.1/§4.1).
PROFILE_LAYER_ORDER: tuple[str, ...] = ("basic", "personality", "identity")

# Threshold (0–1) at which all three tracks are considered match-ready and the
# DiscoveryJudge recommends handoff to Stage 2 (spec 19 §7). Mirrors the
# frontend HANDOFF_THRESHOLD on DiscoverHomePage.
HANDOFF_THRESHOLD = Decimal("0.5")


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

    async def start_unified_session(
        self, user_id: UUID, *, fresh: bool = False
    ) -> DiscoverySession:
        """Start (or resume) the unified, track-less Uni conversation. Normally
        there is only ever one active unified session per student, so we reuse the
        most recent active `discovery` session when present. When ``fresh`` is True
        we always create a NEW thread instead — the chat tab gives each session its
        own independent conversation. Either way the extractor is content-based and
        writes goals / needs / identity to the student's GLOBAL profile (keyed by
        student_id), so separate threads never fragment matching."""
        student_id = await self._profile_id_for_user(user_id)
        if not fresh:
            existing = await self.db.execute(
                select(DiscoverySession)
                .where(
                    DiscoverySession.student_id == student_id,
                    DiscoverySession.track == "discovery",
                    DiscoverySession.status == "active",
                )
                .order_by(DiscoverySession.started_at.desc())
            )
            session = existing.scalars().first()
            if session is not None:
                return session
        return await self.start_session(user_id, track="discovery", layer=None)

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

        becoming_completed = status == "completed" and session.status != "completed"
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

        # When a session crosses into 'completed', refresh the denormalized
        # discovery_completion summary on student_profiles. Phase B's home
        # page reads this without joining discovery_sessions per render.
        if becoming_completed:
            await self._refresh_profile_completion_summary(student_id)

        return session

    async def _knowledge_summary(self, snapshot) -> str:
        """Rendered grounding block for the orchestrator, gated on
        ai_uni_knowledge_v1. Never raises — empty string on off/error so the
        conversation degrades to the ungrounded path."""
        from unipaith.config import settings

        if not settings.ai_uni_knowledge_v1:
            return ""
        try:
            from unipaith.services.uni_knowledge import UniKnowledgeRetriever

            bundle = await UniKnowledgeRetriever(self.db).retrieve(snapshot)
            return bundle.render()
        except Exception:
            return ""

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
        # Spec 61 §4 — Safety & crisis floor, BEFORE anything else. If the
        # student signals self-harm / abuse / acute distress, we never run the
        # normal probe: we respond with empathy and escalate to a human / crisis
        # resource. Deterministic + always-on (a safety floor is not flag-gated).
        escalation = await self._maybe_escalate_for_crisis(
            session=session, student_message=student_message
        )
        if escalation is not None:
            return escalation

        # Local imports — keep the module load cheap when the flag is off.
        from unipaith.ai.artifacts import (
            persist_extraction,
            snapshot_from_extracted_signals_history,
        )
        from unipaith.ai.client import ConsentDeniedError
        from unipaith.ai.extractor import get_extractor
        from unipaith.ai.orchestrator import TurnContext, get_orchestrator
        from unipaith.ai.validator import default_validator

        # Hoisted so the post-turn layer-advance and the rule-based fallback
        # prompt can both read it after the try/except.
        verdict = None
        try:
            # 1. Extract from the just-arrived student turn. Best-effort: a
            # consent denial (analytics off / trial lapsed) or any extractor
            # failure skips enrichment but must never crash the turn.
            extraction = None
            try:
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
                # The chat just updated the student's structured profile (field /
                # goals / needs). Mark matches stale so the next Refresh/read
                # re-derives the feature vector — otherwise the recompute scores a
                # FROZEN vector and the list never reflects the conversation.
                try:
                    from unipaith.services.match_service import MatchService

                    await MatchService(self.db).invalidate_for_profile_change(student_id)
                except Exception:  # noqa: BLE001 — invalidation must never fail the turn
                    pass
            except ConsentDeniedError:
                # Best-effort: a consent denial (e.g. analytics off / trial lapsed)
                # must not crash the turn — skip enrichment, keep the reply. Genuine
                # provider outages still propagate to the rule_based fallback below.
                logger.info(
                    "Extractor consent-denied for session=%s — skipping signal "
                    "extraction; the conversation continues normally.",
                    session.id,
                )

            # 3. Build snapshot from the session's accumulated extractions.
            history = await self._load_extracted_signals_for_session(session.id)
            snapshot = snapshot_from_extracted_signals_history(history)

            # 4. Validate the current track / layer.
            # PROFILE.BASIC: deterministic; cheap, every turn.
            # PROFILE.PERSONALITY / IDENTITY: deterministic gate + LLM-as-judge
            # (judge only when count gate passes — saves tokens on
            # clearly-incomplete layers).
            # GOALS / NEEDS: flat tracks, deterministic only.
            verdict = None
            if session.track == "profile" and session.layer in {
                "basic",
                "personality",
                "identity",
            }:
                if session.layer == "basic":
                    verdict = default_validator.validate(layer="basic", snapshot=snapshot)
                else:
                    verdict, _judge_outcome = await default_validator.validate_with_judge(
                        layer=session.layer,  # type: ignore[arg-type]
                        snapshot=snapshot,
                        db=self.db,
                    )
                session.completion_pct = verdict.completion_pct
            elif session.track in {"goals", "needs"}:
                verdict = default_validator.validate_track(
                    track=session.track,  # type: ignore[arg-type]
                    snapshot=snapshot,
                )
                session.completion_pct = verdict.completion_pct
            elif session.track == "discovery":
                # Unified conversation — the extractor already populated all
                # signal types by content; combine the three validators so
                # completion reflects coverage across self/goals/needs and Uni
                # is steered toward the least-covered area next.
                from unipaith.ai.state import LayerVerdict

                parts = [
                    default_validator.validate(layer="basic", snapshot=snapshot),
                    default_validator.validate_track(track="goals", snapshot=snapshot),
                    default_validator.validate_track(track="needs", snapshot=snapshot),
                ]
                avg = sum((p.completion_pct for p in parts), Decimal("0")) / Decimal(len(parts))
                weakest = min(parts, key=lambda p: p.completion_pct)
                verdict = LayerVerdict(
                    layer_complete=all(p.layer_complete for p in parts),
                    completion_pct=avg,
                    missing_signals=[s for p in parts for s in p.missing_signals],
                    next_probe_hint=weakest.next_probe_hint,
                )
                session.completion_pct = avg
                # Persist the per-track split so the handoff gate sees real
                # per-track gaps instead of the masking average. parts order is
                # [basic→profile, goals, needs]. Floats: asyncpg's JSON codec
                # doesn't handle Decimal.
                session.completion_breakdown = {
                    "profile": float(parts[0].completion_pct),
                    "goals": float(parts[1].completion_pct),
                    "needs": float(parts[2].completion_pct),
                }

            # 4b. Phase B1 — fire the feature emitter on completion.
            # Best-effort: errors here never fail the turn. The matcher
            # falls back to the previous feature_vector row if emission
            # fails; if there's no previous row, the student has no
            # match results until Discovery is re-attempted.
            if verdict is not None and verdict.layer_complete:
                await self._emit_features_for_completion(student_id=student_id, snapshot=snapshot)

            # 5. Orchestrate — generate the assistant turn.
            history_msgs = await self._load_message_history(session.id)
            cross_track = await self._cross_track_summary(
                student_id=student_id, current_track=session.track
            )
            ctx = TurnContext(
                track=session.track,  # type: ignore[arg-type]
                layer=session.layer,  # type: ignore[arg-type]
                completion_pct=float(session.completion_pct or 0),
                verdict=verdict,
                known_profile_summary=_summarize_snapshot(snapshot),
                recent_signals_summary=_summarize_extraction(extraction),
                cross_track_summary=cross_track,
                history=history_msgs,
                guided=settings.ai_uni_guided_v1,
                completion_breakdown=session.completion_breakdown or {},
                knowledge_summary=await self._knowledge_summary(snapshot),
            )
            orch_response = await get_orchestrator().respond(
                ctx=ctx,
                student_id=student_id,
                db=self.db,
            )

            assistant_text = orch_response.text
            assistant_signals = {
                "_phase": "A2",
                "requested_layer_advance": orch_response.requested_layer_advance,
                "advance_rationale": orch_response.advance_rationale,
                "record_artifact_calls": orch_response.record_artifact_calls,
                # Spec 19 §3/§5 — tappable reply chips surfaced to the UI.
                "suggested_options": orch_response.suggested_options,
                # Interactive UX Phase 2 — optional multi/scale affordance hint.
                "suggested_input": orch_response.suggested_input,
            }
            if not assistant_text:
                # The orchestrator returned no text — never show a dead
                # "(empty response)" string. Serve a real next probe and tag
                # rule_based so the UI shows the limited-mode banner instead.
                assistant_text = (
                    verdict.next_probe_hint
                    if verdict is not None and verdict.next_probe_hint
                    else _rule_based_opener(session.track, session.layer)
                )
                assistant_signals["_mode"] = "rule_based"
        except Exception as exc:  # pragma: no cover — degraded path
            logger.exception(
                "Discovery v2 turn failed for session=%s; serving rule-based prompt",
                session.id,
            )
            # Spec 19 §9: on agent failure serve a rule-based next prompt
            # (not an apology) so the conversation keeps moving; the UI shows
            # the "Limited mode active — your replies are still saved" banner
            # off the `_mode: rule_based` marker.
            assistant_text = (
                verdict.next_probe_hint
                if verdict is not None and verdict.next_probe_hint
                else _rule_based_opener(session.track, session.layer)
            )
            assistant_signals = {
                "_phase": "A2_error",
                "_mode": "rule_based",
                "error": str(exc)[:240],
            }

        assistant = DiscoveryMessage(
            session_id=session.id,
            role="assistant",
            content=assistant_text,
            extracted_signals=assistant_signals,
        )
        self.db.add(assistant)
        await self.db.flush()
        await self.db.refresh(assistant)

        # Persist the orchestrator's inline record_artifact captures (best-effort —
        # never fails the turn). Idempotent vs the extractor (persist_extraction
        # de-dups), so it only adds obvious claims the extractor missed.
        _arts = assistant_signals.get("record_artifact_calls")
        if _arts:
            try:
                await self._persist_record_artifacts(student_id, session.id, _arts)
            except Exception:
                logger.warning(
                    "record_artifact persist failed for session=%s", session.id, exc_info=True
                )

        # Spec 19 §2.1/§4.1 — auto-advance the profile layer once this layer's
        # exit conditions are met (basic→personality→identity). No-op for
        # goals/needs and for incomplete layers.
        await self._maybe_advance_profile_layer(session=session, verdict=verdict)
        return assistant

    async def _maybe_escalate_for_crisis(
        self,
        *,
        session: DiscoverySession,
        student_message: DiscoveryMessage,
    ) -> DiscoveryMessage | None:
        """Spec 61 §4 — deterministic crisis screen on the student's turn.

        Returns an escalation assistant message (and the caller skips the normal
        LLM turn) when a self-harm / abuse / acute-distress signal fires;
        otherwise ``None`` and the caller proceeds to the usual pipeline. Always
        on — the safety floor is never feature-flag-gated, and it runs the same
        whether or not ``ai_discovery_v2_enabled`` is set.
        """
        from unipaith.ai.safety import screen

        verdict = screen(student_message.content or "")
        if not verdict.is_crisis:
            return None

        assistant = DiscoveryMessage(
            session_id=session.id,
            role="assistant",
            content=verdict.response,
            extracted_signals={
                "_phase": "safety_escalation",
                "_mode": "crisis_escalation",
                "safety_category": verdict.category,
                "safety_subtype": verdict.subtype,
                # The matched span is intentionally NOT persisted verbatim — the
                # subtype is enough for audit / metrics without re-storing a
                # distressing phrase.
            },
        )
        self.db.add(assistant)
        await self.db.flush()
        await self.db.refresh(assistant)
        logger.warning(
            "Discovery crisis signal (%s) for session=%s — escalation served, normal turn skipped",
            verdict.subtype,
            session.id,
        )
        return assistant

    async def _maybe_advance_profile_layer(
        self,
        *,
        session: DiscoverySession,
        verdict,  # LayerVerdict | None — typed loosely to avoid an import
    ) -> None:
        """Advance the profile track to its next layer once the current
        layer's exit conditions are met (spec 19 §2.1/§4.1).

        Strategy: complete the current layer's session (it keeps its high
        completion_pct, so the per-track max in the completion map stays put
        and never regresses) and spawn a fresh active session for the next
        layer. Identity is the deepest layer — it completes terminally with no
        successor. No-op for goals/needs and whenever the verdict is not
        layer-complete.
        """
        if session.track != "profile" or session.status != "active":
            return
        if verdict is None or not verdict.layer_complete:
            return
        if session.layer not in PROFILE_LAYER_ORDER:
            return

        idx = PROFILE_LAYER_ORDER.index(session.layer)
        next_layer = PROFILE_LAYER_ORDER[idx + 1] if idx + 1 < len(PROFILE_LAYER_ORDER) else None

        session.status = "completed"
        if session.completed_at is None:
            session.completed_at = func.now()  # type: ignore[assignment]

        if next_layer is not None:
            self.db.add(
                DiscoverySession(
                    student_id=session.student_id,
                    track="profile",
                    layer=next_layer,
                    status="active",
                    completion_pct=Decimal("0"),
                )
            )
        await self.db.flush()
        # Keep the denormalized journey summary on student_profiles fresh.
        await self._refresh_profile_completion_summary(session.student_id)

    async def get_personality_signals(self, user_id: UUID) -> list[dict[str, object]]:
        """Spec 19 §6 — personality-layer signals for the artifact rail.

        Personality facets aren't persisted to a typed table (the extractor
        writes goals / needs / identity only), so we reconstruct them from the
        student's profile-session message extractions. De-duplicated by facet,
        newest wins, each with a 0–100 confidence so the widget can show dots.
        """
        student_id = await self._profile_id_for_user(user_id)

        # All extracted_signals across the student's profile-track sessions,
        # chronological. We parse the raw dicts directly (rather than via the
        # snapshot) because the snapshot's PersonalityEntry drops the
        # extractor's per-facet confidence, which the rail widget needs.
        result = await self.db.execute(
            select(DiscoveryMessage.extracted_signals)
            .join(DiscoverySession, DiscoveryMessage.session_id == DiscoverySession.id)
            .where(
                DiscoverySession.student_id == student_id,
                # The default unified conversation runs on the "discovery"
                # track; personality facets are extracted there too, so the
                # rail must read both tracks or it stays permanently empty.
                DiscoverySession.track.in_(("profile", "discovery")),
            )
            .order_by(DiscoveryMessage.created_at)
        )

        # De-dup by facet, last write wins (history is chronological).
        by_facet: dict[str, dict[str, object]] = {}
        for (signals,) in result.all():
            if not isinstance(signals, dict):
                continue
            for p in signals.get("personality") or []:
                if not isinstance(p, dict):
                    continue
                facet = p.get("facet")
                value = p.get("value")
                if not facet or not value:
                    continue
                by_facet[facet] = {
                    "facet": facet,
                    "value": value,
                    "evidence": p.get("evidence"),
                    "confidence": _normalize_confidence(p.get("confidence")),
                }
        return list(by_facet.values())

    async def evaluate_handoff(self, user_id: UUID) -> dict[str, object]:
        """Deterministic DiscoveryJudge (spec 19 §7/§10).

        Returns whether the student is match-ready — all three tracks at or
        above the handoff threshold — plus a short reason. The LLM judge is a
        documented follow-up; this rule covers the spec's testable behavior
        and backs the "Generate strategy" handoff nudge.
        """
        completion = await self.get_completion_map(user_id)
        per_track = {k: completion.get(k, Decimal("0")) for k in ("profile", "goals", "needs")}
        ready = all(v >= HANDOFF_THRESHOLD for v in per_track.values())
        if ready:
            reason = "All three tracks are far enough along to generate a strategy."
        else:
            behind = [k for k, v in per_track.items() if v < HANDOFF_THRESHOLD]
            reason = "Keep going on: " + ", ".join(behind)
        return {
            "should_handoff": ready,
            "handoff_target": "recommendation" if ready else None,
            "reason": reason,
            "completion": {k: float(v) for k, v in completion.items()},
        }

    # ── Phase A3.2: SSE streaming variant ──────────────────────────────────

    async def stream_message(
        self,
        user_id: UUID,
        session_id: UUID,
        *,
        role: str,
        content: str,
        extracted_signals: dict | None = None,
    ):
        """Streaming counterpart to append_message.

        Yields (event_name, payload_dict) tuples. The API layer wraps each
        as an SSE frame. Only role='student' is supported here — assistant
        / system messages must use the non-streaming endpoint (no LLM
        round-trip needed for those).

        Order of events:
          1. student_message      — persisted row dump
          2. delta (n times)      — token chunks from orchestrator
          3. tool_use (0+)        — record_artifact / request_layer_advance
          4. assistant_message    — final persisted assistant row
          5. error (terminal)     — only if a stage failed; no further events
        """
        if role != "student":
            yield (
                "error",
                {
                    "message": (
                        "stream_message accepts role='student' only; "
                        "use append_message for non-student messages."
                    ),
                },
            )
            return

        if not settings.ai_discovery_v2_enabled:
            # Flag off — fall through to the stub. We still emit the same
            # event sequence so the frontend can have one code path.
            student_msg, assistant_msg = await self.append_message(
                user_id,
                session_id,
                role=role,
                content=content,
                extracted_signals=extracted_signals,
            )
            yield ("student_message", _msg_dict(student_msg))
            if assistant_msg is not None:
                yield ("delta", {"text": assistant_msg.content})
                yield ("assistant_message", _msg_dict(assistant_msg))
            return

        student_id = await self._profile_id_for_user(user_id)
        session = await self._get_session_for_student(session_id, student_id)
        if session.status != "active":
            yield (
                "error",
                {"message": f"session status='{session.status}' is not active"},
            )
            return

        # Persist the student message up front so the client can render it
        # immediately and we have a turn id for ledger linking.
        student_msg = DiscoveryMessage(
            session_id=session.id,
            role=role,
            content=content,
            extracted_signals=extracted_signals,
        )
        self.db.add(student_msg)
        await self.db.flush()
        await self.db.refresh(student_msg)
        yield ("student_message", _msg_dict(student_msg))

        # Spec 61 §4 — Safety & crisis floor (streaming path). Screen the
        # student turn before the LLM pipeline; on a self-harm / abuse / acute-
        # distress signal, stream the empathetic escalation reply and skip the
        # orchestrator entirely. Always on — never feature-flag-gated.
        from unipaith.ai.safety import screen as _safety_screen

        _crisis = _safety_screen(student_msg.content or "")
        if _crisis.is_crisis:
            crisis_assistant = DiscoveryMessage(
                session_id=session.id,
                role="assistant",
                content=_crisis.response,
                extracted_signals={
                    "_phase": "safety_escalation",
                    "_mode": "crisis_escalation",
                    "safety_category": _crisis.category,
                    "safety_subtype": _crisis.subtype,
                },
            )
            self.db.add(crisis_assistant)
            await self.db.flush()
            await self.db.refresh(crisis_assistant)
            logger.warning(
                "Discovery crisis signal (%s) for session=%s — escalation streamed, "
                "orchestrator skipped",
                _crisis.subtype,
                session.id,
            )
            yield ("delta", {"text": _crisis.response})
            yield ("assistant_message", _msg_dict(crisis_assistant))
            return

        # Run the LLM pipeline up to but not including the orchestrator
        # (extract → persist artifacts → snapshot → validate). These are
        # silent; the orchestrator stream is the user-visible part.
        try:
            from unipaith.ai.artifacts import (
                persist_extraction,
                snapshot_from_extracted_signals_history,
            )
            from unipaith.ai.client import ConsentDeniedError
            from unipaith.ai.extractor import get_extractor
            from unipaith.ai.orchestrator import TurnContext, get_orchestrator
            from unipaith.ai.validator import default_validator

            # Signal extraction is a SILENT, best-effort enrichment step — it must
            # never crash the student's conversation. If it is consent-gated off
            # (e.g. analytics consent withdrawn, or the trial lapsed) or otherwise
            # fails, skip it and let the orchestrator still generate Uni's reply on
            # the live model. (Previously a ConsentDeniedError here bubbled to the
            # outer handler and degraded the whole turn to "hit a snag".)
            extraction = None
            try:
                extraction = await get_extractor().extract(
                    student_turn=student_msg.content,
                    student_id=student_id,
                    discovery_message_id=student_msg.id,
                    db=self.db,
                )
                if extraction.raw_response is not None:
                    student_msg.extracted_signals = extraction.raw_response
                    await self.db.flush()
                await persist_extraction(
                    db=self.db,
                    student_id=student_id,
                    session_id=session.id,
                    extraction=extraction,
                )
                # The chat just updated the student's structured profile (field /
                # goals / needs). Mark matches stale so the next Refresh/read
                # re-derives the feature vector — otherwise the recompute scores a
                # FROZEN vector and the list never reflects the conversation.
                try:
                    from unipaith.services.match_service import MatchService

                    await MatchService(self.db).invalidate_for_profile_change(student_id)
                except Exception:  # noqa: BLE001 — invalidation must never fail the turn
                    pass
            except ConsentDeniedError:
                # Best-effort: a consent denial (e.g. analytics off / trial lapsed)
                # must not crash the turn — skip enrichment, keep the reply. Genuine
                # provider outages still propagate to the rule_based fallback below.
                logger.info(
                    "Extractor consent-denied for session=%s — skipping signal "
                    "extraction; the conversation continues normally.",
                    session.id,
                )

            history = await self._load_extracted_signals_for_session(session.id)
            snapshot = snapshot_from_extracted_signals_history(history)

            verdict = None
            if session.track == "profile" and session.layer in {
                "basic",
                "personality",
                "identity",
            }:
                if session.layer == "basic":
                    verdict = default_validator.validate(layer="basic", snapshot=snapshot)
                else:
                    verdict, _judge = await default_validator.validate_with_judge(
                        layer=session.layer,  # type: ignore[arg-type]
                        snapshot=snapshot,
                        db=self.db,
                    )
                session.completion_pct = verdict.completion_pct
            elif session.track in {"goals", "needs"}:
                verdict = default_validator.validate_track(
                    track=session.track,  # type: ignore[arg-type]
                    snapshot=snapshot,
                )
                session.completion_pct = verdict.completion_pct
            elif session.track == "discovery":
                from unipaith.ai.state import LayerVerdict

                parts = [
                    default_validator.validate(layer="basic", snapshot=snapshot),
                    default_validator.validate_track(track="goals", snapshot=snapshot),
                    default_validator.validate_track(track="needs", snapshot=snapshot),
                ]
                avg = sum((p.completion_pct for p in parts), Decimal("0")) / Decimal(len(parts))
                weakest = min(parts, key=lambda p: p.completion_pct)
                verdict = LayerVerdict(
                    layer_complete=all(p.layer_complete for p in parts),
                    completion_pct=avg,
                    missing_signals=[s for p in parts for s in p.missing_signals],
                    next_probe_hint=weakest.next_probe_hint,
                )
                session.completion_pct = avg
                # See append_message: persist the per-track split for the
                # handoff gate (parts order is [basic→profile, goals, needs]).
                session.completion_breakdown = {
                    "profile": float(parts[0].completion_pct),
                    "goals": float(parts[1].completion_pct),
                    "needs": float(parts[2].completion_pct),
                }

            history_msgs = await self._load_message_history(session.id)
            cross_track = await self._cross_track_summary(
                student_id=student_id, current_track=session.track
            )
            ctx = TurnContext(
                track=session.track,  # type: ignore[arg-type]
                layer=session.layer,  # type: ignore[arg-type]
                completion_pct=float(session.completion_pct or 0),
                verdict=verdict,
                known_profile_summary=_summarize_snapshot(snapshot),
                recent_signals_summary=_summarize_extraction(extraction),
                cross_track_summary=cross_track,
                history=history_msgs,
                guided=settings.ai_uni_guided_v1,
                completion_breakdown=session.completion_breakdown or {},
                knowledge_summary=await self._knowledge_summary(snapshot),
            )

            text_buffer: list[str] = []
            record_calls: list[dict] = []
            requested_advance = False
            advance_rationale: str | None = None

            async for event_type, payload in get_orchestrator().stream(
                ctx=ctx, student_id=student_id, db=self.db
            ):
                if event_type == "text_delta":
                    text_buffer.append(payload)
                    yield ("delta", {"text": payload})
                elif event_type == "tool_use":
                    yield ("tool_use", payload)
                    if payload.get("name") == "record_artifact":
                        record_calls.append(payload.get("input") or {})
                    elif payload.get("name") == "request_layer_advance":
                        requested_advance = True
                        advance_rationale = (payload.get("input") or {}).get("rationale")
                elif event_type == "done":
                    # `payload` is an OrchestratorResponse — prefer its
                    # parsed text (more reliable than our buffer concat).
                    final_text = payload.text or "".join(text_buffer)
                    record_calls = payload.record_artifact_calls or record_calls
                    requested_advance = payload.requested_layer_advance or requested_advance
                    advance_rationale = payload.advance_rationale or advance_rationale
                    stream_signals = {
                        "_phase": "A3_2_stream",
                        "requested_layer_advance": requested_advance,
                        "advance_rationale": advance_rationale,
                        "record_artifact_calls": record_calls,
                        "suggested_options": payload.suggested_options,
                        "suggested_input": payload.suggested_input,
                    }
                    if not final_text:
                        # Never persist/show a dead "(empty response)" — serve a
                        # real probe and tag rule_based for the limited-mode banner.
                        final_text = _rule_based_opener(session.track, session.layer)
                        stream_signals["_mode"] = "rule_based"
                    assistant = DiscoveryMessage(
                        session_id=session.id,
                        role="assistant",
                        content=final_text,
                        extracted_signals=stream_signals,
                    )
                    self.db.add(assistant)
                    await self.db.flush()
                    await self.db.refresh(assistant)
                    # Auto-advance the profile layer on the streaming path too.
                    await self._maybe_advance_profile_layer(session=session, verdict=verdict)
                    # Mirror the non-streaming path: when a layer/track completes,
                    # emit features + recompute matches (best-effort — never fails
                    # the turn). Without this, finishing Discovery on the live
                    # streaming path left match_results empty until a manual refresh.
                    if verdict is not None and verdict.layer_complete:
                        await self._emit_features_for_completion(
                            student_id=student_id, snapshot=snapshot
                        )
                    # Persist the orchestrator's inline record_artifact captures
                    # (best-effort — never fails the turn). Idempotent vs the
                    # extractor (persist_extraction de-dups).
                    if record_calls:
                        try:
                            await self._persist_record_artifacts(
                                student_id, session.id, record_calls
                            )
                        except Exception:
                            logger.warning(
                                "record_artifact persist failed for session=%s",
                                session.id,
                                exc_info=True,
                            )
                    yield ("assistant_message", _msg_dict(assistant))
        except Exception as exc:  # pragma: no cover — degraded path
            logger.exception("Discovery stream_message failed for session=%s", session_id)
            assistant = DiscoveryMessage(
                session_id=session.id,
                role="assistant",
                content=(
                    "Sorry — I hit a snag generating that reply. Could you "
                    "try rephrasing your last message?"
                ),
                extracted_signals={"_phase": "A3_2_stream_error", "error": str(exc)[:240]},
            )
            self.db.add(assistant)
            await self.db.flush()
            await self.db.refresh(assistant)
            yield ("error", {"message": str(exc)[:240]})
            yield ("assistant_message", _msg_dict(assistant))

    async def _persist_record_artifacts(
        self, student_id: UUID, session_id: UUID, calls: list[dict]
    ) -> None:
        """Persist the orchestrator's inline ``record_artifact`` captures.

        The extractor is the primary signal path; these are the "obvious claim"
        artifacts the responder committed mid-turn (the inline "Noticed" chips).
        ``persist_extraction`` de-dups + gates, so this is idempotent against the
        extractor and only adds claims it missed. Callers wrap this best-effort so
        it can never fail the turn.
        """
        from unipaith.ai.artifacts import persist_extraction
        from unipaith.ai.extractor import ExtractedSignals

        goals: list[dict] = []
        needs: list[dict] = []
        identity: list[dict] = []
        personality: list[dict] = []
        basic: dict = {}
        conf: dict[str, float] = {}
        for c in calls or []:
            if not isinstance(c, dict):
                continue
            kind = c.get("type")
            value = c.get("value")
            evidence = (c.get("evidence") or "").strip()
            if not isinstance(value, dict):
                continue
            if kind == "goal":
                goals.append({**value, "evidence": evidence})
                conf["goals"] = 0.85
            elif kind == "need":
                needs.append({**value, "evidence": evidence})
                conf["needs"] = 0.85
            elif kind == "identity_claim":
                identity.append({**value, "evidence": evidence})
                conf["identity"] = 0.85
            elif kind == "personality_field":
                personality.append({**value, "evidence": evidence})
                conf["personality"] = 0.85
            elif kind == "basic_field":
                basic.update(value)
        if not (goals or needs or identity or personality or basic):
            return
        extraction = ExtractedSignals(
            basic=basic,
            personality=personality,
            identity=identity,
            goals=goals,
            needs=needs,
            confidence_per_key={k: Decimal(str(v)) for k, v in conf.items()},
            raw_response={"record_artifacts": calls},
        )
        await persist_extraction(
            db=self.db, student_id=student_id, session_id=session_id, extraction=extraction
        )

    async def _emit_features_for_completion(self, *, student_id: UUID, snapshot) -> None:
        """Phase B1 — fire the A4 Feature Emitter when a layer/track
        completes. Best-effort: any error is logged but doesn't propagate.

        We re-emit on every completion (bump_version=True) so the
        downstream match_rationales cache invalidates whenever the
        student's profile changes. This is cheap (~$0.005/emit on
        Haiku) and keeps recommendations fresh.

        On successful emit we chain into `_recompute_matches_for_student`
        — without that hook `match_results` stays empty even after
        Discovery completes, which is the gap §10 closes.
        """
        from unipaith.ai.feature_emitter import (
            get_feature_emitter,
            persist_features,
        )

        try:
            features = await get_feature_emitter().emit(
                snapshot=snapshot, student_id=student_id, db=self.db
            )
            if features.is_valid():
                await persist_features(db=self.db, student_id=student_id, features=features)
                await self._recompute_matches_for_student(student_id=student_id)
            else:
                logger.warning(
                    "FeatureEmitter returned invalid features for student=%s; "
                    "skipping persist (this turn keeps the previous vector).",
                    student_id,
                )
        except Exception:  # pragma: no cover — degraded path
            logger.exception(
                "Feature emission failed for student=%s — recommendations "
                "will use the previous feature vector.",
                student_id,
            )

    async def _recompute_matches_for_student(self, *, student_id: UUID) -> None:
        """Phase D wiring — re-score the catalog after a feature emit.

        Loads all published Programs, projects each to ProgramRow, and
        hands off to `MatchService.compute_matches_for_student`. The
        service handles the rerank + persist; this hook just delivers
        the catalog.

        Best-effort: if the catalog read or match compute fails, the
        student keeps whatever stale `match_results` they had. The next
        Discovery completion (or an explicit refresh) retries.

        Catalog size in production will likely sit in the hundreds, then
        thousands once partners onboard. Computing a few thousand
        cosine + soft_align + needs scores is fast (~<1s); the cost
        center is rationale (lazy, per-click) not matching.
        """
        # Local imports — defers institution + matching imports until
        # discovery is actually running, and avoids a circular load when
        # MatchService imports back into the AI stack.
        from unipaith.models.institution import Program
        from unipaith.services.match_service import MatchService
        from unipaith.services.program_features import program_row_from_orm

        try:
            result = await self.db.execute(select(Program).where(Program.is_published.is_(True)))
            programs = list(result.scalars().all())
            if not programs:
                logger.info(
                    "Match recompute skipped for student=%s: no published programs in catalog.",
                    student_id,
                )
                return
            program_rows = [program_row_from_orm(p) for p in programs]
            svc = MatchService(self.db)
            # Use ONLY already-cached program embeddings — never embed the catalog
            # inside this request. ensure_program_embeddings embeds every uncached
            # program sequentially; at ~7k programs that is minutes of embedding
            # calls that timed out the onboarding seed / matches recompute, so a
            # fresh student got zero matches. The matcher drops cosine +
            # renormalizes for un-embedded programs, so matches still compute fast.
            program_embeddings: dict = {}
            if await svc.can_match(student_id):
                program_embeddings = svc.cached_program_embeddings(programs)
            rows = await svc.compute_matches_for_student(
                student_id, program_rows=program_rows, program_embeddings=program_embeddings
            )
            logger.info(
                "Match recompute for student=%s produced %d rows over %d programs.",
                student_id,
                len(rows),
                len(programs),
            )
        except Exception:  # pragma: no cover — degraded path
            logger.exception(
                "Match recompute failed for student=%s — UI will keep prior "
                "match_results until next emit.",
                student_id,
            )

    async def _cross_track_summary(self, *, student_id: UUID, current_track: str) -> str:
        """Spec 19 §15 — one line per OTHER track's completion, so the
        orchestrator stays coherent across Profile / Goals / Needs and won't
        re-ask what another track already covered."""
        completion = await self._completion_for_student(student_id)
        labels = {
            "profile": "Profile",
            "goals": "Goals",
            "needs": "Needs",
        }
        lines: list[str] = []
        for key, label in labels.items():
            if key == current_track:
                continue
            pct = int(round(float(completion.get(key, 0)) * 100))
            lines.append(f"- {label}: {pct}% complete")
        return "\n".join(lines)

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

    async def recompute_completion_for_session(self, session_id: UUID) -> dict[str, float]:
        """Recompute per-track discovery completion from the student's CURRENT
        structured signals and write it onto the bound session's
        ``completion_pct`` + ``completion_breakdown``.

        This is the managed-agent counterpart to the in-app orchestrator's
        inline completion write (``append_message`` step 4). The host path
        persists typed goals/needs/identity (via ``save_signals`` or the host
        extractor safety net) but never computed completion — so the
        Profile/Goals/Needs counters read 0 (``_completion_for_student`` treats
        a NULL breakdown as 0 on a 'discovery' session) and ``evaluate_handoff``
        never fired, which is why matches never unlocked after a conversation.
        Calling this after each persist makes the counters move and lets the
        handoff gate open. On full completion it also emits the feature vector
        (best-effort) so an explicit Explore/Refresh has matches to show.

        Best-effort: any failure leaves the prior completion untouched.
        """
        from unipaith.ai.artifacts import snapshot_from_structured_tables
        from unipaith.ai.validator import default_validator

        session = await self.db.get(DiscoverySession, session_id)
        if session is None:
            return {"profile": 0.0, "goals": 0.0, "needs": 0.0}
        try:
            snapshot = await snapshot_from_structured_tables(self.db, session.student_id)
            parts = [
                default_validator.validate(layer="basic", snapshot=snapshot),
                default_validator.validate_track(track="goals", snapshot=snapshot),
                default_validator.validate_track(track="needs", snapshot=snapshot),
            ]
            avg = sum((p.completion_pct for p in parts), Decimal("0")) / Decimal(len(parts))
            breakdown = {
                "profile": float(parts[0].completion_pct),
                "goals": float(parts[1].completion_pct),
                "needs": float(parts[2].completion_pct),
            }
            session.completion_pct = avg
            session.completion_breakdown = breakdown
            await self.db.flush()
            if all(p.layer_complete for p in parts):
                # Bootstraps the feature vector so the explicit Explore/Refresh
                # path (which never emits one on its own) can score matches.
                await self._emit_features_for_completion(
                    student_id=session.student_id, snapshot=snapshot
                )
            await self.db.commit()
            return breakdown
        except Exception:  # pragma: no cover — degraded path
            await self.db.rollback()
            logger.exception("recompute_completion_for_session failed for session=%s", session_id)
            return {"profile": 0.0, "goals": 0.0, "needs": 0.0}

    async def _completion_for_student(self, student_id: UUID) -> dict[str, Decimal]:
        """Inner query — returns the per-track + identity completion dict
        keyed by student_id directly. Used both by the public API endpoint
        and by the profile-summary write hook.

        Counts both ACTIVE and completed sessions (everything except
        'abandoned'). The live conversation writes `completion_pct` onto the
        active session each turn, so the Discover progress bars + the
        Generate-strategy gate (spec 19 §3/§7) must see active progress, not
        only finished sessions. Per-track value is the max completion across
        the student's sessions for that track; this stays monotonic across
        profile layer auto-advance because each completed layer keeps its
        high `completion_pct` while the next layer starts a fresh row."""
        result = await self.db.execute(
            select(
                DiscoverySession.track,
                DiscoverySession.layer,
                DiscoverySession.completion_pct,
                DiscoverySession.completion_breakdown,
            ).where(
                DiscoverySession.student_id == student_id,
                DiscoverySession.status != "abandoned",
            )
        )
        rows = result.all()

        out: dict[str, Decimal] = {
            "profile": Decimal("0"),
            "goals": Decimal("0"),
            "needs": Decimal("0"),
            "identity": Decimal("0"),
        }
        for track, layer, pct, breakdown in rows:
            value = pct or Decimal("0")
            if track == "discovery":
                # Unified Uni conversation covers self/goals/needs in one
                # session. completion_pct is the masking AVERAGE, so feed each
                # track its own value from completion_breakdown — the handoff
                # gate must see a weak track, not just the mean. When a session
                # has no breakdown yet (legacy rows, or a session whose first
                # turn hasn't computed it — the column is nullable with no
                # backfill), treat each track as 0 so the gate stays
                # CONSERVATIVE: never unlock the matches reward off the masking
                # average. The breakdown is populated on the next discovery turn.
                bd = breakdown or {}
                for key in ("profile", "goals", "needs"):
                    sub = bd.get(key)
                    sub_val = Decimal(str(sub)) if sub is not None else Decimal("0")
                    if sub_val > out[key]:
                        out[key] = sub_val
                continue
            if track in out and value > out[track]:
                out[track] = value
            if track == "profile" and layer == "identity" and value > out["identity"]:
                out["identity"] = value
        return out

    async def get_completion_map(self, user_id: UUID) -> dict[str, Decimal]:
        """Return per-track completion 0–1 plus a separate 'identity'
        dimension. Per-track value is the max completion_pct across the
        student's active + completed sessions for that track (or 0 if none).
        Identity is the max completion_pct of sessions with track='profile'
        AND layer='identity'."""
        student_id = await self._profile_id_for_user(user_id)
        return await self._completion_for_student(student_id)

    async def _refresh_profile_completion_summary(self, student_id: UUID) -> None:
        """Recompute discovery_completion and write it to student_profiles.
        Called from update_session whenever a session reaches `completed`,
        so the home page can read live progress without joining."""
        completion = await self._completion_for_student(student_id)
        # JSON-friendly: floats not Decimals (asyncpg's json codec doesn't
        # know about Decimal).
        json_completion = {k: float(v) for k, v in completion.items()}
        await self.db.execute(
            update(StudentProfile)
            .where(StudentProfile.id == student_id)
            .values(discovery_completion=json_completion)
        )
        await self.db.flush()


# ── Module helpers (state-header rendering) ────────────────────────────────


# Spec 19 §9/§14 — deterministic next prompts served when the LLM orchestrator
# fails. Keyed (track, layer); the basic opener matches the spec copy verbatim.
_RULE_BASED_OPENERS: dict[tuple[str, str | None], str] = {
    ("profile", "basic"): "Tell me about a course you actually enjoyed this year.",
    ("profile", "personality"): "What's something your friends rely on you for?",
    ("profile", "identity"): "What's a value of yours that's been tested recently?",
    ("goals", None): "What does success look like a year after you finish?",
    ("needs", None): "What's one thing you can't do without in a school environment?",
    (
        "discovery",
        None,
    ): "Thinking back over this past year, when was a moment you felt really absorbed?",
}


def _rule_based_opener(track: str, layer: str | None) -> str:
    """A safe, on-topic next question for the degraded (rule-based) path."""
    return (
        _RULE_BASED_OPENERS.get((track, layer))
        or _RULE_BASED_OPENERS.get((track, None))
        or "Tell me a bit more about what you're looking for."
    )


def _normalize_confidence(raw: object) -> int | None:
    """Normalize an extractor confidence to a 0–100 int for the UI.

    The codebase is mixed on scale (state-machine thresholds use 0–1; the
    agent specs describe 0–100), so accept either: a value <= 1 is treated as
    a 0–1 fraction and scaled up; anything larger is treated as already 0–100.
    Clamped to [0, 100]; None/garbage → None."""
    if raw is None:
        return None
    try:
        v = float(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if v <= 1.0:
        v *= 100.0
    return max(0, min(100, int(round(v))))


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
    # Personality + identity summaries (truncated — full evidence stays in
    # the audit trail; the orchestrator only needs gist-level grounding).
    if snapshot.personality:
        for p in snapshot.personality[:6]:
            parts.append(f"- personality.{p.facet}: {p.value}")
    if snapshot.identity_claims:
        for c in snapshot.identity_claims[:6]:
            parts.append(f"- identity.{c.facet}: {c.claim[:120]}")
    # Goals + needs (Phase A3.2 — when in those tracks, the orchestrator
    # needs to see what's already been captured so it doesn't restart).
    if snapshot.goals:
        for g in snapshot.goals[:6]:
            confirmed = "✓" if g.user_confirmed else "?"
            parts.append(
                f"- goal.{g.category} [{int(g.completeness * 100)}%{confirmed}]: {g.specific[:100]}"
            )
    if snapshot.needs:
        for n in snapshot.needs[:6]:
            sev = f"sev={n.severity}" if n.severity else ""
            parts.append(f"- need.{n.maslow_level} {sev}: {n.signal}")
    return "\n".join(parts) or "(nothing yet)"


def _summarize_extraction(extraction) -> str:  # type: ignore[no-untyped-def]
    """One-line-per-signal summary of the latest extraction. Used in the
    orchestrator's state header so the model knows what was just captured."""
    if extraction is None:
        return ""
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


def _msg_dict(msg: DiscoveryMessage) -> dict:
    """Compact JSON-serializable dict of a DiscoveryMessage for SSE frames."""
    return {
        "id": str(msg.id),
        "session_id": str(msg.session_id),
        "role": msg.role,
        "content": msg.content,
        "extracted_signals": msg.extracted_signals,
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }
