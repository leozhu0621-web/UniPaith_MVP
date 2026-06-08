"""Tests for the canonical Harvard profile enrichment (unipaith.data.harvard_profile).

apply() is sync (it runs inside the Alembic data migration). We exercise the
exact sync path via AsyncSession.run_sync, which hands apply() a sync Session
over the test connection. Mirrors test_mit_profile.
"""

import uuid

import pytest
from sqlalchemy import select

from unipaith.data import harvard_profile
from unipaith.models.institution import Institution, Program, School
from unipaith.models.user import User, UserRole

pytestmark = pytest.mark.asyncio


async def _make_harvard(db_session) -> Institution:
    admin = User(
        id=uuid.uuid4(),
        email=f"harvard-admin-{uuid.uuid4().hex[:6]}@example.com",
        cognito_sub=f"dev-sub-{uuid.uuid4().hex[:8]}",
        role=UserRole("institution_admin"),
        is_active=True,
    )
    db_session.add(admin)
    await db_session.flush()
    inst = Institution(
        admin_user_id=admin.id,
        name=harvard_profile.INSTITUTION_NAME,
        type="university",
        country="United States",
        description_text="stub",
        student_body_size=1,
        is_verified=True,
        ranking_data={"qs_world_university_rankings": {"rank": 5, "year": 2025}},
        school_outcomes={"employed_or_continuing_ed": 0.95},
    )
    db_session.add(inst)
    await db_session.commit()
    return inst


async def test_apply_enriches_institution(db_session):
    inst = await _make_harvard(db_session)

    changed = await db_session.run_sync(harvard_profile.apply)
    assert changed is True

    await db_session.refresh(inst)
    assert inst.ranking_data["qs_world_university_rankings"]["rank"] == 5
    assert inst.ranking_data["times_higher_education"]["rank"] == 3
    assert inst.ranking_data["us_news_national"]["rank"] == 3
    assert inst.school_outcomes["admit_rate"] == 0.0359
    assert inst.school_outcomes["median_earnings_10yr"] == 101817
    assert inst.school_outcomes["test_scores"]["act_25_75"] == [34, 36]
    assert inst.school_outcomes["flagship"]["nobel_laureates"] == 161
    assert inst.school_outcomes["flagship"]["us_presidents"] == 8
    assert inst.school_outcomes["flagship"]["applicants"] == 54008
    assert any(s["source"].startswith("U.S. Dept") for s in inst.school_outcomes["sources"])
    assert any(s["source"] == "Harvard at a Glance" for s in inst.school_outcomes["sources"])
    assert inst.student_body_size == 7601
    assert inst.school_outcomes["scale"]["endowment_usd"] == 53200000000
    assert inst.school_outcomes["scale"]["student_faculty_ratio"] == "7:1"
    assert inst.school_outcomes["financial_aid"]["scholarship_rate"] == 0.55
    assert inst.school_outcomes["financial_aid"]["cost_of_attendance"] == 86926
    assert any("Wyss" in lab for lab in inst.school_outcomes["research"]["labs"])
    assert inst.school_outcomes["campus_life"]["varsity_sports"] == 42
    assert "oldest" in inst.description_text
    assert inst.founded_year == 1636
    assert inst.campus_setting == "urban"


async def test_apply_sets_twelve_real_schools(db_session):
    inst = await _make_harvard(db_session)
    db_session.add_all(
        [
            School(institution_id=inst.id, name="Legacy School of Widgets"),
            School(institution_id=inst.id, name="Harvard Law School"),  # pre-existing canonical
        ]
    )
    await db_session.commit()

    await db_session.run_sync(harvard_profile.apply)

    rows = (
        (await db_session.execute(select(School).where(School.institution_id == inst.id)))
        .scalars()
        .all()
    )
    names = sorted(s.name for s in rows)
    assert names == sorted(s["name"] for s in harvard_profile.SCHOOLS)
    assert len(names) == 12
    # descriptions + ordering applied
    fas = next(s for s in rows if s.name == "Harvard Faculty of Arts & Sciences")
    assert fas.sort_order == 1
    assert fas.description_text and "largest faculty" in fas.description_text


