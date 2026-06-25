"""todo 1.1 — completing onboarding seeds matches.

Before this wire, a student who only signed up + finished the onboarding wizard
had NO feature vector, so the matcher returned [] until they happened to chat
with Uni. ``patch_onboarding_state(completed=True)`` must now emit a feature
vector AND compute matches, reusing the same path Discovery uses. Fail-soft: a
seed failure must never break the onboarding PATCH.
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
from unipaith.schemas.student import OnboardingAnswers, PatchOnboardingStateRequest
from unipaith.services.student_service import StudentService


async def _seed_student(db: AsyncSession) -> StudentProfile:
    user = User(
        id=uuid4(),
        email=f"seed-{uuid4().hex[:6]}@example.com",
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


async def _seed_published_programs(db: AsyncSession, *, n: int = 3) -> list[Program]:
    admin = User(
        id=uuid4(),
        email=f"inst-{uuid4().hex[:6]}@example.com",
        cognito_sub=f"dev-sub-{uuid4().hex[:8]}",
        role=UserRole.institution_admin,
        is_active=True,
    )
    db.add(admin)
    await db.flush()
    inst = Institution(admin_user_id=admin.id, name="SeedU", type="university", country="US")
    db.add(inst)
    await db.flush()
    programs: list[Program] = []
    for i in range(n):
        p = Program(
            institution_id=inst.id,
            program_name=f"Program {i}",
            degree_type="MS",
            description_text=f"Description {i}",
            is_published=True,
        )
        db.add(p)
        programs.append(p)
    await db.commit()
    return programs


def _stub_emitter(monkeypatch):
    from unipaith.ai import feature_emitter as fe

    fake = fe.EmittedFeatures(
        sparse_features={
            "education_level": "bachelors",
            "intended_degrees": ["masters"],
            "intended_majors": ["computer science"],
            "geo_must": ["US"],
            "geo_avoid": [],
            "interest_themes": ["machine_learning"],
            "career_arcs": ["research"],
            "values": ["impact"],
            "needs_signals": {},
            "social_prefs": {},
            "feature_completeness": 0.85,
        },
        applicant_summary="Seeded at onboarding.",
        embedding=[0.1] * 1024,
    )

    class _Stub:
        async def emit(self, *, snapshot, student_id, db):  # noqa: ARG002
            return fake

    monkeypatch.setattr(fe, "get_feature_emitter", lambda: _Stub())


@pytest.mark.asyncio
async def test_onboarding_completion_seeds_feature_vector_and_matches(
    db_session: AsyncSession, monkeypatch
):
    student = await _seed_student(db_session)
    programs = await _seed_published_programs(db_session, n=3)
    _stub_emitter(monkeypatch)

    svc = StudentService(db_session)
    await svc.patch_onboarding_state(
        student.user_id,
        PatchOnboardingStateRequest(
            answers=OnboardingAnswers(degree_level="masters", interests=["cs_data_ai"]),
            completed=True,
        ),
    )
    await db_session.commit()

    sfv = await db_session.scalar(
        select(StudentFeatureVector).where(StudentFeatureVector.student_id == student.id)
    )
    assert sfv is not None, "onboarding completion must emit a feature vector"

    rows = (
        (await db_session.execute(select(MatchResult).where(MatchResult.student_id == student.id)))
        .scalars()
        .all()
    )
    assert len(rows) == len(programs), "matches should appear immediately after onboarding"


@pytest.mark.asyncio
async def test_onboarding_seed_does_not_embed_catalog(db_session: AsyncSession, monkeypatch):
    """Regression: the in-request match recompute must NEVER embed the catalog.
    ensure_program_embeddings embeds every uncached program one-at-a-time; at ~7k
    programs that timed out onboarding completion / matches refresh and a fresh
    student saw zero matches. The recompute now uses cached embeddings only, so
    matches still seed without any embedding work."""
    from unipaith.services.match_service import MatchService

    student = await _seed_student(db_session)
    programs = await _seed_published_programs(db_session, n=3)
    _stub_emitter(monkeypatch)

    async def _must_not_call(self, programs):  # noqa: ANN001, ARG001
        raise AssertionError("request path must not embed the catalog (use cached only)")

    monkeypatch.setattr(MatchService, "ensure_program_embeddings", _must_not_call)

    svc = StudentService(db_session)
    await svc.patch_onboarding_state(
        student.user_id,
        PatchOnboardingStateRequest(
            answers=OnboardingAnswers(degree_level="masters", interests=["cs_data_ai"]),
            completed=True,
        ),
    )
    await db_session.commit()

    rows = (
        (await db_session.execute(select(MatchResult).where(MatchResult.student_id == student.id)))
        .scalars()
        .all()
    )
    assert len(rows) == len(programs), "matches seed via cached-only embeddings, no catalog embed"


@pytest.mark.asyncio
async def test_cached_program_embeddings_reads_only(db_session: AsyncSession):
    """cached_program_embeddings returns only already-stored, version-current
    vectors and computes nothing (no embed calls, no DB writes)."""
    from unipaith.services.match_service import MatchService

    programs = await _seed_published_programs(db_session, n=3)
    programs[0].embedding = [0.2] * 8
    programs[0].embedding_version = programs[0].feature_version
    programs[1].embedding = [0.3] * 8
    programs[1].embedding_version = (programs[1].feature_version or 0) + 99  # stale → skipped
    await db_session.commit()

    out = MatchService(db_session).cached_program_embeddings(programs)
    assert set(out) == {programs[0].id}  # only the fresh, embedded one
    assert out[programs[0].id] == [0.2] * 8


@pytest.mark.asyncio
async def test_onboarding_seed_is_fail_soft(db_session: AsyncSession, monkeypatch):
    """If the emitter blows up, onboarding still completes (no feature vector,
    no matches, no exception) — the student seeds on their first Discovery turn."""
    from unipaith.ai import feature_emitter as fe

    student = await _seed_student(db_session)
    await _seed_published_programs(db_session, n=2)

    class _Boom:
        async def emit(self, *, snapshot, student_id, db):  # noqa: ARG002
            raise RuntimeError("emitter down")

    monkeypatch.setattr(fe, "get_feature_emitter", lambda: _Boom())

    svc = StudentService(db_session)
    state = await svc.patch_onboarding_state(
        student.user_id,
        PatchOnboardingStateRequest(
            answers=OnboardingAnswers(degree_level="masters", interests=["cs_data_ai"]),
            completed=True,
        ),
    )
    await db_session.commit()

    assert state["completed_at"] is not None  # onboarding still succeeded
    sfv = await db_session.scalar(
        select(StudentFeatureVector).where(StudentFeatureVector.student_id == student.id)
    )
    assert sfv is None
