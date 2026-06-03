"""Spec 66 §6 — institution-side prospect segmentation (deterministic).

The segmentation bands an institution dashboard reads (`Business Methodology`:577-580):
**fit-to-program-family**, **likelihood-to-apply**, **nurture-needed**. This is the
cold-start / deterministic floor — fit is computed against the program's *stated
requirements* (no admit history needed). The learned "taste" vector (`66` §3,
reverse-projected from admit history) is the flagged enrichment that needs real
partner data + a fairness pass to activate; this rule-based path always runs and
never encodes a protected attribute (`46` §6).
"""

from __future__ import annotations


def fit_to_program_band(prospect: dict, requirements: dict) -> str:
    """How well a prospect fits the program's stated requirements (high/med/low).
    Deterministic over GPA-vs-min, test-vs-min, and field match — ACADEMIC signals
    only (no protected/proxy attribute, `46` §6)."""
    score = 0.0
    checks = 0

    min_gpa = requirements.get("min_gpa")
    gpa = prospect.get("gpa")
    if min_gpa is not None and gpa is not None:
        checks += 1
        if gpa >= min_gpa:
            score += 1
        elif gpa >= min_gpa - 0.3:
            score += 0.5

    min_test = requirements.get("min_test")
    test = prospect.get("test_score")
    if min_test is not None and test is not None:
        checks += 1
        if test >= min_test:
            score += 1
        elif test >= min_test * 0.95:
            score += 0.5

    fields = requirements.get("fields_cip")
    cip = prospect.get("cip_family")
    if fields and cip:
        checks += 1
        if cip in fields:
            score += 1

    ratio = (score / checks) if checks else 0.5
    return "high" if ratio >= 0.75 else "medium" if ratio >= 0.4 else "low"


def likelihood_to_apply_band(engagement: dict) -> str:
    """From engagement signals (saved / viewed / events / messages) — deterministic
    point-weighted bands (the funnel-readiness proxy, §6)."""
    points = (
        2 * engagement.get("saved", 0)
        + engagement.get("page_views", 0)
        + 3 * engagement.get("events_attended", 0)
        + 2 * engagement.get("messages_sent", 0)
    )
    return "high" if points >= 6 else "medium" if points >= 2 else "low"


def nurture_band(fit_band: str, likelihood_band: str, *, following: bool = False) -> str:
    """High interest + low readiness → ``nurture_needed`` (`Business Methodology`:580);
    strong fit → ``ready``; otherwise ``monitor``."""
    high_interest = likelihood_band in ("high", "medium") or following
    low_readiness = fit_band in ("low", "medium")
    if high_interest and low_readiness:
        return "nurture_needed"
    if fit_band == "high":
        return "ready"
    return "monitor"


def segment_prospect(prospect: dict, requirements: dict, engagement: dict) -> dict:
    """Compute the three §6 bands for one prospect against one program."""
    fit = fit_to_program_band(prospect, requirements)
    likelihood = likelihood_to_apply_band(engagement)
    nurture = nurture_band(fit, likelihood, following=bool(prospect.get("following")))
    return {"fit_band": fit, "likelihood_band": likelihood, "nurture_band": nurture}
