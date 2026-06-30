"""AI Structure (Spec 2 §3.4) — derive a baseline target-applicant ProgramPreference
from real program attributes. Grounded-only; omit-never-guess. The output keys mirror
exactly what matching.cpef_program_to_student reads."""

from __future__ import annotations

from unipaith.services.match.derive_preferences import (
    DERIVED_CONFIDENCE,
    DERIVED_SOURCE,
    derive_program_preference,
)


def test_masters_cs_program_derives_fields_levels_source():
    pref = derive_program_preference(
        program_name="Master of Science in Computer Science", degree_type="masters"
    )
    assert pref is not None
    assert pref["pref_fields"] == ["computer_science"]
    # masters target -> eligible current levels (inverse of the veto compat table)
    assert pref["pref_levels"] == ["bachelors", "masters", "working"]
    assert pref["source"] == DERIVED_SOURCE
    assert pref["confidence"] == DERIVED_CONFIDENCE == 0.4
    assert "pref_min_gpa" not in pref  # no class profile -> omitted


def test_bachelors_full_word_levels_and_field():
    pref = derive_program_preference(
        program_name="Bachelor of Science in Biology", degree_type="bachelors"
    )
    assert pref["pref_fields"] == ["biology"]
    assert pref["pref_levels"] == ["high_school", "gap_year"]


def test_phd_full_word_maps_to_doctoral_levels():
    pref = derive_program_preference(program_name="PhD in Economics", degree_type="phd")
    assert pref["pref_fields"] == ["economics"]
    assert pref["pref_levels"] == ["bachelors", "masters", "working"]


def test_cip_family_fallback_when_name_unclassifiable():
    pref = derive_program_preference(
        cip_code="11.0701", program_name="Program XYZ", degree_type="masters"
    )
    assert pref["pref_fields"] == ["computer_science"]  # CIP 11 -> CS


def test_class_profile_gpa_floor_prefers_p25():
    pref = derive_program_preference(
        program_name="MS Statistics",
        degree_type="masters",
        class_profile={"gpa_p25": 3.6, "gpa_p50": 3.8},
    )
    assert pref["pref_min_gpa"] == 3.6


def test_gpa_omitted_when_only_test_scores_present():
    pref = derive_program_preference(
        program_name="MS Statistics",
        degree_type="masters",
        class_profile={"gre_p50": 320},
    )
    assert "pref_min_gpa" not in pref


def test_gpa_reads_editorial_median_gpa_key():
    # Program.class_profile JSONB uses median_gpa (MIT 3.92), not the typed gpa_p* keys.
    pref = derive_program_preference(
        program_name="MS Business Analytics",
        degree_type="masters",
        class_profile={"median_gpa": 3.92, "cohort_size": "~130 students"},
    )
    assert pref["pref_min_gpa"] == 3.92


def test_gpa_reads_editorial_avg_gpa_key():
    # Harvard/Stanford JSONB use avg_gpa.
    pref = derive_program_preference(
        program_name="MS Statistics", degree_type="masters", class_profile={"avg_gpa": 3.76}
    )
    assert pref["pref_min_gpa"] == 3.76


def test_gpa_precedence_p25_floor_over_editorial_median():
    pref = derive_program_preference(
        program_name="MS Statistics",
        degree_type="masters",
        class_profile={"gpa_p25": 3.5, "median_gpa": 3.9},
    )
    assert pref["pref_min_gpa"] == 3.5  # a true 25th-pct floor wins over the median


def test_certificate_level_is_ambiguous_so_omitted():
    # certificate -> no target level (omit pref_levels); unclassifiable name -> no
    # field -> nothing grounds -> None (the program keeps "no opinion").
    pref = derive_program_preference(program_name="Certificate Program", degree_type="certificate")
    assert pref is None


def test_unclassifiable_name_and_no_degree_returns_none():
    assert derive_program_preference(program_name="General Studies", degree_type=None) is None


def test_certificate_with_classifiable_field_still_derives_fields_only():
    pref = derive_program_preference(
        program_name="Graduate Certificate in Data Science", degree_type="certificate"
    )
    assert pref is not None
    assert pref["pref_fields"] == ["data_science"]
    assert "pref_levels" not in pref  # certificate target ambiguous -> omitted


