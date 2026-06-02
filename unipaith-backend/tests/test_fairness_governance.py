"""Spec 46 §6 · Fairness governance — disparate-impact compute + auto-halt.

Covers the §6 commitments and the §9 (G-T3) named test:
- DI math + severity ladder (pure functions).
- Auto-halt after Δ > threshold for **two consecutive weeks** (G-T3).
- Insufficient-sample cohorts are flagged, never halted.
- Override workflow: rationale ≥100 chars enforced; flips state + expiry + audit;
  revoke re-halts.
- MatchService skips scoring a halted cohort (existing scores untouched), and
  an active override resumes scoring.
- consent.training lever is carried in the consent mask (G-T2 contract).
- API smoke: recompute / overview / override (422 + ok) / threshold.
"""

import uuid
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from unipaith.ai.consent import get_consent_mask
from unipaith.models.fairness import FairnessOverride, FairnessSignal
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentDataConsent, StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.models.workflow import Notification
from unipaith.services.fairness_service import (
    FairnessService,
    disparate_impact,
    severity_for,
    week_start_of,
)
from unipaith.services.match_service import MatchService

pytestmark = pytest.mark.asyncio

WEEK1 = date(2026, 5, 25)  # Monday
WEEK2 = date(2026, 6, 1)  # following Monday


# ── seeding helpers ──────────────────────────────────────────────────────────


async def _seed_program(db, *, admin_user_id=None, threshold=None) -> tuple[Institution, Program]:
    if admin_user_id is None:
        iu = User(
            id=uuid.uuid4(),
            email=f"inst-{uuid.uuid4().hex[:6]}@example.com",
            cognito_sub=f"sub-{uuid.uuid4().hex[:8]}",
            role=UserRole("institution_admin"),
            is_active=True,
        )
        db.add(iu)
        await db.flush()
        admin_user_id = iu.id
    inst = Institution(admin_user_id=admin_user_id, name="Foo U", type="university", country="US")
    db.add(inst)
    await db.flush()
    program = Program(
        institution_id=inst.id,
        program_name="MS Computer Science",
        degree_type="masters",
        is_published=True,
    )
    if threshold is not None:
        program.fairness_threshold = Decimal(str(threshold))
    db.add(program)
    await db.flush()
    return inst, program


async def _seed_cohort(
    db,
    program_id,
    week_monday,
    *,
    n_majority,
    n_minority,
    maj_fitness,
    min_fitness,
    maj_gender="man",
    min_gender="woman",
) -> None:
    """Create scored applicants for one (program, week): a majority gender group
    with one positive rate and a minority gender group with another."""
    when = datetime.combine(week_monday, time(12, 0), tzinfo=UTC) + timedelta(days=1)
    profiles: list[StudentProfile] = []
    for gender, count in ((maj_gender, n_majority), (min_gender, n_minority)):
        for _ in range(count):
            sp_id = uuid.uuid4()
            u = User(
                id=uuid.uuid4(),
                email=f"s-{uuid.uuid4().hex[:8]}@example.com",
                cognito_sub=f"sub-{uuid.uuid4().hex[:8]}",
                role=UserRole("student"),
                is_active=True,
            )
            db.add(u)
            db.add(StudentProfile(id=sp_id, user_id=u.id, gender_identity=gender))
            profiles.append((sp_id, maj_fitness if gender == maj_gender else min_fitness))
    await db.flush()
    for sp_id, fitness in profiles:
        db.add(
            MatchResult(
                student_id=sp_id,
                program_id=program_id,
                fitness_score=Decimal(str(fitness)),
                confidence_score=Decimal("0.80"),
                computed_at=when,
            )
        )
    await db.flush()


# ── pure-function tests ──────────────────────────────────────────────────────


async def test_disparate_impact_math():
    assert week_start_of(date(2026, 6, 3)).weekday() == 0
    assert disparate_impact(0.3, 0.9) == pytest.approx(0.3333, abs=1e-3)
    assert disparate_impact(0.0, 1.0) == 0.0
    assert disparate_impact(0.0, 0.0) == 1.0  # no positives anywhere → no disparity
    assert disparate_impact(0.5, 0.0) > 1.0  # reverse disparity, clamped


async def test_severity_ladder():
    assert severity_for(0.67, 0.20, sample_sufficient=True) == "high"
    assert severity_for(0.17, 0.20, sample_sufficient=True) == "warning"
    assert severity_for(0.05, 0.20, sample_sufficient=True) == "info"
    assert severity_for(None, 0.20, sample_sufficient=False) == "info"


# ── G-T3: auto-halt after two consecutive breaches ───────────────────────────


