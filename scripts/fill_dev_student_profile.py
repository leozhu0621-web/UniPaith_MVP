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
    """last_name + nationality unblock the 15% basic_profile step."""
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
    if not patch:
        print("  basic profile: already filled")
        return
    r2 = await client.put(f"{API}/students/me/profile", json=patch)
    r2.raise_for_status()
    print(f"  basic profile: patched {list(patch)}")


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
    }
    r = await client.post(f"{API}/students/me/academics", json=body)
    r.raise_for_status()
    print("  academics: added BS Computer Science record")


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
    }
    r = await client.post(f"{API}/students/me/test-scores", json=body)
    r.raise_for_status()
    print("  test scores: added TOEFL 108")


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
    if existing:
        print("  preferences: already set")
        return
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
    }
    r = await client.put(f"{API}/students/me/preferences", json=body)
    r.raise_for_status()
    print("  preferences: set target countries + career goals")


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

        after = (await client.get(f"{API}/students/me/onboarding")).json()
        print(f"\nAfter:  {after.get('completion_percentage', '?')}%")
        print(f"Steps:  {after.get('steps_completed')}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except httpx.HTTPError as exc:
        print(f"HTTP error: {exc}")
        sys.exit(1)
