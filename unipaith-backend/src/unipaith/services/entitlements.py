"""Feature entitlements — the free-vs-paid gate map (Spec 06 §4.1).

The Master Paper's monetization model is a 7-day full-access trial → ``$15/mo``
"Plus". The Business Plan's freemium ladder informs *what* is free vs paid
*within* that model:

- **Free** (trial lapsed, no card): the portable Universal Profile, baseline
  readiness, and *limited* matching (a capped shortlist). This is the
  "make great advising accessible" floor (Spec 06 §5 equal-access).
- **Paid** (Plus, or anyone inside the trial window): expanded matching,
  real-time deadline alerts, scholarship/affordability tools, and the
  structured writing workflows (Workshops).

``ad_free`` is orthogonal — a ``$5/mo`` add-on, not a plan tier — so it is not
modeled here; the subscription's ``ad_free`` flag governs it directly.

This module is pure logic (no DB, no I/O) so it is trivially testable and can be
imported anywhere (API guard, service, tests).
"""

from __future__ import annotations

import enum

from unipaith.models.billing import PLAN_FREE, PLAN_PLUS, PLAN_TRIAL

# Free users can see this many match results before the upgrade nudge; paid get
# the full ranked set. "Limited matching" from Spec 06 §4.1.
FREE_MATCH_LIMIT = 5


class Feature(enum.StrEnum):
    """Gateable product capabilities. Add new paid surfaces here."""

    # Always-on (free): the durable profile is portable for everyone — it is the
    # defensible core that survives even the verification-first pivot (06 §9).
    PROFILE = "profile"
    BASELINE_READINESS = "baseline_readiness"
    LIMITED_MATCH = "limited_match"

    # Paid (Plus / trial):
    EXPANDED_MATCH = "expanded_match"  # full ranked list + match rationale/explain
    DEADLINE_ALERTS = "deadline_alerts"  # real-time deadline alerts
    SCHOLARSHIP_TOOLS = "scholarship_tools"  # affordability / net-price tools
    WORKSHOPS = "workshops"  # structured writing workflows (essay/resume/test)


# Features available on the free tier. Everything else requires an entitled plan.
_FREE_FEATURES: frozenset[Feature] = frozenset(
    {Feature.PROFILE, Feature.BASELINE_READINESS, Feature.LIMITED_MATCH}
)

# The full paid set (Plus / trial get all of it).
_PAID_FEATURES: frozenset[Feature] = frozenset(
    {
        Feature.EXPANDED_MATCH,
        Feature.DEADLINE_ALERTS,
        Feature.SCHOLARSHIP_TOOLS,
        Feature.WORKSHOPS,
    }
)

_ALL_FEATURES: frozenset[Feature] = _FREE_FEATURES | _PAID_FEATURES

# plan → entitled feature set.
PLAN_ENTITLEMENTS: dict[str, frozenset[Feature]] = {
    PLAN_TRIAL: _ALL_FEATURES,  # full access during the 7-day trial
    PLAN_PLUS: _ALL_FEATURES,  # paying subscriber
    PLAN_FREE: _FREE_FEATURES,  # trial lapsed without a card
}


def entitlements_for(plan: str) -> frozenset[Feature]:
    """Return the feature set a plan is entitled to. Unknown plans → free set
    (fail-closed to the floor, never to full access)."""
    return PLAN_ENTITLEMENTS.get(plan, _FREE_FEATURES)


def is_entitled(plan: str, feature: Feature | str) -> bool:
    """Whether ``plan`` may use ``feature``."""
    try:
        feat = Feature(feature)
    except ValueError:
        return False
    return feat in entitlements_for(plan)


def feature_matrix() -> dict[str, dict[str, bool]]:
    """plan → {feature: bool} — the full grid, for the API/UI to render the
    'what's included' comparison (the 'explain everything' brand value)."""
    return {
        plan: {feat.value: (feat in feats) for feat in _ALL_FEATURES}
        for plan, feats in PLAN_ENTITLEMENTS.items()
    }