async def test_auto_halt_two_consecutive_weeks(db_session):
    """Spec 46 §6.6 (G-T3): Δ > 0.20 for two consecutive weeks halts scoring."""
    inst, program = await _seed_program(db_session)
    fsvc = FairnessService(db_session)

    # Week 1: large gap (majority 100% positive, minority 0%) → Δ = 1.0 > 0.20.
    await _seed_cohort(
        db_session,
        program.id,
        WEEK1,
        n_majority=70,
        n_minority=60,
        maj_fitness=0.9,
        min_fitness=0.3,
    )
    await fsvc.compute_week(program.id, WEEK1)
    await db_session.refresh(program)
    assert program.matching_halted is False, "one breach must not halt"

    # Week 2: same gap (fresh applicants — match_results is unique per student).
    await _seed_cohort(
        db_session,
        program.id,
        WEEK2,
        n_majority=70,
        n_minority=60,
        maj_fitness=0.9,
        min_fitness=0.3,
    )
    await fsvc.compute_week(program.id, WEEK2)
    await db_session.refresh(program)
    assert program.matching_halted is True, "second consecutive breach must halt"

    # The week-2 gender signal escalated to auto_halt.
    sig = (
        (
            await db_session.execute(
                select(FairnessSignal).where(
                    FairnessSignal.program_id == program.id,
                    FairnessSignal.week_start == WEEK2,
                    FairnessSignal.protected_attribute == "gender",
                )
            )
        )
        .scalars()
        .first()
    )
    assert sig is not None and sig.severity == "auto_halt"
    assert float(sig.delta) > 0.20

    # The institution admin was notified.
    notif = (
        (
            await db_session.execute(
                select(Notification).where(Notification.notification_type == "fairness_auto_halt")
            )
        )
        .scalars()
        .first()
    )
    assert notif is not None and notif.user_id == inst.admin_user_id


