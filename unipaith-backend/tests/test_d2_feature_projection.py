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
