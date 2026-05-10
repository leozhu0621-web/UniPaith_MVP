"""JSON schema for the feature-emitter's `emit_features` tool call.

The A4 Feature Emitter is forced to call this single tool — see
`tool_choice` in the caller. The emitter reads a complete StudentSnapshot
(post-Discovery) plus the audit-trail signals and returns:

  - sparse_features: the typed feature dict the ML matcher consumes
  - applicant_summary: a 200-word narrative the A5 Rationale agent uses

The dense embedding (voyage-3-large, 1024-d) is computed separately by
the emitter — Voyage doesn't run through Anthropic tool-use.

Schema versioning
-----------------
Bumped on any field add/remove. Increment SCHEMA_VERSION when changing
shape; downstream consumers (ML matcher) check the version on read.
"""

from __future__ import annotations

SCHEMA_VERSION = 1


# ── Sparse-feature vocabulary ───────────────────────────────────────────────
# Curated lists keep the matcher's feature space stable. The emitter MAY
# emit values outside these lists (the schema doesn't enum them), but the
# matcher's program-side features only score against this vocabulary —
# anything extra is ignored. Keep the vocabulary in sync with the program
# emitter (`unipaith.services.program_features`).

INTEREST_THEMES = [
    "machine_learning",
    "data_analysis",
    "biomedical_research",
    "public_health",
    "policy",
    "economics",
    "finance",
    "design",
    "fine_art",
    "film_media",
    "literature",
    "history",
    "philosophy",
    "education_pedagogy",
    "engineering_systems",
    "robotics",
    "neuroscience",
    "psychology",
    "sociology",
    "anthropology",
    "law_society",
    "entrepreneurship",
    "sustainability",
    "urban_planning",
    "computational_biology",
]

CAREER_ARCS = [
    "ml_research",
    "data_science_industry",
    "biomedical_research",
    "clinical_medicine",
    "family_medicine",
    "public_health_policy",
    "public_interest_law",
    "corporate_law",
    "academic_humanities",
    "creative_practice",
    "product_design",
    "founder_track",
    "consulting_finance",
    "education_practice",
    "social_work",
    "nonprofit_leadership",
    "civil_engineering",
    "software_engineering",
    "research_engineering",
    "policy_analysis",
]

VALUE_TAGS = [
    "service_to_community",
    "intellectual_rigor",
    "applied_impact",
    "creative_autonomy",
    "mentorship_culture",
    "loyalty_to_people",
    "challenging_peers",
    "intrinsic_motivation",
    "social_mobility",
    "environmental_responsibility",
    "diversity_inclusion",
    "intellectual_diversity",
    "tradition_continuity",
    "boundary_pushing",
]

NEED_SIGNAL_TAGS = [
    # Physiological
    "needs_housing",
    "needs_food_security",
    "climate_warm",
    "climate_cold",
    # Safety
    "healthcare_access",
    "low_income_aid",
    "visa_support",
    "policy_safe_environment",
    "lgbtq_safety",
    "religious_safety",
    "mental_health_support",
    "near_family",
    # Social
    "small_cohort",
    "large_community",
    "strong_diversity",
    "identity_affinity_groups",
    # Self-esteem
    "recognition_scholarship",
    "brand_prestige",
    "peer_caliber",
    # Self-actualization
    "research_opportunities",
    "study_abroad",
    "alumni_network",
    "career_services",
    "specific_extracurriculars",
]


# ── Tool schema ─────────────────────────────────────────────────────────────


EMIT_FEATURES_TOOL = {
    "name": "emit_features",
    "description": (
        "Convert a complete StudentSnapshot (post-Discovery) into the typed "
        "sparse-feature dict the ML matcher consumes, plus a 200-word "
        "applicant summary for the rationale agent. Stay close to the "
        "controlled vocabulary; soft features should be in [0,1]."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "required": ["sparse_features", "applicant_summary"],
        "properties": {
            "sparse_features": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "education_level",
                    "intended_degrees",
                    "intended_majors",
                    "geo_must",
                    "geo_avoid",
                    "interest_themes",
                    "career_arcs",
                    "values",
                    "needs_signals",
                    "social_prefs",
                    "feature_completeness",
                ],
                "properties": {
                    # Hard filters (rule layer)
                    "education_level": {
                        "type": "string",
                        "enum": [
                            "high_school",
                            "bachelors",
                            "masters",
                            "gap_year",
                            "working",
                            "unknown",
                        ],
                    },
                    "intended_degrees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Target degrees (e.g. 'MD', 'MS-CS', 'MBA', 'PhD-CS', 'BFA')."
                        ),
                    },
                    "intended_majors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "CIP-codes preferred; free-text accepted.",
                    },
                    "geo_must": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "ISO-3166 country/region codes the student requires.",
                    },
                    "geo_avoid": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "budget_max_usd_per_year": {
                        "type": ["number", "null"],
                    },
                    "needs_aid": {"type": ["boolean", "null"]},
                    "first_gen": {"type": ["boolean", "null"]},
                    "gpa": {"type": ["number", "null"]},
                    "test_scores": {
                        "type": "object",
                        "description": "{type: score} dict; e.g. {'GRE': 332, 'TOEFL': 110}.",
                        "additionalProperties": {"type": "number"},
                    },
                    "deadline_horizon_months": {"type": ["integer", "null"]},
                    # Soft features (weighted into fitness)
                    "interest_themes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "3–7 normalized tags from INTEREST_THEMES vocab; "
                            "off-vocab tags accepted but ignored by matcher."
                        ),
                    },
                    "career_arcs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags from CAREER_ARCS vocab.",
                    },
                    "social_prefs": {
                        "type": "object",
                        "description": (
                            "Soft preferences in [0,1]. Recommended keys: small_cohort, "
                            "large_community, urban, suburban, rural, mentorship, peer_collab, "
                            "independent."
                        ),
                        "additionalProperties": {"type": "number"},
                    },
                    "values": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags from VALUE_TAGS vocab.",
                    },
                    "needs_signals": {
                        "type": "object",
                        "description": (
                            "Need tag → severity in [0,1]. Tags from NEED_SIGNAL_TAGS vocab; "
                            "the matcher uses these to compute the needs_match component."
                        ),
                        "additionalProperties": {"type": "number"},
                    },
                    # Derived
                    "applicant_archetype": {
                        "type": ["string", "null"],
                        "description": (
                            "One of ~15 hand-curated archetypes (e.g. "
                            "'first_gen_research_aspirant', "
                            "'creative_autonomy_seeker'); the matcher uses this for "
                            "explainability, not scoring."
                        ),
                    },
                    "feature_completeness": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "description": (
                            "How complete the student's source data was at emission "
                            "time. Drives the confidence score downstream."
                        ),
                    },
                },
            },
            "applicant_summary": {
                "type": "string",
                "minLength": 200,
                "maxLength": 1500,
                "description": (
                    "200-word free-text narrative of the applicant. Concrete, "
                    "specific, references actual claims from the snapshot. "
                    "The rationale agent embeds this back into program "
                    "recommendations."
                ),
            },
        },
    },
}


# ── Changelog ───────────────────────────────────────────────────────────────
# v1 (2026-05-10): initial schema for Phase B1.
