"""The canonical profile standard — extracted ONLY from the MIT / Sloan / MBAn
reference instance, and audited (2026-06-10) to be the complete, correct
dotted-path mirror of what the gold detail pages actually render.

Each level (institution / school / program) declares the ordered sections a
gold-standard profile must carry, each section's fields, where each field lives
in the profile snapshot (a dotted ``path`` into the JSONB blobs / columns), and
the sourcing rule the enrichment gate must satisfy.

Field/Section flags:
- ``required``   — the gold pages render it as primary content; conformance fails without it.
- ``enrich``     — True if THIS profile owns the field. False marks fields that are
                   *inherited* from a parent (e.g. a school's quick-facts come from its
                   institution) or *render-only* (per-student, not a fact) — documented
                   in the manifest but excluded from this profile's conformance/enrichment.

``STANDARD_VERSION`` is the single knob: bumping it re-conforms the whole fleet.
The MIT trio is conformant *by definition* — if a certification test fails, the
manifest is wrong, not the MIT data.
"""

from __future__ import annotations

from dataclasses import dataclass

STANDARD_VERSION = 2

SOURCING = {
    "first_party": "A designated first-party / official source; citation required.",
    "authoritative_2x": "Two independent authoritative sources must agree; citation required.",
    "official_or_curated": "Official page or curated editorial; citation when it is a stat.",
    "none": "Structural / derived; no external citation required.",
}


@dataclass(frozen=True)
class Field:
    """One leaf of a section. ``path`` is dotted into the level snapshot."""

    key: str
    label: str
    path: str
    required: bool = True
    sourcing: str = "official_or_curated"
    cited: bool = False
    enrich: bool = True  # False = inherited from parent or render-only (not this profile's job)


@dataclass(frozen=True)
class Section:
    id: str
    title: str
    order: int
    fields: list[Field]
    required: bool = True
    widget: str = "stat-grid"


def _f(key, label, path, **kw):
    return Field(key, label, path, **kw)


