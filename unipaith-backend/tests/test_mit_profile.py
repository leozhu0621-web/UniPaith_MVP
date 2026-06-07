"""Tests for the canonical MIT profile enrichment (unipaith.data.mit_profile).

apply() is sync (it runs inside the Alembic data migration). We exercise the
exact sync path via AsyncSession.run_sync, which hands apply() a sync Session
over the test connection.
"""

import uuid

import pytest
from sqlalchemy import select

from unipaith.data import mit_profile
from unipaith.models.institution import Institution, Program, School
from unipaith.models.user import User, UserRole

pytestmark = pytest.mark.asyncio


async def _make_mit(db_session) -> Institution:
    admin = User(
        id=uuid.uuid4(),
        email=f"mit-admin-{uuid.uuid4().hex[:6]}@example.com",
        cognito_sub=f"dev-sub-{uuid.uuid4().hex[:8]}",
        role=UserRole("institution_admin"),
        is_active=True,
    )
    db_session.add(admin)
    await db_session.flush()
    inst = Institution(
        admin_user_id=admin.id,
        name=mit_profile.INSTITUTION_NAME,
        type="university",
        country="United States",
        description_text="stub",
        student_body_size=1,
        is_verified=True,
        ranking_data={"qs_world_university_rankings": {"rank": 1, "year": 2025}},
        school_outcomes={"employed_or_continuing_ed": 0.94},
    )
    db_session.add(inst)
    await db_session.commit()
    return inst


async def test_apply_enriches_institution(db_session):
    inst = await _make_mit(db_session)

    changed = await db_session.run_sync(mit_profile.apply)
    assert changed is True

    await db_session.refresh(inst)
    assert inst.ranking_data["qs_world_university_rankings"]["rank"] == 1
    assert inst.ranking_data["times_higher_education"]["rank"] == 2
    assert inst.ranking_data["us_news_national"]["rank"] == 2
    assert inst.school_outcomes["avg_net_price"] == 20111
    assert inst.school_outcomes["median_earnings_10yr"] == 143372
    assert inst.school_outcomes["test_scores"]["act_25_75"] == [34, 36]
    assert inst.school_outcomes["flagship"]["nobel_laureates"] == 106
    assert any(s["source"].startswith("U.S. Dept") for s in inst.school_outcomes["sources"])
    assert inst.student_body_size == 4561
    assert inst.school_outcomes["scale"]["faculty_count"] == 1466
    assert inst.school_outcomes["financial_aid"]["no_loan_debt_rate"] == 0.88
    assert inst.school_outcomes["flagship"]["national_medal_science"] == 64
    assert "CSAIL" in inst.school_outcomes["research"]["labs"]
    assert inst.school_outcomes["campus_life"]["varsity_sports"] == 33
    assert "Mens et Manus" in inst.description_text


async def test_apply_sets_six_real_schools(db_session):
    inst = await _make_mit(db_session)
    db_session.add_all(
        [
            School(institution_id=inst.id, name="Legacy College of Widgets"),
            School(institution_id=inst.id, name="School of Engineering"),  # pre-existing canonical
        ]
    )
    await db_session.commit()

    await db_session.run_sync(mit_profile.apply)

    rows = (
        (await db_session.execute(select(School).where(School.institution_id == inst.id)))
        .scalars()
        .all()
    )
    names = sorted(s.name for s in rows)
    assert names == sorted(s["name"] for s in mit_profile.SCHOOLS)
    assert len(names) == 6
    # descriptions + ordering applied
    eng = next(s for s in rows if s.name == "School of Engineering")
    assert eng.sort_order == 1
    assert eng.description_text and "largest school" in eng.description_text


async def test_apply_builds_real_program_catalog_idempotently(db_session):
    inst = await _make_mit(db_session)
    db_session.add(
        Program(
            institution_id=inst.id,
            program_name="Legacy MS in Widgets",
            degree_type="masters",
            is_published=True,
            slug="mit-legacy-widgets",
        )
    )
    await db_session.commit()

    await db_session.run_sync(mit_profile.apply)
    await db_session.run_sync(mit_profile.apply)  # second run → idempotent, no dupes

    progs = (
        (await db_session.execute(select(Program).where(Program.institution_id == inst.id)))
        .scalars()
        .all()
    )
    slugs = sorted(p.slug for p in progs)
    assert slugs == sorted(mit_profile.PROGRAM_SLUGS)  # canonical set exactly; legacy gone
    assert all(p.is_published for p in progs)
    # programs map to the real schools
    eecs = next(p for p in progs if p.slug == "mit-eecs-bs")
    sch = await db_session.get(School, eecs.school_id)
    assert sch.name == "School of Engineering"
    assert eecs.degree_type == "bachelors"
    assert eecs.tuition == 64730  # undergrads pay MIT's single published rate
    phd = next(p for p in progs if p.slug == "mit-eecs-phd")
    assert phd.tuition == 0  # PhDs are funded
    assert phd.cost_data and phd.cost_data["funded"] is True
    mba = next(p for p in progs if p.slug == "mit-sloan-mba")
    assert mba.tuition == 89000  # Sloan MBA professional rate (2025-26)
    # Online, non-degree credential carries through (crawl phase 2).
    mm = next(p for p in progs if p.slug == "mit-mm-finance")
    assert mm.degree_type == "certificate"
    assert mm.delivery_format == "online"
    assert mm.tuition is None  # online/MicroMasters pricing varies → null
    # Official admission-requirements baseline populates per program type.
    assert eecs.application_requirements["test_policy"]["stance"] == "required"
    assert eecs.application_requirements["source"] == "MIT Admissions"
    assert mba.application_requirements["recommendations"]["required_count"] == 1


async def test_program_has_dependents_false_for_unreferenced_program(db_session):
    """The FK-introspection guard runs cleanly and reports no dependents for a
    fresh program (the negative path that lets the reconcile delete it)."""
    inst = await _make_mit(db_session)
    p = Program(
        institution_id=inst.id,
        program_name="Unreferenced",
        degree_type="masters",
        slug="mit-unreferenced",
        is_published=True,
    )
    db_session.add(p)
    await db_session.commit()
    has = await db_session.run_sync(lambda s: mit_profile._program_has_dependents(s, p.id))
    assert has is False


async def test_apply_is_noop_when_mit_absent(db_session):
    changed = await db_session.run_sync(mit_profile.apply)
    assert changed is False
