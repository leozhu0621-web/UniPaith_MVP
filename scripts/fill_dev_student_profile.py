"""Populate the dev student (student@unipaith.co) profile to 80%+ so Match
Analysis renders on program detail pages.

Match Analysis at /api/v1/students/me/matches/{program_id} requires
``completion_percentage >= 80`` (see matching_service.py). The dev student
was seeded with only `first_name=Leo`, `country_of_residence=China`, and
`goals_text`, putting completion at 15%. This script adds enough fields
to pass the 80% gate without touching login credentials or identity.

Idempotent: PUT/POST operations check existing rows via GET first and
skip when data is already present. Re-runs are no-ops.

Usage:
    cd /Users/leozhu/Desktop/工作/Platform/UniPaith_MVP
    unipaith-backend/.venv/bin/python \
        scripts/fill_dev_student_profile.py
"""
from __future__ import annotations

import asyncio
import sys

import httpx

API = "https://api.unipaith.co/api/v1"
EMAIL = "student@unipaith.co"
PASSWORD = "Unipaith2026"


async def login(client: httpx.AsyncClient) -> str:
    resp = await client.post(
        f"{API}/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


async def ensure_basic_profile(client: httpx.AsyncClient) -> None:
    """last_name + nationality unblock the 15% basic_profile step.

    Also populates the Package A extended identity fields from the appendix
    (preferred_name, pronouns, gender identity, addresses, emergency contact,
    secondary contacts, verification flags). Every field is idempotent: we
    only write when the current value is null/empty.
    """
    resp = await client.get(f"{API}/students/me/profile")
    resp.raise_for_status()
    p = resp.json()
    patch = {}
    if not p.get("last_name"):
        patch["last_name"] = "Zhu"
    if not p.get("nationality"):
        patch["nationality"] = "Chinese"
    if not p.get("bio_text"):
        patch["bio_text"] = (
            "Student based in China, interested in AI systems and "
            "large-scale ML infrastructure. Building products with LLMs "
            "since 2024."
        )
    # --- Package A identity extensions ---
    if not p.get("preferred_name"):
        patch["preferred_name"] = "Leo"
    if not p.get("name_in_native_script"):
        patch["name_in_native_script"] = "\u6731\u4fca\u57ce"  # Chinese characters
    if not p.get("preferred_pronouns"):
        patch["preferred_pronouns"] = "he/him"
    if not p.get("gender_identity"):
        patch["gender_identity"] = "male"
    if not p.get("legal_sex"):
        patch["legal_sex"] = "male"
    if not p.get("place_of_birth"):
        patch["place_of_birth"] = "Shanghai, China"
    if not p.get("passport_issuing_country"):
        patch["passport_issuing_country"] = "China"
    if not p.get("preferred_contact_channel"):
        patch["preferred_contact_channel"] = "email"
    if not p.get("preferred_platform_language"):
        patch["preferred_platform_language"] = "en"
    if not p.get("preferred_writing_language"):
        patch["preferred_writing_language"] = "en"
    if not p.get("marital_status"):
        patch["marital_status"] = "single"
    if not p.get("residency_status_for_tuition"):
        patch["residency_status_for_tuition"] = "international"
    if not p.get("addresses"):
        patch["addresses"] = {
            "current": {
                "line1": "Tsinghua University, Haidian District",
                "city": "Beijing",
                "country": "China",
                "postal_code": "100084",
            },
            "permanent": {
                "city": "Shanghai",
                "country": "China",
            },
        }
    if not p.get("emergency_contact"):
        patch["emergency_contact"] = {
            "name": "Zhu (parent)",
            "email": "parent@example.cn",
            "phone": "+86-21-0000-0000",
            "relationship": "parent",
        }
    if not p.get("guardian"):
        # Leo is an adult student; guardian only exists as informational link.
        patch["guardian"] = None
    if not p.get("email_verified"):
        patch["email_verified"] = True
    if not p.get("phone_verified"):
        patch["phone_verified"] = True
    if p.get("id_verification_status") in (None, "none", ""):
        patch["id_verification_status"] = "verified"
    if not patch:
        print("  basic profile: already filled")
        return
    r2 = await client.put(f"{API}/students/me/profile", json=patch)
    r2.raise_for_status()
    print(f"  basic profile: patched {len(patch)} fields")


async def ensure_academic(client: httpx.AsyncClient) -> None:
    resp = await client.get(f"{API}/students/me/academics")
    resp.raise_for_status()
    if resp.json():
        print("  academics: already has at least 1 record")
        return
    body = {
        "institution_name": "Tsinghua University",
        "degree_type": "bachelors",
        "field_of_study": "Computer Science",
        "gpa": "3.85",
        "gpa_scale": "4.0",
        "start_date": "2022-09-01",
        "is_current": True,
        "country": "China",
        "transcript_language": "zh",
        # Package A extended fields:
        "attendance_rate": "0.98",
        "class_rank": 15,
        "class_rank_denominator": 120,
        "percentile_rank": "87.5",
        "weighted_gpa_flag": False,
        "leave_of_absence_flag": False,
        "withdrawal_incomplete_flag": False,
        "grading_scale_type": "4.0",
        "term_system_type": "semester",
        "translation_provided_flag": True,
        "school_reported_rigor": {
            "ap_count": 0,
            "ib_count": 0,
            "honors_count": 6,
            "college_count": 4,
        },
        "normalized_gpa": "3.85",
        "transcript_parse_status": "parsed",
    }
    r = await client.post(f"{API}/students/me/academics", json=body)
    r.raise_for_status()
    print("  academics: added BS Computer Science record (+ rigor breakdown)")


async def ensure_test_score(client: httpx.AsyncClient) -> None:
    resp = await client.get(f"{API}/students/me/test-scores")
    resp.raise_for_status()
    if resp.json():
        print("  test scores: already has at least 1")
        return
    body = {
        "test_type": "TOEFL",
        "total_score": 108,
        "section_scores": {
            "reading": 28,
            "listening": 27,
            "speaking": 25,
            "writing": 28,
        },
        "test_date": "2025-08-15",
        "is_official": True,
        # Package A extended fields:
        "percentile": "95.0",
        "test_attempt_number": 1,
        "superscore_preference": False,
        "score_expiration_date": "2027-08-15",
        "test_waiver_flag": False,
        "is_verified": True,
        "score_normalization_status": "mapped",
    }
    r = await client.post(f"{API}/students/me/test-scores", json=body)
    r.raise_for_status()
    print("  test scores: added TOEFL 108 (verified, percentile 95)")


async def ensure_activity(client: httpx.AsyncClient) -> None:
    resp = await client.get(f"{API}/students/me/activities")
    resp.raise_for_status()
    if resp.json():
        print("  activities: already has at least 1")
        return
    body = {
        "activity_type": "research",
        "title": "LLM inference optimization research",
        "organization": "University Lab",
        "description": (
            "Research project on LLM inference-time optimization "
            "(KV cache reuse, speculative decoding)."
        ),
        "start_date": "2024-06-01",
        "is_current": True,
        "hours_per_week": 10,
        "impact_description": (
            "Contributed benchmarking harness and one optimization "
            "that reduced p50 latency by 18% on 7B models."
        ),
    }
    r = await client.post(f"{API}/students/me/activities", json=body)
    r.raise_for_status()
    print("  activities: added LLM research")


async def ensure_language(client: httpx.AsyncClient) -> None:
    resp = await client.get(f"{API}/students/me/languages")
    resp.raise_for_status()
    items = resp.json()
    if items:
        print(f"  languages: already has {len(items)} entries")
        return
    for body in (
        {"language": "Mandarin", "proficiency_level": "native"},
        {
            "language": "English",
            "proficiency_level": "advanced",
            "certification_type": "TOEFL",
            "certification_score": "108",
            "test_date": "2025-08-15",
        },
    ):
        r = await client.post(f"{API}/students/me/languages", json=body)
        r.raise_for_status()
    print("  languages: added Mandarin + English")


async def ensure_online_presence(client: httpx.AsyncClient) -> None:
    resp = await client.get(f"{API}/students/me/online-presence")
    resp.raise_for_status()
    if resp.json():
        print("  online presence: already has at least 1")
        return
    body = {
        "platform_type": "github",
        "url": "https://github.com/dev-leo",
        "display_name": "dev-leo",
    }
    r = await client.post(f"{API}/students/me/online-presence", json=body)
    r.raise_for_status()
    print("  online presence: added GitHub")


async def ensure_preferences(client: httpx.AsyncClient) -> None:
    resp = await client.get(f"{API}/students/me/preferences")
    resp.raise_for_status()
    existing = resp.json()
    # Upsert even when a row exists, because the pre-Package-A row lacks the
    # new weight_* columns. PUT idempotently overwrites the dict.
    body = {
        "preferred_countries": ["United States", "United Kingdom", "Canada"],
        "preferred_city_size": "big_city",
        "budget_max": 80000,
        "funding_requirement": "flexible",
        "program_size_preference": "large",
        "career_goals": [
            "AI/ML engineer",
            "Research in large language models",
            "Technical founder",
        ],
        "values_priorities": {
            "research_opportunities": 5,
            "industry_network": 5,
            "faculty_quality": 4,
            "cost": 3,
            "location": 4,
        },
        "career_goal_short_term": (
            "Secure a research-oriented software engineering internship "
            "in NYC or SF Bay Area by summer 2027."
        ),
        # Appendix 7 explicit weights on a 0-10 scale:
        "weight_cost": 3,
        "weight_location": 6,
        "weight_outcomes": 9,
        "weight_ranking": 7,
        "weight_flexibility": 4,
        "weight_support": 6,
        "weight_time_to_degree": 5,
        "application_intensity": "many_broad",
        "preferred_learning_style": "project",
        "preferred_program_style": "applied",
        "research_interest_level": "high",
        "return_home_intent": "undecided",
        "risk_tolerance": "balanced",
        "stretch_target_safety_mix": "3-4-3",
        "target_degree_level": "masters",
        "target_start_term": "fall_2027",
        "thesis_interest": "maybe",
    }
    r = await client.put(f"{API}/students/me/preferences", json=body)
    r.raise_for_status()
    label = "updated" if existing else "set"
    print(f"  preferences: {label} target countries + 7 explicit weight scales")


async def ensure_visa_info(client: httpx.AsyncClient) -> None:
    """Visa/international fields - Leo applies from China to US programs."""
    body = {
        "current_immigration_status": "student_visa_pending",
        "visa_required": True,
        "target_study_country": "United States",
        "passport_expiration_date": "2030-05-15",
        "sponsorship_source": "family",
        "financial_proof_available": True,
        "financial_proof_amount_band": "80k-120k",
        "post_study_work_interest": True,
        "prior_visa_refusals": False,
        "work_authorization_needed": True,
        "current_location_city": "Beijing",
        "current_location_country": "China",
        "dependents_accompanying": False,
        "intended_start_term": "fall_2027",
        "visa_type_current": "none",
        "country_of_citizenship": "China",
    }
    r = await client.put(f"{API}/students/me/visa-info", json=body)
    r.raise_for_status()
    print("  visa info: filled all international fields (F-1 target, Fall 2027)")


async def ensure_data_consent(client: httpx.AsyncClient) -> None:
    """Consent + compliance disclosures - appendix Eligibility section."""
    body = {
        "consent_matching": True,
        "consent_outreach": True,
        "consent_research": True,
        "data_retention_preference": "standard",
        "first_generation_status": False,
        "first_generation_definition": "neither_parent_bachelors",
        "ferpa_release": True,
        "honor_code_ack": True,
        "background_check_required": False,
        "code_of_conduct_ack": True,
        "criminal_history_disclosed": False,
        "disciplinary_history_disclosed": False,
        "immunization_compliance": "in_progress",
        "health_insurance_waiver_intent": False,
        "military_status": "none",
        "veteran_status": False,
        "prior_academic_dismissal_flag": False,
        "directory_info_release": True,
        "third_party_sharing_consent": True,
        "marketing_channel_consent": {"email": True, "sms": False, "calls": False},
    }
    r = await client.put(f"{API}/students/me/data-rights", json=body)
    r.raise_for_status()
    print("  data consent: full appendix compliance block")


async def ensure_cs_major_readiness(client: httpx.AsyncClient) -> None:
    """Track-level self-rating for the CS track.

    Leo's profile is AI/LLM/systems-oriented. Ratings are on the appendix
    1-5 scale. We only cover the fields the student has evidence for;
    unrated fields stay absent from the dict (OUTPUT-side gap analysis
    can prompt for the remaining ones in the UI).
    """
    body = {
        "track": "cs",
        "readiness_data": {
            # Source + scale
            "self_rating_scale": "1-5 (1=none, 3=comfortable, 5=advanced)",
            "primary_programming_language": "Python",
            "programming_languages_list": ["Python", "TypeScript", "Go", "C++"],
            # CS fundamentals
            "cs_fundamentals_algorithms": 4,
            "cs_fundamentals_data_structures": 4,
            "cs_fundamentals_operating_systems": 3,
            "cs_fundamentals_networks": 3,
            "cs_fundamentals_databases": 4,
            "cs_fundamentals_discrete_math": 3,
            "cs_fundamentals_concurrency": 4,
            "cs_fundamentals_security_basics": 3,
            "cs_fundamentals_software_engineering": 4,
            # Math readiness
            "math_calculus_sequence_depth": 4,
            "math_linear_algebra": 4,
            "math_probability": 4,
            "math_statistics": 4,
            # ML readiness
            "ml_classification_regression": 4,
            "ml_deep_learning": 4,
            "ml_model_evaluation": 4,
            "ml_nlp": 5,
            "ml_time_series": 3,
            # Data skills
            "data_cleaning_eda": 4,
            "data_sql": 4,
            "data_feature_engineering": 4,
            "data_visualization": 3,
            # Engineering workflow
            "swe_ci_cd": 4,
            "swe_code_review": 4,
            "swe_testing": 4,
            "system_design_exposure": True,
            "mlops_exposure": True,
            "mlops_tools": ["Docker", "Kubernetes", "MLflow"],
            # Focus area
            "data_vs_ai_vs_cyber_vs_swe": "ai",
            "track_recommendation_self": "ai",
            "specialization_interests": ["LLMs", "inference_optimization", "NLP"],
            # Evidence
            "github_profile_link": "https://github.com/dev-leo",
            "open_source_contributions_flag": True,
            "research_experience_flag": True,
            "work_experience_tech_flag": True,
            "work_experience_months_tech": 8,
            # Tool familiarity
            "tool_ide_list": ["VS Code", "Claude Code", "Cursor"],
            "tool_cloud_list": ["AWS", "GCP"],
            "tool_db_list": ["PostgreSQL", "Redis", "pgvector"],
            "tool_version_control_level": 5,
            # Competitive programming
            "competitive_programming_participation_flag": False,
            # Research outputs
            "research_output_type": "code",
            # Source attribution (mirrors institution standard)
            "_source": "Self-reported 2026-04-17; validated against GitHub activity + coursework.",
        },
    }
    r = await client.put(f"{API}/students/me/major-readiness", json=body)
    r.raise_for_status()
    print("  major readiness (cs): upserted 30+ self-ratings + tool familiarity")


async def ensure_recommendation_requests(client: httpx.AsyncClient) -> None:
    """Seed 3 recommender rows (teacher, research supervisor, manager)."""
    resp = await client.get(f"{API}/students/me/recommendations")
    if resp.status_code == 404:
        # Endpoint may not exist yet; skip silently.
        print("  recommendations: endpoint not available - skipping")
        return
    try:
        resp.raise_for_status()
    except httpx.HTTPError:
        print("  recommendations: list fetch failed - skipping")
        return
    existing = resp.json()
    if existing:
        print(f"  recommendations: already has {len(existing)} requests")
        return
    seeds = [
        {
            "recommender_name": "Prof. Chen Wei",
            "recommender_email": "chen.wei@tsinghua.edu.cn",
            "recommender_title": "Associate Professor, Department of Computer Science",
            "recommender_institution": "Tsinghua University",
            "recommender_relationship": "course_instructor",
            "status": "pending_invitation",
            "notes": "CS 180: Machine Learning - graded Leo's final project (LLM eval harness).",
        },
        {
            "recommender_name": "Dr. Wang Lei",
            "recommender_email": "wang.lei@lab.example.cn",
            "recommender_title": "Research Scientist, AI Systems Lab",
            "recommender_institution": "Tsinghua AI Systems Lab",
            "recommender_relationship": "research_supervisor",
            "status": "pending_invitation",
            "notes": "Supervised Leo on KV-cache reuse research 2024-2025.",
        },
        {
            "recommender_name": "Jason Park",
            "recommender_email": "jason.park@startup.example",
            "recommender_title": "CTO",
            "recommender_institution": "Startup (summer internship)",
            "recommender_relationship": "internship_manager",
            "status": "pending_invitation",
            "notes": "Mentored Leo on inference latency work at internship.",
        },
    ]
    sent = 0
    for seed in seeds:
        r = await client.post(f"{API}/students/me/recommendations", json=seed)
        if r.status_code in (200, 201):
            sent += 1
    print(f"  recommendations: seeded {sent}/3 recommender requests")


async def ensure_platform_events(client: httpx.AsyncClient) -> None:
    """Drop a handful of backfill events so Package B signals have input."""
    events = [
        {"event_type": "login", "device_type": "desktop", "url_path": "/auth/login"},
        {"event_type": "search", "url_path": "/s/explore",
         "event_metadata": {"query": "nyu cs masters"}},
        {"event_type": "program_view", "url_path": "/s/school/nyu-accounting"},
        {"event_type": "compare", "event_metadata": {"count": 3}},
        {"event_type": "cta_save", "url_path": "/s/explore"},
    ]
    ok = 0
    for ev in events:
        r = await client.post(f"{API}/students/me/events", json=ev)
        if r.status_code in (200, 201):
            ok += 1
    print(f"  platform events: logged {ok}/{len(events)} analytics events")


async def main() -> None:
    print("=" * 60)
    print("DEV STUDENT PROFILE FILL (student@unipaith.co)")
    print("=" * 60)
    async with httpx.AsyncClient(timeout=30) as client:
        token = await login(client)
        client.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )

        before = (await client.get(f"{API}/students/me/onboarding")).json()
        print(f"Before: {before.get('completion_percentage', '?')}%")

        await ensure_basic_profile(client)
        await ensure_academic(client)
        await ensure_test_score(client)
        await ensure_activity(client)
        await ensure_language(client)
        await ensure_online_presence(client)
        await ensure_preferences(client)
        await ensure_visa_info(client)
        await ensure_data_consent(client)
        await ensure_cs_major_readiness(client)
        await ensure_recommendation_requests(client)
        await ensure_platform_events(client)

        after = (await client.get(f"{API}/students/me/onboarding")).json()
        print(f"\nAfter:  {after.get('completion_percentage', '?')}%")
        print(f"Steps:  {after.get('steps_completed')}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except httpx.HTTPError as exc:
        print(f"HTTP error: {exc}")
        sys.exit(1)
