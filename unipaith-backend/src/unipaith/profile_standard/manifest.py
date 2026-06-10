"""The canonical profile standard — extracted ONLY from the MIT / Sloan / MBAn
reference instance.

Each level (institution / school / program) declares the ordered sections a
gold-standard profile must carry, each section's fields, where each field lives
in the profile snapshot (a dotted ``path`` into the JSONB blobs / columns), and
the sourcing rule the Phase-2 enrichment gate must satisfy.

``STANDARD_VERSION`` is the single knob: bumping it re-conforms the whole fleet
(every profile stamped with an older version becomes stale and is re-enriched).
The MIT trio is conformant *by definition* — if a certification test fails, the
manifest is wrong, not the MIT data.
"""

from __future__ import annotations

from dataclasses import dataclass

STANDARD_VERSION = 1

# Sourcing rules — resolved in detail by playbook.md and enforced by the
# Phase-2 verification gate.
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


@dataclass(frozen=True)
class Section:
    id: str
    title: str
    order: int
    fields: list[Field]
    required: bool = True
    widget: str = "stat-grid"


# --- Institution level (renders InstitutionDetail) ---
INSTITUTION: list[Section] = [
    Section(
        "identity",
        "Identity & description",
        1,
        widget="prose",
        fields=[
            Field(
                "description_text",
                "Description",
                "description_text",
                sourcing="official_or_curated",
            ),
            Field(
                "student_body_size",
                "Student body size",
                "student_body_size",
                sourcing="first_party",
            ),
            Field("campus_photo", "Campus photo", "media_gallery", sourcing="none"),
        ],
    ),
    Section(
        "rankings",
        "Rankings & classification",
        2,
        widget="chip-list",
        fields=[
            Field(
                "qs_world_university_rankings",
                "QS world rank",
                "ranking_data.qs_world_university_rankings",
                sourcing="first_party",
            ),
            Field(
                "times_higher_education",
                "THE rank",
                "ranking_data.times_higher_education",
                sourcing="first_party",
            ),
            Field(
                "us_news_national",
                "US News national",
                "ranking_data.us_news_national",
                sourcing="first_party",
            ),
            Field(
                "carnegie_classification",
                "Carnegie classification",
                "ranking_data.carnegie_classification",
                sourcing="first_party",
            ),
            Field("accreditor", "Accreditor", "ranking_data.accreditor", sourcing="first_party"),
        ],
    ),
    Section(
        "report_card",
        "Report-card key stats",
        3,
        fields=[
            Field("admit_rate", "Admit rate", "school_outcomes.admit_rate", sourcing="first_party"),
            Field(
                "avg_net_price",
                "Average net price",
                "school_outcomes.avg_net_price",
                sourcing="first_party",
            ),
            Field(
                "median_earnings_10yr",
                "Median earnings (10yr)",
                "school_outcomes.median_earnings_10yr",
                sourcing="authoritative_2x",
            ),
            Field(
                "graduation_rate_6yr",
                "6-yr graduation rate",
                "school_outcomes.graduation_rate_6yr",
                sourcing="first_party",
            ),
            Field(
                "retention_rate_first_year",
                "First-year retention",
                "school_outcomes.retention_rate_first_year",
                sourcing="first_party",
            ),
        ],
    ),
    Section(
        "admissions_funnel",
        "Admissions funnel",
        4,
        fields=[
            Field(
                "test_scores", "Test scores", "school_outcomes.test_scores", sourcing="first_party"
            ),
            Field(
                "demographics",
                "Demographics",
                "school_outcomes.demographics",
                required=False,
                sourcing="first_party",
            ),
        ],
    ),
    Section(
        "campus_resources",
        "Campus resources",
        5,
        widget="chip-list",
        fields=[
            Field(
                "research",
                "Research & labs",
                "school_outcomes.research",
                sourcing="official_or_curated",
            ),
            Field(
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
        6,
        widget="none",
        required=False,
        fields=[
            Field(
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
        7,
        widget="citation-block",
        fields=[
            Field("sources", "Source citations", "school_outcomes.sources", sourcing="none"),
        ],
    ),
]

# --- School level (renders SchoolSubunitPage) ---
SCHOOL: list[Section] = [
    Section(
        "identity",
        "Identity",
        1,
        widget="prose",
        fields=[
            Field("name", "Name", "name", sourcing="first_party"),
            Field("description", "Description", "description", sourcing="official_or_curated"),
            Field("website_url", "Website", "website_url", sourcing="first_party"),
        ],
    ),
    Section(
        "about_detail",
        "About — facts, leadership, faculty",
        2,
        fields=[
            Field("founded", "Founded", "about_detail.founded", sourcing="first_party"),
            Field("leadership", "Leadership", "about_detail.leadership", sourcing="first_party"),
            Field(
                "faculty", "Notable faculty", "about_detail.faculty", sourcing="official_or_curated"
            ),
            Field(
                "research_centers",
                "Research centers",
                "about_detail.research_centers",
                sourcing="official_or_curated",
            ),
            Field("source", "Source", "about_detail.source", required=False, sourcing="none"),
        ],
    ),
    Section(
        "feeds",
        "Events & updates feeds",
        3,
        widget="none",
        required=False,
        fields=[
            Field(
                "content_sources",
                "Channel feeds + socials",
                "content_sources",
                sourcing="first_party",
            ),
        ],
    ),
]

# --- Program level (renders ProgramDetailPage) ---
PROGRAM: list[Section] = [
    Section(
        "basics",
        "Basic info",
        1,
        fields=[
            Field("program_name", "Full program name", "program_name", sourcing="first_party"),
            Field("degree_type", "Degree", "degree_type", sourcing="first_party"),
            Field("duration_months", "Length", "duration_months", sourcing="first_party"),
            Field("delivery_format", "Format", "delivery_format", sourcing="first_party"),
            Field(
                "description_text",
                "Description",
                "description_text",
                sourcing="official_or_curated",
            ),
            Field("website_url", "Website", "website_url", sourcing="first_party"),
        ],
    ),
    Section(
        "admissions",
        "Admissions",
        2,
        fields=[
            Field(
                "materials",
                "Required materials",
                "application_requirements.materials",
                sourcing="first_party",
            ),
            Field(
                "deadlines",
                "Deadlines / timeline",
                "application_requirements.deadlines",
                sourcing="first_party",
            ),
            Field(
                "evaluation",
                "Evaluation criteria",
                "application_requirements.evaluation",
                required=False,
                sourcing="official_or_curated",
            ),
            Field(
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
        3,
        fields=[
            Field("tuition_usd", "Tuition", "cost_data.tuition_usd", sourcing="first_party"),
            Field(
                "total_cost_of_attendance",
                "Total cost of attendance",
                "cost_data.total_cost_of_attendance",
                required=False,
                sourcing="first_party",
            ),
            Field("cost_source", "Cost source", "cost_data.source", sourcing="none"),
        ],
    ),
    Section(
        "outcomes",
        "Outcomes",
        4,
        widget="distribution",
        fields=[
            Field(
                "employment_rate",
                "Employment rate",
                "outcomes_data.employment_rate",
                sourcing="first_party",
            ),
            Field(
                "median_salary",
                "Median base salary",
                "outcomes_data.median_salary",
                sourcing="first_party",
            ),
            Field(
                "salary_25th",
                "25th percentile",
                "outcomes_data.salary_25th",
                required=False,
                sourcing="first_party",
            ),
            Field(
                "salary_75th",
                "75th percentile",
                "outcomes_data.salary_75th",
                required=False,
                sourcing="first_party",
            ),
            Field(
                "top_industries",
                "Top industries",
                "outcomes_data.top_industries",
                sourcing="first_party",
            ),
            Field(
                "conditions",
                "Methodology / conditions",
                "outcomes_data.conditions",
                sourcing="first_party",
            ),
            Field("outcomes_source", "Outcomes source", "outcomes_data.source", sourcing="none"),
        ],
    ),
    Section(
        "insights",
        "Insights — class profile, faculty, reviews",
        5,
        required=False,
        fields=[
            Field(
                "class_profile",
                "Class profile",
                "class_profile.cohort_size",
                required=False,
                sourcing="first_party",
            ),
            Field(
                "faculty", "Faculty", "faculty.lead", required=False, sourcing="official_or_curated"
            ),
            Field(
                "reviews", "Reviews", "reviews.summary", required=False, sourcing="authoritative_2x"
            ),
        ],
    ),
]

MANIFEST: dict[str, list[Section]] = {
    "institution": INSTITUTION,
    "school": SCHOOL,
    "program": PROGRAM,
}
