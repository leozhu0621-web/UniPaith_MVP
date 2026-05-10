"""Phase D2 — outcome ingestion + calibrator refit driver.

Verifies the D2 training-data pipeline end-to-end:
- record_outcome inserts pairs with the right predicted_confidence
- load_pairs_for_calibrator filters by kind/window
- backfill_aged_out_negatives stamps 0-outcomes on stale matches
- refit_calibrator_from_outcomes saves a CalibratorState
- The application/offer/enrollment event hooks fire recording calls

Uses the real DB so the ai_turns + match_results + confidence_outcome
joins are exercised end-to-end.
"""

from __future__ import annotations

import datetime as _dt
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.application import (
    Application,
    EnrollmentRecord,
    OfferLetter,
)
from unipaith.models.confidence_outcome import ConfidenceOutcomePair
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.services.confidence_outcome_service import (
    VALID_OUTCOME_KINDS,
    backfill_aged_out_negatives,
    load_pairs_for_calibrator,
    record_outcome,
    refit_calibrator_from_outcomes,
)
from unipaith.services.event_hooks import (
    on_application_submitted,
    on_enrollment_confirmed,
    on_offer_responded,
)
from unipaith.services.ml_state import load_calibrator_state

# ── Fixtures ───────────────────────────────────────────────────────────────


