"""Slice D.2 — matcher feature projection (Spec 3): student GPA/field + program
preferences overlaid onto the matcher sparse vectors so the CPEF program→student
direction fires with real data."""

from decimal import Decimal

import pytest

from tests._uni_helpers import ensure_profile
from unipaith.models.ai_artifacts import StudentFeatureVector
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.models.student import AcademicRecord
from unipaith.services.match_service import MatchService
from unipaith.services.matching import ProgramFeatures


@pytest.mark.asyncio
async def test_student_gpa_and_field_overlaid(db_session, mock_student_user):
    profile = await ensure_profile(db_session, mock_student_user)
    db_session.add(
        AcademicRecord(
            student_id=profile.id,
            is_current=True,
            normalized_gpa=Decimal("3.70"),
            # RAW free-text, as real applicants enter it — the overlay must
            # CANONICALIZE it to the FIELD_SIM_TABLE vocab so the s→p field
            # signal matches the (canonicalized) program-side fields_offered.
            # Seeding an already-canonical value here previously hid this gap.
            field_of_study="Computer Science",
            institution_name="Prior University",
            degree_type="bachelors",
        )
    )
    db_session.add(
        StudentFeatureVector(
            student_id=profile.id, sparse_features={"education_level": "bachelors"}
        )
    )
    await db_session.flush()

    feats = await MatchService(db_session)._student_features(profile.id)
    assert feats is not None
    assert feats.sparse["gpa"] == 3.7
    # canonicalized from the raw "Computer Science" — NOT the raw string
    assert feats.sparse["field_of_study"] == "computer_science"
    # existing keys preserved
    assert feats.sparse["education_level"] == "bachelors"


@pytest.mark.asyncio
async def test_program_preferences_overlaid(institution_client, db_session, mock_institution_user):
    inst = Institution(
        admin_user_id=mock_institution_user.id, name="Test U", type="university", country="USA"
    )
    db_session.add(inst)
    await db_session.flush()
    prog = Program(institution_id=inst.id, program_name="MS in Data Science", degree_type="masters")
    db_session.add(prog)
    await db_session.flush()
    db_session.add(
        ProgramPreference(
            program_id=prog.id,
            pref_min_gpa=Decimal("3.50"),
            pref_fields=["data_science"],
            pref_levels=["bachelors"],
            source="derived",
        )
    )
    await db_session.flush()

    pf = ProgramFeatures(program_id=prog.id, sparse={})
    await MatchService(db_session)._overlay_program_prefs([pf])
    assert pf.sparse["pref_min_gpa"] == 3.5
    assert pf.sparse["pref_fields"] == ["data_science"]
    assert pf.sparse["pref_levels"] == ["bachelors"]


@pytest.mark.asyncio
async def test_program_without_prefs_is_untouched(db_session):
    import uuid

    pf = ProgramFeatures(program_id=uuid.uuid4(), sparse={})
    await MatchService(db_session)._overlay_program_prefs([pf])
    assert "pref_min_gpa" not in pf.sparse  # no opinion → no keys


# ── AI Structure round-3 livewire: real two-sided confidence on live data ────


@pytest.mark.asyncio
async def test_c_student_varies_with_real_profile_completeness(db_session, mock_student_user):
    """GAP 1 — c_student (extractor_quality) must be DERIVED from the profile's
    real feature_completeness, not the old hardcoded 0.85 constant. A deeper
    profile yields a higher c_student than a thin one."""
    profile = await ensure_profile(db_session, mock_student_user)
    db_session.add(
        StudentFeatureVector(
            student_id=profile.id,
            sparse_features={"education_level": "bachelors", "feature_completeness": 0.2},
        )
    )
    await db_session.flush()
    thin = await MatchService(db_session)._student_features(profile.id)
    assert thin is not None
    thin_c = thin.extractor_quality

    # Deepen the profile → completeness climbs → c_student must climb too.
    fv = await db_session.get(StudentFeatureVector, profile.id)
    assert fv is not None
    fv.sparse_features = {"education_level": "bachelors", "feature_completeness": 0.95}
    await db_session.flush()
    deep = await MatchService(db_session)._student_features(profile.id)
    assert deep is not None
    assert deep.extractor_quality > thin_c
    # not the old constant
    assert thin_c != 0.85
    assert 0.0 <= thin_c <= 1.0 and 0.0 <= deep.extractor_quality <= 1.0


