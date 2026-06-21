from __future__ import annotations

import pytest


def test_profile_intelligence_requires_evidence_for_every_conclusion():
    from pydantic import ValidationError

    from unipaith.schemas.profile_intelligence import ProfileIntelligence

    with pytest.raises(ValidationError):
        ProfileIntelligence.model_validate(
            {
                "standard_version": 1,
                "profile_version": 1,
                "sections": {
                    "academic_orientation": {
                        "findings": [
                            {
                                "statement": "This program is analytically rigorous.",
                                "source_type": "inferred",
                                "confidence": 0.8,
                                "freshness": {"status": "current"},
                                "evidence": [],
                            }
                        ]
                    }
                },
            }
        )


def test_profile_intelligence_rejects_stale_time_sensitive_conclusion():
    from pydantic import ValidationError

    from unipaith.schemas.profile_intelligence import ProfileIntelligence

    with pytest.raises(ValidationError):
        ProfileIntelligence.model_validate(
            {
                "standard_version": 1,
                "profile_version": 1,
                "sections": {
                    "career_pathways": {
                        "findings": [
                            {
                                "statement": "The deadline is still open.",
                                "source_type": "fact",
                                "confidence": 0.9,
                                "time_sensitive": True,
                                "freshness": {"status": "stale"},
                                "evidence": [
                                    {
                                        "label": "Program admissions",
                                        "url": "https://example.edu/admissions",
                                        "source_type": "official",
                                        "freshness": {"status": "stale"},
                                    }
                                ],
                            }
                        ]
                    }
                },
            }
        )


def test_target_profile_rejects_protected_trait_scoring():
    from pydantic import ValidationError

    from unipaith.schemas.profile_intelligence import TargetProfile

    with pytest.raises(ValidationError):
        TargetProfile.model_validate(
            {
                "standard_version": 1,
                "layers": {
                    "background_academic": [
                        {
                            "attribute": "race",
                            "preferred_values": ["any"],
                            "weight": 0.2,
                            "confidence": 0.8,
                            "evidence": [
                                {
                                    "label": "Bad source",
                                    "url": "https://example.edu",
                                    "source_type": "official",
                                    "freshness": {"status": "current"},
                                }
                            ],
                        }
                    ],
                    "goals_behaviors_learning_working_style": [],
                    "values_motivations_community": [],
                },
            }
        )


def test_target_profile_rejects_protected_trait_omissions():
    from pydantic import ValidationError

    from unipaith.schemas.profile_intelligence import TargetProfile

    with pytest.raises(ValidationError):
        TargetProfile.model_validate(
            {
                "standard_version": 1,
                "layers": {
                    "background_academic": [],
                    "goals_behaviors_learning_working_style": [],
                    "values_motivations_community": [],
                },
                "omissions": [
                    {
                        "layer": "values_motivations_community",
                        "reason": "No gender-specific target evidence.",
                        "source": "derived",
                    }
                ],
            }
        )


def test_builds_program_intelligence_with_cited_sections():
    from unipaith.models.institution import Program
    from unipaith.services.profile_enrichment.intelligence import (
        build_program_profile_intelligence,
    )

    program = Program(
        program_name="Master of Business Analytics",
        degree_type="masters",
        description_text=(
            "A rigorous analytics program using optimization, machine learning, "
            "team projects, and a capstone with employer sponsors."
        ),
        website_url="https://mitsloan.mit.edu/master-of-business-analytics",
        who_its_for="Students with strong quantitative preparation seeking data-science careers.",
        tracks={
            "learning_format": "Team-based coursework and a year-long Analytics Capstone",
            "curriculum": [{"term": "Fall", "courses": ["Optimization", "Machine Learning"]}],
        },
        outcomes_data={
            "median_salary": 143000,
            "top_industries": ["Technology", "Consulting"],
            "source": "MIT Sloan MBAn Employment Report",
            "source_url": "https://mitsloan.mit.edu/sites/default/files/2026-04/2025%20MBAn%20Employment%20Report.pdf",
        },
        external_reviews={
            "summary": "Students praise the rigor and close cohort while noting the intense pace.",
            "themes": [{"label": "Intense pace", "sentiment": "caution", "detail": "Fast year."}],
            "sources": [
                {
                    "label": "MIT Sloan MBAn profile",
                    "url": "https://mitsloan.mit.edu/master-of-business-analytics",
                }
            ],
        },
    )

    intel = build_program_profile_intelligence(program)

    assert intel["standard_version"] == 1
    assert intel["sections"]["academic_orientation"]["findings"]
    assert intel["sections"]["career_pathways"]["findings"]
    assert intel["sections"]["who_thrives"]["findings"]
    assert intel["sections"]["challenges_tradeoffs"]["findings"]
    for section in intel["sections"].values():
        for finding in section.get("findings", []):
            assert finding["evidence"], finding
            assert all(e.get("url", "").startswith("http") for e in finding["evidence"])


