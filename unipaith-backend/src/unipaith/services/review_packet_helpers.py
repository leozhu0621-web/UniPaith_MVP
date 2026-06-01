"""Pure transforms for the Spec 32 review packet — blind-review redaction (§7A.1),
rubric-score aggregation + variance (§4), holistic context flags (§7A.4), and
test-optional analysis (§7A.3).

Kept side-effect-free (no DB, no LLM) so they are unit-testable and the service
stays thin. ``ReviewPipelineService`` calls these after loading rows.
"""

from __future__ import annotations

from datetime import date
from typing import Any

# Δ at/above which reviewers are flagged divergent on a criterion (spec 32 §4).
VARIANCE_THRESHOLD = 1.5

# Identity-revealing fields redacted during blind review (spec 32 §7A.1):
# name, age, gender, geography precision, and (optionally) prior school.
BLIND_REDACTED_KEYS = (
    "first_name",
    "last_name",
    "preferred_name",
    "name_in_native_script",
    "preferred_pronouns",
    "date_of_birth",
    "age",
    "gender_identity",
    "legal_sex",
    "nationality",
    "place_of_birth",
    "country_of_residence",
    "photo_url",
)


def blind_redact_student(
    summary: dict[str, Any], *, blind: bool, revealed: bool
) -> tuple[dict[str, Any], list[str]]:
    """Redact identity-revealing fields when blind review is on and identity
    has not been revealed. Returns ``(summary, redacted_keys)``.

    The display name collapses to an opaque "Applicant ####" so reviewers score
    on substance. Prior-school names are masked too (the "optionally school
    name" clause). Returns the summary untouched when not in blind mode or after
    an audit-logged reveal.
    """
    if not blind or revealed:
        return summary, []

    redacted: list[str] = []
    out = dict(summary)
    short = str(out.get("student_id", "") or "")[:8]
    out["display_name"] = f"Applicant {short}" if short else "Applicant"
    for key in BLIND_REDACTED_KEYS:
        if out.get(key) not in (None, ""):
            redacted.append(key)
        out[key] = None
    # Mask prior-institution names in academics (keep degree/field/GPA — the
    # substance reviewers should weigh).
    masked_academics = []
    for rec in out.get("academics") or []:
        r = dict(rec)
        if r.get("institution"):
            r["institution"] = "[School hidden]"
        masked_academics.append(r)
    if masked_academics:
        out["academics"] = masked_academics
        redacted.append("academics.institution")
    return out, redacted


def aggregate_rubric_scores(
    criteria: list[dict[str, Any]],
    scores: list[dict[str, Any]],
    reviewer_names: dict[str, str],
) -> list[dict[str, Any]]:
    """Build the spec §8 ``rubric_scores`` shape: per criterion, each reviewer's
    score in a column, the variance, and a divergence flag (Δ ≥ 1.5, §4).

    ``criteria``: rubric criteria [{name, weight, max_score?}]. When empty,
    criteria are inferred from the union of ``criterion_scores`` keys.
    ``scores``: ApplicationScore dicts with ``reviewer_id``, ``criterion_scores``,
    ``reviewer_notes``. ``synthesized_recommendation`` is left ``None`` here and
    filled by the (Sonnet) synthesis endpoint on demand.
    """
    # Infer criteria if no rubric was supplied.
    if not criteria:
        names: list[str] = []
        for s in scores:
            for k in s.get("criterion_scores") or {}:
                if k not in names:
                    names.append(k)
        criteria = [{"name": n, "weight": None} for n in names]

    out: list[dict[str, Any]] = []
    for crit in criteria:
        name = crit.get("name")
        if not name:
            continue
        per_reviewer: list[dict[str, Any]] = []
        vals: list[float] = []
        for s in scores:
            cs = s.get("criterion_scores") or {}
            if name not in cs:
                continue
            try:
                val = float(cs[name])
            except (TypeError, ValueError):
                continue
            vals.append(val)
            rid = str(s.get("reviewer_id"))
            per_reviewer.append(
                {
                    "reviewer_id": rid,
                    "reviewer_name": reviewer_names.get(rid, "Reviewer"),
                    "score": val,
                    "note": s.get("reviewer_notes"),
                }
            )
        variance = round(max(vals) - min(vals), 2) if len(vals) >= 2 else 0.0
        out.append(
            {
                "criterion": name,
                "weight": crit.get("weight"),
                "max_score": crit.get("max_score", 5),
                "per_reviewer": per_reviewer,
                "variance": variance,
                "divergent": variance >= VARIANCE_THRESHOLD,
                "synthesized_recommendation": None,
            }
        )
    return out


