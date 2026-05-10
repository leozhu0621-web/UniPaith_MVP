"""Phase D wiring — Discovery completion → match recompute.

When the FeatureEmitter persists a fresh `student_feature_vectors`
row at end-of-layer, the discovery service must chain into
`MatchService.compute_matches_for_student` so `match_results`
actually populates.

Before this hook, `match_results` stayed empty even after Discovery
completed — the matcher was wired but dark. This test suite covers
the chain at the seam: emit succeeds → recompute fires → rows land
in the DB.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.ai_artifacts import StudentFeatureVector
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.services.discovery_service import DiscoveryService

# ── Fixtures ───────────────────────────────────────────────────────────────


async def _seed_student(db: AsyncSession) -> StudentProfile:
    user = User(
        id=uuid4(),
        email=f"hook-{uuid4().hex[:6]}@example.com",
        cognito_sub=f"dev-sub-{uuid4().hex[:8]}",
        role=UserRole.student,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    profile = StudentProfile(user_id=user.id)
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def _seed_published_programs(
    db: AsyncSession, *, n: int = 3, published: bool = True
) -> list[Program]:
    admin = User(
        id=uuid4(),
        email=f"inst-{uuid4().hex[:6]}@example.com",
        cognito_sub=f"dev-sub-{uuid4().hex[:8]}",
        role=UserRole.institution_admin,
        is_active=True,
    )
    db.add(admin)
    await db.flush()
    inst = Institution(
        admin_user_id=admin.id,
        name="HookU",
        type="university",
        country="US",
    )
    db.add(inst)
    await db.flush()
    programs: list[Program] = []
    for i in range(n):
        p = Program(
            institution_id=inst.id,
            program_name=f"Program {i}",
            degree_type="MS",
            description_text=f"Description {i}",
            is_published=published,
        )
        db.add(p)
        programs.append(p)
    await db.commit()
    for p in programs:
        await db.refresh(p)
    return programs


async def _seed_feature_vector(
    db: AsyncSession, student_id, *, version: int = 1
) -> StudentFeatureVector:
    sfv = StudentFeatureVector(
        student_id=student_id,
        profile_version=version,
        embedding=[0.1] * 1024,
        sparse_features={
            "education_level": "bachelors",
            "feature_completeness": 0.8,
            "interest_themes": ["machine_learning"],
        },
        applicant_summary="Has a feature vector.",
    )
    db.add(sfv)
    await db.commit()
    await db.refresh(sfv)
    return sfv


# ── Direct hook tests ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_recompute_creates_match_results(db_session: AsyncSession):
    """Happy path: student has a feature vector, catalog has programs,
    the hook fires → match_results rows appear."""
    student = await _seed_student(db_session)
    await _seed_feature_vector(db_session, student.id)
    await _seed_published_programs(db_session, n=3)

    svc = DiscoveryService(db_session)
    await svc._recompute_matches_for_student(student_id=student.id)
    await db_session.commit()

    result = await db_session.execute(
        select(MatchResult).where(MatchResult.student_id == student.id)
    )
    rows = list(result.scalars().all())
    assert len(rows) == 3


@pytest.mark.asyncio
async def test_recompute_skips_when_no_published_programs(
    db_session: AsyncSession,
):
    """Empty catalog → no-op, no exception, no rows."""
    student = await _seed_student(db_session)
    await _seed_feature_vector(db_session, student.id)
    # No programs seeded.

    svc = DiscoveryService(db_session)
    await svc._recompute_matches_for_student(student_id=student.id)

    rows = await db_session.execute(select(MatchResult).where(MatchResult.student_id == student.id))
    assert list(rows.scalars().all()) == []


@pytest.mark.asyncio
async def test_recompute_ignores_unpublished_programs(
    db_session: AsyncSession,
):
    """Unpublished programs shouldn't show up in match_results — they're
    not browsable on the frontend, so matching them is wasted work."""
    student = await _seed_student(db_session)
    await _seed_feature_vector(db_session, student.id)
    await _seed_published_programs(db_session, n=2, published=False)
    pub = await _seed_published_programs(db_session, n=1, published=True)

    svc = DiscoveryService(db_session)
    await svc._recompute_matches_for_student(student_id=student.id)
    await db_session.commit()

    rows = await db_session.execute(select(MatchResult).where(MatchResult.student_id == student.id))
    rows = list(rows.scalars().all())
    assert len(rows) == 1
    assert rows[0].program_id == pub[0].id


@pytest.mark.asyncio
async def test_recompute_replaces_existing_match_results(
    db_session: AsyncSession,
):
    """On re-emit (profile change) the hook re-runs and stale rows go
    away. Otherwise match_results bloats every time the student
    re-completes Discovery."""
    student = await _seed_student(db_session)
    await _seed_feature_vector(db_session, student.id)
    programs = await _seed_published_programs(db_session, n=2)

    svc = DiscoveryService(db_session)
    await svc._recompute_matches_for_student(student_id=student.id)
    await db_session.commit()

    pre_rows = await db_session.execute(
        select(MatchResult).where(MatchResult.student_id == student.id)
    )
    pre_ids = {r.program_id for r in pre_rows.scalars().all()}
    assert pre_ids == {p.id for p in programs}

    # Add another program then re-run.
    new = await _seed_published_programs(db_session, n=1)
    await svc._recompute_matches_for_student(student_id=student.id)
    await db_session.commit()

    post_rows = await db_session.execute(
        select(MatchResult).where(MatchResult.student_id == student.id)
    )
    post_ids = {r.program_id for r in post_rows.scalars().all()}
    assert post_ids == {p.id for p in programs} | {new[0].id}
    # Stale rows replaced, not appended.
    assert len(post_ids) == 3


@pytest.mark.asyncio
async def test_recompute_when_no_feature_vector_returns_empty(
    db_session: AsyncSession,
):
    """Defensive: a student with no feature vector yields zero matches
    (the service guards against this). The hook should not crash."""
    student = await _seed_student(db_session)
    await _seed_published_programs(db_session, n=2)

    svc = DiscoveryService(db_session)
    await svc._recompute_matches_for_student(student_id=student.id)
    await db_session.commit()

    rows = await db_session.execute(select(MatchResult).where(MatchResult.student_id == student.id))
    assert list(rows.scalars().all()) == []


# ── End-to-end via _emit_features_for_completion ───────────────────────────


@pytest.mark.asyncio
async def test_emit_chain_persists_features_and_runs_matches(
    db_session: AsyncSession,
    monkeypatch,
):
    """End-to-end: stub the FeatureEmitter, then assert
    _emit_features_for_completion both persists the feature vector
    AND fires the match recompute."""
    from unipaith.ai import feature_emitter as fe

    student = await _seed_student(db_session)
    await _seed_published_programs(db_session, n=2)

    fake_features = fe.EmittedFeatures(
        sparse_features={
            "education_level": "bachelors",
            "intended_degrees": ["masters"],
            "intended_majors": ["cs"],
            "geo_must": ["US"],
            "geo_avoid": [],
            "interest_themes": ["machine_learning"],
            "career_arcs": ["research"],
            "values": ["impact"],
            "needs_signals": {},
            "social_prefs": {},
            "feature_completeness": 0.85,
        },
        applicant_summary="Stub summary",
        embedding=[0.1] * 1024,
    )

    class _StubEmitter:
        async def emit(self, *, snapshot, student_id, db):  # noqa: ARG002
            return fake_features

    monkeypatch.setattr(fe, "get_feature_emitter", lambda: _StubEmitter())

    svc = DiscoveryService(db_session)
    await svc._emit_features_for_completion(student_id=student.id, snapshot=None)
    await db_session.commit()

    sfv = await db_session.scalar(
        select(StudentFeatureVector).where(StudentFeatureVector.student_id == student.id)
    )
    assert sfv is not None
    assert sfv.applicant_summary == "Stub summary"

    matches = await db_session.execute(
        select(MatchResult).where(MatchResult.student_id == student.id)
    )
    rows = list(matches.scalars().all())
    assert len(rows) == 2
