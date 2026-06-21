from __future__ import annotations

from uuid import uuid4

import pytest


def _program_view():
    from unipaith.ai.rationale import ProgramView

    return ProgramView(
        name="Master of Business Analytics",
        description=(
            "A rigorous analytics program using machine learning, optimization, "
            "team projects, and a capstone with employer sponsors."
        ),
        sparse={
            "degree_type": "masters",
            "duration_months": 12,
            "delivery_format": "in_person",
            "tuition": 93834,
            "who_its_for": "Quantitative students seeking data-science careers.",
            "tracks": {
                "learning_format": "Team-based coursework and Analytics Capstone",
                "curriculum": [{"courses": ["Machine Learning", "Optimization"]}],
            },
            "outcomes": {
                "top_industries": ["Technology", "Consulting"],
                "median_salary": 143000,
                "source_url": "https://example.edu/employment-report",
            },
            "requirements": {
                "evaluation": "Quantitative aptitude, programming readiness, and collaboration.",
                "materials": [{"name": "Resume", "required": True}],
            },
            "profile_intelligence": {
                "sections": {
                    "learning_experience": {
                        "findings": [
                            {
                                "statement": "The program is collaborative and project-heavy.",
                                "evidence": [{"url": "https://example.edu/program"}],
                            }
                        ]
                    }
                }
            },
        },
        program_id=uuid4(),
        program_version=3,
    )


def test_decision_brief_requires_evidence_per_item():
    from pydantic import ValidationError

    from unipaith.schemas.profile_intelligence import DecisionBrief

    with pytest.raises(ValidationError):
        DecisionBrief.model_validate(
            {
                "program_profile_version": 1,
                "student_profile_version": 1,
                "sections": {
                    "fit": [
                        {
                            "statement": "You fit the program.",
                            "confidence": 0.8,
                            "evidence": [],
                        }
                    ]
                },
            }
        )


def test_decision_brief_rejects_protected_trait_reasoning():
    from pydantic import ValidationError

    from unipaith.schemas.profile_intelligence import DecisionBrief

    with pytest.raises(ValidationError):
        DecisionBrief.model_validate(
            {
                "program_profile_version": 1,
                "student_profile_version": 1,
                "sections": {
                    "fit": [
                        {
                            "statement": "This is a fit because of religion.",
                            "confidence": 0.8,
                            "evidence": [
                                {"side": "program", "path": "description", "label": "Program"}
                            ],
                        }
                    ]
                },
            }
        )


def test_decision_brief_changes_for_contrasting_student_profiles():
    from unipaith.services.decision_brief import build_decision_brief

    program = _program_view()
    analytics_student = {
        "gpa": 3.9,
        "field_of_study": "data_science",
        "interest_themes": ["machine_learning", "data_analysis"],
        "career_arcs": ["data_science_industry"],
        "values": ["applied_impact", "intellectual_rigor"],
        "social_prefs": {"peer_collab": 0.9},
        "budget_max_usd_per_year": 120000,
    }
    studio_student = {
        "gpa": 3.1,
        "field_of_study": "fine_art",
        "interest_themes": ["fine_art", "creative_practice"],
        "career_arcs": ["creative_practice"],
        "values": ["creative_autonomy"],
        "social_prefs": {"independent": 0.9},
        "budget_max_usd_per_year": 30000,
    }

    a = build_decision_brief(
        student_sparse=analytics_student,
        program=program,
        fitness_breakdown={"soft_align": {"value": 0.92}},
        confidence_breakdown={"profile_depth": {"value": 0.8}},
        student_profile_version=4,
    )
    b = build_decision_brief(
        student_sparse=studio_student,
        program=program,
        fitness_breakdown={"soft_align": {"value": 0.25}},
        confidence_breakdown={"profile_depth": {"value": 0.8}},
        student_profile_version=4,
    )

    assert a != b
    assert any("data-science" in item["statement"] for item in a["sections"]["career_alignment"])
    assert any("academic" in item["statement"].lower() for item in b["sections"]["academic_gaps"])
    assert any("cost" in item["statement"].lower() for item in b["sections"]["cost_aid"])
    for brief in (a, b):
        for items in brief["sections"].values():
            for item in items:
                assert item["evidence"], item


async def test_match_rationale_cache_carries_decision_brief(db_session):
    from unipaith.models.ai_artifacts import MatchRationale
    from unipaith.models.institution import Institution, Program
    from unipaith.models.student import StudentProfile
    from unipaith.models.user import User, UserRole

    student_user = User(
        id=uuid4(),
        email=f"student-{uuid4().hex}@example.com",
        cognito_sub=f"student-{uuid4().hex}",
        role=UserRole.student,
    )
    admin_user = User(
        id=uuid4(),
        email=f"admin-{uuid4().hex}@example.com",
        cognito_sub=f"admin-{uuid4().hex}",
        role=UserRole.institution_admin,
    )
    student = StudentProfile(user_id=student_user.id)
    institution = Institution(
        admin_user_id=admin_user.id,
        name="Evidence University",
        type="university",
        country="US",
    )
    program = Program(
        institution=institution,
        program_name="Evidence Analytics",
        degree_type="masters",
        is_published=True,
    )
    db_session.add_all([student_user, admin_user, student, institution, program])
    await db_session.flush()

    brief = {
        "program_profile_version": 2,
        "student_profile_version": 7,
        "sections": {
            "fit": [
                {
                    "statement": "Evidence-backed fit.",
                    "confidence": 0.8,
                    "evidence": [{"side": "program", "path": "description", "label": "Program"}],
                }
            ]
        },
    }
    row = MatchRationale(
        student_id=student.id,
        program_id=program.id,
        profile_version=7,
        program_version=2,
        prompt_version=99,
        rationale_text="A grounded rationale.",
        decision_brief=brief,
        cited_student_fields=[],
        cited_program_fields=["description"],
    )
    db_session.add(row)
    await db_session.flush()

    assert row.decision_brief == brief