def _age_from_dob(dob: date | None, today: date) -> int | None:
    if not dob:
        return None
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def holistic_context(
    *,
    nationality: str | None,
    country_of_residence: str | None,
    institution_country: str | None,
    language_count: int,
    prior_institutions: list[str],
) -> dict[str, Any]:
    """Spec 32 §7A.4 — equity-positive context that informs holistic review
    *without becoming a selection shortcut*.

    Returns ``{standard: [...], high_sensitivity: [...], note}``. We surface only
    honestly-derivable, equity-positive context (international status,
    multilingualism, prior-school context). High-sensitivity flags
    (legacy/development, athletic-recruit) are NOT collected by the platform, so
    that list is empty — but the gated structure is here so the UI can render the
    fairness rules and a future data source plugs in behind the same gate.
    """
    standard: list[dict[str, Any]] = []
    inst_c = (institution_country or "").strip().lower()
    applicant_c = (country_of_residence or nationality or "").strip()
    if applicant_c and inst_c and applicant_c.lower() != inst_c:
        standard.append(
            {
                "key": "international",
                "label": "International applicant",
                "value": applicant_c,
                "sensitivity": "standard",
                "source": "profile.nationality",
            }
        )
    if language_count >= 2:
        standard.append(
            {
                "key": "multilingual",
                "label": "Multilingual",
                "value": f"{language_count} languages",
                "sensitivity": "standard",
                "source": "profile.languages",
            }
        )
    if prior_institutions:
        standard.append(
            {
                "key": "school_context",
                "label": "Prior institution context",
                "value": ", ".join(prior_institutions[:3]),
                "sensitivity": "standard",
                "source": "academics.institution",
            }
        )
    return {
        "standard": standard,
        # legacy/development + athletic-recruit are high-sensitivity (§7A.4):
        # shown only to policy-permitted roles, every use audit-logged, never a
        # positive weight in matching/ranking. Not collected → empty for now.
        "high_sensitivity": [],
        "note": (
            "Context cards inform holistic review only — never a selection "
            "shortcut. Legacy/development and athletic-recruit status are never "
            "a positive weight in matching or ranking."
        ),
    }


def test_optional_analysis(*, has_test_scores: bool, program: dict[str, Any]) -> dict[str, Any]:
    """Spec 32 §7A.3 / spec 42 §4.6 — per-applicant test-policy context. NEVER a
    penalty: non-submission must not count against the applicant, and the UI
    says so.
    """
    reqs = program.get("requirements") if isinstance(program.get("requirements"), dict) else {}
    # Best-effort policy detection from the program requirements blob.
    raw = " ".join(str(v) for v in (reqs or {}).values()).lower() if reqs else ""
    policy_field = str((reqs or {}).get("test_policy", "")).lower()
    if "required" in policy_field or "test_required" in raw or "gre required" in raw:
        policy = "required"
    elif "blind" in policy_field or "test-blind" in raw or "test blind" in raw:
        policy = "test_blind"
    else:
        # Default posture for the MVP catalogue is test-optional.
        policy = "test_optional"

    if policy == "test_blind":
        compatibility = "not_considered"
        recommendation = "This program does not consider test scores. Scores on file are ignored."
    elif policy == "required":
        compatibility = "submitted" if has_test_scores else "missing_required"
        recommendation = (
            "Test scores are on file as required."
            if has_test_scores
            else (
                "Program requires test scores; none on file — treat as a "
                "completeness item, not a quality signal."
            )
        )
    else:  # test_optional
        compatibility = "submitted" if has_test_scores else "withheld_ok"
        recommendation = (
            "Applicant submitted optional test scores — weigh as supporting context."
            if has_test_scores
            else "Test-optional: applicant withheld scores. This is never a penalty."
        )

    return {
        "policy": policy,
        "submitted": has_test_scores,
        "compatibility": compatibility,
        "recommendation": recommendation,
        "guardrail": "Non-submission must never count against an applicant.",
    }


def round_label(
    *,
    program_name: str,
    degree_type: str | None,
    program_start_date: date | None,
    intake_term: str | None,
) -> str:
    """Build the spec §2 header label, e.g. "CS MS · Fall 2027". Round number is
    not linked per-application in the schema, so it is omitted rather than
    fabricated; the intake term is shown when known."""
    parts = [program_name]
    if degree_type:
        parts.append(degree_type.upper() if len(degree_type) <= 3 else degree_type.title())
    term = intake_term
    if not term and program_start_date:
        month = program_start_date.month
        season = "Fall" if month >= 8 else "Summer" if month >= 5 else "Spring"
        term = f"{season} {program_start_date.year}"
    label = " · ".join(parts)
    if term:
        label += f" · {term}"
    return label
