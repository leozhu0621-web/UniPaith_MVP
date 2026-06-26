"""Spec 44 — Adaptive Intake Engine (§11 test matrix).

Covers, per §11:
- per-intake-channel ingest → normalized field + provenance + confidence + version
- conflict resolution per §7
- match-ready and apply-ready gating per §4
- consent enforcement: matching=false → no LLM call
- clarification loop: low-confidence input → visible in /clarifications → confirm → 95
- cross-module fanout: signal change invalidates downstream caches (match_results)
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import select

from unipaith.core.exceptions import BadRequestException
from unipaith.models.institution import Institution, Program
from unipaith.models.intake import (
    RawInput,
    SignalChangeEvent,
)
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentDataConsent, StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.services.intake.intake_engine_service import IntakeEngineService

pytestmark = pytest.mark.asyncio


# ── helpers ──────────────────────────────────────────────────────────────────
async def _student(db, *, matching: bool = True) -> StudentProfile:
    u = User(
        id=uuid.uuid4(),
        email=f"s-{uuid.uuid4().hex[:8]}@example.com",
        cognito_sub=f"sub-{uuid.uuid4().hex[:8]}",
        role=UserRole("student"),
        is_active=True,
    )
    db.add(u)
    await db.flush()
    p = StudentProfile(user_id=u.id)
    db.add(p)
    await db.flush()
    db.add(StudentDataConsent(student_id=p.id, consent_matching=matching))
    await db.flush()
    return p


async def _program(db, *, app_requirements: dict | None = None) -> Program:
    iu = User(
        id=uuid.uuid4(),
        email=f"i-{uuid.uuid4().hex[:8]}@example.com",
        cognito_sub=f"sub-{uuid.uuid4().hex[:8]}",
        role=UserRole("institution_admin"),
        is_active=True,
    )
    db.add(iu)
    await db.flush()
    inst = Institution(admin_user_id=iu.id, name="Test University", type="university", country="US")
    db.add(inst)
    await db.flush()
    prog = Program(
        institution_id=inst.id,
        program_name="MS in Computer Science",
        degree_type="master",
        is_published=True,
        application_requirements=app_requirements,
    )
    db.add(prog)
    await db.flush()
    return prog


_CORE_FILL = {
    "legal_name": "Jane Doe",
    "primary_email": "jane@example.com",
    "nationality": "India",
    "country_of_residence": "India",
    "current_academic_year_level": "undergraduate",
    "expected_graduation_date": "2026-06-01",
    "gpa_reported": "3.8",
    "target_degree_level": "master",
    "target_major_field_primary": "Computer Science",
    "target_start_term_season": "fall",
    "target_start_term_year": 2027,
    "budget_band_annual_total": "40-60k",
    "preferred_modality": "in_person",
}


async def _fill_core(svc: IntakeEngineService, sid) -> None:
    for k, v in _CORE_FILL.items():
        await svc.ingest_form_save(sid, k, v)


# ── §5.2 form-save channel: normalize + provenance + confidence + version ─────
async def test_form_save_normalizes_with_provenance(db_session):
    p = await _student(db_session)
    svc = IntakeEngineService(db_session)

    out = await svc.ingest_form_save(p.id, "target_degree_level", "master's")

    assert out["value"] == "master"  # free-text → enum (§3.1)
    assert out["source"] == "student-typed"
    assert out["confidence"] == 95  # §5 structured student-typed
    assert out["record_version"] == 1
    assert out["valid"] is True

    # raw-inputs layer is written (immutable).
    raws = (
        (await db_session.execute(select(RawInput).where(RawInput.student_id == p.id)))
        .scalars()
        .all()
    )
    assert len(raws) == 1
    assert raws[0].channel == "form"

    # normalized signal carries provenance + value_normalized.
    sig = await svc._get_signal(p.id, "target_degree_level")
    assert sig.value == {"v": "master"}
    assert sig.value_normalized == {"v": "master"}
    assert len(sig.provenance_chain) == 1
    assert sig.provenance_chain[0]["event"] == "created"

    # append-only ledger records the change.
    events = (
        (
            await db_session.execute(
                select(SignalChangeEvent).where(SignalChangeEvent.student_id == p.id)
            )
        )
        .scalars()
        .all()
    )
    assert any(e.event == "created" and e.signal_name == "target_degree_level" for e in events)


async def test_version_increments_and_is_monotonic(db_session):
    p = await _student(db_session)
    svc = IntakeEngineService(db_session)
    await svc.ingest_form_save(p.id, "primary_email", "a@x.com")
    out2 = await svc.ingest_form_save(p.id, "primary_email", "b@x.com")
    assert out2["record_version"] == 2  # §9.3 monotonic
    sig = await svc._get_signal(p.id, "primary_email")
    assert sig.value == {"v": "b@x.com"}  # two student-typed → latest wins (§7)
    assert len(sig.provenance_chain) == 2


# ── §7 conflict resolution ────────────────────────────────────────────────────
async def test_reconciliation_source_priority(db_session):
    p = await _student(db_session)
    svc = IntakeEngineService(db_session)

    # student-typed first.
    await svc.ingest_form_save(p.id, "gpa_reported", "3.8")

    # system-extracted loses to student-typed → kept (§7 row 1).
    lost = await svc.ingest_signal(
        p.id,
        "gpa_reported",
        "3.2",
        channel="discovery_chat",
        source="system-extracted",
        structured=False,
    )
    assert lost["status"] == "reconciled_kept"
    sig = await svc._get_signal(p.id, "gpa_reported")
    assert sig.value == {"v": "3.8"}
    # the losing attempt is preserved in the chain.
    assert any(e["event"] == "reconciled_kept" for e in sig.provenance_chain)

    # institution-supplied wins over student-typed (§7 row 4 — test-score case).
    won = await svc.ingest_signal(
        p.id, "gpa_reported", "3.9", channel="institution", source="institution-supplied"
    )
    assert won["status"] == "updated"
    sig = await svc._get_signal(p.id, "gpa_reported")
    assert sig.value == {"v": "3.9"}
    assert sig.source == "institution-supplied"

    # third-party-verified beats everything (§7 row 3).
    await svc.ingest_signal(
        p.id, "gpa_reported", "4.0", channel="institution", source="third-party-verified"
    )
    sig = await svc._get_signal(p.id, "gpa_reported")
    assert sig.value == {"v": "4.0"}
    assert sig.confidence == 99


# ── §4.1 / §6.1 match-ready gating ────────────────────────────────────────────
async def test_match_ready_gate_flips_when_core_complete(db_session):
    p = await _student(db_session)
    svc = IntakeEngineService(db_session)

    before = await svc.get_match_ready(p.id)
    assert before["match_ready"] is False
    assert before["missing_count"] > 0

    await _fill_core(svc, p.id)
    # geography + at least 3 of 7 priority weights (§6.1).
    await svc.ingest_form_save(p.id, "preferred_countries", ["US", "UK"])
    await svc.ingest_form_save(
        p.id, "preference_weights", {"cost": 5, "outcomes": 4, "location": 3}
    )

    after = await svc.get_match_ready(p.id)
    assert after["match_ready"] is True, after["missing"]
    assert after["completeness_pct"] >= 35
    assert after["missing"] == []


async def test_match_ready_geography_via_relocation(db_session):
    """Geography satisfied by willingness_to_relocate=conditional (§6.1)."""
    p = await _student(db_session)
    svc = IntakeEngineService(db_session)
    await _fill_core(svc, p.id)
    await svc.ingest_form_save(p.id, "willingness_to_relocate", "conditional")
    await svc.ingest_form_save(p.id, "preference_weights", {"cost": 5, "outcomes": 4, "culture": 2})
    after = await svc.get_match_ready(p.id)
    assert after["match_ready"] is True, after["missing"]


# ── §4.2 / §6.2 apply-ready gating ────────────────────────────────────────────
async def test_apply_ready_gate_per_program(db_session):
    p = await _student(db_session)
    svc = IntakeEngineService(db_session)
    prog = await _program(
        db_session, app_requirements={"recommendations_required": 2, "test_policy": "required"}
    )
    await _fill_core(svc, p.id)

    ar = await svc.get_apply_ready(p.id, prog.id)
    assert ar["ready_to_submit"] is False
    core = next(r for r in ar["requirements"] if r["key"] == "core_profile")
    assert core["satisfied"] is True
    recs = next(r for r in ar["requirements"] if r["key"] == "recommendations")
    assert recs["satisfied"] is False  # 0/2

    await svc.ingest_form_save(p.id, "recommenders_count", 2)
    await svc.ingest_form_save(p.id, "test_scores_provided", True)

    ar2 = await svc.get_apply_ready(p.id, prog.id)
    assert ar2["ready_to_submit"] is True


# ── §6 clarification loop ─────────────────────────────────────────────────────
async def test_clarification_loop_low_confidence_then_confirm(db_session):
    p = await _student(db_session)
    svc = IntakeEngineService(db_session)

    # low-confidence extraction (<60) opens a clarification (§5/§6).
    out = await svc.ingest_signal(
        p.id,
        "target_major_field_primary",
        "Robotics",
        channel="discovery_chat",
        source="system-extracted",
        structured=False,
        llm_confidence=40,
    )
    assert out["confidence"] == 40
    assert out["clarification_id"] is not None

    clars = await svc.list_clarifications(p.id)
    assert len(clars) == 1
    assert clars[0]["signal_name"] == "target_major_field_primary"
    assert clars[0]["suggested_value"] == "Robotics"

    # confirm → confidence 95, clarification closes (§6 / §9.4 replace not blend).
    res = await svc.resolve_clarification(p.id, uuid.UUID(clars[0]["id"]), action="confirm")
    assert res["status"] == "confirmed"
    sig = await svc._get_signal(p.id, "target_major_field_primary")
    assert sig.confidence == 95
    assert sig.source == "student-typed"
    assert await svc.list_clarifications(p.id) == []


async def test_clarification_correct_overrides_value(db_session):
    p = await _student(db_session)
    svc = IntakeEngineService(db_session)
    out = await svc.ingest_signal(
        p.id,
        "target_major_field_primary",
        "Robotics",
        channel="discovery_chat",
        source="system-extracted",
        structured=False,
        llm_confidence=30,
    )
    clar_id = uuid.UUID(out["clarification_id"])
    res = await svc.resolve_clarification(
        p.id, clar_id, action="correct", value="Mechanical Engineering"
    )
    assert res["status"] == "corrected"
    sig = await svc._get_signal(p.id, "target_major_field_primary")
    assert sig.value == {"v": "Mechanical Engineering"}
    assert sig.confidence == 95


# ── §10/§11 consent enforcement: matching=false → no LLM call ─────────────────
async def test_consent_off_takes_deterministic_path_no_llm(db_session, monkeypatch):
    import unipaith.ai.document_parse_triage as triage_mod
    from unipaith import config as config_mod

    monkeypatch.setattr(config_mod.settings, "ai_intake_engine_v2_enabled", True, raising=False)

    calls: list = []

    async def _spy(**kwargs):  # pragma: no cover — should not run when consent off
        calls.append(kwargs)
        return None

    monkeypatch.setattr(triage_mod, "triage_parse", _spy)

    # consent_matching OFF → no LLM call (§11).
    p_off = await _student(db_session, matching=False)
    svc = IntakeEngineService(db_session)
    await svc.ingest_document_upload(
        p_off.id, file_ref="transcript.pdf", parsed_fields={"gpa_reported": "3.5"}
    )
    assert calls == []  # the triage agent was never invoked
    sig = await svc._get_signal(p_off.id, "gpa_reported")
    assert sig is not None and sig.source == "student-uploaded"

    # consent ON + flag ON → the LLM triage path IS taken (spy fires).
    p_on = await _student(db_session, matching=True)
    await svc.ingest_document_upload(
        p_on.id, file_ref="transcript.pdf", parsed_fields={"gpa_reported": "3.5"}
    )
    assert len(calls) == 1


async def test_should_use_llm_respects_flag_and_consent(db_session, monkeypatch):
    from unipaith import config as config_mod

    svc = IntakeEngineService(db_session)
    p_on = await _student(db_session, matching=True)
    p_off = await _student(db_session, matching=False)

    monkeypatch.setattr(config_mod.settings, "ai_intake_engine_v2_enabled", False, raising=False)
    assert await svc._should_use_llm(p_on.id) is False  # flag off

    monkeypatch.setattr(config_mod.settings, "ai_intake_engine_v2_enabled", True, raising=False)
    assert await svc._should_use_llm(p_on.id) is True
    assert await svc._should_use_llm(p_off.id) is False  # consent off


async def test_message_channel_requires_matching_consent(db_session):
    """§5.1 conversational intake is consent-gated; raw input still recorded."""
    p = await _student(db_session, matching=False)
    svc = IntakeEngineService(db_session)
    # fetch the user id behind the profile
    user_id = (
        await db_session.execute(select(StudentProfile.user_id).where(StudentProfile.id == p.id))
    ).scalar_one()
    with pytest.raises(BadRequestException):
        await svc.ingest_message(user_id, uuid.uuid4(), "I want to study CS")
    raws = (
        (
            await db_session.execute(
                select(RawInput).where(
                    RawInput.student_id == p.id, RawInput.channel == "discovery_chat"
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(raws) == 1  # raw input layer captured even when LLM is gated off


# ── §3.4 cross-module fanout ──────────────────────────────────────────────────
async def test_fanout_invalidates_match_results(db_session):
    p = await _student(db_session)
    svc = IntakeEngineService(db_session)
    prog = await _program(db_session)
    db_session.add(
        MatchResult(
            student_id=p.id,
            program_id=prog.id,
            fitness_score=Decimal("0.5"),
            confidence_score=Decimal("0.5"),
        )
    )
    await db_session.flush()

    await svc.ingest_form_save(p.id, "target_degree_level", "master")

    remaining = (
        (await db_session.execute(select(MatchResult).where(MatchResult.student_id == p.id)))
        .scalars()
        .all()
    )
    # A signal change marks materialized matches STALE (it no longer deletes them),
    # so the lazy recompute on the next GET /me/matches regenerates them instead of
    # collapsing to an empty list. (Deleting left zero rows the lazy path — which
    # only fires on stale rows — could never detect, so matches never came back.)
    assert len(remaining) == 1
    assert remaining[0].is_stale is True


# ── §5.4 external link + §4 completeness ──────────────────────────────────────
async def test_external_link_validation_and_confidence(db_session):
    p = await _student(db_session)
    svc = IntakeEngineService(db_session)
    with pytest.raises(BadRequestException):
        await svc.ingest_external_link(p.id, url="not-a-url", kind="linkedin")
    out = await svc.ingest_external_link(p.id, url="https://linkedin.com/in/jane", kind="linkedin")
    assert out["source"] == "student-link"
    assert out["confidence"] == 75  # §5


async def test_completeness_map_counts_by_category(db_session):
    p = await _student(db_session)
    svc = IntakeEngineService(db_session)
    await svc.ingest_form_save(p.id, "legal_name", "Jane Doe")
    await svc.ingest_form_save(p.id, "primary_email", "jane@example.com")
    comp = await svc.get_completeness(p.id)
    assert comp["overall_profile_completeness_pct"] > 0
    identity = next(c for c in comp["categories"] if c["category"] == "identity")
    assert identity["present"] >= 2


async def test_invalid_enum_value_opens_clarification(db_session):
    """A value that fails the schema check (§3.2) is persisted low-confidence
    with a clarification rather than 5xxing (§6)."""
    p = await _student(db_session)
    svc = IntakeEngineService(db_session)
    out = await svc.ingest_form_save(p.id, "target_start_term_season", "monsoon")
    assert out["valid"] is False
    assert out["confidence"] <= 40
    assert out["clarification_id"] is not None


# ── API smoke (router wiring + auth scoping) ──────────────────────────────────
async def test_intake_api_endpoints_smoke(student_client, db_session, mock_student_user):
    p = StudentProfile(user_id=mock_student_user.id)
    db_session.add(p)
    await db_session.flush()
    db_session.add(StudentDataConsent(student_id=p.id, consent_matching=True))
    await db_session.flush()

    r = await student_client.post(
        "/api/v1/students/me/intake/form-save",
        json={"signal_name": "target_degree_level", "value": "master's"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["value"] == "master"

    r2 = await student_client.get("/api/v1/students/me/intake/match-ready")
    assert r2.status_code == 200
    assert r2.json()["match_ready"] is False

    r3 = await student_client.get("/api/v1/students/me/intake/completeness")
    assert r3.status_code == 200
    assert r3.json()["overall_profile_completeness_pct"] >= 0

    r4 = await student_client.get("/api/v1/students/me/intake/clarifications")
    assert r4.status_code == 200
    assert "clarifications" in r4.json()