async def _seed_student(db: AsyncSession) -> StudentProfile:
    user = User(
        id=uuid4(),
        email=f"d2-{uuid4().hex[:6]}@example.com",
        cognito_sub=f"dev-sub-{uuid4().hex[:8]}",
        role=UserRole.student,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    profile = StudentProfile(user_id=user.id)
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def _seed_program(db: AsyncSession) -> Program:
    admin = User(
        id=uuid4(),
        email=f"inst-{uuid4().hex[:6]}@example.com",
        cognito_sub=f"dev-sub-{uuid4().hex[:8]}",
        role=UserRole.institution_admin,
        is_active=True,
    )
    db.add(admin)
    await db.flush()
    inst = Institution(
        admin_user_id=admin.id,
        name="D2U",
        type="university",
        country="US",
    )
    db.add(inst)
    await db.flush()
    p = Program(
        institution_id=inst.id,
        program_name="D2 Test Program",
        degree_type="masters",
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


async def _seed_match(
    db: AsyncSession,
    student_id,
    program_id,
    *,
    confidence: str = "0.75",
) -> MatchResult:
    m = MatchResult(
        student_id=student_id,
        program_id=program_id,
        fitness_score=Decimal("0.80"),
        confidence_score=Decimal(confidence),
        fitness_breakdown={"cosine": 0.7},
        confidence_breakdown={"profile_completeness": 0.85},
    )
    db.add(m)
    await db.commit()
    await db.refresh(m)
    return m


# ── record_outcome ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_record_outcome_inserts_with_matchresult_confidence(
    db_session: AsyncSession,
):
    student = await _seed_student(db_session)
    program = await _seed_program(db_session)
    await _seed_match(db_session, student.id, program.id, confidence="0.83")

    pair = await record_outcome(
        db_session,
        student_id=student.id,
        program_id=program.id,
        outcome_kind="applied",
    )
    await db_session.commit()
    assert pair is not None
    assert pair.outcome == 1
    assert pair.outcome_kind == "applied"
    assert pair.predicted_confidence == Decimal("0.8300")


@pytest.mark.asyncio
async def test_record_outcome_returns_none_when_no_match(
    db_session: AsyncSession,
):
    """A student who applies to a program outside the recommendation
    surface has no MatchResult — recording is a no-op."""
    student = await _seed_student(db_session)
    program = await _seed_program(db_session)
    # No match seeded.
    pair = await record_outcome(
        db_session,
        student_id=student.id,
        program_id=program.id,
        outcome_kind="applied",
    )
    assert pair is None


@pytest.mark.asyncio
async def test_record_outcome_rejects_unknown_kind(
    db_session: AsyncSession,
):
    student = await _seed_student(db_session)
    program = await _seed_program(db_session)
    with pytest.raises(ValueError):
        await record_outcome(
            db_session,
            student_id=student.id,
            program_id=program.id,
            outcome_kind="invented_kind",
        )


@pytest.mark.asyncio
async def test_record_outcome_rejects_bad_outcome_value(
    db_session: AsyncSession,
):
    student = await _seed_student(db_session)
    program = await _seed_program(db_session)
    with pytest.raises(ValueError):
        await record_outcome(
            db_session,
            student_id=student.id,
            program_id=program.id,
            outcome_kind="applied",
            outcome=2,
        )


def test_valid_outcome_kinds_match_check_constraint() -> None:
    """The Python whitelist must mirror the DB CHECK constraint or
    `record_outcome` will let through values the DB rejects."""
    assert set(VALID_OUTCOME_KINDS) == {"applied", "accepted", "enrolled", "aged_out"}


# ── load_pairs_for_calibrator ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_load_pairs_filters_by_kind(db_session: AsyncSession):
    student = await _seed_student(db_session)
    program = await _seed_program(db_session)
    await _seed_match(db_session, student.id, program.id, confidence="0.70")
    await record_outcome(
        db_session, student_id=student.id, program_id=program.id, outcome_kind="applied"
    )
    await record_outcome(
        db_session, student_id=student.id, program_id=program.id, outcome_kind="enrolled"
    )
    await db_session.commit()

    applied = await load_pairs_for_calibrator(db_session, outcome_kind="applied")
    enrolled = await load_pairs_for_calibrator(db_session, outcome_kind="enrolled")
    all_pairs = await load_pairs_for_calibrator(db_session)
    assert len(applied) == 1
    assert len(enrolled) == 1
    assert len(all_pairs) == 2


@pytest.mark.asyncio
async def test_load_pairs_respects_window(db_session: AsyncSession):
    from sqlalchemy import update as _update

    student = await _seed_student(db_session)
    program = await _seed_program(db_session)
    await _seed_match(db_session, student.id, program.id, confidence="0.70")
    pair = await record_outcome(
        db_session, student_id=student.id, program_id=program.id, outcome_kind="applied"
    )
    await db_session.commit()
    # Back-date the row via raw UPDATE — ORM assignment fights the
    # server_default on created_at.
    await db_session.execute(
        _update(ConfidenceOutcomePair)
        .where(ConfidenceOutcomePair.id == pair.id)
        .values(created_at=_dt.datetime.now(_dt.UTC) - _dt.timedelta(days=30))
    )
    await db_session.commit()

    pairs_7d = await load_pairs_for_calibrator(db_session, window_days=7)
    pairs_60d = await load_pairs_for_calibrator(db_session, window_days=60)
    assert pairs_7d == []
    assert len(pairs_60d) == 1


# ── backfill_aged_out_negatives ───────────────────────────────────────────


async def _backdate_match(db: AsyncSession, match_id, days: int) -> None:
    """Push computed_at into the past via raw UPDATE — ORM attribute
    reassignment doesn't always win against `server_default=now()`."""
    from sqlalchemy import update as _update

    await db.execute(
        _update(MatchResult)
        .where(MatchResult.id == match_id)
        .values(computed_at=_dt.datetime.now(_dt.UTC) - _dt.timedelta(days=days))
    )
    await db.commit()


@pytest.mark.asyncio
async def test_backfill_stamps_aged_out_negatives(db_session: AsyncSession):
    """MatchResults older than `age_days` with no existing outcome get
    a 0-outcome `aged_out` stamp."""
    student = await _seed_student(db_session)
    program = await _seed_program(db_session)
    m = await _seed_match(db_session, student.id, program.id)
    await _backdate_match(db_session, m.id, days=120)

    inserted = await backfill_aged_out_negatives(db_session, age_days=90)
    await db_session.commit()
    assert inserted == 1

    pairs = await load_pairs_for_calibrator(db_session, outcome_kind="aged_out")
    assert len(pairs) == 1
    assert pairs[0][1] == 0


@pytest.mark.asyncio
async def test_backfill_skips_when_outcome_already_exists(
    db_session: AsyncSession,
):
    """Re-running backfill on a (student, program) that already has any
    outcome row should be a no-op for that pair."""
    student = await _seed_student(db_session)
    program = await _seed_program(db_session)
    m = await _seed_match(db_session, student.id, program.id)
    await _backdate_match(db_session, m.id, days=120)
    await record_outcome(
        db_session, student_id=student.id, program_id=program.id, outcome_kind="applied"
    )
    await db_session.commit()

    inserted = await backfill_aged_out_negatives(db_session, age_days=90)
    assert inserted == 0


# ── refit driver ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_refit_below_minimum_saves_unfitted_state(
    db_session: AsyncSession,
):
    student = await _seed_student(db_session)
    program = await _seed_program(db_session)
    await _seed_match(db_session, student.id, program.id, confidence="0.70")
    await record_outcome(
        db_session, student_id=student.id, program_id=program.id, outcome_kind="applied"
    )
    await db_session.commit()

    state = await refit_calibrator_from_outcomes(db_session)
    await db_session.commit()
    assert state.fitted is False
    assert state.n_samples == 1
    # The cold-start state was saved to model_registry.
    loaded = await load_calibrator_state(db_session)
    assert loaded.fitted is False


