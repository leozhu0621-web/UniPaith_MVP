"""Enrichment planner (AI Structure, Spec 1) — picks the next Prompt-Library
signal(s) to enrich.

Pure and deterministic: it takes a *signal state* snapshot (field key → current
value + confidence) and returns the next signals to ask/confirm, ordered by
priority (essentials → high-value gaps → low-confidence re-asks). The DB → state
adapter is a thin service layer on top; this module has no I/O so it is trivially
testable.

Decision per field (Spec 1 §2.2):
    missing            → ASK
    inferred  (weak)   → ASK
    imported  (okay)   → CONFIRM (1-tap)
    confirmed (solid)  → SKIP
"""

from __future__ import annotations

from typing import Any

# Confidence tier thresholds (Spec 1 §3). `confidence` is 0..1.
CONFIRMED_MIN = 0.85  # solid → skip
IMPORTED_MIN = 0.50  # okay → confirm (1-tap); below this is inferred/weak → ask

# Field types (drive the quantify step) and the widget ask kind (drive the UI).
# tiers: "essential" (block matching — Spec 3 prerequisite) / "high_value" / "standard".
# NOTE: school "ranking" importance is intentionally absent — it is never a
# scored value (founder decision), so we never ask for it.
#
# This CATALOG is the single Prompt Library: every field carries its canonical
# "question" (the counselor-voiced prompt shown to the student — it REPLACES the
# old generic "{Field} · Add this to sharpen your matches" wording) and, for
# choice/multi fields with a fixed set of answers, an "options" list of human
# labels that double as the stored value. number/date/range/scale/text fields —
# and the open-ended categoricals nationality/country_of_residence (too many
# countries → free text) — carry no options (``options`` is None / absent).
CATALOG: list[dict[str, Any]] = [
    # ── essentials (common-sense basics + direction) ──
    {
        "key": "gender",
        "type": "categorical",
        "tier": "essential",
        "ask_kind": "choice",
        "question": "Which best describes you?",
        "options": ["Woman", "Man", "Non-binary", "Another identity", "Prefer not to say"],
    },
    {
        "key": "nationality",
        "type": "categorical",
        "tier": "essential",
        "ask_kind": "typeahead",
        "question": "Which country are you a citizen of?",
        "options": None,  # resolves against countries reference list
    },
    {
        "key": "date_of_birth",
        "type": "date",
        "tier": "essential",
        "ask_kind": "date",
        "question": "When were you born?",
    },
    {
        "key": "country_of_residence",
        "type": "categorical",
        "tier": "essential",
        "ask_kind": "typeahead",
        "question": "Which country do you live in now?",
        "options": None,  # resolves against countries reference list
    },
    {
        "key": "target_degree_level",
        "type": "categorical",
        "tier": "essential",
        "ask_kind": "choice",
        "question": "What degree are you aiming for?",
        "options": [
            "Associate",
            "Bachelor's",
            "Master's",
            "MBA",
            "Ph.D.",
            "Professional (JD / MD / etc.)",
            "Certificate",
            "Diploma",
            "Exchange / non-degree",
        ],
    },
    {
        "key": "field_of_interest",
        "type": "categorical",
        "tier": "essential",
        "ask_kind": "choice",
        "question": "What do you want to study?",
        "options": [
            "Computer science",
            "Data science & AI",
            "Software engineering",
            "Electrical engineering",
            "Mechanical engineering",
            "Civil engineering",
            "Biomedical engineering",
            "Business & management",
            "Finance",
            "Accounting",
            "Marketing",
            "Economics",
            "Biology & life sciences",
            "Chemistry",
            "Physics",
            "Mathematics & statistics",
            "Environmental science",
            "Medicine",
            "Nursing",
            "Public health",
            "Pharmacy",
            "Psychology",
            "Sociology",
            "Political science",
            "International relations",
            "Law",
            "Education",
            "Communications & media",
            "Journalism",
            "English & literature",
            "History",
            "Philosophy",
            "Linguistics & languages",
            "Architecture",
            "Art & design",
            "Music & performing arts",
            "Film & media",
            "Something else",
        ],
    },
    # ── high-value (sharpen the match most) ──
    {
        "key": "gpa",
        "type": "numeric",
        "tier": "high_value",
        "ask_kind": "number",
        "question": "What's your GPA (on a 4.0 scale)?",
    },
    {
        "key": "test_scores",
        "type": "numeric",
        "tier": "high_value",
        "ask_kind": "number",
        "question": "What's your strongest test score so far?",
    },
    {
        "key": "budget_band",
        "type": "range",
        "tier": "high_value",
        "ask_kind": "range",
        "question": "What's your yearly budget — tuition plus living?",
    },
    {
        "key": "preferred_countries",
        "type": "multi",
        "tier": "high_value",
        "ask_kind": "multi",
        "question": "Which countries are you considering?",
        "options": [
            "United States",
            "United Kingdom",
            "Canada",
            "Australia",
            "Germany",
            "Netherlands",
            "Singapore",
            "Hong Kong",
            "France",
            "Switzerland",
        ],
    },
    {
        "key": "weight_cost",
        "type": "weight",
        "tier": "high_value",
        "ask_kind": "scale",
        "question": "How much does affordability matter to you?",
    },
    {
        "key": "weight_location",
        "type": "weight",
        "tier": "high_value",
        "ask_kind": "scale",
        "question": "How much does location matter to you?",
    },
    {
        "key": "weight_outcomes",
        "type": "weight",
        "tier": "high_value",
        "ask_kind": "scale",
        "question": "How much do career outcomes matter to you?",
    },
    # ── standard (depth) ──
    {
        "key": "weight_flexibility",
        "type": "weight",
        "tier": "standard",
        "ask_kind": "scale",
        "question": "How much does program flexibility matter to you?",
    },
    {
        "key": "weight_support",
        "type": "weight",
        "tier": "standard",
        "ask_kind": "scale",
        "question": "How much does student support matter to you?",
    },
    {
        "key": "weight_time_to_degree",
        "type": "weight",
        "tier": "standard",
        "ask_kind": "scale",
        "question": "How much does finishing quickly matter to you?",
    },
    {
        "key": "funding_requirement",
        "type": "boolean",
        "tier": "standard",
        "ask_kind": "choice",
        "question": "What kind of funding do you need?",
        "options": [
            "Need a full scholarship",
            "Need significant aid",
            "Some aid would help",
            "I can mostly self-fund",
            "Loans are an option",
            "Not sure yet",
        ],
    },
    # ── standard (basics) ──
    {
        "key": "first_generation",
        "type": "categorical",
        "tier": "standard",
        "ask_kind": "choice",
        "question": "Would you be the first in your family to go to college?",
        "options": ["Yes", "No", "Not sure"],
    },
    {
        "key": "current_education_level",
        "type": "categorical",
        "tier": "standard",
        "ask_kind": "choice",
        "question": "Where are you in your education right now?",
        "options": [
            "In high school",
            "Finished high school",
            "In a bachelor's degree",
            "Finished a bachelor's",
            "In a graduate degree",
            "Working professional",
            "Taking a gap year",
        ],
    },
    # ── standard (academics) ──
    {
        "key": "gpa_scale",
        "type": "categorical",
        "tier": "high_value",
        "ask_kind": "choice",
        "question": "What scale is that GPA on?",
        "options": [
            "4.0",
            "4.3",
            "4.5",
            "5.0",
            "10.0",
            "Percentage (out of 100)",
            "UK honours",
            "Other",
        ],
    },
    {
        "key": "tests_taken",
        "type": "multi",
        "tier": "high_value",
        "ask_kind": "multi",
        "question": "Which tests have you taken, or plan to?",
        "options": [
            "SAT",
            "ACT",
            "PSAT",
            "AP exams",
            "IB",
            "A-Levels",
            "TOEFL",
            "IELTS",
            "Duolingo English",
            "GRE",
            "GMAT",
            "LSAT",
            "MCAT",
            "None yet",
        ],
    },
    {
        "key": "english_proficiency",
        "type": "categorical",
        "tier": "standard",
        "ask_kind": "choice",
        "question": "How comfortable are you with English?",
        "options": ["Native speaker", "Fluent", "Advanced", "Intermediate", "Beginner"],
    },
    {
        "key": "strongest_subjects",
        "type": "multi",
        "tier": "standard",
        "ask_kind": "keywords",
        "question": "Which subjects are you strongest in?",
        "options": [
            "Math",
            "Physics",
            "Chemistry",
            "Biology",
            "Computer science",
            "Economics",
            "History",
            "English / writing",
            "Foreign languages",
            "Art",
            "Music",
            "Business",
            "Psychology",
            "Political science",
        ],
    },
    # ── standard (direction) ──
    {
        "key": "specialization",
        "type": "multi",
        "tier": "standard",
        "ask_kind": "keywords",
        "question": "Any specific focus within that?",
        "options": [
            "Machine learning",
            "Artificial intelligence",
            "Cybersecurity",
            "Data analytics",
            "Robotics",
            "Human–computer interaction",
            "Renewable energy",
            "Quantitative finance",
            "Public policy",
            "Neuroscience",
            "Biotech",
            "UX design",
        ],
    },
    {
        "key": "intended_start",
        "type": "categorical",
        "tier": "standard",
        "ask_kind": "choice",
        "question": "When do you want to start?",
        "options": ["Fall 2026", "Spring 2027", "Fall 2027", "2028 or later", "Flexible"],
    },
    {
        "key": "study_mode",
        "type": "categorical",
        "tier": "standard",
        "ask_kind": "choice",
        "question": "How do you want to study?",
        "options": ["On campus", "Online", "Hybrid", "No preference"],
    },
    # ── standard (experience) ──
    {
        "key": "research_experience",
        "type": "categorical",
        "tier": "standard",
        "ask_kind": "choice",
        "question": "Have you done academic research?",
        "options": ["Yes — published", "Yes — assisted a project", "A little", "Not yet"],
    },
    {
        "key": "activities",
        "type": "multi",
        "tier": "standard",
        "ask_kind": "keywords",
        "question": "Which activities are you part of?",
        "options": [
            "Robotics",
            "Debate",
            "Student government",
            "Volunteering",
            "Sports team",
            "Music & arts",
            "Theater / drama",
            "Research",
            "Entrepreneurship",
            "Coding / hackathons",
            "Journalism / writing",
            "Model UN",
            "Tutoring / mentoring",
            "Sustainability",
            "Cultural / religious group",
        ],
    },
    {
        "key": "work_experience",
        "type": "text",
        "tier": "standard",
        "ask_kind": "text",
        "question": "Tell me about a job or internship you've had.",
    },
    {
        "key": "languages",
        "type": "multi",
        "tier": "standard",
        "ask_kind": "multi",
        "question": "Which languages do you speak?",
        "options": [
            "English",
            "Mandarin",
            "Spanish",
            "Hindi",
            "Arabic",
            "French",
            "Bengali",
            "Portuguese",
            "Russian",
            "Japanese",
            "German",
            "Korean",
        ],
    },
    # ── standard (goals) ──
    {
        "key": "career_goal",
        "type": "multi",
        "tier": "high_value",
        "ask_kind": "keywords",
        "question": "What kind of work do you see yourself in?",
        "options": [
            "Software / tech",
            "Finance",
            "Consulting",
            "Medicine / healthcare",
            "Research / academia",
            "Law",
            "Engineering",
            "Entrepreneurship",
            "Design / creative",
            "Public service / policy",
            "Education",
            "Marketing",
            "Data / AI",
            "Still exploring",
        ],
    },
    {
        "key": "goal_after_degree",
        "type": "categorical",
        "tier": "standard",
        "ask_kind": "choice",
        "question": "After this degree, what's the plan?",
        "options": [
            "Start my career",
            "Go further (PhD / more study)",
            "Start a business",
            "Return to my current job",
            "Still figuring it out",
        ],
    },
    {
        "key": "goals",
        "type": "text",
        "tier": "standard",
        "ask_kind": "text",
        "question": "What's a goal you're working toward?",
    },
    # ── standard (where & how) ──
    {
        "key": "preferred_setting",
        "type": "multi",
        "tier": "standard",
        "ask_kind": "multi",
        "question": "What kind of place feels right?",
        "options": [
            "Big city",
            "College town",
            "Suburban",
            "Rural",
            "By the coast",
            "No preference",
        ],
    },
    {
        "key": "school_size",
        "type": "categorical",
        "tier": "standard",
        "ask_kind": "choice",
        "question": "What size of school suits you?",
        "options": [
            "Small (under 5,000)",
            "Medium (5,000–15,000)",
            "Large (over 15,000)",
            "No preference",
        ],
    },
    {
        "key": "institution_type",
        "type": "multi",
        "tier": "standard",
        "ask_kind": "multi",
        "question": "What kinds of schools interest you?",
        "options": [
            "Public university",
            "Private university",
            "Liberal arts college",
            "Research university",
            "Ivy / highly selective",
            "Technical / specialized",
            "Community college",
            "Online-first",
            "Religiously affiliated",
        ],
    },
    {
        "key": "climate",
        "type": "categorical",
        "tier": "standard",
        "ask_kind": "choice",
        "question": "Any climate preference?",
        "options": [
            "Warm year-round",
            "Mild",
            "Four seasons",
            "Cold is fine",
            "No preference",
        ],
    },
    {
        "key": "distance_from_home",
        "type": "categorical",
        "tier": "standard",
        "ask_kind": "choice",
        "question": "How far from home are you open to going?",
        "options": [
            "Stay close to home",
            "Within my country",
            "Within my region",
            "Anywhere in the world",
        ],
    },
    # ── standard (what matters most) ──
    {
        "key": "needs",
        "type": "multi",
        "tier": "standard",
        "ask_kind": "multi",
        "question": "What matters most to you in a school?",
        "options": [
            "Affordability",
            "Safety & wellbeing",
            "Community & belonging",
            "Recognition & prestige",
            "Growth & opportunity",
        ],
    },
    {
        "key": "identity",
        "type": "multi",
        "tier": "standard",
        "ask_kind": "keywords",
        "question": "Which values matter most to you?",
        "options": [
            "Curiosity",
            "Integrity",
            "Community",
            "Ambition",
            "Creativity",
            "Resilience",
            "Independence",
            "Compassion",
            "Excellence",
            "Adventure",
            "Fairness",
            "Growth",
            "Faith",
            "Family",
            "Service",
        ],
    },
]

