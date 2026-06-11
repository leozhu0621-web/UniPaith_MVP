"""Tests for the canonical Princeton profile enrichment (unipaith.data.princeton_profile).

apply() is sync (it runs inside the Alembic data migration). We exercise the exact sync
path via AsyncSession.run_sync, which hands apply() a sync Session over the test
connection. Mirrors test_caltech_profile_apply / test_stanford_profile_apply and runs
against the CI pgvector service container.
"""

import uuid

import pytest
from sqlalchemy import select

from unipaith.data import princeton_profile
from unipaith.models.institution import Institution, Program, School
from unipaith.models.user import User, UserRole

pytestmark = pytest.mark.asyncio


async def _make_princeton(db_session) -> Institution:
    admin = User(
        id=uuid.uuid4(),
        email=f"princeton-admin-{uuid.uuid4().hex[:6]}@example.com",
        cognito_sub=f"dev-sub-{uuid.uuid4().hex[:8]}",
        role=UserRole("institution_admin"),
        is_active=True,
    )
    db_session.add(admin)
    await db_session.flush()
    inst = Institution(
        admin_user_id=admin.id,
        name=princeton_profile.INSTITUTION_NAME,
        type="university",
        country="United States",
        description_text="stub",
        student_body_size=1,
        is_verified=True,
        ranking_data={"qs_world_university_rankings": {"rank": 99, "year": 2026}},
        # A stale, unverified metric the profile treats as omitted — apply() must drop it
        # so it is never served despite being recorded in _standard.omitted.
        school_outcomes={"admit_rate": 0.05, "employed_or_continuing_ed": 0.99},
    )
    db_session.add(inst)
    await db_session.commit()
    return inst


async def test_apply_enriches_institution(db_session):
    inst = await _make_princeton(db_session)

    changed = await db_session.run_sync(princeton_profile.apply)
    assert changed is True

    await db_session.refresh(inst)
    assert inst.ranking_data["qs_world_university_rankings"]["rank"] == 25
    assert inst.ranking_data["times_higher_education"]["rank"] == 3
    assert inst.ranking_data["us_news_national"]["rank"] == 1
    assert inst.ranking_data["accreditor"] == "MSCHE"
    so = inst.school_outcomes
    assert so["admit_rate"] == 0.0462
    assert so["median_earnings_10yr"] == 110066
    assert so["graduation_rate_6yr"] == 0.98
    assert so["flagship"]["applicants"] == 40468
    assert so["flagship"]["admits"] == 1868
    assert so["flagship"]["nobel_laureates"] == 54
    assert so["scale"]["faculty_count"] == 1313
    assert so["scale"]["student_faculty_ratio"] == "5:1"
    assert so["scale"]["endowment_usd"] == 36400000000
    assert so["financial_aid"]["cost_of_attendance"] == 84040
    assert so["financial_aid"]["pell_grant_rate"] == 0.20
    assert any("Plasma" in lab for lab in so["research"]["labs"])
    assert so["campus_life"]["athletics_division"].startswith("NCAA Division I")
    assert so["top_employer_industries"]
    # The honest omission is recorded in the institution's _standard stamp, and the stale
    # pre-existing value is actively dropped (not preserved by the merge).
    assert "school_outcomes.employed_or_continuing_ed" in so["_standard"]["omitted"]
    assert "employed_or_continuing_ed" not in so
    assert inst.student_body_size == 5826
    assert inst.founded_year == 1746
    assert "Princeton" in inst.description_text
    # Gallery leads with a real raster campus photo (the hero picks the first raster).
    assert inst.media_gallery[0].startswith("https://upload.wikimedia.org")
    assert inst.media_gallery[0].lower().endswith(".jpg")