def test_derived_target_profile_has_three_layers_and_no_protected_traits():
    from unipaith.schemas.profile_intelligence import assert_no_protected_traits
    from unipaith.services.match.derive_preferences import derive_program_preference

    pref = derive_program_preference(
        cip_code="11.0802",
        program_name="Master of Business Analytics",
        degree_type="masters",
        class_profile={"gpa_p25": 3.7, "median_gre_quant": 169},
        description=(
            "A rigorous applied analytics program with machine learning, optimization, "
            "team projects, and an Analytics Capstone for sponsor organizations."
        ),
        outcomes_data={
            "top_industries": ["Technology", "Consulting"],
            "source": "Career report",
            "source_url": "https://example.edu/career-report",
        },
        application_requirements={
            "evaluation": "Quantitative aptitude, programming readiness, and collaboration.",
            "source_url": "https://example.edu/apply",
        },
        source_url="https://example.edu/program",
    )

    assert pref is not None
    target = pref["target_profile"]
    assert set(target["layers"]) == {
        "background_academic",
        "goals_behaviors_learning_working_style",
        "values_motivations_community",
    }
    assert all(target["layers"][name] for name in target["layers"])
    assert target["omissions"] == []
    assert_no_protected_traits(target)


def test_partial_derived_target_profile_records_layer_omissions():
    from unipaith.schemas.profile_intelligence import assert_no_protected_traits
    from unipaith.services.match.derive_preferences import derive_program_preference

    pref = derive_program_preference(
        cip_code="23.0101",
        program_name="MA in English",
        degree_type="masters",
        source_url="https://example.edu/english",
    )

    assert pref is not None
    target = pref["target_profile"]
    assert target["layers"]["background_academic"]
    assert target["layers"]["goals_behaviors_learning_working_style"]
    assert target["layers"]["values_motivations_community"] == []
    assert target["omissions"] == [
        {
            "layer": "values_motivations_community",
            "reason": "No eligible public evidence was available for this target-profile layer.",
            "source": "derived",
        }
    ]
    assert_no_protected_traits(target)


def test_omission_only_target_profile_records_all_missing_layers():
    from unipaith.schemas.profile_intelligence import assert_no_protected_traits
    from unipaith.services.match.derive_preferences import derive_program_preference

    pref = derive_program_preference(
        program_name="Graduate Certificate in Classics",
        degree_type="certificate",
        source_url="https://www.college.columbia.edu/",
        allow_omission_only_target_profile=True,
    )

    assert pref is not None
    assert pref["preference_weights"] == {}
    assert pref["provenance"]["method"] == "public_evidence_target_profile_omissions_v1"
    target = pref["target_profile"]
    assert target["layers"] == {
        "background_academic": [],
        "goals_behaviors_learning_working_style": [],
        "values_motivations_community": [],
    }
    assert target["omissions"] == [
        {
            "layer": "background_academic",
            "reason": "No eligible public evidence was available for this target-profile layer.",
            "source": "derived",
        },
        {
            "layer": "goals_behaviors_learning_working_style",
            "reason": "No eligible public evidence was available for this target-profile layer.",
            "source": "derived",
        },
        {
            "layer": "values_motivations_community",
            "reason": "No eligible public evidence was available for this target-profile layer.",
            "source": "derived",
        },
    ]
    assert_no_protected_traits(target)


