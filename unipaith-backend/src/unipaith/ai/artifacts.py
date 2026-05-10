"""Phase A2 — Artifact writer.

Translates `ExtractedSignals` (the LLM's structured output) into rows in:

  - student_goals (#113)
  - student_needs (#113)
  - student_identity (#113)  — single-row JSONB upsert
  - discovery_messages.extracted_signals — audit trail (the *full* extractor
    JSON, including basic-layer fields A2 keeps un-typed for now)

Basic-layer fields (age, education_level, gpa, test_scores, location_prefs,
first_gen) intentionally stay in the JSONB audit trail in A2. A future
"finalize discovery" action will write them to StudentProfile + AcademicRecord
once the student confirms.

Mappings between LLM JSON and DB rows
-------------------------------------
Goals:
  category           ↔ category
  specific           ↔ specific
  measurable         ↔ measurable
  achievable         ↔ achievable_notes
  relevant           ↔ relevant_notes
  time_bound (str)   → parsed Date OR None  (best-effort YYYY[-MM[-DD]])
  completeness < 1   → row dropped (a partial SMART goal is not committed)

Needs:
  maslow_level       ↔ maslow_level
  signal (tag)       ↔ need_type   (controlled vocab)
  free_text          ↔ signal      (description)
  severity (1-5 int) → mapped:
                         5,4 → 'must_have'
                         3   → 'strong_preference'
                         2,1 → 'nice_to_have'
  evidence           ↔ source_quote

Identity:
  facet='value'           → core_values:    [{value, evidence, confidence, source_quote}]
  facet='belief' or 'view'→ worldview:      [{belief, context, confidence, source_quote}]
  facet='self_awareness'  → self_awareness: [{insight, trigger_event, confidence, source_quote}]
  Append-only with simple in-row dedup on (kind, claim).

All discovery-sourced rows carry `source='discovery'` and
`source_session_id=<session_id>`, satisfying the provenance CHECK constraints
on those tables.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.extractor import ExtractedSignals
from unipaith.ai.state import (
    GoalEntry,
    IdentityClaim,
    NeedEntry,
    PersonalityEntry,
    StudentSnapshot,
)
from unipaith.models.goals import StudentGoal
from unipaith.models.identity import StudentIdentity
from unipaith.models.needs import StudentNeed

# ── Mapping helpers ─────────────────────────────────────────────────────────


_SEVERITY_INT_TO_ENUM = {
    5: "must_have",
    4: "must_have",
    3: "strong_preference",
    2: "nice_to_have",
    1: "nice_to_have",
}


def _severity_to_enum(value: Any) -> str:
    """Normalize extractor's int severity to the DB's string enum.

    Defaults to 'strong_preference' on missing / out-of-range — the middle
    bucket avoids both over-counting and silently dropping the signal.
    """
    if isinstance(value, str) and value in {"must_have", "strong_preference", "nice_to_have"}:
        return value
    if isinstance(value, int | float):
        return _SEVERITY_INT_TO_ENUM.get(int(value), "strong_preference")
    return "strong_preference"


_DATE_RE = re.compile(r"^(\d{4})(?:-(\d{1,2})(?:-(\d{1,2}))?)?")


def _parse_time_bound(raw: Any) -> date | None:
    """Best-effort parse of free-text time-bound fields into a Date.

    Accepts 'YYYY', 'YYYY-MM', 'YYYY-MM-DD'. Anything else returns None
    (the column is nullable; we don't fabricate dates from prose).
    """
    if not isinstance(raw, str):
        return None
    m = _DATE_RE.match(raw.strip())
    if not m:
        return None
    y = int(m.group(1))
    mo = int(m.group(2) or 1)
    d = int(m.group(3) or 1)
    try:
        return date(y, mo, d)
    except ValueError:
        return None


# ── Identity dedup keys ────────────────────────────────────────────────────


def _identity_dedup_key(d: dict[str, Any], primary_field: str) -> tuple[str, str]:
    """Stable key for de-duplicating identity entries within an array.

    Uses (primary_field, evidence-or-source_quote-prefix). The 80-char
    prefix is a coarse but effective fingerprint — distinct claims rarely
    share the same first 80 chars of their primary field AND quote.
    """
    return (
        (d.get(primary_field) or "").strip().lower()[:80],
        (d.get("source_quote") or d.get("evidence") or "").strip().lower()[:80],
    )


# ── Public API ──────────────────────────────────────────────────────────────


@dataclass
class WriteResult:
    """Counts of what was persisted, for logging + assertions in tests."""

    goals_written: int = 0
    needs_written: int = 0
    identity_values_added: int = 0
    identity_worldview_added: int = 0
    identity_self_awareness_added: int = 0
    skipped_partial_goals: int = 0
    skipped_low_confidence: int = 0


async def persist_extraction(
    *,
    db: AsyncSession,
    student_id: UUID,
    session_id: UUID,
    extraction: ExtractedSignals,
) -> WriteResult:
    """Write goals + needs + identity rows from a single turn's extraction.

    Caller is responsible for committing the surrounding transaction. This
    function only adds objects to the session and flushes; the discovery
    service drives commit.
    """
    result = WriteResult()

    # Goals — only commit completeness == 1.0; partials stay in the audit
    # trail until the student fills them in via follow-up turns.
    for g in extraction.goals or []:
        completeness = g.get("completeness", 0)
        try:
            completeness = float(completeness)
        except (TypeError, ValueError):
            completeness = 0
        if completeness < 1.0:
            result.skipped_partial_goals += 1
            continue
        if not g.get("specific"):
            result.skipped_partial_goals += 1
            continue
        category = g.get("category")
        if category not in {"academic", "social", "personal"}:
            continue
        confidence = (
            extraction.confidence_per_key.get("goals")
            if "goals" in extraction.confidence_per_key
            else None
        )
        db.add(
            StudentGoal(
                student_id=student_id,
                category=category,
                specific=g["specific"],
                measurable=g.get("measurable"),
                achievable_notes=g.get("achievable"),
                relevant_notes=g.get("relevant"),
                time_bound=_parse_time_bound(g.get("time_bound")),
                status="active",
                source="discovery",
                source_session_id=session_id,
                confidence=confidence,
            )
        )
        result.goals_written += 1

    # Needs — drop only on missing required fields; LLM is allowed to
    # express severity nuance via the int 1–5 scale.
    for n in extraction.needs or []:
        signal_tag = n.get("signal")
        free_text = n.get("free_text") or n.get("evidence") or ""
        maslow_level = n.get("maslow_level")
        if not signal_tag or not maslow_level:
            continue
        if maslow_level not in {
            "physiological",
            "safety",
            "social",
            "self_esteem",
            "self_actualization",
        }:
            continue
        confidence = (
            extraction.confidence_per_key.get("needs")
            if "needs" in extraction.confidence_per_key
            else None
        )
        db.add(
            StudentNeed(
                student_id=student_id,
                maslow_level=maslow_level,
                need_type=signal_tag,
                signal=free_text or signal_tag,
                severity=_severity_to_enum(n.get("severity")),
                source="discovery",
                source_session_id=session_id,
                source_quote=n.get("evidence"),
                confidence=confidence,
            )
        )
        result.needs_written += 1

    # Identity — single-row upsert with append-and-dedup against existing JSONB.
    if extraction.identity:
        await _upsert_identity(
            db=db,
            student_id=student_id,
            session_id=session_id,
            identity_items=extraction.identity,
            confidence=extraction.confidence_per_key.get("identity"),
            result=result,
        )

    await db.flush()
    return result


# ── Identity upsert internals ───────────────────────────────────────────────


async def _upsert_identity(
    *,
    db: AsyncSession,
    student_id: UUID,
    session_id: UUID,
    identity_items: list[dict[str, Any]],
    confidence: Decimal | None,
    result: WriteResult,
) -> None:
    row = await db.scalar(select(StudentIdentity).where(StudentIdentity.student_id == student_id))
    if row is None:
        row = StudentIdentity(
            student_id=student_id,
            core_values=[],
            worldview=[],
            self_awareness=[],
        )
        db.add(row)

    # SQLAlchemy JSONB doesn't track in-place mutations reliably; rebuild
    # each list and reassign so the update is detected.
    core_values = list(row.core_values or [])
    worldview = list(row.worldview or [])
    self_awareness = list(row.self_awareness or [])

    cv_keys = {_identity_dedup_key(d, "value") for d in core_values}
    wv_keys = {_identity_dedup_key(d, "belief") for d in worldview}
    sa_keys = {_identity_dedup_key(d, "insight") for d in self_awareness}

    conf_str = str(confidence) if confidence is not None else None

    for item in identity_items:
        facet = item.get("facet")
        claim = item.get("claim")
        evidence = item.get("evidence") or ""
        if not claim:
            continue

        if facet == "value":
            entry = {
                "value": claim,
                "evidence": evidence,
                "confidence": conf_str,
                "source_quote": evidence,
            }
            key = _identity_dedup_key({"value": claim, "source_quote": evidence}, "value")
            if key not in cv_keys:
                core_values.append(entry)
                cv_keys.add(key)
                result.identity_values_added += 1
        elif facet in {"belief", "view"}:
            entry = {
                "belief": claim,
                "context": evidence,
                "confidence": conf_str,
                "source_quote": evidence,
            }
            key = _identity_dedup_key({"belief": claim, "source_quote": evidence}, "belief")
            if key not in wv_keys:
                worldview.append(entry)
                wv_keys.add(key)
                result.identity_worldview_added += 1
        elif facet == "self_awareness":
            entry = {
                "insight": claim,
                "trigger_event": evidence,
                "confidence": conf_str,
                "source_quote": evidence,
            }
            key = _identity_dedup_key({"insight": claim, "source_quote": evidence}, "insight")
            if key not in sa_keys:
                self_awareness.append(entry)
                sa_keys.add(key)
                result.identity_self_awareness_added += 1

    row.core_values = core_values
    row.worldview = worldview
    row.self_awareness = self_awareness
    row.last_session_id = session_id


# ── Snapshot reconstruction (used by the validator) ─────────────────────────


def snapshot_from_extracted_signals_history(
    extracted_signals: list[dict[str, Any] | None],
) -> StudentSnapshot:
    """Walk the session's accumulated extractions and build a StudentSnapshot.

    Newest-wins for scalars (the student's most recent answer is the
    truth); lists union with dedup. This is what the validator reads each
    turn for the BASIC layer.
    """
    snap = StudentSnapshot()

    # Iterate in chronological order; later turns overwrite earlier scalars.
    for raw in extracted_signals:
        if not isinstance(raw, dict):
            continue
        basic = raw.get("basic") or {}

        if basic.get("age") is not None:
            try:
                snap.age = int(basic["age"])
            except (TypeError, ValueError):
                pass
        if basic.get("education_level"):
            snap.education_level = str(basic["education_level"])
        if basic.get("gpa") is not None:
            try:
                snap.gpa = float(basic["gpa"])
            except (TypeError, ValueError):
                pass
        if basic.get("test_scores"):
            for ts in basic["test_scores"]:
                if isinstance(ts, dict) and "type" in ts and "score" in ts:
                    # Dedup on type — newer overrides older.
                    snap.test_scores = [x for x in snap.test_scores if x.get("type") != ts["type"]]
                    snap.test_scores.append({"type": str(ts["type"]), "score": float(ts["score"])})
        for key in ("location_prefs", "location_avoid"):
            vals = basic.get(key) or []
            if isinstance(vals, list):
                merged = list(getattr(snap, key))
                for v in vals:
                    if v not in merged:
                        merged.append(str(v))
                setattr(snap, key, merged)
        if basic.get("first_gen") is not None:
            snap.first_gen = bool(basic["first_gen"])
        if basic.get("income_band"):
            snap.income_band = str(basic["income_band"])
        if basic.get("gender"):
            snap.gender = str(basic["gender"])

        # PERSONALITY (Phase A3) — append + dedup by (facet, value).
        for p in raw.get("personality") or []:
            if not isinstance(p, dict):
                continue
            facet = p.get("facet")
            value = p.get("value")
            evidence = p.get("evidence") or ""
            if not facet or not value:
                continue
            key = (str(facet), str(value).strip().lower()[:120])
            if any(
                (e.facet, e.value.strip().lower()[:120]) == key for e in snap.personality
            ):
                continue
            snap.personality.append(
                PersonalityEntry(
                    facet=str(facet),
                    value=str(value),
                    evidence=str(evidence),
                )
            )

        # IDENTITY (Phase A3) — append + dedup by (facet, claim, evidence prefix).
        for c in raw.get("identity") or []:
            if not isinstance(c, dict):
                continue
            facet = c.get("facet")
            claim = c.get("claim")
            evidence = c.get("evidence") or ""
            if not facet or not claim:
                continue
            key = (
                str(facet),
                str(claim).strip().lower()[:120],
                str(evidence).strip().lower()[:80],
            )
            if any(
                (
                    e.facet,
                    e.claim.strip().lower()[:120],
                    e.evidence.strip().lower()[:80],
                )
                == key
                for e in snap.identity_claims
            ):
                continue
            snap.identity_claims.append(
                IdentityClaim(
                    facet=str(facet),
                    claim=str(claim),
                    evidence=str(evidence),
                    user_confirmed=bool(c.get("user_confirmed", False)),
                )
            )

        # GOALS (Phase A3.2) — append + dedup by (category, specific prefix).
        for g in raw.get("goals") or []:
            if not isinstance(g, dict):
                continue
            category = g.get("category")
            specific = g.get("specific")
            if category not in {"academic", "social", "personal"} or not specific:
                continue
            try:
                completeness = float(g.get("completeness", 0))
            except (TypeError, ValueError):
                completeness = 0.0
            key = (str(category), str(specific).strip().lower()[:120])
            existing_idx = next(
                (
                    i
                    for i, e in enumerate(snap.goals)
                    if (e.category, e.specific.strip().lower()[:120]) == key
                ),
                None,
            )
            entry = GoalEntry(
                category=str(category),
                specific=str(specific),
                measurable=g.get("measurable") or None,
                achievable=g.get("achievable") or None,
                relevant=g.get("relevant") or None,
                time_bound=g.get("time_bound") or None,
                completeness=max(0.0, min(1.0, completeness)),
                user_confirmed=bool(g.get("user_confirmed", False)),
            )
            if existing_idx is not None:
                # Newer turn refines an earlier draft — keep the higher
                # completeness, OR-merge user_confirmed.
                prev = snap.goals[existing_idx]
                if entry.completeness >= prev.completeness:
                    entry.user_confirmed = entry.user_confirmed or prev.user_confirmed
                    snap.goals[existing_idx] = entry
                else:
                    prev.user_confirmed = prev.user_confirmed or entry.user_confirmed
            else:
                snap.goals.append(entry)

        # NEEDS (Phase A3.2) — append + dedup by (maslow_level, signal).
        for n in raw.get("needs") or []:
            if not isinstance(n, dict):
                continue
            level = n.get("maslow_level")
            tag = n.get("signal")
            if level not in {
                "physiological",
                "safety",
                "social",
                "self_esteem",
                "self_actualization",
            }:
                continue
            if not tag:
                continue
            severity = n.get("severity")
            try:
                severity_int = int(severity) if severity is not None else None
            except (TypeError, ValueError):
                severity_int = None
            key = (str(level), str(tag).strip().lower()[:80])
            if any(
                (e.maslow_level, e.signal.strip().lower()[:80]) == key for e in snap.needs
            ):
                continue
            snap.needs.append(
                NeedEntry(
                    maslow_level=str(level),
                    signal=str(tag),
                    free_text=str(n.get("free_text") or ""),
                    severity=severity_int,
                    evidence=str(n.get("evidence") or ""),
                    user_confirmed=bool(n.get("user_confirmed", False)),
                )
            )

    return snap
