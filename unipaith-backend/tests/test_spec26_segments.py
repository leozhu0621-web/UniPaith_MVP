"""Spec 26 · Audience Segmentation — rule-tree engine, preview, suppression,
uploaded-list merge, NL bridge, and legacy back-compat.

The engine evaluates a nested include/exclude rule tree over the signal
dictionary, scoped to the institution's addressable students, then applies the
global outreach-suppression list. These tests pin the AND/OR/NOT semantics, the
preview count consistency, suppression-before-count, email merge, the NL-bridge
fallback (AI_MOCK_MODE), and that legacy flat `criteria` still resolves so
existing campaigns are unaffected.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from unipaith.models.application import Application
from unipaith.models.engagement import SavedList, SavedListItem, StudentEngagementSignal
from unipaith.models.institution import Institution, Program, TargetSegment
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentDataConsent, StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.services.segment_service import SegmentService

# asyncio_mode = "auto" (pyproject) auto-detects async tests; no module mark needed.


async def _student(db, *, nationality=None, outreach=True):
    user = User(
        id=uuid.uuid4(),
        email=f"s-{uuid.uuid4().hex[:8]}@example.com",
        cognito_sub=f"sub-{uuid.uuid4().hex[:8]}",
        role=UserRole("student"),
        is_active=True,
    )
    db.add(user)
    await db.flush()
    profile = StudentProfile(user_id=user.id, first_name="Test", nationality=nationality)
    db.add(profile)
    await db.flush()
    consent = StudentDataConsent(student_id=profile.id, consent_outreach=outreach)
    db.add(consent)
    await db.flush()
    return user, profile


async def _viewed(db, profile, program, days_ago=1):
    db.add(
        StudentEngagementSignal(
            student_id=profile.id,
            program_id=program.id,
            signal_type="view",
            created_at=datetime.now(UTC) - timedelta(days=days_ago),
        )
    )
    await db.flush()


async def _saved(db, profile, program):
    sl = SavedList(student_id=profile.id, list_name="My List")
    db.add(sl)
    await db.flush()
    db.add(SavedListItem(list_id=sl.id, program_id=program.id))
    await db.flush()


async def _match(db, profile, program, fitness, confidence=0.6):
    db.add(
        MatchResult(
            student_id=profile.id,
            program_id=program.id,
            fitness_score=Decimal(str(fitness)),
            confidence_score=Decimal(str(confidence)),
            is_stale=False,
        )
    )
    await db.flush()


async def _applied(db, profile, program, submitted=True):
    db.add(
        Application(
            student_id=profile.id,
            program_id=program.id,
            status="submitted" if submitted else "draft",
            submitted_at=datetime.now(UTC) if submitted else None,
        )
    )
    await db.flush()


@pytest.fixture
async def scenario(db_session, mock_institution_user):
    """A institution + program with four students:

    A: viewed + saved + fit high, no application, outreach on.
    B: applied, fit medium, outreach on.
    C: viewed + fit high, outreach OFF (suppressed).
    D: only a nationality, NO institution connection (outside the universe).
    """
    db = db_session
    db.add(mock_institution_user)
    await db.flush()
    inst = Institution(
        admin_user_id=mock_institution_user.id, name="Test U", type="university", country="USA"
    )
    db.add(inst)
    await db.flush()
    prog = Program(institution_id=inst.id, program_name="MS CS", degree_type="master")
    db.add(prog)
    await db.flush()

    _ua, a = await _student(db, nationality="USA")
    await _viewed(db, a, prog)
    await _saved(db, a, prog)
    await _match(db, a, prog, 0.80)

    _ub, b = await _student(db, nationality="India")
    await _applied(db, b, prog)
    await _match(db, b, prog, 0.60)

    _uc, c = await _student(db, nationality="USA", outreach=False)
    await _viewed(db, c, prog)
    await _match(db, c, prog, 0.80)

    _ud, d = await _student(db, nationality="USA")  # unconnected

    return {
        "db": db,
        "inst": inst,
        "prog": prog,
        "A": a.id,
        "B": b.id,
        "C": c.id,
        "D": d.id,
    }


# ── universe scoping ─────────────────────────────────────────────────────────


async def test_universe_excludes_unconnected_students(scenario):
    svc = SegmentService(scenario["db"])
    members = await svc.evaluate_rules(scenario["inst"].id, None)
    assert members == {scenario["A"], scenario["B"], scenario["C"]}
    assert scenario["D"] not in members  # nationality match but no connection


# ── include AND/OR/NOT ───────────────────────────────────────────────────────


async def test_include_single_band(scenario):
    svc = SegmentService(scenario["db"])
    rules = {
        "include": {
            "op": "AND",
            "rules": [{"field": "fit_band", "operator": "in", "value": ["high"]}],
        }
    }
    members = await svc.evaluate_rules(scenario["inst"].id, rules)
    assert members == {scenario["A"], scenario["C"]}


async def test_include_and(scenario):
    svc = SegmentService(scenario["db"])
    rules = {
        "include": {
            "op": "AND",
            "rules": [
                {"field": "fit_band", "operator": "in", "value": ["high"]},
                {"field": "saved_program", "operator": "exists"},
            ],
        }
    }
    members = await svc.evaluate_rules(scenario["inst"].id, rules)
    assert members == {scenario["A"]}


async def test_include_or(scenario):
    svc = SegmentService(scenario["db"])
    rules = {
        "include": {
            "op": "OR",
            "rules": [
                {"field": "fit_band", "operator": "in", "value": ["high"]},
                {"field": "started_application", "operator": "exists"},
            ],
        }
    }
    members = await svc.evaluate_rules(scenario["inst"].id, rules)
    assert members == {scenario["A"], scenario["B"], scenario["C"]}


async def test_not_group(scenario):
    svc = SegmentService(scenario["db"])
    rules = {
        "include": {
            "op": "NOT",
            "rules": [{"field": "saved_program", "operator": "exists"}],
        }
    }
    members = await svc.evaluate_rules(scenario["inst"].id, rules)
    assert members == {scenario["B"], scenario["C"]}  # everyone in universe except A


async def test_exclude_branch(scenario):
    svc = SegmentService(scenario["db"])
    rules = {
        "include": {
            "op": "AND",
            "rules": [{"field": "fit_band", "operator": "in", "value": ["high"]}],
        },
        "exclude": {"op": "AND", "rules": [{"field": "saved_program", "operator": "exists"}]},
    }
    members = await svc.evaluate_rules(scenario["inst"].id, rules)
    assert members == {scenario["C"]}  # {A,C} include minus {A} saved


# ── suppression before count ─────────────────────────────────────────────────


async def test_suppression_drops_opted_out(scenario):
    svc = SegmentService(scenario["db"])
    members = await svc.evaluate_rules(scenario["inst"].id, None)
    suppressed = await svc.apply_suppression(members)
    assert scenario["C"] not in suppressed  # outreach off
    assert suppressed == {scenario["A"], scenario["B"]}


async def test_preview_count_consistent_with_suppression(scenario):
    svc = SegmentService(scenario["db"])
    result = await svc.preview(scenario["inst"].id, None)
    # universe {A,B,C} minus suppressed C = 2
    assert result["audience_count"] == 2
    assert result["platform_count"] == 2
    assert len(result["sample"]) == 2
    sample_ids = {s["student_id"] for s in result["sample"]}
    assert str(scenario["C"]) not in sample_ids


async def test_preview_zero_match(scenario):
    svc = SegmentService(scenario["db"])
    rules = {
        "include": {
            "op": "AND",
            "rules": [{"field": "application_decision", "operator": "in", "value": ["admitted"]}],
        }
    }
    result = await svc.preview(scenario["inst"].id, rules)
    assert result["audience_count"] == 0
    assert result["sample"] == []


# ── uploaded list merge by email ─────────────────────────────────────────────


async def test_email_merge_resolves_platform_students(scenario):
    db = scenario["db"]
    # the student B's email should resolve to B's profile id
    row = await db.execute(
        __import__("sqlalchemy")
        .select(User.email)
        .join(StudentProfile, StudentProfile.user_id == User.id)
        .where(StudentProfile.id == scenario["B"])
    )
    email = row.scalar_one()
    svc = SegmentService(db)
    mapping = await svc._emails_to_student_ids({email.lower()})
    assert mapping.get(email.lower()) == scenario["B"]


# ── fairness skew warning (unit) ─────────────────────────────────────────────


def test_fairness_warning_triggers_on_skew():
    svc = SegmentService(None)  # helper is pure
    comp = {"nationality": {"USA": 18, "India": 4}}
    warn = svc._fairness_warning(comp, audience_count=22)
    assert warn and "fairness" in warn.lower()


def test_fairness_warning_silent_when_small():
    svc = SegmentService(None)
    comp = {"nationality": {"USA": 5}}
    assert svc._fairness_warning(comp, audience_count=5) is None


# ── legacy criteria back-compat (campaigns) ──────────────────────────────────


async def test_legacy_criteria_still_resolves(scenario):
    """A segment with only flat `criteria` (no rules) resolves via the legacy
    path so existing campaign wiring is unaffected."""
    from unipaith.services.institution_service import InstitutionService

    db = scenario["db"]
    seg = TargetSegment(
        institution_id=scenario["inst"].id,
        segment_name="Legacy applicants",
        criteria={"has_applied": True},
    )
    db.add(seg)
    await db.flush()
    inst_svc = InstitutionService(db)
    members = await inst_svc.resolve_segment_members(scenario["inst"].id, seg.id)
    assert set(members) == {scenario["B"]}  # only B applied


async def test_rules_segment_resolves_via_engine(scenario):
    from unipaith.services.institution_service import InstitutionService

    db = scenario["db"]
    seg = TargetSegment(
        institution_id=scenario["inst"].id,
        segment_name="High-fit",
        rules={
            "include": {
                "op": "AND",
                "rules": [{"field": "fit_band", "operator": "in", "value": ["high"]}],
            }
        },
    )
    db.add(seg)
    await db.flush()
    inst_svc = InstitutionService(db)
    members = await inst_svc.resolve_segment_members(scenario["inst"].id, seg.id)
    # engine path applies suppression → {A} (C is high-fit but opted out)
    assert set(members) == {scenario["A"]}


# ── endpoints ─────────────────────────────────────────────────────────────────


async def test_signal_dictionary_endpoint(institution_client, db_session, mock_institution_user):
    inst = Institution(
        admin_user_id=mock_institution_user.id, name="Sig U", type="university", country="USA"
    )
    db_session.add(inst)
    await db_session.flush()
    resp = await institution_client.get("/api/v1/institutions/me/segments/signal-dictionary")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["signals"]) >= 20
    keys = {s["key"] for s in body["signals"]}
    assert {"fit_band", "saved_program", "viewed_institution", "budget_band"} <= keys


async def test_nl_bridge_endpoint_fallback(institution_client, db_session, mock_institution_user):
    """In AI_MOCK_MODE the agent returns the keyword-parser fallback (never 5xx)."""
    inst = Institution(
        admin_user_id=mock_institution_user.id, name="NL U", type="university", country="USA"
    )
    db_session.add(inst)
    await db_session.flush()
    resp = await institution_client.post(
        "/api/v1/institutions/me/segments/nl-bridge",
        json={"text": "high-fit masters students who saved our programs but haven't applied"},
    )
    assert resp.status_code == 200
    body = resp.json()
    fields = {r["field"] for r in body["rules"]}
    assert "fit_band" in fields
    assert "saved_program_degree" in fields
    # negation routed to exclude branch
    excl = [r for r in body["rules"] if r["branch"] == "exclude"]
    assert any(r["field"] == "started_application" for r in excl)


async def test_preview_endpoint_unsaved_rules(
    institution_client, db_session, mock_institution_user
):
    inst = Institution(
        admin_user_id=mock_institution_user.id, name="Prev U", type="university", country="USA"
    )
    db_session.add(inst)
    await db_session.flush()
    resp = await institution_client.post(
        "/api/v1/institutions/me/segments/preview",
        json={"rules": {"include": {"op": "AND", "rules": []}}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "audience_count" in body
    assert "sample" in body
    assert "fairness_warning" in body