@pytest.mark.asyncio
async def test_claimed_preference_lifts_c_program(
    institution_client, db_session, mock_institution_user
):
    """Spec 2 claim hinge — a CLAIMED program preference yields a higher
    c_program (data_completeness) than an otherwise-identical derived one."""
    inst = Institution(
        admin_user_id=mock_institution_user.id, name="Claim U", type="university", country="USA"
    )
    db_session.add(inst)
    await db_session.flush()
    claimed_prog = Program(institution_id=inst.id, program_name="MS Claimed", degree_type="masters")
    derived_prog = Program(institution_id=inst.id, program_name="MS Derived", degree_type="masters")
    db_session.add_all([claimed_prog, derived_prog])
    await db_session.flush()
    db_session.add(
        ProgramPreference(
            program_id=claimed_prog.id, pref_fields=["data_science"], source="claimed"
        )
    )
    db_session.add(
        ProgramPreference(
            program_id=derived_prog.id, pref_fields=["data_science"], source="derived"
        )
    )
    await db_session.flush()

    claimed_pf = ProgramFeatures(program_id=claimed_prog.id, sparse={}, data_completeness=0.5)
    derived_pf = ProgramFeatures(program_id=derived_prog.id, sparse={}, data_completeness=0.5)
    await MatchService(db_session)._overlay_program_prefs([claimed_pf, derived_pf])
    assert claimed_pf.data_completeness > derived_pf.data_completeness
    assert claimed_pf.data_completeness >= 0.9


# ── Spec 3 §3 typed-fit columns: the 5 deferred columns now project + fire ───
# Each test seeds the REAL ORM column, asserts the value lands in the matcher
# sparse vector, AND that the corresponding dormant CPEF signal now fires on it.


@pytest.mark.asyncio
async def test_student_preference_typed_fit_attrs_overlaid_and_fire(db_session, mock_student_user):
    """The new StudentPreference columns (desired_time_to_degree_months +
    wants_part_time/online/career_support) must project into the student sparse
    vector via _overlay_student_attrs, and each must drive its CPEF signal."""
    from unipaith.models.student import StudentPreference
    from unipaith.services.match.params import DEFAULT_PARAMS
    from unipaith.services.matching import _build_cpef_signals

    profile = await ensure_profile(db_session, mock_student_user)
    db_session.add(
        StudentPreference(
            student_id=profile.id,
            desired_time_to_degree_months=24,
            wants_part_time=True,
            wants_online=True,
            wants_career_support=True,
        )
    )
    db_session.add(StudentFeatureVector(student_id=profile.id, sparse_features={}))
    await db_session.flush()

    feats = await MatchService(db_session)._student_features(profile.id)
    assert feats is not None
    # each column projected into the sparse vector
    assert feats.sparse["desired_time_to_degree_months"] == 24
    assert feats.sparse["wants_part_time"] is True
    assert feats.sparse["wants_online"] is True
    assert feats.sparse["wants_career_support"] is True

    # and now each dormant signal FIRES against a matching program
    program = ProgramFeatures(
        program_id="p",
        sparse={
            "duration_months": 24,
            "part_time_available": True,
            "online_available": True,
            "career_services": True,
        },
    )
    signals, _db, _w = _build_cpef_signals(feats, program, DEFAULT_PARAMS)
    keys = {s["key"] for s in signals}
    assert "time" in keys
    assert "flexibility" in keys
    assert "support" in keys


@pytest.mark.asyncio
async def test_student_preference_absent_typed_fit_attrs_emit_no_signal(
    db_session, mock_student_user
):
    """Gated: a StudentPreference with the typed-fit columns left NULL injects no
    phantom dimension — no key in the sparse vector, no signal fired."""
    from unipaith.models.student import StudentPreference
    from unipaith.services.match.params import DEFAULT_PARAMS
    from unipaith.services.matching import _build_cpef_signals

    profile = await ensure_profile(db_session, mock_student_user)
    db_session.add(StudentPreference(student_id=profile.id))  # all typed-fit cols null
    db_session.add(StudentFeatureVector(student_id=profile.id, sparse_features={}))
    await db_session.flush()

    feats = await MatchService(db_session)._student_features(profile.id)
    assert feats is not None
    assert "desired_time_to_degree_months" not in feats.sparse
    assert "wants_part_time" not in feats.sparse
    assert "wants_online" not in feats.sparse
    assert "wants_career_support" not in feats.sparse

    program = ProgramFeatures(
        program_id="p",
        sparse={"duration_months": 24, "part_time_available": True, "career_services": True},
    )
    signals, _db, _w = _build_cpef_signals(feats, program, DEFAULT_PARAMS)
    keys = {s["key"] for s in signals}
    assert "time" not in keys
    assert "flexibility" not in keys
    assert "support" not in keys


