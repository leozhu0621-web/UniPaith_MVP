from __future__ import annotations

from typing import Any

from unipaith.ai.rationale import ProgramView
from unipaith.schemas.profile_intelligence import validate_decision_brief


def _program_ev(path: str, label: str, *, url: str | None = None) -> dict:
    return {"side": "program", "path": path, "label": label, **({"url": url} if url else {})}


def _student_ev(path: str, label: str) -> dict:
    return {"side": "student", "path": path, "label": label}


def _append(
    sections: dict[str, list[dict]],
    key: str,
    statement: str,
    evidence: list[dict],
    *,
    confidence: float = 0.65,
    uncertainty: str | None = None,
) -> None:
    if not statement or not evidence:
        return
    sections.setdefault(key, []).append(
        {
            "statement": statement,
            "confidence": confidence,
            "uncertainty": uncertainty,
            "evidence": evidence,
        }
    )


def _list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value if v]
    if isinstance(value, set | tuple):
        return [str(v) for v in value if v]
    return []


def _text(value: Any) -> str:
    return str(value or "").lower()


def _program_url(program: ProgramView) -> str | None:
    sparse = program.sparse or {}
    source = sparse.get("source_url") or sparse.get("website_url")
    if isinstance(source, str) and source.startswith("http"):
        return source
    profile = sparse.get("profile_intelligence")
    if isinstance(profile, dict):
        for section in (profile.get("sections") or {}).values():
            for finding in (section or {}).get("findings", []):
                for ev in finding.get("evidence", []):
                    url = ev.get("url")
                    if isinstance(url, str) and url.startswith("http"):
                        return url
    return None


def _program_career_words(program: ProgramView) -> str:
    outcomes = (program.sparse or {}).get("outcomes") or {}
    industries = outcomes.get("top_industries") or []
    roles = outcomes.get("common_roles") or []
    return " ".join(map(str, [*industries, *roles, program.description, program.name])).lower()


def _program_learning_words(program: ProgramView) -> str:
    sparse = program.sparse or {}
    return " ".join(
        [
            str(program.description or ""),
            str(sparse.get("tracks") or ""),
            str(sparse.get("who_its_for") or ""),
            str(sparse.get("requirements") or ""),
        ]
    ).lower()


def _student_has_analytics_direction(student_sparse: dict[str, Any]) -> bool:
    tokens = " ".join(
        [
            str(student_sparse.get("field_of_study") or ""),
            " ".join(_list(student_sparse.get("interest_themes"))),
            " ".join(_list(student_sparse.get("career_arcs"))),
        ]
    ).lower()
    return any(
        t in tokens
        for t in ("data", "analytics", "machine_learning", "ml", "statistics", "computer")
    )


