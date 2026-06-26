"""Spec 65 §3 — deterministic program featurizer (fills the empty program side).

The matcher's `soft_align` / `needs_match` compare a student's soft features
against the PROGRAM's soft features in a shared controlled vocabulary
(`ai/tools/feature_schema`). Today the program side reads `feature_vector_sparse`
— a column that was never created (`program_features.py:176`) — so every program
scores `interest_themes=[]`, `career_arcs=[]`, `support_signals={}` and the two
structured terms are dead weight (the #2 prototype-smell, `64` §1.2).

This derives those tags **deterministically from a program's real attributes**
(CIP family + field/degree + description keywords) into the *same* vocabulary the
student features use, so the Jaccard overlap is meaningful. It invents nothing:
every tag traces to a real CIP family or an evidenced keyword; absent evidence →
absent tag (never a fabricated support signal). The LLM featurizer (`65` §3,
behind a flag) can later enrich the soft tags; this rule-based path is the floor.
"""

from __future__ import annotations

import re
from typing import Any

from unipaith.ai.tools.feature_schema import (
    CAREER_ARCS,
    INTEREST_THEMES,
    NEED_SIGNAL_TAGS,
    VALUE_TAGS,
)

# CIP 2-digit family → controlled INTEREST_THEMES / CAREER_ARCS / VALUE_TAGS.
# Families chosen to cover the catalog breadth; unknown families fall back to
# keyword extraction (below). Every tag is a member of the controlled vocab.
_CIP_THEMES: dict[str, list[str]] = {
    "11": ["machine_learning", "data_analysis", "engineering_systems"],  # computer/info sciences
    "14": ["engineering_systems", "robotics"],  # engineering
    "13": ["education_pedagogy"],  # education
    "26": ["biomedical_research", "computational_biology", "neuroscience"],  # biological sciences
    "42": ["psychology", "neuroscience"],  # psychology
    "45": ["economics", "sociology", "anthropology", "policy"],  # social sciences
    "51": ["public_health", "biomedical_research"],  # health professions
    "52": ["finance", "economics", "entrepreneurship"],  # business
    "50": ["design", "fine_art", "film_media"],  # visual & performing arts
    "03": ["sustainability"],  # natural resources & conservation
    "22": ["law_society", "policy"],  # legal professions
    "23": ["literature"],  # english language & literature
    "54": ["history"],  # history
    "38": ["philosophy"],  # philosophy & religious studies
    "44": ["policy", "urban_planning"],  # public administration
    "40": ["data_analysis", "sustainability"],  # physical sciences
}
_CIP_ARCS: dict[str, list[str]] = {
    "11": ["software_engineering", "data_science_industry", "ml_research"],
    "14": ["research_engineering", "civil_engineering", "software_engineering"],
    "13": ["education_practice"],
    "26": ["biomedical_research"],
    "42": ["social_work", "research_engineering"],
    "45": ["policy_analysis", "consulting_finance"],
    "51": ["clinical_medicine", "public_health_policy"],
    "52": ["consulting_finance", "founder_track"],
    "50": ["product_design", "creative_practice"],
    "22": ["public_interest_law", "corporate_law"],
    "44": ["policy_analysis", "nonprofit_leadership"],
}
_CIP_VALUES: dict[str, list[str]] = {
    "11": ["intellectual_rigor", "boundary_pushing"],
    "14": ["applied_impact", "intellectual_rigor"],
    "13": ["service_to_community", "mentorship_culture"],
    "26": ["intellectual_rigor", "applied_impact"],
    "45": ["intellectual_rigor", "social_mobility"],
    "51": ["service_to_community", "applied_impact"],
    "52": ["applied_impact", "challenging_peers"],
    "50": ["creative_autonomy", "boundary_pushing"],
    "03": ["environmental_responsibility", "service_to_community"],
    "44": ["service_to_community", "social_mobility"],
}

# Description keyword → INTEREST_THEMES (evidence-based enrichment).
_KEYWORD_THEMES: dict[str, str] = {
    "machine learning": "machine_learning",
    "artificial intelligence": "machine_learning",
    "data": "data_analysis",
    "robot": "robotics",
    "neuro": "neuroscience",
    "entrepreneur": "entrepreneurship",
    "startup": "entrepreneurship",
    "sustainab": "sustainability",
    "climate": "sustainability",
    "urban": "urban_planning",
    "policy": "policy",
    "finance": "finance",
    "design": "design",
}

# Description keyword → NEED_SIGNAL_TAGS support the program plausibly offers.
# Evidence-only: a tag is set ONLY when the keyword is present (never fabricated).
_KEYWORD_SUPPORTS: dict[str, tuple[str, float]] = {
    "research": ("research_opportunities", 0.7),
    "internship": ("career_services", 0.6),
    "co-op": ("career_services", 0.6),
    "career": ("career_services", 0.6),
    "placement": ("career_services", 0.7),
    "scholarship": ("recognition_scholarship", 0.6),
    "funding": ("low_income_aid", 0.5),
    "financial aid": ("low_income_aid", 0.6),
    "alumni": ("alumni_network", 0.6),
    "study abroad": ("study_abroad", 0.7),
    "mental health": ("mental_health_support", 0.6),
    "diversity": ("strong_diversity", 0.6),
}

