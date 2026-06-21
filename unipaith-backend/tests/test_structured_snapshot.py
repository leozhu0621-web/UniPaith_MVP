"""snapshot_from_structured_tables — the managed-agent feature-emission fix (#8).

The live Uni agent persists Discovery signals to the structured tables but never to
discovery_messages.extracted_signals, so the matcher got no feature vector → [] for
every student onboarded through it. This builder reads the structured tables into a
StudentSnapshot for the feature emitter. DB test, no LLM.
"""

from decimal import Decimal

import pytest

from tests._uni_helpers import ensure_profile
from unipaith.ai.artifacts import snapshot_from_structured_tables
from unipaith.models.goals import StudentGoal
from unipaith.models.identity import StudentIdentity
from unipaith.models.needs import StudentNeed
from unipaith.models.student import AcademicRecord


@pytest.mark.asyncio
async def test_snapshot_from_structured_tables_maps_goals_needs_identity_gpa(
    db_session, mock_student_user
):
    profile = await ensure_profile(db_session, mock_student_user)
    db_session.add(
        AcademicRecord(
            student_id=profile.id,
            is_current=True,
            normalized_gpa=Decimal("3.70"),
            institution_name="Prior University",
            degree_type="bachelors",
        )
    )
    db_session.add(
        StudentGoal(
            student_id=profile.id,
            category="academic",
            specific="Get into a top MS in CS",
            measurable="GRE 320",
        )
    )
    db_session.add(
        StudentNeed(
            student_id=profile.id,
            maslow_level="self_esteem",
            need_type="recognition",
            signal="wants a program with strong reputation",
            severity="strong_preference",
            source_quote="I want a name-brand school",
        )
    )
    db_session.add(
        StudentIdentity(
            student_id=profile.id,
            core_values=[{"value": "impact", "source_quote": "I want to help people"}],
            worldview=[{"belief": "tech can do good", "source_quote": "tools help"}],
            self_awareness=[{"insight": "I procrastinate", "source_quote": "I leave things late"}],
        )
    )
    await db_session.flush()

    snap = await snapshot_from_structured_tables(db_session, profile.id)

    assert snap.gpa == 3.7
    assert any(
        g.specific == "Get into a top MS in CS" and g.category == "academic" for g in snap.goals
    )
    # need: tag from need_type, free_text from model.signal, evidence from source_quote
    assert any(
        n.signal == "recognition"
        and "reputation" in n.free_text
        and n.maslow_level == "self_esteem"
        for n in snap.needs
    )
    facets = {c.facet for c in snap.identity_claims}
    assert {"value", "belief", "self_awareness"} <= facets
    assert any(c.claim == "impact" for c in snap.identity_claims)


@pytest.mark.asyncio
async def test_snapshot_empty_for_student_with_no_structured_data(db_session, mock_student_user):
    profile = await ensure_profile(db_session, mock_student_user)
    snap = await snapshot_from_structured_tables(db_session, profile.id)
    assert snap.goals == [] and snap.needs == [] and snap.identity_claims == []
    assert snap.gpa is None


@pytest.mark.asyncio
async def test_ensure_feature_vector_is_noop_when_vector_exists(db_session, mock_student_user):
    """Safety: the managed-path emission hook must NOT re-emit / clobber an existing
    feature vector — it only fills the gap when none exists."""
    from unipaith.models.ai_artifacts import StudentFeatureVector
    from unipaith.services.uni_tools import _ensure_feature_vector

    profile = await ensure_profile(db_session, mock_student_user)
    db_session.add(StudentFeatureVector(student_id=profile.id, sparse_features={"sentinel": 1}))
    await db_session.flush()

    await _ensure_feature_vector(db_session, profile.id)  # must not raise or overwrite

    fv = await db_session.get(StudentFeatureVector, profile.id)
    assert fv is not None
    assert fv.sparse_features == {"sentinel": 1}