@pytest.mark.asyncio
async def test_student_preference_degree_target_overlaid_and_fires(db_session, mock_student_user):
    """StudentPreference.target_degree_level must project into the student sparse
    vector as a canonicalized `degree_level_target` and drive the degree_level
    CPEF signal — previously a dead signal (the key was read by the matcher but
    never written by any production code path)."""
    from unipaith.models.student import StudentPreference
    from unipaith.services.match.params import DEFAULT_PARAMS
    from unipaith.services.matching import _build_cpef_signals

    profile = await ensure_profile(db_session, mock_student_user)
    db_session.add(StudentPreference(student_id=profile.id, target_degree_level="masters"))
    db_session.add(StudentFeatureVector(student_id=profile.id, sparse_features={}))
    await db_session.flush()

    feats = await MatchService(db_session)._student_features(profile.id)
    assert feats is not None
    # the onboarding value ("masters") is canonicalized to the matcher's vocab
    assert feats.sparse["degree_level_target"] == "masters"

    program = ProgramFeatures(program_id="p", sparse={"target_education_level": "masters"})
    signals, _db, _w = _build_cpef_signals(feats, program, DEFAULT_PARAMS)
    assert "degree_level" in {s["key"] for s in signals}


@pytest.mark.asyncio
async def test_student_preference_absent_degree_target_emits_no_degree_signal(
    db_session, mock_student_user
):
    """Gated: a StudentPreference with target_degree_level NULL injects no
    degree_level_target key and fires no degree_level signal (no phantom)."""
    from unipaith.models.student import StudentPreference
    from unipaith.services.match.params import DEFAULT_PARAMS
    from unipaith.services.matching import _build_cpef_signals

    profile = await ensure_profile(db_session, mock_student_user)
    db_session.add(StudentPreference(student_id=profile.id))  # target_degree_level null
    db_session.add(StudentFeatureVector(student_id=profile.id, sparse_features={}))
    await db_session.flush()

    feats = await MatchService(db_session)._student_features(profile.id)
    assert feats is not None
    assert "degree_level_target" not in feats.sparse
    program = ProgramFeatures(program_id="p", sparse={"target_education_level": "masters"})
    signals, _db, _w = _build_cpef_signals(feats, program, DEFAULT_PARAMS)
    assert "degree_level" not in {s["key"] for s in signals}


@pytest.mark.asyncio
async def test_program_part_time_available_projects_and_fires_flexibility(
    institution_client, db_session, mock_institution_user
):
    """The new Program.part_time_available column must flow through
    program_row_from_orm → features_from_row into the program sparse vector, and
    fire the flexibility signal for a student who wants part-time."""
    from unipaith.services.match.params import DEFAULT_PARAMS
    from unipaith.services.matching import StudentFeatures, _build_cpef_signals
    from unipaith.services.program_features import features_from_row, program_row_from_orm

    inst = Institution(
        admin_user_id=mock_institution_user.id, name="PT U", type="university", country="USA"
    )
    db_session.add(inst)
    await db_session.flush()
    prog = Program(
        institution_id=inst.id,
        program_name="MS Flexible",
        degree_type="masters",
        part_time_available=True,
    )
    db_session.add(prog)
    await db_session.flush()

    row = program_row_from_orm(prog)
    assert row.part_time_available is True
    pf = features_from_row(row)
    assert pf.sparse["part_time_available"] is True

    stu = StudentFeatures(sparse={"wants_part_time": True}, extractor_quality=0.9)
    signals, _db, _w = _build_cpef_signals(stu, pf, DEFAULT_PARAMS)
    flex = next(s for s in signals if s["key"] == "flexibility")
    assert flex["f"] == 1.0  # program offers it → full fit


@pytest.mark.asyncio
async def test_program_null_part_time_emits_no_part_time_key(
    institution_client, db_session, mock_institution_user
):
    """A program that never set part_time_available leaves the sparse key absent
    (gated) — never a fabricated False."""
    from unipaith.services.program_features import features_from_row, program_row_from_orm

    inst = Institution(
        admin_user_id=mock_institution_user.id, name="No-PT U", type="university", country="USA"
    )
    db_session.add(inst)
    await db_session.flush()
    prog = Program(institution_id=inst.id, program_name="MS Standard", degree_type="masters")
    db_session.add(prog)
    await db_session.flush()

    row = program_row_from_orm(prog)
    assert row.part_time_available is None
    pf = features_from_row(row)
    assert "part_time_available" not in pf.sparse