async def test_apply_builds_real_program_catalog_idempotently(db_session):
    inst = await _make_harvard(db_session)
    db_session.add(
        Program(
            institution_id=inst.id,
            program_name="Legacy MS in Widgets",
            degree_type="masters",
            is_published=True,
            slug="harvard-legacy-widgets",
        )
    )
    await db_session.commit()

    await db_session.run_sync(harvard_profile.apply)
    await db_session.run_sync(harvard_profile.apply)  # second run → idempotent, no dupes

    progs = (
        (await db_session.execute(select(Program).where(Program.institution_id == inst.id)))
        .scalars()
        .all()
    )
    slugs = sorted(p.slug for p in progs)
    assert slugs == sorted(harvard_profile.PROGRAM_SLUGS)  # canonical set exactly; legacy gone
    assert all(p.is_published for p in progs)
    # CS maps to SEAS and pays Harvard College tuition
    cs = next(p for p in progs if p.slug == "harvard-cs-ab")
    sch = await db_session.get(School, cs.school_id)
    assert sch.name == harvard_profile._SEAS
    assert cs.degree_type == "bachelors"
    assert cs.tuition == 57328  # Harvard College tuition, 2025-26
    # Funded research doctorate
    phd = next(p for p in progs if p.slug == "harvard-economics-phd")
    assert phd.tuition == 0
    assert phd.cost_data and phd.cost_data["funded"] is True
    # Professional schools carry their own published tuition
    mba = next(p for p in progs if p.slug == "harvard-mba")
    assert mba.tuition == 78700  # HBS MBA professional rate (2025-26)
    jd = next(p for p in progs if p.slug == "harvard-jd")
    assert jd.tuition == 78692  # HLS J.D., 2025-26
    # Extension A.L.M. is charged per course → tuition null, but it is a real
    # degree with a real Field-of-Study outcome.
    alm = next(p for p in progs if p.slug == "harvard-alm")
    assert alm.tuition is None
    assert alm.delivery_format == "hybrid"
    assert alm.outcomes_data["scope"] == "program"
    # Official admission-requirements baseline populates per program type/school.
    assert jd.application_requirements["test_policy"]["stance"] == "required"
    assert jd.application_requirements["source"] == "Harvard Law School J.D. Admissions"
    assert mba.application_requirements["recommendations"]["required_count"] == 2
    # Real per-program outcomes from College Scorecard Field-of-Study, with a
    # labelled institution fallback where Harvard's figures are suppressed.
    assert cs.outcomes_data["median_salary"] == 219550
    assert cs.outcomes_data["scope"] == "program"
    chem = next(p for p in progs if p.slug == "harvard-chemistry-ab")
    assert chem.outcomes_data["scope"] == "institution"  # suppressed → Harvard-wide labelled
    cert = next(p for p in progs if p.slug == "harvard-cs50-cert")
    assert cert.outcomes_data is None  # non-degree credential → no outcomes
    # Audience + highlights populate (flagship override + by-type fallback).
    assert mba.who_its_for and "management" in mba.who_its_for
    econ = next(p for p in progs if p.slug == "harvard-economics-ab")
    assert econ.highlights and any("popular" in h for h in econ.highlights)
    assert chem.highlights  # by-type (bachelors) fallback
    assert cs.tracks and any("Artificial Intelligence" in c for c in cs.tracks["concentrations"])
    assert "case method" in mba.description_text  # richer description override
    assert cs.application_deadline is not None  # undergrad deadline (Jan 1)
    assert cert.application_deadline is None  # online/HarvardX → no fixed deadline


async def test_program_has_dependents_false_for_unreferenced_program(db_session):
    """The FK-introspection guard runs cleanly and reports no dependents for a
    fresh program (the negative path that lets the reconcile delete it)."""
    inst = await _make_harvard(db_session)
    p = Program(
        institution_id=inst.id,
        program_name="Unreferenced",
        degree_type="masters",
        slug="harvard-unreferenced",
        is_published=True,
    )
    db_session.add(p)
    await db_session.commit()
    has = await db_session.run_sync(lambda s: harvard_profile._program_has_dependents(s, p.id))
    assert has is False


async def test_apply_is_noop_when_harvard_absent(db_session):
    changed = await db_session.run_sync(harvard_profile.apply)
    assert changed is False