# ── Institution level (renders InstitutionDetail) ──────────────────────────
INSTITUTION: list[Section] = [
    Section(
        "identity",
        "Identity & description",
        1,
        widget="prose",
        fields=[
            _f(
                "description_text",
                "Description",
                "description_text",
                sourcing="official_or_curated",
            ),
            _f(
                "student_body_size",
                "Student body size",
                "student_body_size",
                sourcing="first_party",
            ),
            _f("campus_photo", "Campus photo", "media_gallery", sourcing="none"),
            _f("website_url", "Website", "website_url", required=False, sourcing="first_party"),
            _f("type", "Type", "type", required=False, sourcing="first_party"),
            _f(
                "campus_setting",
                "Campus setting",
                "campus_setting",
                required=False,
                sourcing="first_party",
            ),
            _f("founded_year", "Founded", "founded_year", required=False, sourcing="first_party"),
            _f(
                "social_links",
                "Social links",
                "social_links",
                required=False,
                sourcing="first_party",
            ),
        ],
    ),
    Section(
        "rankings",
        "Rankings & classification",
        2,
        widget="chip-list",
        fields=[
            _f(
                "qs",
                "QS world rank",
                "ranking_data.qs_world_university_rankings",
                sourcing="first_party",
            ),
            _f("the", "THE rank", "ranking_data.times_higher_education", sourcing="first_party"),
            _f(
                "usnews",
                "US News national",
                "ranking_data.us_news_national",
                sourcing="first_party",
            ),
            _f(
                "carnegie",
                "Carnegie classification",
                "ranking_data.carnegie_classification",
                sourcing="first_party",
            ),
            _f("accreditor", "Accreditor", "ranking_data.accreditor", sourcing="first_party"),
        ],
    ),
    Section(
        "report_card",
        "Report-card key stats",
        3,
        fields=[
            _f("admit_rate", "Admit rate", "school_outcomes.admit_rate", sourcing="first_party"),
            _f(
                "avg_net_price",
                "Average net price",
                "school_outcomes.avg_net_price",
                sourcing="first_party",
            ),
            _f(
                "earnings_10yr",
                "Median earnings (10yr)",
                "school_outcomes.median_earnings_10yr",
                sourcing="authoritative_2x",
            ),
            _f(
                "grad_rate",
                "6-yr graduation rate",
                "school_outcomes.graduation_rate_6yr",
                sourcing="first_party",
            ),
            _f(
                "retention",
                "First-year retention",
                "school_outcomes.retention_rate_first_year",
                sourcing="first_party",
            ),
            _f(
                "completion_4yr",
                "4-yr completion",
                "school_outcomes.completion_rate_4yr_150pct",
                required=False,
                sourcing="first_party",
            ),
        ],
    ),
    Section(
        "admissions_funnel",
        "Admissions funnel",
        4,
        fields=[
            _f(
                "applicants",
                "Applicants",
                "school_outcomes.flagship.applicants",
                sourcing="first_party",
            ),
            _f("admits", "Admits", "school_outcomes.flagship.admits", sourcing="first_party"),
            _f(
                "cycle",
                "Admissions cycle",
                "school_outcomes.flagship.admissions_cycle",
                required=False,
                sourcing="first_party",
            ),
            _f("test_scores", "Test scores", "school_outcomes.test_scores", sourcing="first_party"),
        ],
    ),
    Section(
        "diversity",
        "Diversity",
        5,
        fields=[
            _f(
                "demographics",
                "Race & ethnicity",
                "school_outcomes.demographics",
                sourcing="first_party",
            ),
        ],
    ),
    Section(
        "recognition",
        "Recognition",
        6,
        widget="chip-list",
        required=False,
        fields=[
            _f(
                "nobel",
                "Nobel laureates",
                "school_outcomes.flagship.nobel_laureates",
                required=False,
                sourcing="first_party",
            ),
            _f(
                "macarthur",
                "MacArthur Fellows",
                "school_outcomes.flagship.macarthur_fellows",
                required=False,
                sourcing="first_party",
            ),
            _f(
                "medal_science",
                "National Medal of Science",
                "school_outcomes.flagship.national_medal_science",
                required=False,
                sourcing="first_party",
            ),
        ],
    ),
    Section(
        "scale",
        "By the numbers",
        7,
        fields=[
            _f(
                "faculty_count",
                "Faculty",
                "school_outcomes.scale.faculty_count",
                sourcing="first_party",
            ),
            _f(
                "sf_ratio",
                "Student-faculty ratio",
                "school_outcomes.scale.student_faculty_ratio",
                sourcing="first_party",
            ),
            _f(
                "research_centers",
                "Research centers",
                "school_outcomes.scale.research_centers",
                required=False,
                sourcing="first_party",
            ),
            _f(
                "endowment",
                "Endowment",
                "school_outcomes.scale.endowment_usd",
                required=False,
                sourcing="first_party",
            ),
        ],
    ),
    Section(
        "outcomes",
        "Outcomes",
        8,
        fields=[
            _f(
                "placement",
                "Employed or continuing ed",
                "school_outcomes.employed_or_continuing_ed",
                sourcing="first_party",
            ),
            _f(
                "industries",
                "Top industries",
                "school_outcomes.top_employer_industries",
                sourcing="first_party",
            ),
        ],
    ),
    Section(
        "cost_aid",
        "Cost & aid",
        9,
        fields=[
            _f(
                "coa",
                "Cost of attendance",
                "school_outcomes.financial_aid.cost_of_attendance",
                sourcing="first_party",
            ),
            _f(
                "pell",
                "Pell grant rate",
                "school_outcomes.financial_aid.pell_grant_rate",
                sourcing="first_party",
            ),
            _f(
                "loan",
                "Federal loan rate",
                "school_outcomes.financial_aid.federal_loan_rate",
                required=False,
                sourcing="first_party",
            ),
            _f(
                "median_debt",
                "Median debt",
                "school_outcomes.financial_aid.median_debt_completers",
                required=False,
                sourcing="first_party",
            ),
        ],
    ),
    Section(
        "location",
        "Location & campus basics",
        10,
        widget="none",
        fields=[
            _f("lat", "Latitude", "school_outcomes.location.lat", sourcing="first_party"),
            _f("lng", "Longitude", "school_outcomes.location.lng", sourcing="first_party"),
            _f(
                "campus_location",
                "Location",
                "school_outcomes.campus_basics.location",
                required=False,
                sourcing="first_party",
            ),
        ],
    ),
    Section(
        "campus_resources",
        "Campus resources",
        11,
        widget="chip-list",
        fields=[
            _f(
                "research",
                "Research & labs",
                "school_outcomes.research",
                sourcing="official_or_curated",
            ),
            _f(
                "campus_life",
                "Campus life",
                "school_outcomes.campus_life",
                sourcing="official_or_curated",
            ),
        ],
    ),
    Section(
        "feeds",
        "Events & updates feeds",
        12,
        widget="none",
        required=False,
        fields=[
            _f(
                "content_sources",
                "Channel feeds + socials",
                "content_sources",
                sourcing="first_party",
            ),
        ],
    ),
    Section(
        "citation",
        "Sources",
        13,
        widget="citation-block",
        fields=[
            _f("sources", "Source citations", "school_outcomes.sources", sourcing="none"),
        ],
    ),
]