ESSENTIAL_KEYS = [f["key"] for f in CATALOG if f["tier"] == "essential"]
_TIER_RANK = {"essential": 0, "high_value": 1, "standard": 2}
_ACTION_RANK = {"ask": 0, "confirm": 1}
_CATALOG_ORDER = {f["key"]: i for i, f in enumerate(CATALOG)}

# Profile-tab → CATALOG keys (Spec "Profile refinement v2" Ship 2). When the
# enrich planner is scoped to a section, only the catalog entries whose key is
# in SECTION_FIELDS[section] are considered. An unknown/absent section means
# "all of CATALOG" (the global next). This is the shared contract both the
# backend planner and the per-tab EnrichPanel use.
SECTION_FIELDS: dict[str, list[str]] = {
    "identity": ["identity"],
    "academics": ["gpa", "test_scores", "activities", "work_experience", "languages"],
    "goals": ["goals"],
    "needs": ["needs"],
    "preferences": [
        "budget_band",
        "preferred_countries",
        "weight_cost",
        "weight_location",
        "weight_outcomes",
        "weight_flexibility",
        "weight_support",
        "weight_time_to_degree",
        "funding_requirement",
    ],
    "strategy": ["target_degree_level", "field_of_interest"],
}


def action_for(entry: dict[str, Any] | None) -> str:
    """Decide ask / confirm / skip for one field's stored state.

    `entry` is ``{"value": ..., "confidence": float | None, "source": str | None}``
    or ``None`` (missing). Missing or null value → ask.
    """
    if not entry or entry.get("value") in (None, "", []):
        return "ask"
    conf = entry.get("confidence")
    if conf is None:
        # Present but unattributed → treat as imported: confirm with one tap.
        return "confirm"
    if conf >= CONFIRMED_MIN:
        return "skip"
    if conf >= IMPORTED_MIN:
        return "confirm"
    return "ask"  # inferred / weak


