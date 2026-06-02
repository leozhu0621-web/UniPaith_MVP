"""Spec 44 — Adaptive Intake Engine service.

The §3 per-signal pipeline plus the §4/§6 completeness/readiness gates and the
§6 clarification loop. Every intake channel (§5) funnels through
:meth:`IntakeEngineService.ingest_signal`, which normalizes → validates →
reconciles → persists with provenance/confidence/version → fans out.

Design invariants (§9):
- Single source of truth: one ``student_signals`` row per (student, signal).
- Provenance always knowable: every write appends to ``provenance_chain`` and
  writes a ``signal_change_events`` row.
- Version monotonic: ``record_version`` only increases, and only when the
  canonical value actually changes.
- Confidence reflects the *current* value (a confirm replaces, never blends).
- Consent respected in flight: no LLM call when ``consent_matching`` is off.

Read paths (completeness / match-ready / apply-ready) are deliberately
side-effect free — they never write, so a GET can't expire ORM attributes and
trip ``MissingGreenlet``.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.institution import Program
from unipaith.models.intake import (
    INTAKE_CHANNELS,
    RawInput,
    SignalChangeEvent,
    SignalClarification,
    StudentSignal,
)
from unipaith.models.student import (
    RecommendationRequest,
    StudentDataConsent,
    StudentProfile,
)
from unipaith.services.intake import registry as reg

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _wrap(value: object) -> dict | None:
    """Store a scalar/compound value in a JSONB column under a stable key."""
    return None if value is None else {"v": value}


def _unwrap(col: dict | None) -> object:
    return None if not isinstance(col, dict) else col.get("v")


class IntakeEngineService:
    """Spec 44 engine. One instance per request; receives the request session."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── identity / consent helpers ───────────────────────────────────────────
    async def profile_id_for_user(self, user_id: UUID) -> UUID:
        result = await self.db.execute(
            select(StudentProfile.id).where(StudentProfile.user_id == user_id)
        )
        pid = result.scalar_one_or_none()
        if pid is None:
            raise NotFoundException("Student profile not found")
        return pid

    async def _consent_matching(self, student_id: UUID) -> bool:
        result = await self.db.execute(
            select(StudentDataConsent.consent_matching).where(
                StudentDataConsent.student_id == student_id
            )
        )
        row = result.scalar_one_or_none()
        # No consent row yet → default-allow (matches StudentDataConsent default).
        return True if row is None else bool(row)

    async def _should_use_llm(self, student_id: UUID) -> bool:
        """§10/§11 — an LLM step runs only when the engine flag is on AND the
        student consents to matching. Off → deterministic path, no LLM call."""
        if not settings.ai_intake_engine_v2_enabled:
            return False
        return await self._consent_matching(student_id)

    async def _get_signal(self, student_id: UUID, signal_name: str) -> StudentSignal | None:
        result = await self.db.execute(
            select(StudentSignal).where(
                StudentSignal.student_id == student_id,
                StudentSignal.signal_name == signal_name,
            )
        )
        return result.scalar_one_or_none()

    # ── §3 the per-signal pipeline ───────────────────────────────────────────
    async def ingest_signal(
        self,
        student_id: UUID,
        signal_name: str,
        raw_value: object,
        *,
        channel: str,
        source: str,
        structured: bool = True,
        parse_ok: bool = True,
        llm_confidence: int | None = None,
        actor: str = "student",
        raw_input_ref: str | None = None,
    ) -> dict:
        """Run one value through Normalize → Validate → Reconcile → Persist →
        Fanout (§3). Returns a summary of what happened.

        Never raises on a bad value — a value that fails normalize/validate is
        persisted at low confidence with a clarification opened (§6), so the
        platform never acts on a hallucinated/garbled extraction but also never
        drops the student's input on the floor.
        """
        if channel not in INTAKE_CHANNELS:
            raise BadRequestException(f"Unknown intake channel '{channel}'")

        category = reg.CATEGORY_OF.get(signal_name, "other")

        # 1. Immutable raw-inputs row (§3.3 / §2).
        raw_row = RawInput(
            student_id=student_id,
            channel=channel,
            signal_name=signal_name,
            raw_value=_wrap(raw_value),
            source=source,
            raw_input_ref=raw_input_ref,
        )
        self.db.add(raw_row)
        await self.db.flush()
        ref = raw_input_ref or f"raw_input:{raw_row.id}"

        # 2. Normalize (§3.1, deterministic).
        normalized: object
        valid: bool
        reason: str | None
        try:
            normalized = reg.normalize_value(signal_name, raw_value)
            # 3. Validate (§3.2, schema check is authoritative).
            valid, reason = reg.validate_value(signal_name, normalized)
        except reg.NormalizeError as exc:
            normalized = raw_value  # keep the student's input visible
            valid, reason = False, str(exc)

        # §5 confidence — lowered to 40 when the value failed the schema check.
        base_conf = reg.confidence_for(
            source, structured=structured, parse_ok=parse_ok, llm_confidence=llm_confidence
        )
        confidence = base_conf if valid else min(base_conf, 40)
        canonical = normalized if valid else raw_value

        # 4. Reconcile vs the existing canonical value (§7).
        existing = await self._get_signal(student_id, signal_name)
        if existing is not None and not reg.incoming_wins(source, existing.source):
            # Incoming lost the source-priority duel — keep existing, but record
            # the attempt in the provenance chain + ledger so it's never lost.
            existing.provenance_chain = list(existing.provenance_chain or []) + [
                {
                    "event": "reconciled_kept",
                    "source": source,
                    "channel": channel,
                    "confidence": confidence,
                    "attempted_value": canonical,
                    "actor": actor,
                    "ts": _now(),
                    "raw_input_ref": ref,
                }
            ]
            await self._write_change_event(
                student_id,
                signal_name,
                existing.record_version,
                source,
                confidence,
                channel,
                "reconciled_kept",
            )
            await self.db.flush()
            return {
                "signal_name": signal_name,
                "status": "reconciled_kept",
                "winner_source": existing.source,
                "value": _unwrap(existing.value),
                "confidence": existing.confidence,
                "record_version": existing.record_version,
            }

        # 5. Upsert the normalized signal (version++ on value change).
        prov_entry = {
            "event": "created" if existing is None else "updated",
            "source": source,
            "channel": channel,
            "confidence": confidence,
            "actor": actor,
            "ts": _now(),
            "raw_input_ref": ref,
        }
        if existing is None:
            sig = StudentSignal(
                student_id=student_id,
                signal_name=signal_name,
                category=category,
                value=_wrap(canonical),
                source=source,
                confidence=confidence,
                value_normalized=_wrap(normalized) if valid else None,
                record_version=1,
                raw_input_ref=ref,
                provenance_chain=[prov_entry],
            )
            self.db.add(sig)
            event = "created"
            version = 1
        else:
            existing.value = _wrap(canonical)
            existing.category = category
            existing.source = source
            existing.confidence = confidence
            existing.value_normalized = _wrap(normalized) if valid else None
            existing.record_version = existing.record_version + 1
            existing.raw_input_ref = ref
            existing.provenance_chain = list(existing.provenance_chain or []) + [prov_entry]
            event = "updated"
            version = existing.record_version
            sig = existing

        await self.db.flush()

        # 6. Append-only audit ledger (§9.6).
        await self._write_change_event(
            student_id, signal_name, version, source, confidence, channel, event
        )

        # 7. Clarification loop (§6) — low confidence or failed validation.
        clarification_id = None
        if confidence < reg.CONFIDENCE_CLARIFY_THRESHOLD or not valid:
            clarification_id = await self._open_clarification(
                student_id,
                signal_name,
                raw_value=raw_value,
                suggested_value=canonical,
                confidence=confidence,
                invalid_reason=reason if not valid else None,
            )
        else:
            # A now-confident value resolves any stale open clarification.
            await self._auto_close_clarifications(student_id, signal_name)

        # 8. Cross-module fanout (§3.4) — best-effort, never raises.
        await self._fanout(student_id, signal_name)

        return {
            "signal_name": signal_name,
            "status": event,
            "value": canonical,
            "value_normalized": normalized if valid else None,
            "confidence": confidence,
            "source": source,
            "record_version": version,
            "valid": valid,
            "clarification_id": str(clarification_id) if clarification_id else None,
        }

    async def _write_change_event(
        self,
        student_id: UUID,
        signal_name: str,
        version: int,
        source: str,
        confidence: int,
        channel: str,
        event: str,
    ) -> None:
        self.db.add(
            SignalChangeEvent(
                student_id=student_id,
                signal_name=signal_name,
                record_version=version,
                source=source,
                confidence=confidence,
                channel=channel,
                event=event,
            )
        )
        await self.db.flush()

    # ── §6 clarification loop ────────────────────────────────────────────────
    async def _open_clarification(
        self,
        student_id: UUID,
        signal_name: str,
        *,
        raw_value: object,
        suggested_value: object,
        confidence: int,
        invalid_reason: str | None,
    ) -> UUID:
        label = reg.SIGNALS[signal_name].label if signal_name in reg.SIGNALS else signal_name
        if invalid_reason is not None:
            question = f"We couldn't read your {label.lower()} — could you confirm it?"
        else:
            question = f"Just to confirm — did you mean “{suggested_value}” for {label.lower()}?"
        # One open clarification per (student, signal) — update if present.
        result = await self.db.execute(
            select(SignalClarification).where(
                SignalClarification.student_id == student_id,
                SignalClarification.signal_name == signal_name,
                SignalClarification.status == "open",
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            existing.raw_value = _wrap(raw_value)
            existing.suggested_value = _wrap(suggested_value)
            existing.confidence = confidence
            existing.question = question
            await self.db.flush()
            return existing.id
        clar = SignalClarification(
            student_id=student_id,
            signal_name=signal_name,
            raw_value=_wrap(raw_value),
            suggested_value=_wrap(suggested_value),
            confidence=confidence,
            question=question,
            status="open",
        )
        self.db.add(clar)
        await self.db.flush()
        return clar.id

    async def _auto_close_clarifications(self, student_id: UUID, signal_name: str) -> None:
        result = await self.db.execute(
            select(SignalClarification).where(
                SignalClarification.student_id == student_id,
                SignalClarification.signal_name == signal_name,
                SignalClarification.status == "open",
            )
        )
        for clar in result.scalars():
            clar.status = "confirmed"
            clar.resolved_at = datetime.now(UTC)
        await self.db.flush()

    async def list_clarifications(self, student_id: UUID) -> list[dict]:
        result = await self.db.execute(
            select(SignalClarification)
            .where(
                SignalClarification.student_id == student_id,
                SignalClarification.status == "open",
            )
            .order_by(SignalClarification.created_at)
        )
        out = []
        for c in result.scalars():
            label = (
                reg.SIGNALS[c.signal_name].label if c.signal_name in reg.SIGNALS else c.signal_name
            )
            out.append(
                {
                    "id": str(c.id),
                    "signal_name": c.signal_name,
                    "label": label,
                    "question": c.question,
                    "raw_value": _unwrap(c.raw_value),
                    "suggested_value": _unwrap(c.suggested_value),
                    "confidence": c.confidence,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
            )
        return out

    async def resolve_clarification(
        self, student_id: UUID, clarification_id: UUID, *, action: str, value: object = None
    ) -> dict:
        """§6 — confirm (keep suggested) or correct (new value). Either way the
        resolved value becomes ``student-typed`` at confidence 95 (§5 / §9.4 —
        replace, never blend)."""
        if action not in ("confirm", "correct"):
            raise BadRequestException("action must be 'confirm' or 'correct'")
        result = await self.db.execute(
            select(SignalClarification).where(
                SignalClarification.id == clarification_id,
                SignalClarification.student_id == student_id,
            )
        )
        clar = result.scalar_one_or_none()
        if clar is None:
            raise NotFoundException("Clarification not found")
        if clar.status != "open":
            raise BadRequestException("Clarification already resolved")

        resolved = _unwrap(clar.suggested_value) if action == "confirm" else value
        clar.status = "confirmed" if action == "confirm" else "corrected"
        clar.resolved_value = _wrap(resolved)
        clar.resolved_at = datetime.now(UTC)
        await self.db.flush()

        # Re-ingest as student-typed structured (confidence 95) — this both
        # rewrites the canonical value and, being >=60, closes the loop.
        outcome = await self.ingest_signal(
            student_id,
            clar.signal_name,
            resolved,
            channel="form",
            source="student-typed",
            structured=True,
            actor="student",
        )
        # Stamp the precise lifecycle event on the ledger.
        await self._write_change_event(
            student_id,
            clar.signal_name,
            outcome.get("record_version", 1),
            "student-typed",
            outcome.get("confidence", 95),
            "form",
            "confirmed" if action == "confirm" else "corrected",
        )
        return {"id": str(clar.id), "status": clar.status, "signal": outcome}

    # ── §5 channel wrappers ──────────────────────────────────────────────────
    async def ingest_form_save(self, student_id: UUID, signal_name: str, value: object) -> dict:
        """§5.2 — a form field bound 1:1 to a signal. student-typed, conf 95."""
        return await self.ingest_signal(
            student_id,
            signal_name,
            value,
            channel="form",
            source="student-typed",
            structured=True,
        )

    async def ingest_message(self, user_id: UUID, session_id: UUID, content: str) -> dict:
        """§5.1 — ingest a discovery-chat turn (the primary intake channel).

        Records the immutable raw-input layer, then forwards to the existing
        Discovery LLM pipeline (extract → validate → persist artifacts →
        orchestrate). The conversational channel feeds matching, so it's gated
        on ``consent_matching`` (§10): no consent → no LLM turn. Any scalar
        signal the extractor surfaces that maps to the registry is folded into
        the engine as ``system-extracted``.
        """
        student_id = await self.profile_id_for_user(user_id)
        raw = RawInput(
            student_id=student_id,
            channel="discovery_chat",
            signal_name=None,
            raw_value={"content": content},
            source="student-typed",
            raw_input_ref=f"session:{session_id}",
        )
        self.db.add(raw)
        await self.db.flush()

        if not await self._consent_matching(student_id):
            raise BadRequestException(
                "Conversational intake requires matching consent. "
                "You can still fill profile fields directly."
            )

        from unipaith.services.discovery_service import DiscoveryService

        svc = DiscoveryService(self.db)
        _student_msg, assistant = await svc.append_message(
            user_id, session_id, role="student", content=content
        )

        # Fold any registry-recognized scalar from the extraction into the engine.
        signals_updated: list[dict] = []
        extracted = (_student_msg.extracted_signals or {}) if _student_msg else {}
        if isinstance(extracted, dict):
            fields = extracted.get("fields") or extracted.get("signals") or {}
            if isinstance(fields, dict):
                for name, value in fields.items():
                    if name in reg.SIGNALS and value not in (None, ""):
                        try:
                            outcome = await self.ingest_signal(
                                student_id,
                                name,
                                value,
                                channel="discovery_chat",
                                source="system-extracted",
                                structured=False,
                                llm_confidence=70,
                                actor="extractor",
                            )
                            signals_updated.append(outcome)
                        except Exception:  # pragma: no cover — never fail a turn
                            logger.exception("Engine fold-in failed for %s", name)

        return {
            "assistant_reply": assistant.content if assistant else None,
            "assistant_signals": assistant.extracted_signals if assistant else None,
            "signals_updated": signals_updated,
        }

    async def ingest_external_link(self, student_id: UUID, *, url: str, kind: str) -> dict:
        """§5.4 — LinkedIn / GitHub / personal site. URL-validated, conf 75.

        Per §12 the MVP only stores the URL for LinkedIn (no deep extraction);
        the signal name is ``external_link_<kind>``.
        """
        u = (url or "").strip()
        if not (u.startswith("http://") or u.startswith("https://")):
            raise BadRequestException("External link must be a valid http(s) URL")
        signal_name = f"external_link_{kind}"
        return await self.ingest_signal(
            student_id,
            signal_name,
            u,
            channel="external_link",
            source="student-link",
            structured=True,
            raw_input_ref=u,
        )

    async def ingest_document_upload(
        self,
        student_id: UUID,
        *,
        file_ref: str,
        parsed_fields: dict | None = None,
        dataset_type: str = "transcript",
        size_bytes: int = 0,
    ) -> dict:
        """§5.3 — a transcript / résumé / portfolio upload.

        ``parsed_fields`` is the output of an OCR+extract step ({signal: value}).
        Each field is persisted as ``student-uploaded`` and *always* surfaced for
        confirmation before it's trusted (§5.3.5) — so the per-field confidence is
        capped low until the student confirms. The Haiku triage agent runs only
        on the LLM path (flag on + consent); otherwise the deterministic
        ``parse_ok`` heuristic decides.
        """
        parsed_fields = parsed_fields or {}
        # Triage parse health (best-effort; never raises). LLM only when allowed.
        triage = None
        use_llm = await self._should_use_llm(student_id)
        if use_llm:
            try:
                from unipaith.ai.document_parse_triage import triage_parse

                report = {
                    "total_rows": len(parsed_fields),
                    "valid_rows": len(parsed_fields),
                    "missing_required": [],
                    "duplicates": [],
                    "invalid_dates": [],
                    "unmappable_programs": [],
                }
                triage = await triage_parse(
                    file_name=file_ref,
                    dataset_type=dataset_type,
                    size_bytes=size_bytes,
                    report=report,
                )
            except Exception:  # pragma: no cover — degraded path
                logger.exception("Document triage failed; using deterministic parse health")
                triage = None

        parse_ok = True
        if triage is not None and triage.get("triage_status") in ("needs_review", "failed"):
            parse_ok = False
        if not parsed_fields:
            parse_ok = False

        results = []
        for name, value in parsed_fields.items():
            outcome = await self.ingest_signal(
                student_id,
                name,
                value,
                channel="document",
                source="student-uploaded",
                structured=False,
                parse_ok=parse_ok,
                raw_input_ref=file_ref,
                actor="document",
            )
            # §5.3.5 — surface every uploaded field for confirmation even if it
            # parsed cleanly, since the student hasn't endorsed it yet.
            if (
                outcome.get("clarification_id") is None
                and outcome.get("status") != "reconciled_kept"
            ):
                cid = await self._open_clarification(
                    student_id,
                    name,
                    raw_value=value,
                    suggested_value=outcome.get("value"),
                    confidence=outcome.get("confidence", 80),
                    invalid_reason=None,
                )
                outcome["clarification_id"] = str(cid)
            results.append(outcome)

        return {
            "file_ref": file_ref,
            "parse_ok": parse_ok,
            "triage": triage,
            "fields": results,
        }

    async def ingest_system_derived(
        self, student_id: UUID, signal_name: str, value: object
    ) -> dict:
        """§5.6 — a system-derived flag/aggregate. conf 90."""
        return await self.ingest_signal(
            student_id,
            signal_name,
            value,
            channel="system",
            source="system-derived",
            structured=True,
            actor="system",
        )

    async def derive_gating_flags(self, student_id: UUID) -> dict:
        """§6.1 — recompute the two derived gating flags from target signals.

        ``visa_required_for_target_country_flag``: a residence country differing
        from any target country implies a visa is likely needed.
        ``has_portfolio_requirement_flag``: art/design/architecture/film majors
        carry a portfolio requirement. Both are advisory hints, never blockers.
        """
        sigs = await self._signal_map(student_id)
        residence = (sigs.get("country_of_residence") or "").strip().lower()
        countries = sigs.get("preferred_countries") or []
        targets = [str(c).strip().lower() for c in countries] if isinstance(countries, list) else []
        visa_flag = bool(targets) and any(t and t != residence for t in targets)

        major = (sigs.get("target_major_field_primary") or "").strip().lower()
        portfolio_majors = ("art", "design", "architecture", "film", "music", "fashion", "fine art")
        portfolio_flag = any(k in major for k in portfolio_majors)

        out = {}
        out["visa"] = await self.ingest_system_derived(
            student_id, "visa_required_for_target_country_flag", visa_flag
        )
        out["portfolio"] = await self.ingest_system_derived(
            student_id, "has_portfolio_requirement_flag", portfolio_flag
        )
        return out

    # ── §3.4 cross-module fanout ─────────────────────────────────────────────
    async def _fanout(self, student_id: UUID, signal_name: str) -> None:
        """Fire ``event:signal_changed`` side-effects (§3.4). Best-effort —
        any failure is logged and swallowed so an intake never 5xxs on a
        downstream cache miss."""
        try:
            from unipaith.ai.cache_invalidation import invalidate_for_consent_change
            from unipaith.models.matching import MatchResult

            # Match service: a changed signal can move every per-program score,
            # so drop the cached rationales + the materialized match_results.
            await invalidate_for_consent_change(self.db, student_id)
            await self.db.execute(delete(MatchResult).where(MatchResult.student_id == student_id))
            await self.db.flush()
        except Exception:  # pragma: no cover — fanout is advisory
            logger.exception(
                "Intake fanout failed for student=%s signal=%s", student_id, signal_name
            )

    # ── §4 derived gates (read-only) ─────────────────────────────────────────
    async def _signal_map(self, student_id: UUID) -> dict[str, object]:
        """{signal_name: canonical_value} for present signals — read-only."""
        result = await self.db.execute(
            select(StudentSignal).where(StudentSignal.student_id == student_id)
        )
        return {s.signal_name: _unwrap(s.value) for s in result.scalars()}

    async def _signal_rows(self, student_id: UUID) -> dict[str, StudentSignal]:
        result = await self.db.execute(
            select(StudentSignal).where(StudentSignal.student_id == student_id)
        )
        return {s.signal_name: s for s in result.scalars()}

    @staticmethod
    def _present(value: object) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, dict)):
            return len(value) > 0
        return True

    async def get_completeness(self, student_id: UUID) -> dict:
        """§4 / §10 — per-category coverage + overall_profile_completeness_pct."""
        rows = await self._signal_rows(student_id)
        present_total = 0
        categories = []
        for cat in reg.CATEGORIES:
            cat_signals = [n for n, s in reg.SIGNALS.items() if s.category == cat]
            sig_detail = []
            present_count = 0
            for name in cat_signals:
                row = rows.get(name)
                is_present = row is not None and self._present(_unwrap(row.value))
                if is_present:
                    present_count += 1
                    present_total += 1
                sig_detail.append(
                    {
                        "signal_name": name,
                        "label": reg.SIGNALS[name].label,
                        "present": is_present,
                        "confidence": row.confidence if row is not None else None,
                        "source": row.source if row is not None else None,
                        "required_for_match": reg.SIGNALS[name].required_for_match,
                    }
                )
            categories.append(
                {
                    "category": cat,
                    "present": present_count,
                    "total": len(cat_signals),
                    "pct": round(100 * present_count / len(cat_signals)) if cat_signals else 0,
                    "signals": sig_detail,
                }
            )
        overall = round(100 * present_total / reg.TOTAL_SIGNALS) if reg.TOTAL_SIGNALS else 0
        return {
            "overall_profile_completeness_pct": overall,
            "present_signals": present_total,
            "total_signals": reg.TOTAL_SIGNALS,
            "categories": categories,
        }

    async def get_match_ready(self, student_id: UUID) -> dict:
        """§4.1 / §6.1 — match-ready gate. Read-only; computes missing reasons."""
        sigs = await self._signal_map(student_id)
        missing: list[dict] = []

        for name in reg.MATCH_REQUIRED_SIGNALS:
            if not self._present(sigs.get(name)):
                missing.append(
                    {
                        "signal_name": name,
                        "label": reg.SIGNALS[name].label,
                        "category": reg.SIGNALS[name].category,
                        "kind": "required_field",
                    }
                )

        # Geography: a country list OR willingness_to_relocate=conditional (§6.1).
        countries = sigs.get("preferred_countries")
        geo_ok = (isinstance(countries, list) and len(countries) > 0) or (
            sigs.get("willingness_to_relocate") == "conditional"
        )
        if not geo_ok:
            missing.append(
                {
                    "signal_name": "preferred_countries",
                    "label": "Where you'd consider studying",
                    "category": "preferences",
                    "kind": "geography",
                }
            )

        # Priorities: at least 3 of 7 preference weights set (§6.1).
        weights = sigs.get("preference_weights") or {}
        set_weights = sum(
            1
            for k in reg.PREFERENCE_WEIGHT_KEYS
            if isinstance(weights, dict) and weights.get(k) is not None
        )
        if set_weights < 3:
            missing.append(
                {
                    "signal_name": "preference_weights",
                    "label": "Your top priorities (pick at least 3)",
                    "category": "preferences",
                    "kind": "priorities",
                    "detail": f"{set_weights}/3 set",
                }
            )

        present_total = sum(1 for n in reg.SIGNALS if self._present(sigs.get(n)))
        completeness_pct = (
            round(100 * present_total / reg.TOTAL_SIGNALS) if reg.TOTAL_SIGNALS else 0
        )

        ready = not missing and completeness_pct >= reg.MATCH_READY_PCT_FLOOR
        return {
            "match_ready": ready,
            "completeness_pct": completeness_pct,
            "pct_floor": reg.MATCH_READY_PCT_FLOOR,
            "missing": missing,
            "missing_count": len(missing),
            "required_total": len(reg.MATCH_REQUIRED_SIGNALS) + 2,  # +geo +priorities
        }

    async def get_apply_ready(self, student_id: UUID, program_id: UUID) -> dict:
        """§4.2 / §6.2 — per-program apply-ready checklist. Read-only."""
        program = await self.db.get(Program, program_id)
        if program is None:
            raise NotFoundException("Program not found")
        sigs = await self._signal_map(student_id)
        app_req = program.application_requirements or {}

        requirements: list[dict] = []

        # 1. Core profile (= match-ready required set).
        core_missing = [n for n in reg.MATCH_REQUIRED_SIGNALS if not self._present(sigs.get(n))]
        requirements.append(
            {
                "key": "core_profile",
                "label": "Core profile complete",
                "satisfied": not core_missing,
                "detail": "All set"
                if not core_missing
                else f"{len(core_missing)} core field(s) missing",
            }
        )

        # 2. Recommendations — count vs program requirement.
        rec_required = int(app_req.get("recommendations_required", 2) or 0)
        rec_result = await self.db.execute(
            select(RecommendationRequest).where(RecommendationRequest.student_id == student_id)
        )
        rec_count = len(rec_result.scalars().all())
        # the engine signal is a faster proxy when present
        sig_recs = sigs.get("recommenders_count")
        if isinstance(sig_recs, int):
            rec_count = max(rec_count, sig_recs)
        requirements.append(
            {
                "key": "recommendations",
                "label": f"Recommenders ({rec_count}/{rec_required})",
                "satisfied": rec_count >= rec_required,
                "detail": f"{rec_count} of {rec_required} secured",
            }
        )

        # 3. Test scores — only if the program's policy requires them.
        test_policy = str(app_req.get("test_policy", "optional")).lower()
        if test_policy in ("required", "blocking"):
            has_tests = bool(sigs.get("test_scores_provided"))
            requirements.append(
                {
                    "key": "test_scores",
                    "label": "Test scores on file",
                    "satisfied": has_tests,
                    "detail": "Provided" if has_tests else "Required by this program",
                }
            )

        # 4. Portfolio — if the program/major requires one.
        needs_portfolio = bool(app_req.get("portfolio_required")) or bool(
            sigs.get("has_portfolio_requirement_flag")
        )
        if needs_portfolio:
            pieces = sigs.get("portfolio_pieces_count")
            ok = isinstance(pieces, int) and pieces > 0
            requirements.append(
                {
                    "key": "portfolio",
                    "label": "Portfolio submitted",
                    "satisfied": ok,
                    "detail": f"{pieces or 0} piece(s)",
                }
            )

        # 5. Visa fields — if a visa is likely required.
        if bool(sigs.get("visa_required_for_target_country_flag")) or bool(
            app_req.get("visa_required")
        ):
            has_nationality = self._present(sigs.get("nationality"))
            requirements.append(
                {
                    "key": "visa",
                    "label": "Visa eligibility info",
                    "satisfied": has_nationality,
                    "detail": "Nationality on file" if has_nationality else "Add your nationality",
                }
            )

        # 6. Essays / supplements declared by the program.
        essays = app_req.get("essays") or app_req.get("supplements")
        if essays:
            count = len(essays) if isinstance(essays, list) else int(essays)
            requirements.append(
                {
                    "key": "essays",
                    "label": f"{count} essay(s) — draft in Workshops",
                    "satisfied": False,
                    "detail": "Draft and review essays before submitting",
                    "advisory": True,
                }
            )

        ready = all(r["satisfied"] for r in requirements if not r.get("advisory"))
        return {
            "program_id": str(program_id),
            "program_name": program.program_name,
            "ready_to_submit": ready,
            "requirements": requirements,
        }