async def test_backfill_inserts_derived_rows_idempotently_and_skips_claimed(db_session):
    """backfill_program_preferences derives a row per program that lacks one, never
    overwrites an existing (claimed/derived) row, and is idempotent on re-run."""
    from decimal import Decimal

    from sqlalchemy import select

    from unipaith.models.institution import (
        Institution,
        Program,
        ProgramPreference,
    )
    from unipaith.models.user import User, UserRole
    from unipaith.services.match.derive_preferences import backfill_program_preferences

    admin = User(email="backfill-admin@example.com", role=UserRole.institution_admin)
    db_session.add(admin)
    await db_session.flush()
    inst = Institution(
        admin_user_id=admin.id,
        name="Backfill Test University",
        type="university",
        country="United States",
    )
    db_session.add(inst)
    await db_session.flush()

    p_cs = Program(
        institution_id=inst.id,
        program_name="Master of Science in Computer Science",
        degree_type="masters",
        slug="bf-cs",
    )
    p_bio = Program(
        institution_id=inst.id,
        program_name="Bachelor of Science in Biology",
        degree_type="bachelors",
        slug="bf-bio",
    )
    # Already-claimed program: must NOT be overwritten.
    p_claimed = Program(
        institution_id=inst.id,
        program_name="PhD in Economics",
        degree_type="phd",
        slug="bf-econ",
    )
    db_session.add_all([p_cs, p_bio, p_claimed])
    await db_session.flush()
    claimed_pref = ProgramPreference(
        program_id=p_claimed.id,
        source="claimed",
        confidence=Decimal("1.00"),
        pref_fields=["finance"],
    )
    db_session.add(claimed_pref)
    await db_session.flush()

    inst_id, cs_id, claimed_id = inst.id, p_cs.id, p_claimed.id

    # backfill_program_preferences is sync; run it on the sync bind of the async
    # session's transaction, doing all reads inside the sync block (no cross-session
    # identity-map games). Never commit — the fixture rolls the transaction back.
    sync_conn = await db_session.connection()

    def _run(conn):
        from sqlalchemy.orm import Session

        with Session(bind=conn) as s:
            n1 = backfill_program_preferences(s, institution_id=inst_id)
            n2 = backfill_program_preferences(s, institution_id=inst_id)  # idempotent re-run
            rows = s.scalars(select(ProgramPreference)).all()
            data = {
                str(r.program_id): (
                    r.source,
                    list(r.pref_fields or []),
                    float(r.confidence) if r.confidence is not None else None,
                )
                for r in rows
            }
            return n1, n2, data

    n1, n2, data = await sync_conn.run_sync(_run)
    assert n1 == 2  # cs + bio derived; claimed skipped
    assert n2 == 0  # idempotent — no new rows on re-run
    assert data[str(cs_id)][0] == "derived"
    assert data[str(cs_id)][1] == ["computer_science"]
    assert data[str(cs_id)][2] == 0.4
    # claimed row untouched
    assert data[str(claimed_id)][0] == "claimed"
    assert data[str(claimed_id)][1] == ["finance"]


async def test_refresh_sets_gpa_floor_on_existing_derived_rows_from_jsonb(db_session):
    """refresh_derived_gpa_floors fills pref_min_gpa on a derived row that lacks it,
    reading the editorial Program.class_profile JSONB; never touches a claimed row nor an
    already-set value, and is idempotent."""
    from decimal import Decimal

    from sqlalchemy import select

    from unipaith.models.institution import Institution, Program, ProgramPreference
    from unipaith.models.user import User, UserRole
    from unipaith.services.match.derive_preferences import refresh_derived_gpa_floors

    admin = User(email="refresh-admin@example.com", role=UserRole.institution_admin)
    db_session.add(admin)
    await db_session.flush()
    inst = Institution(
        admin_user_id=admin.id, name="Refresh Test U", type="university", country="United States"
    )
    db_session.add(inst)
    await db_session.flush()

    # derived row missing gpa; program HAS class_profile JSONB with median_gpa -> filled.
    p1 = Program(
        institution_id=inst.id,
        program_name="MS Data Science",
        degree_type="masters",
        slug="rf-ds",
        class_profile={"median_gpa": 3.8},
    )
    # derived row already has gpa -> must NOT change.
    p2 = Program(
        institution_id=inst.id,
        program_name="MS Statistics",
        degree_type="masters",
        slug="rf-st",
        class_profile={"median_gpa": 3.5},
    )
    # claimed row missing gpa -> must NOT change (first-party never touched).
    p3 = Program(
        institution_id=inst.id,
        program_name="PhD Economics",
        degree_type="phd",
        slug="rf-ec",
        class_profile={"median_gpa": 3.9},
    )
    db_session.add_all([p1, p2, p3])
    await db_session.flush()
    db_session.add_all(
        [
            ProgramPreference(
                program_id=p1.id,
                source="derived",
                confidence=Decimal("0.40"),
                pref_fields=["data_science"],
            ),
            ProgramPreference(
                program_id=p2.id,
                source="derived",
                confidence=Decimal("0.40"),
                pref_min_gpa=Decimal("3.10"),
            ),
            ProgramPreference(program_id=p3.id, source="claimed", confidence=Decimal("1.00")),
        ]
    )
    await db_session.flush()
    inst_id, id1, id2, id3 = inst.id, p1.id, p2.id, p3.id
    sync_conn = await db_session.connection()

    def _run(conn):
        from sqlalchemy.orm import Session

        with Session(bind=conn) as s:
            n1 = refresh_derived_gpa_floors(s, institution_id=inst_id)
            n2 = refresh_derived_gpa_floors(s, institution_id=inst_id)  # idempotent
            rows = {
                str(r.program_id): (
                    r.source,
                    float(r.pref_min_gpa) if r.pref_min_gpa is not None else None,
                )
                for r in s.scalars(select(ProgramPreference)).all()
            }
            return n1, n2, rows

    n1, n2, rows = await sync_conn.run_sync(_run)
    assert n1 == 1  # only p1 filled
    assert n2 == 0  # idempotent
    assert rows[str(id1)] == ("derived", 3.8)  # filled from JSONB median_gpa
    assert rows[str(id2)] == ("derived", 3.1)  # already set -> unchanged
    assert rows[str(id3)] == ("claimed", None)  # claimed untouched
