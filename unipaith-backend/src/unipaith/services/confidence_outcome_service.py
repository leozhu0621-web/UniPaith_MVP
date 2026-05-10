"""Phase D2 — outcome ingestion + calibrator retraining driver.

Two responsibilities:

  1. **Record outcomes.** Event hooks call `record_outcome(...)` when
     an Application is submitted, an OfferLetter is accepted, or an
     EnrollmentRecord is created. The service looks up the
     `MatchResult.confidence_score` the student actually saw at
     recommendation time and stamps it onto a new
     `confidence_outcome_pairs` row.

  2. **Refit the calibrator.** `refit_calibrator_from_outcomes(...)`
     reads recent pairs, calls `fit_calibrator(...)`, and saves the
     state via `services.ml_state.save_calibrator_state`. Returns the
     resulting `CalibratorState` so callers can surface "Fitted on N
     samples, ECE=...".

Cold-start contract
-------------------
- If no MatchResult exists for the (student, program), the recording
  is a no-op (logged at INFO). A student who applied to a program
  outside the recommendation surface has nothing to teach the
  calibrator.
- Below `MIN_PAIRS_FOR_CALIBRATION` (1k), `fit_calibrator` returns an
  unfitted state and the matcher falls through to identity. The refit
  driver is still safe to call.
"""

from __future__ import annotations

import datetime as _dt
import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.confidence_outcome import ConfidenceOutcomePair
from unipaith.models.matching import MatchResult
from unipaith.services.confidence_calibrator import (
    CalibratorState,
    fit_calibrator,
)
from unipaith.services.ml_state import save_calibrator_state

logger = logging.getLogger(__name__)


VALID_OUTCOME_KINDS = ("applied", "accepted", "enrolled", "aged_out")


# ── Record outcomes ────────────────────────────────────────────────────────


async def record_outcome(
    db: AsyncSession,
    *,
    student_id: UUID,
    program_id: UUID,
    outcome_kind: str,
    outcome: int = 1,
) -> ConfidenceOutcomePair | None:
    """Insert a (predicted_confidence, outcome) pair into the calibrator's
    training table.

    `predicted_confidence` is looked up from `match_results` — the
    confidence the student actually saw when the recommendation was
    surfaced. If no MatchResult exists (e.g. the student applied to a
    program outside the recommendation surface), returns None.

    Idempotency: this function does not check for duplicates. The event
    hooks fire on state transitions, so callers shouldn't double-fire,
    but a duplicate row is cheap and the calibrator deduplicates by
    treating each pair as a separate observation. If duplicate
    suppression becomes important, key on (student_id, program_id,
    outcome_kind).
    """
    if outcome_kind not in VALID_OUTCOME_KINDS:
        raise ValueError(
            f"outcome_kind={outcome_kind!r} not in {VALID_OUTCOME_KINDS}"
        )
    if outcome not in (0, 1):
        raise ValueError(f"outcome={outcome!r} must be 0 or 1")

    match = await db.scalar(
        select(MatchResult).where(
            MatchResult.student_id == student_id,
            MatchResult.program_id == program_id,
        )
    )
    if match is None:
        logger.info(
            "record_outcome: no MatchResult for student=%s program=%s; "
            "outcome=%s skipped (student applied outside the recommendation "
            "surface)",
            student_id,
            program_id,
            outcome_kind,
        )
        return None

    pair = ConfidenceOutcomePair(
        student_id=student_id,
        program_id=program_id,
        predicted_confidence=match.confidence_score,
        outcome=outcome,
        outcome_kind=outcome_kind,
        matched_at=getattr(match, "computed_at", None),
    )
    db.add(pair)
    await db.flush()
    return pair


# ── Backfill negatives ─────────────────────────────────────────────────────


