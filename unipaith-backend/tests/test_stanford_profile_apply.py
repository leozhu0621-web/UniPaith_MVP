"""Tests for the canonical Stanford profile enrichment (unipaith.data.stanford_profile).

apply() is sync (it runs inside the Alembic data migration). We exercise the exact
sync path via AsyncSession.run_sync, which hands apply() a sync Session over the
test connection. Mirrors test_mit_profile / test_harvard_profile and runs against
the CI pgvector service container.
"""

import uuid

import pytest
from sqlalchemy import select

from unipaith.data import stanford_profile
from unipaith.models.institution import Institution, Program, School
from unipaith.models.user import User, UserRole

pytestmark = pytest.mark.asyncio


async def _make_stanford(db_session) -> Institution:
    admin = User(
        id=uuid.uuid4(),
        email=f"stanford-admin-{uuid.uuid4().hex[:6]}@example.com",
        cognito_sub=f"dev-sub-{uuid.uuid4().hex[:8]}",
        role=UserRole("institution_admin"),
        is_active=True,
    )
    db_session.add(admin)
    await db_session.flush()
    inst = Institution(
        admin_user_id=admin.id,
        name=stanford_profile.INSTITUTION_NAME,
        type="university",
        country="United States",
        description_text="stub",
        student_body_size=1,
        is_verified=True,
        ranking_data={"qs_world_university_rankings": {"rank": 3, "year": 2026}},
        # A stale, unverified metric the profile treats as omitted — apply() must
        # drop it so it is never served despite being recorded in _standard.omitted.
        school_outcomes={"admit_rate": 0.0361, "employed_or_continuing_ed": 0.99},
    )
    db_session.add(inst)
    await db_session.commit()
    return inst


async def test_apply_enriches_institution(db_session):
    inst = await _make_stanford(db_session)

    changed = await db_session.run_sync(stanford_profile.apply)
    assert changed is True

    await db_session.refresh(inst)
    assert inst.ranking_data["qs_world_university_rankings"]["rank"] == 3
    assert inst.ranking_data["times_higher_education"]["rank"] == 6
    assert inst.ranking_data["us_news_national"]["rank"] == 4
    assert inst.ranking_data["accreditor"] == "WSCUC"
    so = inst.school_outcomes
    assert so["admit_rate"] == 0.0361
    assert so["median_earnings_10yr"] == 124080
    assert so["test_scores"]["act_25_75"] == [34, 35]
    assert so["flagship"]["applicants"] == 57326
    assert so["flagship"]["admits"] == 2067
    assert so["flagship"]["nobel_laureates"] == 58
    assert so["scale"]["endowment_usd"] == 37600000000
    assert so["scale"]["student_faculty_ratio"] == "5:1"
    assert so["financial_aid"]["cost_of_attendance"] == 87833
    assert any("SLAC" in lab for lab in so["research"]["labs"])
    assert so["campus_life"]["varsity_sports"] == 36
    assert so.get("media_credit", "").startswith("Wikimedia Commons")
    # The honest omission is recorded in the institution's _standard stamp, and the
    # stale pre-existing value is actively dropped (not preserved by the merge).
    assert "school_outcomes.employed_or_continuing_ed" in so["_standard"]["omitted"]
    assert "employed_or_continuing_ed" not in so
    assert inst.student_body_size == 7554
    assert "Silicon Valley" in inst.description_text
    # Gallery leads with a real raster campus photo (the hero picks the first raster).
    assert inst.media_gallery[0].startswith("https://upload.wikimedia.org")
    assert inst.media_gallery[0].lower().endswith(".jpg")


async def test_apply_sets_seven_real_schools(db_session):
    inst = await _make_stanford(db_session)
    db_session.add_all(
        [
            School(institution_id=inst.id, name="Legacy School of Widgets"),
            School(institution_id=inst.id, name=stanford_profile._GSB),  # pre-existing canonical
        ]
    )
    await db_session.commit()

    await db_session.run_sync(stanford_profile.apply)

    rows = (
        (await db_session.execute(select(School).where(School.institution_id == inst.id)))
        .scalars()
        .all()
    )
    names = sorted(s.name for s in rows)
    assert names == sorted(s["name"] for s in stanford_profile.SCHOOLS)
    assert len(names) == 7
    gsb = next(s for s in rows if s.name == stanford_profile._GSB)
    assert gsb.sort_order == 4
    assert gsb.about_detail and "Sarah Soule" in gsb.about_detail["leadership"]
    # Medicine honestly omits its faculty roster — recorded in the school _standard.
    med = next(s for s in rows if s.name == stanford_profile._MED)
    assert "about_detail.faculty" in med.about_detail["_standard"]["omitted"]
    # Every school carries content_sources (GSB its own Insights RSS; others keyword-filtered).
    hs = next(s for s in rows if s.name == stanford_profile._HS)
    assert hs.content_sources and hs.content_sources.get("news_rss")
    assert gsb.content_sources and gsb.content_sources.get("news_rss")