# ── School level (renders SchoolSubunitPage) ───────────────────────────────
SCHOOL: list[Section] = [
    Section(
        "identity",
        "Identity",
        1,
        widget="prose",
        fields=[
            _f("name", "Name", "name", sourcing="first_party"),
            _f("description", "Description", "description_text", sourcing="official_or_curated"),
            _f("website_url", "Website", "website_url", sourcing="first_party"),
        ],
    ),
    Section(
        "about_detail",
        "About — facts, leadership, faculty",
        2,
        fields=[
            _f("founded", "Founded", "about_detail.founded", sourcing="first_party"),
            _f("leadership", "Leadership", "about_detail.leadership", sourcing="first_party"),
            _f(
                "faculty", "Notable faculty", "about_detail.faculty", sourcing="official_or_curated"
            ),
            _f(
                "research_centers",
                "Research centers",
                "about_detail.research_centers",
                sourcing="official_or_curated",
            ),
            _f(
                "named_for",
                "Named for",
                "about_detail.named_for",
                required=False,
                sourcing="first_party",
            ),
            _f("source", "Source", "about_detail.source", required=False, sourcing="none"),
        ],
    ),
    Section(
        "quick_facts",
        "Quick facts (inherited from institution)",
        3,
        widget="none",
        required=False,
        fields=[
            _f(
                "admit_rate",
                "Acceptance (parent)",
                "institution.school_outcomes.admit_rate",
                required=False,
                sourcing="first_party",
                enrich=False,
            ),
            _f(
                "grad_rate",
                "Grad rate (parent)",
                "institution.school_outcomes.graduation_rate_6yr",
                required=False,
                sourcing="first_party",
                enrich=False,
            ),
            _f(
                "students",
                "Students (parent)",
                "institution.student_body_size",
                required=False,
                sourcing="first_party",
                enrich=False,
            ),
        ],
    ),
    Section(
        "feeds",
        "Events & updates feeds",
        4,
        widget="none",
        required=False,
        fields=[
            _f(
                "content_sources",
                "Channel feeds + socials",
                "content_sources",
                sourcing="first_party",
            ),
        ],
    ),
]