def test_derived_target_profile_does_not_echo_protected_terms_from_program_name():
    from unipaith.schemas.profile_intelligence import assert_no_protected_traits
    from unipaith.services.match.derive_preferences import derive_program_preference

    pref = derive_program_preference(
        cip_code="23.0101",
        program_name="PhD in English and Women's and Gender Studies",
        degree_type="phd",
        description=(
            "A rigorous applied literature research program with collaborative "
            "project work and capstone-style scholarly practice."
        ),
        source_url="https://example.edu/program",
    )

    assert pref is not None
    assert pref["pref_fields"] == ["english"]
    target = pref["target_profile"]
    assert_no_protected_traits(target)
    assert "gender" not in str(target).lower()


def test_target_profile_allows_protected_terms_in_citation_urls_only():
    from unipaith.schemas.profile_intelligence import assert_no_protected_traits
    from unipaith.services.match.derive_preferences import derive_program_preference

    pref = derive_program_preference(
        cip_code="23.0101",
        program_name="PhD in English and Women's and Gender Studies",
        degree_type="phd",
        description=(
            "A rigorous applied literature research program with collaborative "
            "project work and capstone-style scholarly practice."
        ),
        source_url="https://example.edu/english-and-gender-studies",
    )

    assert pref is not None
    target = pref["target_profile"]
    for signals in target["layers"].values():
        for signal in signals:
            assert_no_protected_traits(
                {
                    "attribute": signal["attribute"],
                    "preferred_values": signal["preferred_values"],
                    "statement": signal["statement"],
                }
            )
    assert "english-and-gender-studies" in str(target).lower()


async def test_profile_intelligence_skips_claimed_program(db_session):
    from unipaith.models.institution import Institution, Program
    from unipaith.models.user import User, UserRole
    from unipaith.services.profile_enrichment.intelligence import ProfileIntelligenceService

    admin = User(email="intel-claim@example.com", role=UserRole.institution_admin)
    db_session.add(admin)
    await db_session.flush()
    inst = Institution(admin_user_id=admin.id, name="Claimed U", type="university", country="US")
    db_session.add(inst)
    await db_session.flush()
    program = Program(
        institution_id=inst.id,
        program_name="MS Analytics",
        degree_type="masters",
        description_text="A rigorous analytics program.",
        website_url="https://example.edu/ms-analytics",
        is_claimed=True,
    )
    db_session.add(program)
    await db_session.flush()

    changed = await ProfileIntelligenceService(db_session).enrich_program(program.id)
    await db_session.refresh(program)

    assert changed is False
    assert program.profile_intelligence is None


async def test_backfill_skips_claimed_program_without_preference_row(db_session):
    from sqlalchemy import select

    from unipaith.models.institution import Institution, Program, ProgramPreference
    from unipaith.models.user import User, UserRole
    from unipaith.services.match.derive_preferences import backfill_program_preferences

    admin = User(email="pref-claim@example.com", role=UserRole.institution_admin)
    db_session.add(admin)
    await db_session.flush()
    inst = Institution(
        admin_user_id=admin.id, name="Claimed Pref U", type="university", country="US"
    )
    db_session.add(inst)
    await db_session.flush()
    program = Program(
        institution_id=inst.id,
        program_name="Master of Science in Computer Science",
        degree_type="masters",
        slug="claimed-cs",
        is_claimed=True,
    )
    db_session.add(program)
    await db_session.flush()

    inst_id = inst.id
    sync_conn = await db_session.connection()

    def _run(conn):
        from sqlalchemy.orm import Session

        with Session(bind=conn) as s:
            return backfill_program_preferences(s, institution_id=inst_id)

    inserted = await sync_conn.run_sync(_run)
    rows = (await db_session.execute(select(ProgramPreference))).scalars().all()

    assert inserted == 0
    assert rows == []


