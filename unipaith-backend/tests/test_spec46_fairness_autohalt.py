"""Spec 46 §6 — Fairness auto-halt engine tests.

G-T3 (§6.6): seed a synthetic cohort with disparate-impact Δ > 0.20 for two
consecutive weeks → assert programs.matching_halted = true after the second
week's compute. Plus unit coverage: the 4/5ths DI math, the 50-sample
"insufficient" gate, single-week-no-halt, the override workflow, and the
match-gate's halted-program resolver.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from unipaith.config import settings
from unipaith.models.fairness import FairnessSignal
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.services.fairness_service import FairnessService

# pyproject sets asyncio_mode = "auto" — async tests run without a mark.

WEEK1 = date(2026, 4, 6)  # a Monday
WEEK2 = WEEK1 + timedelta(days=7)


async def _institution_with_program(db) -> tuple[Institution, Program]:
    admin = User(
        id=uuid.uuid4(),
        email=f"admin-{uuid.uuid4().hex[:6]}@example.com",
        cognito_sub=f"sub-{uuid.uuid4().hex[:8]}",
        role=UserRole.institution_admin,
        is_active=True,
    )
    db.add(admin)
    await db.flush()
    inst = Institution(
        admin_user_id=admin.id, name="U of Foo", type="university", country="United States"
    )
    db.add(inst)
    await db.flush()
    program = Program(
        institution_id=inst.id, program_name="MS CS", degree_type="masters", is_published=True
    )
    db.add(program)
    await db.flush()
    return inst, program


async def _seed_week(
    db,
    program_id,
    week_start: date,
    *,
    per_group: int = 25,
    man_positive: int | None = None,
    woman_positive: int | None = None,
) -> None:
    """Seed `per_group` 'man' + `per_group` 'woman' scored applicants for the
    week. `*_positive` controls how many in each group are recommended-by-match
    (fitness ≥ 0.60). Defaults: man all-recommended, woman 20% — Δ ≈ 0.80.
    """
    man_positive = per_group if man_positive is None else man_positive
    woman_positive = round(per_group * 0.2) if woman_positive is None else woman_positive
    window = datetime(week_start.year, week_start.month, week_start.day, 12, tzinfo=UTC)

    # Persist users + profiles first, then match_results — the
    # student_profiles↔student_strategies FK cycle in the metadata defeats the
    # unit-of-work auto-ordering for the relationship-less match_results FK, so
    # flush the parent rows before the children.
    seeded: list[tuple[uuid.UUID, bool]] = []
    for gender, positive_count in (("man", man_positive), ("woman", woman_positive)):
        for i in range(per_group):
            uid = uuid.uuid4()
            pid = uuid.uuid4()
            db.add(
                User(
                    id=uid,
                    email=f"s-{uid.hex[:10]}@example.com",
                    cognito_sub=f"sub-{uid.hex[:10]}",
                    role=UserRole.student,
                    is_active=True,
                )
            )
            db.add(StudentProfile(id=pid, user_id=uid, gender_identity=gender))
            seeded.append((pid, i < positive_count))
    await db.flush()
    for pid, recommended in seeded:
        db.add(
            MatchResult(
                student_id=pid,
                program_id=program_id,
                fitness_score=Decimal("0.90") if recommended else Decimal("0.30"),
                confidence_score=Decimal("0.80"),
                computed_at=window,
            )
        )
    await db.flush()


async def test_g_t3_two_consecutive_weeks_auto_halts(db_session, monkeypatch):
    """G-T3 — Δ>0.20 for two consecutive weeks halts matching."""
    monkeypatch.setattr(settings, "fairness_autohalt_v2_enabled", True)
    _, program = await _institution_with_program(db_session)
    svc = FairnessService(db_session)

    # Week 1 — disparate. Single week → high signal, NO halt yet.
    await _seed_week(db_session, program.id, WEEK1)
    await svc.compute_for_week(WEEK1, program_id=program.id)
    await db_session.refresh(program)
    assert program.matching_halted is False

    # Week 2 — disparate again → second consecutive breach → halt.
    await _seed_week(db_session, program.id, WEEK2)
    await svc.compute_for_week(WEEK2, program_id=program.id)
    await db_session.refresh(program)
    assert program.matching_halted is True

    # An auto_halt signal was recorded for the gender attribute in week 2.
    sigs = await svc.list_signals(program.institution_id, program_id=program.id)
    week2 = WEEK2.isoformat()
    auto = [s for s in sigs if s["severity"] == "auto_halt" and s["week_start"] == week2]
    assert auto, "expected an auto_halt fairness signal for week 2"
    assert auto[0]["delta"] is not None and auto[0]["delta"] > 0.20


async def test_single_disparate_week_does_not_halt(db_session, monkeypatch):
    monkeypatch.setattr(settings, "fairness_autohalt_v2_enabled", True)
    _, program = await _institution_with_program(db_session)
    svc = FairnessService(db_session)
    await _seed_week(db_session, program.id, WEEK1)
    await svc.compute_for_week(WEEK1, program_id=program.id)
    await db_session.refresh(program)
    assert program.matching_halted is False


async def test_insufficient_sample_never_halts(db_session, monkeypatch):
    """Below 50 scored applicants → 'insufficient sample', never a breach."""
    monkeypatch.setattr(settings, "fairness_autohalt_v2_enabled", True)
    _, program = await _institution_with_program(db_session)
    svc = FairnessService(db_session)
    # 10 per group = 20 < 50 even though the split is maximally disparate.
    await _seed_week(db_session, program.id, WEEK1, per_group=10)
    await _seed_week(db_session, program.id, WEEK2, per_group=10)
    await svc.compute_for_week(WEEK1, program_id=program.id)
    await svc.compute_for_week(WEEK2, program_id=program.id)
    await db_session.refresh(program)
    assert program.matching_halted is False
    sigs = await svc.list_signals(program.institution_id, program_id=program.id)
    gender = [s for s in sigs if s["protected_attribute"] == "gender"]
    assert gender and all(s["sample_sufficient"] is False for s in gender)


async def test_fair_cohort_does_not_halt(db_session, monkeypatch):
    monkeypatch.setattr(settings, "fairness_autohalt_v2_enabled", True)
    _, program = await _institution_with_program(db_session)
    svc = FairnessService(db_session)
    # Both groups ~80% recommended → DI ≈ 1.0, Δ ≈ 0.
    await _seed_week(db_session, program.id, WEEK1, man_positive=20, woman_positive=20)
    await _seed_week(db_session, program.id, WEEK2, man_positive=20, woman_positive=20)
    await svc.compute_for_week(WEEK1, program_id=program.id)
    await svc.compute_for_week(WEEK2, program_id=program.id)
    await db_session.refresh(program)
    assert program.matching_halted is False


def test_di_delta_four_fifths_rule():
    di, delta = FairnessService._di_delta({"man": [True] * 25, "woman": [True] * 5 + [False] * 20})
    assert di == pytest.approx(0.20, abs=0.001)  # 0.2 / 1.0
    assert delta == pytest.approx(0.80, abs=0.001)
    # Single group → no comparison.
    assert FairnessService._di_delta({"man": [True, False]}) == (None, None)
    # Equal rejection → no disparate impact.
    di2, delta2 = FairnessService._di_delta({"a": [False, False], "b": [False, False]})
    assert delta2 == pytest.approx(0.0)


async def test_override_lifts_halt(db_session, monkeypatch):
    monkeypatch.setattr(settings, "fairness_autohalt_v2_enabled", True)
    inst, program = await _institution_with_program(db_session)
    svc = FairnessService(db_session)
    await _seed_week(db_session, program.id, WEEK1)
    await _seed_week(db_session, program.id, WEEK2)
    await svc.compute_for_week(WEEK1, program_id=program.id)
    await svc.compute_for_week(WEEK2, program_id=program.id)
    await db_session.refresh(program)
    assert program.matching_halted is True

    signal = (
        await db_session.execute(
            FairnessSignal.__table__.select().where(
                FairnessSignal.program_id == program.id,
                FairnessSignal.week_start == WEEK2,
                FairnessSignal.protected_attribute == "gender",
            )
        )
    ).first()
    admin_id = inst.admin_user_id
    override = await svc.request_override(
        institution_id=inst.id,
        signal_id=signal.id,
        admin_user_id=admin_id,
        rationale=(
            "Reviewed the cohort manually; the disparity reflects a small applicant "
            "pool in this round, not a scoring bias. Lifting for one week pending audit."
        ),
    )
    await db_session.refresh(program)
    assert program.matching_halted is False
    assert program.fairness_override_active is True
    assert program.override_expires_at is not None
    assert override.override_expires_at > datetime.now(UTC)

    # The halted-program resolver (match-gate input) no longer includes it.
    halted = await svc.halted_program_ids()
    assert program.id not in halted


async def test_override_requires_long_rationale(db_session, monkeypatch):
    from unipaith.core.exceptions import BadRequestException

    monkeypatch.setattr(settings, "fairness_autohalt_v2_enabled", True)
    inst, program = await _institution_with_program(db_session)
    svc = FairnessService(db_session)
    await _seed_week(db_session, program.id, WEEK1)
    await svc.compute_for_week(WEEK1, program_id=program.id)
    sig = (
        await db_session.execute(
            FairnessSignal.__table__.select().where(FairnessSignal.program_id == program.id)
        )
    ).first()
    with pytest.raises(BadRequestException):
        await svc.request_override(
            institution_id=inst.id,
            signal_id=sig.id,
            admin_user_id=inst.admin_user_id,
            rationale="too short",
        )


async def test_halted_program_ids_resolver(db_session):
    """The match-gate's halt resolver: halted (no live override) → in set."""
    _, program = await _institution_with_program(db_session)
    svc = FairnessService(db_session)
    assert program.id not in await svc.halted_program_ids()

    program.matching_halted = True
    await db_session.flush()
    assert program.id in await svc.halted_program_ids()

    # Active, unexpired override → NOT halted for scoring.
    program.fairness_override_active = True
    program.override_expires_at = datetime.now(UTC) + timedelta(days=3)
    await db_session.flush()
    assert program.id not in await svc.halted_program_ids()

    # Expired override → halted again.
    program.override_expires_at = datetime.now(UTC) - timedelta(days=1)
    await db_session.flush()
    assert program.id in await svc.halted_program_ids()


async def test_flag_off_records_signals_but_does_not_halt(db_session, monkeypatch):
    """Safe rollout: flag off → signals still recorded, matching never halts."""
    monkeypatch.setattr(settings, "fairness_autohalt_v2_enabled", False)
    _, program = await _institution_with_program(db_session)
    svc = FairnessService(db_session)
    await _seed_week(db_session, program.id, WEEK1)
    await _seed_week(db_session, program.id, WEEK2)
    await svc.compute_for_week(WEEK1, program_id=program.id)
    await svc.compute_for_week(WEEK2, program_id=program.id)
    await db_session.refresh(program)
    assert program.matching_halted is False
    sigs = await svc.list_signals(program.institution_id, program_id=program.id)
    assert any(s["delta"] is not None and s["delta"] > 0.20 for s in sigs)
