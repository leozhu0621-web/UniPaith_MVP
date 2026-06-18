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
            field_of_study="data_science",
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
    assert feats.sparse["field_of_study"] == "data_science"
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