async def test_backfill_fills_missing_target_profile_on_existing_derived_row(db_session):
    from decimal import Decimal

    from sqlalchemy import select

    from unipaith.models.institution import Institution, Program, ProgramPreference
    from unipaith.models.user import User, UserRole
    from unipaith.services.match.derive_preferences import backfill_program_preferences

    admin = User(email="pref-retrofit@example.com", role=UserRole.institution_admin)
    db_session.add(admin)
    await db_session.flush()
    inst = Institution(
        admin_user_id=admin.id,
        name="Preference Retrofit U",
        type="university",
        country="US",
    )
    db_session.add(inst)
    await db_session.flush()
    program = Program(
        institution_id=inst.id,
        program_name="MA in English",
        cip_code="23.0101",
        degree_type="masters",
        website_url="https://example.edu/english",
        slug="retrofit-english",
    )
    db_session.add(program)
    await db_session.flush()
    db_session.add(
        ProgramPreference(
            program_id=program.id,
            source="derived",
            confidence=Decimal("0.40"),
            pref_fields=["english"],
            target_profile=None,
        )
    )
    await db_session.flush()

    inst_id = inst.id
    program_id = program.id
    sync_conn = await db_session.connection()

    def _run(conn):
        from sqlalchemy.orm import Session

        with Session(bind=conn) as s:
            return backfill_program_preferences(s, institution_id=inst_id)

    inserted = await sync_conn.run_sync(_run)
    row = (
        await db_session.execute(
            select(ProgramPreference).where(ProgramPreference.program_id == program_id)
        )
    ).scalar_one()

    assert inserted == 0
    assert row.target_profile is not None
    assert row.target_profile["layers"]["background_academic"]
    assert row.target_profile["omissions"] == [
        {
            "layer": "values_motivations_community",
            "reason": "No eligible public evidence was available for this target-profile layer.",
            "source": "derived",
        }
    ]


async def test_backfill_fills_omission_only_target_profile_on_existing_derived_row(
    db_session,
):
    from decimal import Decimal

    from sqlalchemy import select

    from unipaith.models.institution import Institution, Program, ProgramPreference
    from unipaith.models.user import User, UserRole
    from unipaith.services.match.derive_preferences import backfill_program_preferences

    admin = User(email="pref-omission-retrofit@example.com", role=UserRole.institution_admin)
    db_session.add(admin)
    await db_session.flush()
    inst = Institution(
        admin_user_id=admin.id,
        name="Preference Omission Retrofit U",
        type="university",
        country="US",
    )
    db_session.add(inst)
    await db_session.flush()
    program = Program(
        institution_id=inst.id,
        program_name="Graduate Certificate in Classics",
        degree_type="certificate",
        website_url="https://www.college.columbia.edu/",
        slug="retrofit-classics-certificate",
    )
    db_session.add(program)
    await db_session.flush()
    db_session.add(
        ProgramPreference(
            program_id=program.id,
            source="derived",
            confidence=Decimal("0.40"),
            target_profile=None,
        )
    )
    await db_session.flush()

    inst_id = inst.id
    program_id = program.id
    sync_conn = await db_session.connection()

    def _run(conn):
        from sqlalchemy.orm import Session

        with Session(bind=conn) as s:
            return backfill_program_preferences(s, institution_id=inst_id)

    inserted = await sync_conn.run_sync(_run)
    row = (
        await db_session.execute(
            select(ProgramPreference).where(ProgramPreference.program_id == program_id)
        )
    ).scalar_one()

    assert inserted == 0
    assert row.target_profile is not None
    assert all(not signals for signals in row.target_profile["layers"].values())
    assert [item["layer"] for item in row.target_profile["omissions"]] == [
        "background_academic",
        "goals_behaviors_learning_working_style",
        "values_motivations_community",
    ]
    assert row.preference_weights == {}
    assert row.provenance["method"] == "public_evidence_target_profile_omissions_v1"