def essentials_present(
    signal_state: dict[str, Any], *, catalog: list[dict[str, Any]] | None = None
) -> bool:
    """Spec 3 prerequisite: every essential field has a non-null value
    (any confidence). Direction + basic identity must exist before matching.

    `catalog` defaults to the in-code CATALOG; pass the DB-loaded catalog
    (CatalogService.load) to drive this from the data-driven Prompt Library."""
    keys = (
        ESSENTIAL_KEYS
        if catalog is None
        else [f["key"] for f in catalog if f["tier"] == "essential"]
    )
    for key in keys:
        entry = signal_state.get(key)
        if not entry or entry.get("value") in (None, "", []):
            return False
    return True


def plan_next(
    signal_state: dict[str, Any],
    *,
    limit: int = 3,
    section: str | None = None,
    catalog: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return up to `limit` next signals to enrich, highest priority first.

    Priority = (tier, action, catalog order): essentials before high-value
    before standard; within a tier, ASK (missing/weak) before CONFIRM (1-tap).
    SKIP fields are omitted.

    When `section` is a known key in ``SECTION_FIELDS`` the candidate set is
    restricted to that tab's fields (the same tier/action/catalog-order ranking
    is preserved among them). An unknown or ``None`` section is unscoped — the
    global next over all of ``CATALOG`` — so behavior is unchanged by default.
    """
    cat = CATALOG if catalog is None else catalog
    order = _CATALOG_ORDER if catalog is None else {f["key"]: i for i, f in enumerate(cat)}
    allowed = SECTION_FIELDS.get(section) if section is not None else None
    candidates: list[dict[str, Any]] = []
    for field in cat:
        key = field["key"]
        if allowed is not None and key not in allowed:
            continue
        entry = signal_state.get(key)
        action = action_for(entry)
        if action == "skip":
            continue
        candidates.append(
            {
                "field": key,
                "type": field["type"],
                "tier": field["tier"],
                "ask_kind": field["ask_kind"],
                "question": field["question"],
                "options": field.get("options"),
                "action": action,
                "current_value": (entry or {}).get("value"),
                "confidence": (entry or {}).get("confidence"),
            }
        )
    candidates.sort(
        key=lambda c: (
            _TIER_RANK[c["tier"]],
            _ACTION_RANK[c["action"]],
            order[c["field"]],
        )
    )
    return candidates[: max(0, limit)]
