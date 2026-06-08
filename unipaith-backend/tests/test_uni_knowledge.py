"""Uni knowledge grounding — retriever + bundle (mostly deterministic)."""

from __future__ import annotations

import pytest

from unipaith.ai.state import GoalEntry, NeedEntry, StudentSnapshot
from unipaith.services.uni_knowledge import (
    KnowledgeBundle,
    ProgramFact,
    UniKnowledgeRetriever,
    build_query,
)


def _snap(**kw) -> StudentSnapshot:
    return StudentSnapshot(**kw)


def test_build_query_none_without_interest() -> None:
    # Counselor-paced gate: no goal interest → no retrieval.
    assert build_query(_snap()) is None
    needs_only = _snap(needs=[NeedEntry(maslow_level="safety", signal="affordability")])
    assert build_query(needs_only) is None


def test_build_query_from_goals_and_location() -> None:
    q = build_query(
        _snap(
            goals=[GoalEntry(category="academic", specific="study marine biology")],
            location_prefs=["Maine"],
        )
    )
    assert q is not None
    assert "marine biology" in q.query
    assert q.location == "Maine"


def test_bundle_render_empty_is_blank() -> None:
    assert KnowledgeBundle().render() == ""


def test_bundle_render_lists_programs_cited() -> None:
    b = KnowledgeBundle(
        programs=[
            ProgramFact(
                program_id="p1",
                name="Marine Biology BS",
                school="U Maine",
                degree_type="bachelors",
                tuition=18000,
                acceptance_rate=0.7,
                median_salary=52000,
            )
        ]
    )
    out = b.render()
    assert "From your knowledge base" in out
    assert "Marine Biology BS" in out and "U Maine" in out
    assert "18,000" in out and "52,000" in out


@pytest.mark.asyncio
async def test_retrieve_empty_without_interest(db_session) -> None:
    bundle = await UniKnowledgeRetriever(db_session).retrieve(StudentSnapshot())
    assert bundle.is_empty()


@pytest.mark.asyncio
async def test_retrieve_returns_programs_for_interest(db_session) -> None:
    # Seed an institution-admin user + institution + a published program so the
    # full-text search finds it (institutions.admin_user_id is not-null).
    import uuid

    from unipaith.models.institution import Institution, Program
    from unipaith.models.user import User, UserRole

    iu = User(
        id=uuid.uuid4(),
        email=f"i-{uuid.uuid4().hex[:8]}@example.com",
        cognito_sub=f"sub-{uuid.uuid4().hex[:8]}",
        role=UserRole("institution_admin"),
        is_active=True,
    )
    db_session.add(iu)
    await db_session.flush()
    inst = Institution(admin_user_id=iu.id, name="U Maine", type="university", country="US")
    db_session.add(inst)
    await db_session.flush()
    db_session.add(
        Program(
            institution_id=inst.id,
            program_name="Marine Biology BS",
            degree_type="bachelors",
            tuition=18000,
            description_text="marine biology coastal field study",
            is_published=True,
        )
    )
    await db_session.flush()

    snap = StudentSnapshot(goals=[GoalEntry(category="academic", specific="marine biology")])
    bundle = await UniKnowledgeRetriever(db_session).retrieve(snap)
    assert any("Marine Biology" in p.name for p in bundle.programs)
    assert "From your knowledge base" in bundle.render()