async def test_apply_sets_real_academic_units(db_session):
    inst = await _make_princeton(db_session)
    db_session.add_all(
        [
            School(institution_id=inst.id, name="Legacy School of Widgets"),
            School(institution_id=inst.id, name=princeton_profile._SEAS),  # pre-existing canonical
        ]
    )
    await db_session.commit()

    await db_session.run_sync(princeton_profile.apply)

    rows = (
        (await db_session.execute(select(School).where(School.institution_id == inst.id)))
        .scalars()
        .all()
    )
    names = sorted(s.name for s in rows)
    assert names == sorted(s["name"] for s in princeton_profile.SCHOOLS)
    assert len(names) == 5
    seas = next(s for s in rows if s.name == princeton_profile._SEAS)
    assert seas.sort_order == 1
    assert seas.about_detail and seas.about_detail["founded"] == 1921
    assert "Houck" in seas.about_detail["leadership"]
    # A faculty division honestly omits founding year + leadership — recorded in _standard.
    nat = next(s for s in rows if s.name == princeton_profile._NAT)
    assert "about_detail.founded" in nat.about_detail["_standard"]["omitted"]
    assert "about_detail.leadership" in nat.about_detail["_standard"]["omitted"]
    assert nat.about_detail["research_centers"]


async def test_apply_builds_real_program_catalog_idempotently(db_session):
    inst = await _make_princeton(db_session)
    db_session.add_all(
        [
            Program(
                institution_id=inst.id,
                program_name="Legacy MS in Widgets",
                degree_type="masters",
                is_published=True,
                slug="princeton-legacy-widgets",
            ),
            # A pre-existing canonical row carrying stale, unverified tracks + feeds.
            # apply() must clear both on a non-flagship program, since the profile records
            # them as omitted and they feed the matcher / content-ingest.
            Program(
                institution_id=inst.id,
                program_name="Physics",
                degree_type="bachelors",
                is_published=True,
                slug="princeton-physics-bs",
                tracks={"label": "Stale", "items": [{"name": "old"}]},
                content_sources={"news_rss": "https://stale.example/feed"},
            ),
        ]
    )
    await db_session.commit()

    await db_session.run_sync(princeton_profile.apply)
    await db_session.run_sync(princeton_profile.apply)  # second run → idempotent, no dupes

    progs = (
        (await db_session.execute(select(Program).where(Program.institution_id == inst.id)))
        .scalars()
        .all()
    )
    slugs = sorted(pr.slug for pr in progs)
    assert slugs == sorted(princeton_profile.PROGRAM_SLUGS)  # canonical set exactly; legacy gone
    assert all(pr.is_published for pr in progs)
    # Flagship CS BS: own feed, real FOS outcome, tracks, faculty, reviews, undergrad tuition.
    cs = next(pr for pr in progs if pr.slug == "princeton-computer-science-bs")
    sch = await db_session.get(School, cs.school_id)
    assert sch.name == princeton_profile._SEAS
    assert cs.tuition == 62688
    assert cs.outcomes_data["median_salary"] == 146624
    assert cs.outcomes_data["scope"] == "program"
    assert cs.outcomes_data["cip"] == "11.07"
    assert cs.tracks and cs.tracks["items"]
    assert cs.faculty_contacts["lead"]
    assert cs.external_reviews["summary"]
    assert cs.content_sources and "computer science" in cs.content_sources["keywords"]
    # Every program honestly records its missing per-program employment fields.
    assert "outcomes_data.employment_rate" in cs.outcomes_data["_standard"]["omitted"]
    # The fully-funded SPIA MPA carries the funded flag and is a masters.
    mpa = next(pr for pr in progs if pr.slug == "princeton-public-affairs-mpa")
    assert mpa.degree_type == "masters"
    assert mpa.cost_data and mpa.cost_data["funded"] is True
    assert mpa.outcomes_data["median_salary"] == 85111
    # Stale tracks on the pre-existing canonical Physics BS row were cleared (it is not
    # the flagship and has no verified tracks). Its stale feed is REPLACED with the real
    # Princeton news feed filtered to physics-relevant items — every program now carries a
    # working content_sources so its Events & Updates populate (never null).
    phys_bs = next(pr for pr in progs if pr.slug == "princeton-physics-bs")
    assert phys_bs.tracks is None
    assert phys_bs.content_sources is not None
    assert phys_bs.content_sources["news_rss"].startswith("https://www.princeton.edu/news")
    assert "physics" in phys_bs.content_sources["keywords"]
    assert phys_bs.content_sources["news_rss"] != "https://stale.example/feed"
    assert phys_bs.tuition == 62688
    # A catalog program with no FOS earnings falls back to the institution median.
    assert phys_bs.outcomes_data["median_salary"] == 110066
    assert phys_bs.outcomes_data["scope"] == "institution"
