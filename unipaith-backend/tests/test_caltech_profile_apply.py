"""Tests for the canonical Caltech profile enrichment (unipaith.data.caltech_profile).

apply() is sync (it runs inside the Alembic data migration). We exercise the exact
sync path via AsyncSession.run_sync, which hands apply() a sync Session over the
test connection. Mirrors test_stanford_profile_apply and runs against the CI
pgvector service container.
"""

import uuid

import pytest
from sqlalchemy import select

from unipaith.data import caltech_profile
from unipaith.models.institution import Institution, Program, School
from unipaith.models.user import User, UserRole

pytestmark = pytest.mark.asyncio


async def _make_caltech(db_session) -> Institution:
    admin = User(
        id=uuid.uuid4(),
        email=f"caltech-admin-{uuid.uuid4().hex[:6]}@example.com",
        cognito_sub=f"dev-sub-{uuid.uuid4().hex[:8]}",
        role=UserRole("institution_admin"),
        is_active=True,
    )
    db_session.add(admin)
    await db_session.flush()
    inst = Institution(
        admin_user_id=admin.id,
        name=caltech_profile.INSTITUTION_NAME,
        type="university",
        country="United States",
        description_text="stub",
        student_body_size=1,
        is_verified=True,
        ranking_data={"qs_world_university_rankings": {"rank": 10, "year": 2026}},
        # A stale, unverified metric the profile treats as omitted — apply() must
        # drop it so it is never served despite being recorded in _standard.omitted.
        school_outcomes={"admit_rate": 0.0257, "top_employer_industries": ["Stale"]},
    )
    db_session.add(inst)
    await db_session.commit()
    return inst


async def test_apply_enriches_institution(db_session):
    inst = await _make_caltech(db_session)

    changed = await db_session.run_sync(caltech_profile.apply)
    assert changed is True

    await db_session.refresh(inst)
    assert inst.ranking_data["qs_world_university_rankings"]["rank"] == 10
    assert inst.ranking_data["times_higher_education"]["rank"] == 7
    assert inst.ranking_data["us_news_national"]["rank"] == 11
    assert inst.ranking_data["accreditor"] == "WSCUC"
    so = inst.school_outcomes
    assert so["admit_rate"] == 0.0257
    assert so["median_earnings_10yr"] == 128566
    assert so["graduation_rate_6yr"] == 0.944
    assert so["flagship"]["applicants"] == 13856
    assert so["flagship"]["admits"] == 356
    assert so["flagship"]["nobel_laureates"] == 49
    assert so["scale"]["faculty_count"] == 323
    assert so["scale"]["student_faculty_ratio"] == "3:1"
    assert so["financial_aid"]["cost_of_attendance"] == 86886
    assert so["financial_aid"]["pell_grant_rate"] == 0.1799
    assert any("JPL" in lab for lab in so["research"]["labs"])
    assert so["campus_life"]["athletics_division"].startswith("NCAA Division III")
    assert so["employed_or_continuing_ed"] == 0.87
    # The honest omission is recorded in the institution's _standard stamp, and the
    # stale pre-existing value is actively dropped (not preserved by the merge).
    assert "school_outcomes.top_employer_industries" in so["_standard"]["omitted"]
    assert "top_employer_industries" not in so
    assert inst.student_body_size == 987
    assert "Pasadena" in inst.description_text
    # Gallery leads with a real raster campus photo (the hero picks the first raster).
    assert inst.media_gallery[0].startswith("https://upload.wikimedia.org")
    assert inst.media_gallery[0].lower().endswith(".jpg")