# ── Event hook integration ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_on_application_submitted_records_applied_outcome(
    db_session: AsyncSession,
):
    student = await _seed_student(db_session)
    program = await _seed_program(db_session)
    await _seed_match(db_session, student.id, program.id, confidence="0.66")
    app = Application(
        student_id=student.id,
        program_id=program.id,
        status="submitted",
    )
    db_session.add(app)
    await db_session.commit()
    await db_session.refresh(app)

    # The hook fans out to notification + CRM (which require the real
    # institution row) plus the D2 outcome recorder. Resolve the actual
    # student-user + the institution that owns the program so the FK
    # constraints on touchpoints are satisfied — otherwise the parent
    # try/except swallows the recording too.
    student_user = await db_session.scalar(
        select(User).where(User.id == student.user_id)
    )
    program_row = await db_session.scalar(
        select(Program).where(Program.id == program.id)
    )
    inst = await db_session.scalar(
        select(Institution).where(Institution.id == program_row.institution_id)
    )
    assert student_user is not None and inst is not None
    await on_application_submitted(
        db_session,
        student_id=student.id,
        student_user_id=student_user.id,
        application_id=app.id,
        program_id=program.id,
        institution_id=inst.id,
        admin_user_id=inst.admin_user_id,
        confirmation_number="TEST-001",
    )
    await db_session.commit()

    pair = await db_session.scalar(
        select(ConfidenceOutcomePair).where(
            ConfidenceOutcomePair.student_id == student.id,
            ConfidenceOutcomePair.program_id == program.id,
        )
    )
    assert pair is not None
    assert pair.outcome_kind == "applied"
    assert pair.predicted_confidence == Decimal("0.6600")


@pytest.mark.asyncio
async def test_on_offer_responded_records_accepted_only(
    db_session: AsyncSession,
):
    student = await _seed_student(db_session)
    program = await _seed_program(db_session)
    await _seed_match(db_session, student.id, program.id, confidence="0.55")
    app = Application(student_id=student.id, program_id=program.id, status="submitted")
    db_session.add(app)
    await db_session.commit()
    await db_session.refresh(app)
    offer = OfferLetter(
        application_id=app.id,
        offer_type="standard",
        status="active",
        student_response="accepted",
    )
    db_session.add(offer)
    await db_session.commit()
    await db_session.refresh(offer)

    await on_offer_responded(db_session, application_id=app.id, offer_id=offer.id)
    await db_session.commit()

    pair = await db_session.scalar(
        select(ConfidenceOutcomePair).where(
            ConfidenceOutcomePair.student_id == student.id,
            ConfidenceOutcomePair.program_id == program.id,
        )
    )
    assert pair is not None
    assert pair.outcome_kind == "accepted"


@pytest.mark.asyncio
async def test_on_offer_responded_skips_declined(
    db_session: AsyncSession,
):
    """A declined offer doesn't strictly mean the prediction was wrong
    (the student may have multiple offers). We don't record it as
    accepted."""
    student = await _seed_student(db_session)
    program = await _seed_program(db_session)
    await _seed_match(db_session, student.id, program.id)
    app = Application(student_id=student.id, program_id=program.id, status="submitted")
    db_session.add(app)
    await db_session.commit()
    await db_session.refresh(app)
    offer = OfferLetter(
        application_id=app.id,
        offer_type="standard",
        student_response="declined",
    )
    db_session.add(offer)
    await db_session.commit()
    await db_session.refresh(offer)

    await on_offer_responded(db_session, application_id=app.id, offer_id=offer.id)
    await db_session.commit()

    pair = await db_session.scalar(
        select(ConfidenceOutcomePair).where(
            ConfidenceOutcomePair.student_id == student.id,
        )
    )
    assert pair is None


@pytest.mark.asyncio
async def test_on_enrollment_confirmed_records_enrolled_outcome(
    db_session: AsyncSession,
):
    student = await _seed_student(db_session)
    program = await _seed_program(db_session)
    await _seed_match(db_session, student.id, program.id, confidence="0.91")
    app = Application(student_id=student.id, program_id=program.id, status="submitted")
    db_session.add(app)
    await db_session.commit()
    await db_session.refresh(app)
    enrollment = EnrollmentRecord(
        application_id=app.id,
        student_id=student.id,
        program_id=program.id,
        enrollment_status="confirmed",
    )
    db_session.add(enrollment)
    await db_session.commit()
    await db_session.refresh(enrollment)

    await on_enrollment_confirmed(db_session, enrollment_id=enrollment.id)
    await db_session.commit()

    pair = await db_session.scalar(
        select(ConfidenceOutcomePair).where(
            ConfidenceOutcomePair.student_id == student.id,
            ConfidenceOutcomePair.program_id == program.id,
        )
    )
    assert pair is not None
    assert pair.outcome_kind == "enrolled"
    assert pair.predicted_confidence == Decimal("0.9100")
