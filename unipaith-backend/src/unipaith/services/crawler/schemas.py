"""Spec 60 §13 — the per-domain extraction target schemas.

One schema per reference domain: the target table, the dedup key, the field set,
and (for free-text crawl pages) the labeled patterns the rule-based extractor
keys off. The extractor emits ONLY fields named here AND grounded in the source —
the schema is the allowlist of *what may be written*, never an instruction to
invent (§15: "never writes a field absent from source").
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DomainSchema:
    domain: str
    target_table: str
    key_field: str  # the dedup / canonical key (e.g. soc_code, cip_code, code)
    fields: tuple[str, ...]  # every writable field (key_field included)
    # Labeled regex patterns for the Tier-3/4 free-text path: field -> regex with
    # one capture group. Absent fields simply aren't extractable from text.
    text_patterns: dict[str, str] = field(default_factory=dict)
    numeric_fields: frozenset[str] = field(default_factory=frozenset)
    list_fields: frozenset[str] = frozenset()
    json_fields: frozenset[str] = frozenset()


DOMAIN_SCHEMAS: dict[str, DomainSchema] = {
    "occupations": DomainSchema(
        "occupations",
        "ref_occupations",
        "soc_code",
        (
            "soc_code",
            "title",
            "description",
            "median_salary",
            "employment",
            "projected_growth_pct",
            "outlook",
            "education_typical",
            "related_majors",
        ),
        text_patterns={
            "median_salary": r"[Mm]edian (?:annual )?(?:pay|salary)[:\s]+\$?([\d,]+)",
            "projected_growth_pct": r"(?:projected|job outlook)[^%\d]{0,40}([\-\d.]+)\s?%",
        },
        numeric_fields=frozenset({"median_salary", "employment", "projected_growth_pct"}),
        list_fields=frozenset({"related_majors"}),
    ),
    "tests": DomainSchema(
        "tests",
        "ref_tests",
        "code",
        (
            "code",
            "name",
            "category",
            "sections",
            "score_min",
            "score_max",
            "validity_years",
            "superscore_allowed",
        ),
        numeric_fields=frozenset({"score_min", "score_max", "validity_years"}),
        list_fields=frozenset({"sections"}),
    ),
    "visas": DomainSchema(
        "visas",
        "ref_visas",
        "code",
        (
            "country",
            "code",
            "name",
            "requirements",
            "work_rights",
            "duration",
            "financial_proof_required",
        ),
        json_fields=frozenset({"requirements", "work_rights"}),
    ),
    "cost": DomainSchema(
        "cost",
        "ref_geo_cost",
        "locale",
        ("locale", "country", "cost_of_living_index", "rent_index", "monthly_estimate", "currency"),
        numeric_fields=frozenset({"cost_of_living_index", "rent_index", "monthly_estimate"}),
    ),
    "majors": DomainSchema(
        "majors",
        "ref_majors",
        "cip_code",
        (
            "cip_code",
            "title",
            "description",
            "typical_curriculum",
            "prerequisites",
            "related_occupations",
        ),
        list_fields=frozenset({"typical_curriculum", "prerequisites", "related_occupations"}),
    ),
    "rankings": DomainSchema(
        "rankings",
        "ref_rankings",
        "entity_name",
        ("ranker", "entity_name", "entity_type", "scope", "rank", "year"),
        numeric_fields=frozenset({"rank", "year"}),
    ),
    "accreditation": DomainSchema(
        "accreditation",
        "ref_accreditation",
        "entity_name",
        ("body", "body_type", "entity_name", "accreditation_status", "scope", "valid_through"),
    ),
    "scholarships": DomainSchema(
        "scholarships",
        "scholarships",
        "slug",
        (
            "name",
            "slug",
            "scholarship_type",
            "sponsor",
            "amount_min",
            "amount_max",
            "currency",
            "eligibility",
            "deadline",
            "application_url",
        ),
        numeric_fields=frozenset({"amount_min", "amount_max"}),
        json_fields=frozenset({"eligibility"}),
    ),
}


def schema_for(domain: str) -> DomainSchema | None:
    return DOMAIN_SCHEMAS.get(domain)