# Description keyword → CAREER_ARCS / VALUE_TAGS — a fallback so programs with no
# (or an unmapped) CIP code still get career + value tags from their description,
# instead of the whole crawler slice being mutually indistinguishable. Anything
# not in the controlled vocab is dropped by _dedup_in_vocab.
_KEYWORD_ARCS: dict[str, str] = {
    "software": "software_engineering",
    "data science": "data_science_industry",
    "machine learning": "ml_research",
    "research": "research_engineering",
    "clinical": "clinical_medicine",
    "public health": "public_health_policy",
    "policy": "policy_analysis",
    "consulting": "consulting_finance",
    "finance": "consulting_finance",
    "entrepreneur": "founder_track",
    "startup": "founder_track",
    "design": "product_design",
    "nonprofit": "nonprofit_leadership",
}
_KEYWORD_VALUES: dict[str, str] = {
    "research": "intellectual_rigor",
    "rigorous": "intellectual_rigor",
    "impact": "applied_impact",
    "applied": "applied_impact",
    "community": "service_to_community",
    "service": "service_to_community",
    "mentorship": "mentorship_culture",
    "creativ": "creative_autonomy",
    "sustainab": "environmental_responsibility",
}

# campus_setting / description cue → the student social_prefs vocab (small_cohort,
# large_community, urban, suburban, rural, mentorship, peer_collab, independent).
# Program social_features were ALWAYS empty, so the 30% social term of soft_align
# was dead for every program; derive them from the program's real attributes.
_CAMPUS_SOCIAL: dict[str, str] = {
    "urban": "urban",
    "city": "urban",
    "metropolitan": "urban",
    "suburban": "suburban",
    "rural": "rural",
    "small town": "rural",
}
_KEYWORD_SOCIAL: dict[str, str] = {
    "small cohort": "small_cohort",
    "small program": "small_cohort",
    "intimate": "small_cohort",
    "close-knit": "small_cohort",
    "large community": "large_community",
    "mentorship": "mentorship",
    "mentor": "mentorship",
    "advising": "mentorship",
    "collaborat": "peer_collab",
    "cohort-based": "peer_collab",
    "team-based": "peer_collab",
    "independent": "independent",
    "self-directed": "independent",
}

_VOCAB = {
    "interest_themes": set(INTEREST_THEMES),
    "career_arcs": set(CAREER_ARCS),
    "values": set(VALUE_TAGS),
    "support_signals": set(NEED_SIGNAL_TAGS),
}


def _cip_family(cip_code: str | None) -> str | None:
    if not cip_code:
        return None
    m = re.match(r"(\d{2})", str(cip_code).strip())
    return m.group(1) if m else None


def _dedup_in_vocab(tags: list[str], vocab_key: str) -> list[str]:
    allowed = _VOCAB[vocab_key]
    seen: list[str] = []
    for t in tags:
        if t in allowed and t not in seen:
            seen.append(t)
    return seen


def featurize_program(
    *,
    cip_code: str | None = None,
    degree_type: str | None = None,
    name: str = "",
    description: str = "",
    campus_setting: str | None = None,
) -> dict[str, Any]:
    """Derive the program's soft features in the shared controlled vocabulary.

    Deterministic + grounded: CIP family drives the field tags; description
    keywords enrich them and evidence support signals; absent evidence → absent
    tag. Returns the sparse soft-feature dict the matcher reads (§3)."""
    fam = _cip_family(cip_code)
    text = f"{name} {description}".lower()

    themes = list(_CIP_THEMES.get(fam, [])) if fam else []
    arcs = list(_CIP_ARCS.get(fam, [])) if fam else []
    values = list(_CIP_VALUES.get(fam, [])) if fam else []

    for kw, theme in _KEYWORD_THEMES.items():
        if kw in text:
            themes.append(theme)
    # Description fallbacks so a program with no / an unmapped CIP still gets
    # career + value tags (otherwise the crawler slice is indistinguishable).
    for kw, arc in _KEYWORD_ARCS.items():
        if kw in text:
            arcs.append(arc)
    for kw, val in _KEYWORD_VALUES.items():
        if kw in text:
            values.append(val)

    supports: dict[str, float] = {}
    for kw, (tag, strength) in _KEYWORD_SUPPORTS.items():
        if kw in text and tag in _VOCAB["support_signals"]:
            supports[tag] = max(supports.get(tag, 0.0), strength)
    # A doctoral program is evidence of research opportunity even without the word.
    if (degree_type or "").lower() in ("doctoral", "phd"):
        supports["research_opportunities"] = max(supports.get("research_opportunities", 0.0), 0.8)

    # Social features in the student social_prefs vocab — campus setting +
    # description cues. Previously always empty (dead 30% of soft_align).
    social: dict[str, float] = {}
    cs = (campus_setting or "").strip().lower()
    for cue, key in _CAMPUS_SOCIAL.items():
        if cue in cs:
            social[key] = 1.0
    for kw, key in _KEYWORD_SOCIAL.items():
        if kw in text:
            social[key] = 1.0

    return {
        "interest_themes": _dedup_in_vocab(themes, "interest_themes"),
        "career_arcs": _dedup_in_vocab(arcs, "career_arcs"),
        "values": _dedup_in_vocab(values, "values"),
        "support_signals": supports,
        "social_features": social,
    }


def soft_feature_completeness(sparse: dict[str, Any]) -> float:
    """Fraction of the four soft-feature axes that are non-empty (feeds the
    matcher's program `data_completeness`, distinct from `68`'s outcomes one)."""
    axes = ("interest_themes", "career_arcs", "values", "support_signals")
    present = sum(1 for a in axes if sparse.get(a))
    return round(present / len(axes), 4)