# ── Program level (renders ProgramDetailPage) ──────────────────────────────
PROGRAM: list[Section] = [
    Section(
        "basics",
        "Basic info",
        1,
        fields=[
            _f("program_name", "Full program name", "program_name", sourcing="first_party"),
            _f("degree_type", "Degree", "degree_type", sourcing="first_party"),
            _f("duration_months", "Length", "duration_months", sourcing="first_party"),
            _f("delivery_format", "Format", "delivery_format", sourcing="first_party"),
            _f(
                "description_text",
                "Description",
                "description_text",
                sourcing="official_or_curated",
            ),
            _f("website_url", "Website", "website_url", sourcing="first_party"),
            _f("department", "Department", "department", required=False, sourcing="first_party"),
            _f(
                "highlights",
                "Highlights",
                "highlights",
                required=False,
                sourcing="official_or_curated",
            ),
            _f(
                "who_its_for",
                "Who it's for",
                "who_its_for",
                required=False,
                sourcing="official_or_curated",
            ),
        ],
    ),
    Section(
        "tracks",
        "Curriculum & structure",
        2,
        fields=[
            _f("tracks", "Tracks / curriculum", "tracks", sourcing="official_or_curated"),
        ],
    ),
    Section(
        "admissions",
        "Admissions",
        3,
        fields=[
            _f(
                "materials",
                "Required materials",
                "application_requirements.materials",
                sourcing="first_party",
            ),
            _f(
                "deadlines",
                "Deadlines / timeline",
                "application_requirements.deadlines",
                sourcing="first_party",
            ),
            _f(
                "recommendations",
                "Recommendations",
                "application_requirements.recommendations",
                required=False,
                sourcing="first_party",
            ),
            _f(
                "international",
                "International requirements",
                "application_requirements.international",
                required=False,
                sourcing="first_party",
            ),
            _f(
                "application_fee",
                "Application fee",
                "application_requirements.application_fee",
                required=False,
                sourcing="first_party",
            ),
            _f(
                "req_source",
                "Requirements source",
                "application_requirements.source",
                sourcing="none",
            ),
        ],
    ),
    Section(
        "costs",
        "Costs & aid",
        4,
        fields=[
            _f("tuition", "Tuition", "cost_data.tuition_usd", sourcing="first_party"),
            _f(
                "total_coa",
                "Total cost of attendance",
                "cost_data.total_cost_of_attendance",
                required=False,
                sourcing="first_party",
            ),
            _f(
                "breakdown",
                "Cost breakdown",
                "cost_data.breakdown",
                required=False,
                sourcing="first_party",
            ),
            _f("cost_source", "Cost source", "cost_data.source", sourcing="none"),
        ],
    ),
    Section(
        "outcomes",
        "Outcomes",
        5,
        widget="distribution",
        fields=[
            _f(
                "employment_rate",
                "Employment rate",
                "outcomes_data.employment_rate",
                sourcing="first_party",
            ),
            _f(
                "median_salary",
                "Median base salary",
                "outcomes_data.median_salary",
                sourcing="first_party",
            ),
            _f(
                "salary_25th",
                "25th percentile",
                "outcomes_data.salary_25th",
                required=False,
                sourcing="first_party",
            ),
            _f(
                "salary_75th",
                "75th percentile",
                "outcomes_data.salary_75th",
                required=False,
                sourcing="first_party",
            ),
            _f(
                "mean_salary",
                "Mean base salary",
                "outcomes_data.mean_salary",
                required=False,
                sourcing="first_party",
            ),
            _f(
                "signing_bonus",
                "Median signing bonus",
                "outcomes_data.median_signing_bonus",
                required=False,
                sourcing="first_party",
            ),
            _f(
                "top_industries",
                "Top industries",
                "outcomes_data.top_industries",
                sourcing="first_party",
            ),
            _f(
                "top_employers",
                "Top employers",
                "outcomes_data.top_employers",
                required=False,
                sourcing="first_party",
            ),
            _f(
                "class_size",
                "Class size",
                "outcomes_data.class_size",
                required=False,
                sourcing="first_party",
            ),
            _f(
                "conditions",
                "Methodology / conditions",
                "outcomes_data.conditions",
                sourcing="first_party",
            ),
            _f("outcomes_source", "Outcomes source", "outcomes_data.source", sourcing="none"),
            _f(
                "outcomes_source_url",
                "Outcomes source URL",
                "outcomes_data.source_url",
                required=False,
                sourcing="none",
            ),
        ],
    ),
    Section(
        "insights",
        "Insights — class profile, faculty, reviews",
        6,
        fields=[
            _f(
                "class_profile",
                "Class profile",
                "class_profile.cohort_size",
                sourcing="first_party",
            ),
            _f(
                "class_intl",
                "International %",
                "class_profile.international_pct",
                required=False,
                sourcing="first_party",
            ),
            _f(
                "class_source",
                "Class profile source",
                "class_profile.source",
                required=False,
                sourcing="none",
            ),
            _f("faculty", "Faculty", "faculty_contacts.lead", sourcing="official_or_curated"),
            _f(
                "faculty_dir",
                "Faculty directory",
                "faculty_contacts.directory_url",
                required=False,
                sourcing="official_or_curated",
            ),
            _f("reviews", "Reviews", "external_reviews.summary", sourcing="authoritative_2x"),
            _f(
                "reviews_themes",
                "Review themes",
                "external_reviews.themes",
                required=False,
                sourcing="authoritative_2x",
            ),
            _f(
                "reviews_sources",
                "Review sources",
                "external_reviews.sources",
                required=False,
                sourcing="authoritative_2x",
            ),
        ],
    ),
    Section(
        "feeds",
        "Events & updates feeds",
        7,
        widget="none",
        fields=[
            _f(
                "content_sources",
                "Channel feeds + socials",
                "content_sources",
                sourcing="first_party",
            ),
        ],
    ),
]

MANIFEST: dict[str, list[Section]] = {
    "institution": INSTITUTION,
    "school": SCHOOL,
    "program": PROGRAM,
}