async def test_compute_is_idempotent(db_session):
    _, program = await _seed_program(db_session)
    await _seed_cohort(
        db_session,
        program.id,
        WEEK1,
        n_majority=70,
        n_minority=60,
        maj_fitness=0.9,
        min_fitness=0.3,
    )
    fsvc = FairnessService(db_session)
    await fsvc.compute_week(program.id, WEEK1)
    await fsvc.compute_week(program.id, WEEK1)  # re-run
    count = (
        (
            await db_session.execute(
                select(FairnessSignal).where(
                    FairnessSignal.program_id == program.id,
                    FairnessSignal.protected_attribute == "gender",
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(count) == 1, "re-compute must upsert, not duplicate"


async def test_insufficient_sample_not_halted(db_session):
    _, program = await _seed_program(db_session)
    # Below the 50-applicant floor for the week.
    await _seed_cohort(
        db_session, program.id, WEEK1, n_majority=10, n_minority=8, maj_fitness=0.9, min_fitness=0.3
    )
    await _seed_cohort(
        db_session, program.id, WEEK2, n_majority=10, n_minority=8, maj_fitness=0.9, min_fitness=0.3
    )
    fsvc = FairnessService(db_session)
    await fsvc.compute_week(program.id, WEEK1)
    await fsvc.compute_week(program.id, WEEK2)
    await db_session.refresh(program)
    assert program.matching_halted is False
    sig = (
        (
            await db_session.execute(
                select(FairnessSignal).where(
                    FairnessSignal.program_id == program.id,
                    FairnessSignal.week_start == WEEK2,
                    FairnessSignal.protected_attribute == "gender",
                )
            )
        )
        .scalars()
        .first()
    )
    assert sig is not None and sig.sample_sufficient is False and sig.severity == "info"


async def test_balanced_cohort_no_halt(db_session):
    """A fair cohort (equal positive rates) stays green and is never halted."""
    _, program = await _seed_program(db_session)
    for wk in (WEEK1, WEEK2):
        await _seed_cohort(
            db_session,
            program.id,
            wk,
            n_majority=70,
            n_minority=60,
            maj_fitness=0.9,
            min_fitness=0.9,
        )
        await FairnessService(db_session).compute_week(program.id, wk)
    await db_session.refresh(program)
    assert program.matching_halted is False


# ── override workflow (§6.3) ─────────────────────────────────────────────────


async def test_override_requires_rationale_and_flips_state(db_session):
    inst, program = await _seed_program(db_session)
    program.matching_halted = True
    await db_session.flush()
    iu_id = inst.admin_user_id
    fsvc = FairnessService(db_session)

    with pytest.raises(ValueError):
        await fsvc.apply_override(program.id, admin_user_id=iu_id, rationale="too short")

    rationale = (
        "After review with the department chair, the cohort gap reflects a small applicant "
        "pool this cycle rather than scoring bias; resuming while we widen recruiting."
    )
    assert len(rationale) >= 100
    override = await fsvc.apply_override(
        program.id, admin_user_id=iu_id, rationale=rationale, weeks=2
    )
    await db_session.refresh(program)
    assert program.matching_halted is False
    assert program.fairness_override_active is True
    assert program.fairness_override_expires_at is not None
    assert override.override_expires_at > datetime.now(UTC)

    row = (
        (
            await db_session.execute(
                select(FairnessOverride).where(FairnessOverride.program_id == program.id)
            )
        )
        .scalars()
        .first()
    )
    assert row is not None and row.revoked_at is None

    # Revoke re-halts.
    await fsvc.revoke_override(program.id, admin_user_id=iu_id)
    await db_session.refresh(program)
    assert program.matching_halted is True
    assert program.fairness_override_active is False


async def test_set_threshold_range(db_session):
    inst, program = await _seed_program(db_session)
    fsvc = FairnessService(db_session)
    with pytest.raises(ValueError):
        await fsvc.set_threshold(program.id, threshold=0.99, admin_user_id=inst.admin_user_id)
    await fsvc.set_threshold(program.id, threshold=0.10, admin_user_id=inst.admin_user_id)
    await db_session.refresh(program)
    assert float(program.fairness_threshold) == pytest.approx(0.10)


# ── matching respects the halt ────────────────────────────────────────────────


async def test_matching_skips_halted_cohort(db_session):
    _, program = await _seed_program(db_session)
    msvc = MatchService(db_session)

    program.matching_halted = True
    await db_session.flush()
    assert await msvc._halted_program_ids([program.id]) == {program.id}

    # An active, unexpired override resumes scoring.
    program.fairness_override_active = True
    program.fairness_override_expires_at = datetime.now(UTC) + timedelta(days=3)
    await db_session.flush()
    assert await msvc._halted_program_ids([program.id]) == set()

    # An expired override no longer protects → halted again.
    program.fairness_override_expires_at = datetime.now(UTC) - timedelta(days=1)
    await db_session.flush()
    assert await msvc._halted_program_ids([program.id]) == {program.id}


# ── consent.training lever (G-T2 contract) ────────────────────────────────────


async def test_consent_training_lever_in_mask(db_session):
    u = User(
        id=uuid.uuid4(),
        email=f"s-{uuid.uuid4().hex[:8]}@example.com",
        cognito_sub=f"sub-{uuid.uuid4().hex[:8]}",
        role=UserRole("student"),
        is_active=True,
    )
    db_session.add(u)
    await db_session.flush()
    sp = StudentProfile(user_id=u.id)
    db_session.add(sp)
    await db_session.flush()
    db_session.add(StudentDataConsent(student_id=sp.id, consent_training=False))
    await db_session.flush()
    mask = await get_consent_mask(db_session, sp.id)
    assert mask.get("training") is False

    consent = (
        (
            await db_session.execute(
                select(StudentDataConsent).where(StudentDataConsent.student_id == sp.id)
            )
        )
        .scalars()
        .first()
    )
    consent.consent_training = True
    await db_session.flush()
    mask = await get_consent_mask(db_session, sp.id)
    assert mask.get("training") is True


# ── API smoke ─────────────────────────────────────────────────────────────────


async def test_fairness_api_smoke(institution_client, mock_institution_user, db_session):
    inst, program = await _seed_program(db_session, admin_user_id=mock_institution_user.id)
    await _seed_cohort(
        db_session,
        program.id,
        WEEK1,
        n_majority=70,
        n_minority=60,
        maj_fitness=0.9,
        min_fitness=0.3,
    )
    await db_session.flush()

    # recompute populates signals; overview reflects status.
    r = await institution_client.post(
        "/api/v1/institutions/me/fairness/recompute", json={"weeks_back": 2}
    )
    assert r.status_code == 200, r.text
    assert r.json()["computations"] >= 1

    r = await institution_client.get("/api/v1/institutions/me/fairness/overview")
    assert r.status_code == 200, r.text
    assert r.json()["status"] in ("green", "yellow", "red")

    r = await institution_client.get("/api/v1/institutions/me/fairness/cohorts")
    assert r.status_code == 200, r.text
    assert isinstance(r.json()["programs"], list)

    # Override: <100 char rationale is rejected by validation.
    r = await institution_client.post(
        "/api/v1/institutions/me/fairness/override",
        json={"program_id": str(program.id), "rationale": "short"},
    )
    assert r.status_code == 422

    long_rationale = (
        "Reviewed with the department; the gap reflects a thin applicant pool this cycle, "
        "not scoring bias. Resuming scoring while we broaden outreach for the next round."
    )
    r = await institution_client.post(
        "/api/v1/institutions/me/fairness/override",
        json={"program_id": str(program.id), "rationale": long_rationale, "weeks": 2},
    )
    assert r.status_code == 200, r.text
    assert r.json()["fairness_override_active"] is True

    # Threshold update within range.
    r = await institution_client.patch(
        "/api/v1/institutions/me/fairness/threshold",
        json={"program_id": str(program.id), "threshold": 0.15},
    )
    assert r.status_code == 200, r.text
    assert r.json()["fairness_threshold"] == pytest.approx(0.15)