def build_decision_brief(
    *,
    student_sparse: dict[str, Any],
    program: ProgramView,
    fitness_breakdown: dict[str, Any] | None = None,
    confidence_breakdown: dict[str, Any] | None = None,
    student_profile_version: int = 1,
) -> dict[str, Any]:
    """Build a student-safe private decision brief from already-grounded inputs.

    The brief uses qualitative statements, evidence paths, and uncertainty. It
    deliberately omits raw scores and never reads or scores protected traits.
    """
    sparse = program.sparse or {}
    url = _program_url(program)
    program_ev = _program_ev("description", "Program description", url=url)
    sections: dict[str, list[dict]] = {}
    omissions: list[dict[str, str]] = []

    program_words = _program_learning_words(program)
    career_words = _program_career_words(program)
    has_analytics = _student_has_analytics_direction(student_sparse)

    if has_analytics and any(
        t in career_words for t in ("analytics", "data", "technology", "consulting", "machine")
    ):
        _append(
            sections,
            "fit",
            (
                "Your stated data or analytics direction lines up with the program's "
                "analytics and data-science emphasis."
            ),
            [program_ev, _student_ev("sparse.interest_themes", "Student interests")],
            confidence=0.78,
        )
        _append(
            sections,
            "career_alignment",
            (
                "The program's reported pathways are relevant to data-science, "
                "technology, consulting, or analytics roles."
            ),
            [
                _program_ev("sparse.outcomes", "Program outcomes", url=url),
                _student_ev("sparse.career_arcs", "Student career goals"),
            ],
            confidence=0.76,
        )
    else:
        _append(
            sections,
            "conflicts",
            (
                "Your current academic or career direction does not clearly match the "
                "program's analytics-heavy evidence."
            ),
            [program_ev, _student_ev("sparse.interest_themes", "Student interests")],
            confidence=0.7,
            uncertainty=(
                "This may change if your latest goals or coursework are missing from your profile."
            ),
        )

    gpa = student_sparse.get("gpa")
    req_text = _text(sparse.get("requirements"))
    if (gpa is None or float(gpa) < 3.5) and any(
        t in req_text + program_words
        for t in ("quantitative", "programming", "machine learning", "optimization", "rigorous")
    ):
        _append(
            sections,
            "academic_gaps",
            (
                "The main academic gap to investigate is quantitative and programming "
                "readiness for a rigorous analytics curriculum."
            ),
            [
                _program_ev("sparse.requirements", "Program requirements", url=url),
                _student_ev("sparse.gpa", "Academic profile"),
            ],
            confidence=0.72,
        )
    elif gpa is not None:
        _append(
            sections,
            "academic_gaps",
            (
                "No obvious GPA readiness issue appears from the available profile data, "
                "but prerequisites still need verification."
            ),
            [
                _program_ev("sparse.requirements", "Program requirements", url=url),
                _student_ev("sparse.gpa", "Academic profile"),
            ],
            confidence=0.58,
            uncertainty=(
                "Course-level prerequisite evidence is incomplete unless the program "
                "publishes it explicitly."
            ),
        )

    tuition = sparse.get("tuition")
    budget = student_sparse.get("budget_max_usd_per_year")
    if tuition is not None and budget is not None and float(tuition) > float(budget):
        _append(
            sections,
            "cost_aid",
            (
                "Cost is a likely constraint: published tuition appears above your stated "
                "annual budget, so aid, savings, employer support, or alternatives matter "
                "before shortlisting."
            ),
            [
                _program_ev("sparse.tuition", "Program tuition", url=url),
                _student_ev("sparse.budget_max_usd_per_year", "Student budget"),
            ],
            confidence=0.78,
        )
    elif tuition is not None:
        _append(
            sections,
            "cost_aid",
            "Cost should still be modeled with fees and living expenses, not tuition alone.",
            [_program_ev("sparse.tuition", "Program tuition", url=url)],
            confidence=0.62,
        )
    else:
        omissions.append(
            {"section": "cost_aid", "reason": "No cited tuition or cost data in program view."}
        )

    if sparse.get("delivery_format"):
        _append(
            sections,
            "feasibility",
            (
                f"The delivery format is {sparse['delivery_format']}; confirm it matches "
                "your location, modality, and visa constraints."
            ),
            [_program_ev("sparse.delivery_format", "Delivery format", url=url)],
            confidence=0.64,
        )
    if sparse.get("duration_months"):
        _append(
            sections,
            "timeline",
            (
                f"The published duration is {sparse['duration_months']} months, so "
                "application readiness should be planned around that pace."
            ),
            [_program_ev("sparse.duration_months", "Program duration", url=url)],
            confidence=0.7,
        )

    if any(t in program_words for t in ("team", "collaboration", "collaborative", "cohort")):
        _append(
            sections,
            "support_compatibility",
            (
                "The learning model appears collaborative or cohort-based; this is a "
                "strength if you prefer peer work and a friction point if you prefer "
                "mostly independent study."
            ),
            [
                _program_ev("sparse.tracks", "Learning format", url=url),
                _student_ev("sparse.social_prefs", "Learning preferences"),
            ],
            confidence=0.68,
        )

    next_action = (
        "Verify prerequisites and strengthen quantitative evidence before applying."
        if sections.get("academic_gaps")
        else (
            "Compare this program against lower-cost and similar-career alternatives "
            "before committing."
        )
    )
    _append(
        sections,
        "next_actions",
        next_action,
        [program_ev, _student_ev("sparse", "Student profile")],
        confidence=0.72,
    )

    if not sections.get("career_alignment"):
        omissions.append(
            {
                "section": "career_alignment",
                "reason": "Program outcomes or student career goals were insufficiently specific.",
            }
        )
    if not sections.get("support_compatibility"):
        omissions.append(
            {
                "section": "support_compatibility",
                "reason": "Support-service and learning-preference evidence was incomplete.",
            }
        )

    brief = {
        "standard_version": 1,
        "student_profile_version": student_profile_version,
        "program_profile_version": int(program.program_version or 1),
        "sections": sections,
        "omissions": omissions,
    }
    return validate_decision_brief(brief)
