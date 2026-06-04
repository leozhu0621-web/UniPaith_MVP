"""Spec 65 §3 — program dense embeddings revive the matcher cosine term.

Before this, no Program ever carried an embedding, so the cosine term (45% of
fitness) was structurally dead in the live recompute path. These tests prove the
embedding is computed + cached and that cosine actually fires when both the
student and the program are embedded.
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
from unipaith.services.match_service import MatchService
from unipaith.services.program_features import program_row_from_orm


async def _seed(db: AsyncSession) -> tuple[StudentProfile, Program]:
    admin = User(
        id=uuid4(),
        email=f"a{uuid4().hex[:6]}@e.co",
        cognito_sub=f"s{uuid4().hex[:8]}",
        role=UserRole.institution_admin,
        is_active=True,
    )
    db.add(admin)
    await db.flush()
    inst = Institution(admin_user_id=admin.id, name="Test U", type="university", country="US")
    db.add(inst)
    await db.flush()
    program = Program(
        institution_id=inst.id,
        program_name="MS Computer Science",
        degree_type="masters",
        description_text="A research-focused CS masters in machine learning.",
        is_published=True,
    )
    db.add(program)
    await db.flush()
    suser = User(
        id=uuid4(),
        email=f"st{uuid4().hex[:6]}@e.co",
        cognito_sub=f"ss{uuid4().hex[:8]}",
        role=UserRole.student,
        is_active=True,
    )
    db.add(suser)
    await db.flush()
    profile = StudentProfile(user_id=suser.id)
    db.add(profile)
    await db.flush()
    db.add(
        StudentFeatureVector(
            student_id=profile.id,
            profile_version=1,
            sparse_features={
                "feature_completeness": 0.8,
                "education_level": "bachelors",
                "interest_themes": ["machine_learning"],
            },
            applicant_summary="A CS-focused applicant.",
            embedding=[0.1] * 1024,
        )
    )
    await db.commit()
    await db.refresh(program)
    await db.refresh(profile)
    return profile, program


@pytest.mark.asyncio
async def test_ensure_program_embeddings_populates_and_caches(db_session: AsyncSession) -> None:
    _, program = await _seed(db_session)
    svc = MatchService(db_session)

    embs = await svc.ensure_program_embeddings([program])
    assert program.id in embs
    assert isinstance(embs[program.id], list)
    assert len(embs[program.id]) == 1024

    await db_session.refresh(program)
    assert isinstance(program.embedding, list)
    assert len(program.embedding) == 1024
    assert program.embedding_version == program.feature_version

    # Idempotent — a second call reuses the cached vector (no recompute).
    cached = list(program.embedding)
    embs2 = await svc.ensure_program_embeddings([program])
    assert embs2[program.id] == cached


@pytest.mark.asyncio
async def test_cosine_fires_when_both_sides_embedded(db_session: AsyncSession) -> None:
    profile, program = await _seed(db_session)
    svc = MatchService(db_session)
    embs = await svc.ensure_program_embeddings([program])

    rows = await svc.compute_matches_for_student(
        profile.id,
        program_rows=[program_row_from_orm(program)],
        program_embeddings=embs,
    )
    assert rows  # program not eliminated

    mr = (
        (await db_session.execute(select(MatchResult).where(MatchResult.student_id == profile.id)))
        .scalars()
        .first()
    )
    assert mr is not None
    # The whole point of Spec 65: cosine is now applied, not a dead 0.
    assert mr.fitness_breakdown.get("cosine_applied") is True
    assert "cosine" in mr.fitness_breakdown


@pytest.mark.asyncio
async def test_can_match_false_without_feature_vector(db_session: AsyncSession) -> None:
    """A student who hasn't completed Discovery (no feature vector) is not
    match-ready — callers gate the catalog embedding on this so the empty-state
    refresh path doesn't burn embedding calls."""
    user = User(
        id=uuid4(),
        email=f"nf{uuid4().hex[:6]}@e.co",
        cognito_sub=f"nf{uuid4().hex[:8]}",
        role=UserRole.student,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    profile = StudentProfile(user_id=user.id)
    db_session.add(profile)
    await db_session.commit()
    assert await MatchService(db_session).can_match(profile.id) is False


@pytest.mark.asyncio
async def test_can_match_true_when_ready(db_session: AsyncSession) -> None:
    profile, _ = await _seed(db_session)
    assert await MatchService(db_session).can_match(profile.id) is True
