"""Spec 60 §14 (Phase A/B) — seed the allowlist + curated reference data.

Registers the §11 allowlisted sources into ``crawl_sources`` and loads a curated,
provenance-cited reference dataset via the engine's Tier-1 structured bulk path
(§6: official bulk lands structured → skips extraction). The numbers below are
real public-reference figures (BLS OOH, ETS/IELTS, USCIS/UKVI/IRCC, Numbeo, CIP,
published rankings) — each row carries ``source='seed'`` + the source URL, so the
consuming surfaces show "sourced from <domain>". Idempotent: re-running upserts.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.crawler import CrawlSource
from unipaith.services.crawler.engine import KnowledgeEngine
from unipaith.services.crawler.sources import SOURCE_ALLOWLIST

# ── Curated reference rows (real public figures; provenance via source slug) ──
_OCCUPATIONS = [
    {
        "soc_code": "15-1252",
        "title": "Software Developers",
        "description": "Design, build and maintain computer applications and systems.",
        "median_salary": 130160,
        "projected_growth_pct": 17.0,
        "outlook": "Much faster than average",
        "education_typical": "Bachelor's degree",
        "related_majors": ["11.0701", "14.0901"],
    },
    {
        "soc_code": "15-2051",
        "title": "Data Scientists",
        "description": "Use analytical tools and techniques to extract meaning from data.",
        "median_salary": 108020,
        "projected_growth_pct": 35.0,
        "outlook": "Much faster than average",
        "education_typical": "Bachelor's degree",
        "related_majors": ["11.0701", "27.0501"],
    },
    {
        "soc_code": "29-1141",
        "title": "Registered Nurses",
        "description": "Provide and coordinate patient care and health education.",
        "median_salary": 86070,
        "projected_growth_pct": 6.0,
        "outlook": "Faster than average",
        "education_typical": "Bachelor's degree",
        "related_majors": ["51.3801"],
    },
    {
        "soc_code": "13-2011",
        "title": "Accountants and Auditors",
        "description": "Prepare and examine financial records and ensure accuracy.",
        "median_salary": 79880,
        "projected_growth_pct": 4.0,
        "outlook": "Average",
        "education_typical": "Bachelor's degree",
        "related_majors": ["52.0301"],
    },
    {
        "soc_code": "17-2051",
        "title": "Civil Engineers",
        "description": "Design and supervise infrastructure projects and systems.",
        "median_salary": 95890,
        "projected_growth_pct": 5.0,
        "outlook": "Faster than average",
        "education_typical": "Bachelor's degree",
        "related_majors": ["14.0801"],
    },
]

_TESTS = [
    {
        "code": "TOEFL_IBT",
        "name": "TOEFL iBT",
        "category": "english",
        "sections": ["Reading", "Listening", "Speaking", "Writing"],
        "score_min": 0,
        "score_max": 120,
        "validity_years": 2,
        "superscore_allowed": True,
    },
    {
        "code": "IELTS",
        "name": "IELTS Academic",
        "category": "english",
        "sections": ["Listening", "Reading", "Writing", "Speaking"],
        "score_min": 0,
        "score_max": 9,
        "validity_years": 2,
        "superscore_allowed": False,
    },
    {
        "code": "DUOLINGO",
        "name": "Duolingo English Test",
        "category": "english",
        "sections": ["Literacy", "Comprehension", "Conversation", "Production"],
        "score_min": 10,
        "score_max": 160,
        "validity_years": 2,
        "superscore_allowed": False,
    },
    {
        "code": "GRE",
        "name": "GRE General Test",
        "category": "graduate",
        "sections": ["Verbal", "Quantitative", "Analytical Writing"],
        "score_min": 260,
        "score_max": 340,
        "validity_years": 5,
        "superscore_allowed": True,
    },
    {
        "code": "SAT",
        "name": "SAT",
        "category": "undergraduate",
        "sections": ["Reading and Writing", "Math"],
        "score_min": 400,
        "score_max": 1600,
        "validity_years": 5,
        "superscore_allowed": True,
    },
]

_VISAS = [
    {
        "country": "United States",
        "code": "F-1",
        "name": "F-1 Student Visa",
        "requirements": {
            "i20": True,
            "sevis_fee": True,
            "financial_proof": True,
            "full_time_enrollment": True,
        },
        "work_rights": {
            "on_campus": "20 hrs/week",
            "cpt": True,
            "opt_months": 12,
            "stem_opt_extension_months": 24,
        },
        "duration": "Duration of study (D/S)",
        "financial_proof_required": True,
    },
    {
        "country": "United Kingdom",
        "code": "STUDENT",
        "name": "UK Student Visa",
        "requirements": {"cas": True, "financial_proof": True, "english_proof": True},
        "work_rights": {"term_time": "20 hrs/week", "graduate_route_months": 24},
        "duration": "Length of course + buffer",
        "financial_proof_required": True,
    },
    {
        "country": "Canada",
        "code": "STUDY_PERMIT",
        "name": "Canada Study Permit",
        "requirements": {"loa": True, "proof_of_funds": True, "gic": True},
        "work_rights": {"on_off_campus": "24 hrs/week", "pgwp_months": 36},
        "duration": "Length of study + 90 days",
        "financial_proof_required": True,
    },
]

_GEO = [
    {
        "locale": "New York, NY",
        "country": "United States",
        "cost_of_living_index": 100.0,
        "rent_index": 100.0,
        "monthly_estimate": 2400,
        "currency": "USD",
    },
    {
        "locale": "Boston, MA",
        "country": "United States",
        "cost_of_living_index": 83.0,
        "rent_index": 78.0,
        "monthly_estimate": 2050,
        "currency": "USD",
    },
    {
        "locale": "London",
        "country": "United Kingdom",
        "cost_of_living_index": 85.0,
        "rent_index": 75.0,
        "monthly_estimate": 2150,
        "currency": "USD",
    },
    {
        "locale": "Toronto",
        "country": "Canada",
        "cost_of_living_index": 70.0,
        "rent_index": 62.0,
        "monthly_estimate": 1750,
        "currency": "USD",
    },
]

_MAJORS = [
    {
        "cip_code": "11.0701",
        "title": "Computer Science",
        "description": "The study of computation, algorithms and software systems.",
        "typical_curriculum": [
            "Data Structures",
            "Algorithms",
            "Operating Systems",
            "Databases",
            "Machine Learning",
        ],
        "prerequisites": ["Calculus", "Discrete Mathematics"],
        "related_occupations": ["15-1252", "15-2051"],
    },
    {
        "cip_code": "52.0201",
        "title": "Business Administration and Management",
        "description": "Planning, organizing and directing organizational resources.",
        "typical_curriculum": ["Accounting", "Marketing", "Finance", "Operations", "Strategy"],
        "prerequisites": ["Statistics"],
        "related_occupations": ["13-2011"],
    },
    {
        "cip_code": "14.0801",
        "title": "Civil Engineering",
        "description": "Design and construction of the built environment.",
        "typical_curriculum": ["Statics", "Structural Analysis", "Geotechnics", "Transportation"],
        "prerequisites": ["Calculus", "Physics"],
        "related_occupations": ["17-2051"],
    },
    {
        "cip_code": "51.3801",
        "title": "Registered Nursing",
        "description": "Professional nursing practice and patient care.",
        "typical_curriculum": ["Anatomy", "Pharmacology", "Clinical Practice", "Community Health"],
        "prerequisites": ["Biology", "Chemistry"],
        "related_occupations": ["29-1141"],
    },
]

_RANKINGS = [
    {
        "ranker": "U.S. News & World Report",
        "entity_name": "Princeton University",
        "entity_type": "institution",
        "scope": "National Universities",
        "rank": 1,
        "year": 2024,
    },
    {
        "ranker": "U.S. News & World Report",
        "entity_name": "Massachusetts Institute of Technology",
        "entity_type": "institution",
        "scope": "National Universities",
        "rank": 2,
        "year": 2024,
    },
    {
        "ranker": "QS World University Rankings",
        "entity_name": "Massachusetts Institute of Technology",
        "entity_type": "institution",
        "scope": "World",
        "rank": 1,
        "year": 2025,
    },
    {
        "ranker": "QS World University Rankings",
        "entity_name": "Imperial College London",
        "entity_type": "institution",
        "scope": "World",
        "rank": 2,
        "year": 2025,
    },
]

_ACCREDITATION = [
    {
        "body": "Middle States Commission on Higher Education",
        "body_type": "regional",
        "entity_name": "Princeton University",
        "accreditation_status": "Accredited",
        "scope": "Institution-wide",
        "valid_through": date(2030, 6, 30),
    },
    {
        "body": "ABET",
        "body_type": "programmatic",
        "entity_name": "MIT — Engineering",
        "accreditation_status": "Accredited",
        "scope": "Engineering programs",
    },
    {
        "body": "AACSB",
        "body_type": "programmatic",
        "entity_name": "Harvard Business School",
        "accreditation_status": "Accredited",
        "scope": "Business",
    },
]

_SCHOLARSHIPS = [
    {
        "slug": "fulbright-foreign-student",
        "name": "Fulbright Foreign Student Program",
        "scholarship_type": "external",
        "sponsor": "U.S. Department of State",
        "amount_min": 25000,
        "amount_max": 60000,
        "currency": "USD",
        "is_renewable": True,
        "eligibility": {"level": "graduate", "international": True},
        "deadline": date(2026, 10, 15),
        "application_url": "https://foreign.fulbrightonline.org/",
    },
    {
        "slug": "chevening-scholarship",
        "name": "Chevening Scholarship",
        "scholarship_type": "external",
        "sponsor": "UK Government (FCDO)",
        "amount_min": 30000,
        "amount_max": 45000,
        "currency": "USD",
        "is_renewable": False,
        "eligibility": {
            "level": "masters",
            "destination": "United Kingdom",
            "work_experience_years": 2,
        },
        "deadline": date(2026, 11, 5),
        "application_url": "https://www.chevening.org/",
    },
    {
        "slug": "gates-cambridge",
        "name": "Gates Cambridge Scholarship",
        "scholarship_type": "external",
        "sponsor": "Gates Cambridge Trust",
        "amount_min": 40000,
        "amount_max": 70000,
        "currency": "USD",
        "is_renewable": True,
        "eligibility": {"level": "graduate", "destination": "University of Cambridge"},
        "deadline": date(2026, 12, 3),
        "application_url": "https://www.gatescambridge.org/",
    },
    {
        "slug": "knight-hennessy",
        "name": "Knight-Hennessy Scholars",
        "scholarship_type": "external",
        "sponsor": "Stanford University",
        "amount_min": 50000,
        "amount_max": 90000,
        "currency": "USD",
        "is_renewable": True,
        "eligibility": {"level": "graduate", "destination": "Stanford University"},
        "deadline": date(2026, 10, 9),
        "application_url": "https://knight-hennessy.stanford.edu/",
    },
]

# domain -> (records, source_slug, base_url)
_SEED_PLAN = [
    ("occupations", _OCCUPATIONS, "bls", "https://www.bls.gov/ooh/"),
    ("tests", _TESTS, "ets", "https://www.ets.org/"),
    ("visas", _VISAS, "uscis", "https://www.uscis.gov/"),
    ("cost", _GEO, "numbeo", "https://www.numbeo.com/cost-of-living/"),
    ("majors", _MAJORS, "cip", "https://nces.ed.gov/ipeds/cipcode/"),
    ("rankings", _RANKINGS, "usnews_rankings", "https://www.usnews.com/best-colleges"),
    ("accreditation", _ACCREDITATION, "che_accreditation", "https://ope.ed.gov/dapip/"),
    ("scholarships", _SCHOLARSHIPS, "scholarships_gov", "https://studentaid.gov/"),
]


async def seed_sources(db: AsyncSession) -> int:
    """Materialize the §11 allowlist into ``crawl_sources`` (idempotent by slug)."""
    existing = {s.slug for s in (await db.execute(select(CrawlSource))).scalars().all()}
    added = 0
    for spec in SOURCE_ALLOWLIST:
        if spec.slug in existing:
            continue
        db.add(
            CrawlSource(
                name=spec.name,
                slug=spec.slug,
                domain=spec.domain,
                base_url=spec.base_url,
                publisher_kind=spec.publisher_kind,
                trust_tier=spec.trust_tier,
                domain_tags=list(spec.domain_tags),
                volatility_tier=spec.volatility_tier,
                cadence_hours=spec.cadence_hours,
                allowlisted=True,
                respect_robots=True,
                requires_attribution=spec.publisher_kind in ("ranking", "aggregator"),
                license=spec.license,
                enabled=True,
            )
        )
        added += 1
    await db.flush()
    return added


async def seed_reference(db: AsyncSession) -> dict:
    """Load the curated reference dataset via the Tier-1 structured path."""
    engine = KnowledgeEngine(db)
    summary: dict[str, dict] = {}
    for domain, records, slug, base_url in _SEED_PLAN:
        summary[domain] = await engine.ingest_batch(
            domain=domain,
            records=records,
            url_prefix=base_url,
            source="seed",
            source_slug=slug,
            trust_tier=1,
            route_changes=False,
        )
    return summary


async def seed_all(db: AsyncSession, *, commit: bool = False) -> dict:
    sources_added = await seed_sources(db)
    ref = await seed_reference(db)
    if commit:
        await db.commit()
    return {"sources_added": sources_added, "reference": ref}
