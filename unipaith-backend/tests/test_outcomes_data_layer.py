"""Spec 68 — typed outcomes & admissions-history data layer.

Covers the data-layer contract: authority-precedence resolution (first-party-
wins, §7), recency tiebreak, absence-is-None (§2), real ``data_completeness``
(§6), the academic-only ``class_profile`` bias guard (§3 / 46 §6), and the
school-vs-program grain split (§4).
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.institution import Institution, Program, School
from unipaith.models.outcomes import (
    ALLOWED_CLASS_PROFILE_KEYS,
    OUTCOME_METRICS,
    disallowed_class_profile_keys,
)
from unipaith.models.user import User
from unipaith.services.outcomes_service import ClassProfileError, OutcomesService


async def _seed(db: AsyncSession, inst_user: User):
    db.add(inst_user)
    institution = Institution(
        admin_user_id=inst_user.id,
        name="Test University",
        type="university",
        country="United States",
    )
    db.add(institution)
    await db.flush()
    school = School(institution_id=institution.id, name="School of Engineering")
    db.add(school)
    await db.flush()
    program = Program(
        institution_id=institution.id,
        school_id=school.id,
        program_name="CS Masters",
        degree_type="masters",
        is_published=True,
    )
    db.add(program)
    await db.flush()
    return institution, school, program


# ── Pure-function guard (the CI bias-avoidance gate, no DB) ──────────────────


def test_class_profile_guard_allows_academic_keys():
    clean = {"gpa_p50": 3.7, "test_p50": 320, "cohort_size": 40}
    assert disallowed_class_profile_keys(clean) == set()
    # Every allowlisted key is academic — no demographic/proxy slipped in.
    assert "race_share" not in ALLOWED_CLASS_PROFILE_KEYS
    assert "gender_share" not in ALLOWED_CLASS_PROFILE_KEYS
    assert "zip_code" not in ALLOWED_CLASS_PROFILE_KEYS


def test_class_profile_guard_flags_protected_and_proxy_keys():
    dirty = {"gpa_p50": 3.7, "race_share": 0.2, "first_gen_share": 0.3}
    assert disallowed_class_profile_keys(dirty) == {"race_share", "first_gen_share"}
    assert disallowed_class_profile_keys(None) == set()


# ── Authority precedence + recency (§7) ─────────────────────────────────────


@pytest.mark.asyncio
async def test_resolve_picks_highest_authority(db_session: AsyncSession, mock_institution_user):
    _, _, program = await _seed(db_session, mock_institution_user)
    svc = OutcomesService(db_session)
    # Same metric+window, two sources: a crawl (0.80) and institution-reported (0.95).
    await svc.upsert_program_outcome(
        program.id, "employment_rate", "2024", source="crawled", value_numeric=0.80
    )
    await svc.upsert_program_outcome(
        program.id, "employment_rate", "2024", source="reported", value_numeric=0.95
    )
    winner = await svc.resolve_program_outcome(program.id, "employment_rate")
    assert winner is not None
    assert winner.source == "reported"  # first-party-wins (§7)
    assert float(winner.value_numeric) == 0.95


@pytest.mark.asyncio
async def test_resolve_recency_within_authority(db_session: AsyncSession, mock_institution_user):
    _, _, program = await _seed(db_session, mock_institution_user)
    svc = OutcomesService(db_session)
    await svc.upsert_program_outcome(
        program.id, "salary_median", "2022", source="reported", value_numeric=70000
    )
    await svc.upsert_program_outcome(
        program.id, "salary_median", "2024", source="reported", value_numeric=85000
    )
    winner = await svc.resolve_program_outcome(program.id, "salary_median")
    assert winner.reference_period == "2024"  # newest window wins the tie
    assert float(winner.value_numeric) == 85000


@pytest.mark.asyncio
async def test_absence_resolves_to_none(db_session: AsyncSession, mock_institution_user):
    _, _, program = await _seed(db_session, mock_institution_user)
    svc = OutcomesService(db_session)
    # No row written → absence is first-class (§2), never a zero.
    assert await svc.resolve_program_outcome(program.id, "hire_rate") is None


@pytest.mark.asyncio
async def test_value_json_band_payload(db_session: AsyncSession, mock_institution_user):
    _, _, program = await _seed(db_session, mock_institution_user)
    svc = OutcomesService(db_session)
    band = {"p25": 65000, "p50": 80000, "p75": 95000, "currency": "USD"}
    await svc.upsert_program_outcome(
        program.id, "salary_band", "class_of_2025", source="licensed", value_json=band
    )
    winner = await svc.resolve_program_outcome(program.id, "salary_band")
    assert winner.value_json == band
    assert winner.value_numeric is None


# ── data_completeness (§6 — replaces the matcher's 0.5 constant) ─────────────


@pytest.mark.asyncio
async def test_data_completeness_reflects_real_coverage(
    db_session: AsyncSession, mock_institution_user
):
    _, _, program = await _seed(db_session, mock_institution_user)
    svc = OutcomesService(db_session)
    assert await svc.program_data_completeness(program.id) == 0.0  # thin program, honest
    expected = len(OUTCOME_METRICS) + 1
    await svc.upsert_program_outcome(
        program.id, "employment_rate", "2024", source="reported", value_numeric=0.9
    )
    await svc.upsert_program_outcome(
        program.id, "salary_median", "2024", source="reported", value_numeric=82000
    )
    await svc.upsert_program_admissions(program.id, 2024, source="reported", admit_rate=0.18)
    # 2 metrics + admit-history present out of (10 metrics + 1 admit-history).
    assert await svc.program_data_completeness(program.id) == round(3 / expected, 4)


# ── Admissions history + the §3 bias guard ──────────────────────────────────


@pytest.mark.asyncio
async def test_admissions_upsert_academic_profile_ok(
    db_session: AsyncSession, mock_institution_user
):
    _, _, program = await _seed(db_session, mock_institution_user)
    svc = OutcomesService(db_session)
    row = await svc.upsert_program_admissions(
        program.id,
        2024,
        source="reported",
        applicants=1200,
        admits=216,
        enrolled=90,
        admit_rate=0.18,
        yield_rate=0.417,
        class_profile={"gpa_p50": 3.8, "gre_p50": 328, "cohort_size": 90},
        selectivity_band="highly_selective",
    )
    assert row.admit_rate is not None
    hist = await svc.list_program_admissions_history(program.id)
    assert len(hist) == 1 and hist[0].class_profile["gpa_p50"] == 3.8


@pytest.mark.asyncio
async def test_admissions_class_profile_rejects_protected_attr(
    db_session: AsyncSession, mock_institution_user
):
    _, _, program = await _seed(db_session, mock_institution_user)
    svc = OutcomesService(db_session)
    with pytest.raises(ClassProfileError):
        await svc.upsert_program_admissions(
            program.id,
            2024,
            source="reported",
            class_profile={"gpa_p50": 3.8, "race_share": 0.3},  # proxy attr — blocked (§3)
        )


@pytest.mark.asyncio
async def test_unknown_metric_rejected(db_session: AsyncSession, mock_institution_user):
    _, _, program = await _seed(db_session, mock_institution_user)
    svc = OutcomesService(db_session)
    with pytest.raises(ValueError):
        await svc.upsert_program_outcome(program.id, "made_up_metric", "2024", value_numeric=1.0)


# ── School grain is distinct from program grain (§4) ────────────────────────


@pytest.mark.asyncio
async def test_school_outcomes_are_separate_grain(db_session: AsyncSession, mock_institution_user):
    _, school, program = await _seed(db_session, mock_institution_user)
    svc = OutcomesService(db_session)
    # A program employment rate and a school employment rate are different facts.
    await svc.upsert_program_outcome(
        program.id, "employment_rate", "2024", source="reported", value_numeric=0.92
    )
    from unipaith.models.outcomes import SchoolOutcome

    db_session.add(
        SchoolOutcome(
            school_id=school.id,
            metric="employment_rate",
            reference_period="2024",
            source="licensed",
            value_numeric=0.85,
        )
    )
    await db_session.flush()
    prog_rate = await svc.resolve_program_outcome(program.id, "employment_rate")
    school_rate = await svc.resolve_school_outcome(school.id, "employment_rate")
    assert float(prog_rate.value_numeric) == 0.92
    assert float(school_rate.value_numeric) == 0.85  # never averaged up from programs


# ── Featured filters rebind off JSONB (§6 — typed-first, legacy fallback) ────


@pytest.mark.asyncio
async def test_featured_filter_typed_first_legacy_fallback(
    db_session: AsyncSession, mock_institution_user
):
    from unipaith.services.institution_service import InstitutionService

    institution, _, program_a = await _seed(db_session, mock_institution_user)
    # Program B under the same institution: legacy JSONB blob only, no typed row.
    program_b = Program(
        institution_id=institution.id,
        program_name="Legacy CS",
        degree_type="masters",
        is_published=True,
        outcomes_data={"median_salary": 60000},
    )
    db_session.add(program_b)
    await db_session.flush()
    # Program A: typed program_outcomes only, no JSONB.
    svc = OutcomesService(db_session)
    await svc.upsert_program_outcome(
        program_a.id, "salary_median", "2024", source="reported", value_numeric=90000
    )

    inst_svc = InstitutionService(db_session)
    # Filter min salary 80k → the typed program A passes; the 60k legacy B is excluded.
    page = await inst_svc.search_programs(min_median_salary=80000, page_size=50)
    ids = {i.id for i in page.items}
    assert program_a.id in ids and program_b.id not in ids
    a_item = next(i for i in page.items if i.id == program_a.id)
    assert a_item.median_salary == 90000  # surfaced from typed program_outcomes

    # Sort salary_desc → typed A (90k) ranks above legacy B (60k); both resolve.
    page2 = await inst_svc.search_programs(sort_by="salary_desc", page_size=50)
    order = [i.id for i in page2.items]
    assert order.index(program_a.id) < order.index(program_b.id)
    b_item = next(i for i in page2.items if i.id == program_b.id)
    assert b_item.median_salary == 60000  # legacy JSONB fallback still works


# ── Ingestion loader replaces the fabricated rows (§3/§6) ───────────────────


@pytest.mark.asyncio
async def test_loader_populates_typed_tables_deterministically(
    db_session: AsyncSession, mock_institution_user
):
    from unipaith.services.outcomes_loader import OutcomesLoader, curated_program_records

    _, _, program = await _seed(db_session, mock_institution_user)
    loader = OutcomesLoader(db_session)
    outs, adms = curated_program_records("masters", index=3)
    assert await loader.load_program_outcomes(program.id, outs) == len(outs)
    assert await loader.load_program_admissions(program.id, adms) == len(adms)

    svc = OutcomesService(db_session)
    salary = await svc.resolve_program_outcome(program.id, "salary_median")
    assert salary is not None and float(salary.value_numeric) > 0
    assert await svc.program_data_completeness(program.id) > 0.0
    hist = await svc.list_program_admissions_history(program.id)
    assert len(hist) == 2 and hist[0].admit_rate is not None

    # Deterministic (no random.uniform): same inputs → identical figures.
    outs2, _ = curated_program_records("masters", index=3)
    assert [o.value_numeric for o in outs] == [o.value_numeric for o in outs2]
    # The loader can't smuggle a non-academic key past the §3 guard.
    for a in adms:
        assert disallowed_class_profile_keys(a.class_profile) == set()


# ── Review theme-summarisation (§5 — grounded, rule-based default) ───────────


@pytest.mark.asyncio
async def test_review_themes_rule_based_grounded(db_session: AsyncSession, mock_institution_user):
    from unipaith.models.institution import StudentProgramReview
    from unipaith.services.review_theme_service import ReviewThemeService

    _, _, program = await _seed(db_session, mock_institution_user)
    # Career support consistently strong (5), workload consistently weak (2).
    for _ in range(4):
        db_session.add(
            StudentProgramReview(
                program_id=program.id,
                is_published=True,
                rating_teaching=4,
                rating_workload=2,
                rating_career_support=5,
                rating_internship_access=4,
                rating_community_culture=4,
                rating_roi=4,
                rating_overall=4,
                reviewer_context={"type": "alumni"},
            )
        )
    await db_session.flush()

    svc = ReviewThemeService(db_session)
    summary = await svc.get_or_build_program_summary(program.id, "student")
    assert summary.n_reviews == 4
    assert summary.model_version == "review-themes-rule-v1"  # rule-based default (flag off)
    labels = [t["label"] for t in summary.themes]
    assert "Career support" in labels  # the strong dim surfaces as a theme
    assert all(t["supporting_review_ids"] for t in summary.themes)  # grounded
    assert any(t["label"] == "Workload" for t in summary.tradeoffs)  # the weak dim = tradeoff
    assert summary.dimension_rollup["rating_career_support"] == 5.0

    # Cache hit on re-call with no review-count delta → same row, not rebuilt.
    again = await svc.get_or_build_program_summary(program.id, "student")
    assert again.id == summary.id


@pytest.mark.asyncio
async def test_review_themes_empty_is_honest(db_session: AsyncSession, mock_institution_user):
    from unipaith.services.review_theme_service import ReviewThemeService

    _, _, program = await _seed(db_session, mock_institution_user)
    summary = await ReviewThemeService(db_session).get_or_build_program_summary(program.id)
    assert summary.n_reviews == 0
    assert summary.themes == [] and summary.tradeoffs == []  # no reviews → no invented themes