async def backfill_aged_out_negatives(
    db: AsyncSession,
    *,
    age_days: int = 90,
) -> int:
    """Stamp outcome=0 (`aged_out`) onto MatchResult rows older than
    `age_days` that have no positive outcome on record.

    The calibrator needs both 0s and 1s to fit a meaningful curve;
    without negatives the isotonic regression collapses to a
    constant. This is the simple backfill that lets D2 ship without
    a streaming-decisioning surface.

    Returns the number of rows inserted.
    """
    cutoff = _dt.datetime.now(_dt.UTC) - _dt.timedelta(days=age_days)

    # Read every aged-out match.
    matches = list(
        (
            await db.execute(
                select(MatchResult).where(MatchResult.computed_at <= cutoff)
            )
        )
        .scalars()
        .all()
    )
    if not matches:
        return 0

    # Read every (student, program) pair that already has an outcome of
    # any kind. We deduplicate against this set so re-running backfill
    # is idempotent and doesn't overwrite positive history.
    existing_rows = await db.execute(
        select(
            ConfidenceOutcomePair.student_id,
            ConfidenceOutcomePair.program_id,
        ).distinct()
    )
    existing: set[tuple] = {(s, p) for s, p in existing_rows.all()}

    inserted = 0
    for m in matches:
        if (m.student_id, m.program_id) in existing:
            continue
        db.add(
            ConfidenceOutcomePair(
                student_id=m.student_id,
                program_id=m.program_id,
                predicted_confidence=m.confidence_score,
                outcome=0,
                outcome_kind="aged_out",
                matched_at=m.computed_at,
            )
        )
        inserted += 1
    if inserted:
        await db.flush()
    return inserted


# ── Load pairs + refit ─────────────────────────────────────────────────────


async def load_pairs_for_calibrator(
    db: AsyncSession,
    *,
    outcome_kind: str | None = None,
    window_days: int | None = None,
) -> list[tuple[float, int]]:
    """Read pairs ready for `fit_calibrator`.

    - `outcome_kind=None` includes every kind (the default).
    - Pass a specific kind (e.g. `"enrolled"`) to calibrate against
      that signal. Each kind has different semantics; the operator
      decides which one the calibrated confidence should mean.
    - `window_days` filters by `created_at >= now - window_days`.
    """
    stmt = select(
        ConfidenceOutcomePair.predicted_confidence,
        ConfidenceOutcomePair.outcome,
    )
    if outcome_kind is not None:
        stmt = stmt.where(ConfidenceOutcomePair.outcome_kind == outcome_kind)
    if window_days is not None:
        since = _dt.datetime.now(_dt.UTC) - _dt.timedelta(days=window_days)
        stmt = stmt.where(ConfidenceOutcomePair.created_at >= since)
    result = await db.execute(stmt)
    return [(float(p), int(o)) for p, o in result.all()]


async def refit_calibrator_from_outcomes(
    db: AsyncSession,
    *,
    outcome_kind: str | None = None,
    window_days: int | None = None,
) -> CalibratorState:
    """Run the full retrain loop: load → fit → save → return.

    Used by the manual admin endpoint and by a future scheduled job.
    Below MIN_PAIRS_FOR_CALIBRATION the saved state stays unfitted,
    which the matcher already handles as identity.
    """
    pairs = await load_pairs_for_calibrator(
        db, outcome_kind=outcome_kind, window_days=window_days
    )
    state = fit_calibrator(pairs)
    await save_calibrator_state(db, state)
    logger.info(
        "refit_calibrator_from_outcomes: pairs=%d fitted=%s n_samples=%d",
        len(pairs),
        state.fitted,
        state.n_samples,
    )
    return state


# ── Convenience predicted-confidence helper (used by tests) ───────────────


async def lookup_predicted_confidence(
    db: AsyncSession, *, student_id: UUID, program_id: UUID
) -> Decimal | None:
    """Read the confidence the student saw for this match, or None when
    there isn't one yet."""
    m = await db.scalar(
        select(MatchResult).where(
            MatchResult.student_id == student_id,
            MatchResult.program_id == program_id,
        )
    )
    return m.confidence_score if m is not None else None