async def test_apply_sets_six_real_divisions(db_session):
    inst = await _make_caltech(db_session)
    db_session.add_all(
        [
            School(institution_id=inst.id, name="Legacy School of Widgets"),
            School(institution_id=inst.id, name=caltech_profile._BBE),  # pre-existing canonical
        ]
    )
    await db_session.commit()

    await db_session.run_sync(caltech_profile.apply)

    rows = (
        (await db_session.execute(select(School).where(School.institution_id == inst.id)))
        .scalars()
        .all()
    )
    names = sorted(s.name for s in rows)
    assert names == sorted(s["name"] for s in caltech_profile.SCHOOLS)
    assert len(names) == 6
    bbe = next(s for s in rows if s.name == caltech_profile._BBE)
    assert bbe.sort_order == 1
    assert bbe.about_detail and bbe.about_detail["founded"] == 1928
    assert "Sternberg" in bbe.about_detail["leadership"]
    # Chemistry honestly omits its founding year — recorded in the division _standard.
    cce = next(s for s in rows if s.name == caltech_profile._CCE)
    assert "about_detail.founded" in cce.about_detail["_standard"]["omitted"]


async def test_apply_builds_real_program_catalog_idempotently(db_session):
    inst = await _make_caltech(db_session)
    db_session.add_all(
        [
            Program(
                institution_id=inst.id,
                program_name="Legacy MS in Widgets",
                degree_type="masters",
                is_published=True,
                slug="caltech-legacy-widgets",
            ),
            # A pre-existing canonical row carrying stale, unverified tracks + feeds.
            # apply() must clear both on a non-flagship program, since the profile
            # records them as omitted and they feed the matcher / content-ingest.
            Program(
                institution_id=inst.id,
                program_name="Physics",
                degree_type="bachelors",
                is_published=True,
                slug="caltech-physics-bs",
                tracks={"label": "Stale", "items": [{"name": "old"}]},
                content_sources={"news_rss": "https://stale.example/feed"},
            ),
        ]
    )
    await db_session.commit()

    await db_session.run_sync(caltech_profile.apply)
    await db_session.run_sync(caltech_profile.apply)  # second run → idempotent, no dupes

    progs = (
        (await db_session.execute(select(Program).where(Program.institution_id == inst.id)))
        .scalars()
        .all()
    )
    slugs = sorted(p.slug for p in progs)
    assert slugs == sorted(caltech_profile.PROGRAM_SLUGS)  # canonical set exactly; legacy gone
    assert all(p.is_published for p in progs)
    # Flagship CS BS: own feed, real FOS outcome, tracks, faculty, reviews, undergrad tuition.
    cs = next(p for p in progs if p.slug == "caltech-cs-bs")
    sch = await db_session.get(School, cs.school_id)
    assert sch.name == caltech_profile._EAS
    assert cs.tuition == 65898
    assert cs.outcomes_data["median_salary"] == 129693
    assert cs.outcomes_data["scope"] == "program"
    assert cs.outcomes_data["cip"] == "11.07"
    assert cs.tracks and cs.tracks["items"]
    assert cs.faculty_contacts["lead"]
    assert cs.external_reviews["summary"]
    assert cs.content_sources and "computer science" in cs.content_sources["keywords"]
    # Every program honestly records its missing per-program employment fields.
    assert "outcomes_data.employment_rate" in cs.outcomes_data["_standard"]["omitted"]
    # Funded research doctorate carries tuition $0.
    phd = next(p for p in progs if p.slug == "caltech-physics-phd")
    assert phd.tuition == 0
    assert phd.cost_data and phd.cost_data["funded"] is True
    assert phd.degree_type == "phd"
    # Stale tracks + feeds on the pre-existing canonical Physics BS row were cleared
    # (it is not the flagship and has no verified tracks), matching its _standard.
    phys_bs = next(p for p in progs if p.slug == "caltech-physics-bs")
    assert phys_bs.tracks is None
    assert phys_bs.content_sources is None
    # Undergraduate programs carry Caltech's published tuition.
    assert phys_bs.tuition == 65898
    # A catalog program with no FOS earnings falls back to the institution median.
    assert phys_bs.outcomes_data["median_salary"] == 128566
    assert phys_bs.outcomes_data["scope"] == "institution"