async def test_apply_builds_real_program_catalog_idempotently(db_session):
    inst = await _make_stanford(db_session)
    db_session.add_all(
        [
            Program(
                institution_id=inst.id,
                program_name="Legacy MS in Widgets",
                degree_type="masters",
                is_published=True,
                slug="stanford-legacy-widgets",
            ),
            # A pre-existing canonical row carrying stale, unverified tracks + feeds
            # (e.g. crawled or admin-created). apply() must clear both, since the
            # profile records them as omitted for this program and they feed the
            # matcher / the content-ingest selection.
            Program(
                institution_id=inst.id,
                program_name="Computer Science",
                degree_type="bachelors",
                is_published=True,
                slug="stanford-cs-bs",
                tracks={"label": "Stale", "items": [{"name": "old"}]},
                content_sources={"news_rss": "https://stale.example/feed"},
            ),
        ]
    )
    await db_session.commit()

    await db_session.run_sync(stanford_profile.apply)
    await db_session.run_sync(stanford_profile.apply)  # second run → idempotent, no dupes

    progs = (
        (await db_session.execute(select(Program).where(Program.institution_id == inst.id)))
        .scalars()
        .all()
    )
    slugs = sorted(p.slug for p in progs)
    assert slugs == sorted(stanford_profile.PROGRAM_SLUGS)  # canonical set exactly; legacy gone
    assert all(p.is_published for p in progs)
    # Flagship MBA: own professional tuition, full employment-report outcomes, tracks.
    mba = next(p for p in progs if p.slug == "stanford-mba")
    assert mba.tuition == 85755
    assert mba.cost_data["source"].startswith("Stanford GSB")
    assert mba.outcomes_data["employment_rate"] == 0.88
    assert mba.outcomes_data["scope"] == "program"
    assert mba.outcomes_data["conditions"]
    assert mba.class_profile["cohort_size"].startswith("424")
    assert mba.tracks and mba.tracks["items"]
    assert mba.program_name == "Master of Business Administration"
    assert mba.website_url == "https://www.gsb.stanford.edu/programs/mba"
    # Funded research doctorate
    phd = next(p for p in progs if p.slug == "stanford-economics-phd")
    assert phd.tuition == 0
    assert phd.cost_data and phd.cost_data["funded"] is True
    # MS CS: standard grad tuition override; real College Scorecard FOS outcome.
    cs = next(p for p in progs if p.slug == "stanford-cs-ms")
    sch = await db_session.get(School, cs.school_id)
    assert sch.name == stanford_profile._ENG
    assert cs.outcomes_data["median_salary"] == 199761
    assert cs.outcomes_data["scope"] == "program"
    assert cs.outcomes_data["cip"] == "11.07"
    # Catalog programs honestly record their omitted outcome fields in _standard.
    assert "outcomes_data.employment_rate" in cs.outcomes_data["_standard"]["omitted"]
    # Stale tracks on the pre-existing canonical CS BS row were cleared; stale feeds
    # were replaced with the profile's keyword-filtered program feed (not left null).
    cs_bs = next(p for p in progs if p.slug == "stanford-cs-bs")
    assert cs_bs.tracks is None
    assert cs_bs.department == "Department of Computer Science"
    assert cs_bs.content_sources is not None
    assert cs_bs.content_sources["news_rss"] == stanford_profile._LAW_RSS
    events_url = stanford_profile._STANFORD_EVENTS_ICS["url"]
    assert cs_bs.content_sources["events_feed"]["url"] == events_url
    assert cs_bs.content_sources["keywords"]
    assert len(progs) >= 170  # full IPEDS/Scorecard catalog breadth
    # Undergraduate programs carry Stanford's undergrad tuition, not the grad rate.
    assert cs_bs.tuition == 67731
    # Professional degrees carry the professional admissions baseline, and their
    # per-school tuition is omitted (not shown as the wrong standard grad rate).
    jd = next(p for p in progs if p.slug == "stanford-jd")
    assert jd.degree_type == "professional"
    assert jd.application_requirements["source"].startswith("Stanford")
    assert jd.tuition is None
    assert "tuition_usd" not in jd.cost_data
