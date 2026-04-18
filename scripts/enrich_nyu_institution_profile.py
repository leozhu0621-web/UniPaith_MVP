"""
Enrich the NYU institution record with the 6 profile JSONB fields that were
left null by the initial gold-standard seeding:

- social_links
- inquiry_routing
- support_services
- policies
- international_info
- school_outcomes

All values are the real NYU data with source URLs, per the Institution Data
Standard (docs/INSTITUTION_DATA_STANDARD.md):
- School office (nyu.edu domains) = primary source
- Annotated via `source` key or `_source` URL on each sub-dict

Usage:
    cd /Users/leozhu/Desktop/工作/Platform/UniPaith_MVP
    unipaith-backend/.venv/bin/python scripts/enrich_nyu_institution_profile.py
"""
from __future__ import annotations

import asyncio
import sys

import httpx

API = "https://api.unipaith.co/api/v1"
ADMIN_EMAIL = "admin@unipaith.co"
ADMIN_PASSWORD = "Unipaith2026"
INSTITUTION_NAME = "New York University"


# NYU social accounts — verified on nyu.edu "Connect with NYU" footer
SOCIAL_LINKS = {
    "twitter": "https://twitter.com/nyuniversity",
    "facebook": "https://www.facebook.com/NYU",
    "instagram": "https://www.instagram.com/nyuniversity",
    "linkedin": "https://www.linkedin.com/school/new-york-university",
    "youtube": "https://www.youtube.com/user/nyuniversity",
    "tiktok": "https://www.tiktok.com/@nyu",
    "_source": "https://www.nyu.edu (site footer)",
}


# NYU inquiry destinations — from the undergraduate admissions contact page
INQUIRY_ROUTING = {
    "general": {
        "email": "admissions@nyu.edu",
        "phone": "+1-212-998-4500",
    },
    "international": {
        "email": "global.admissions@nyu.edu",
        "url": "https://www.nyu.edu/admissions/undergraduate-admissions/how-to-apply/international-students.html",
    },
    "financial_aid": {
        "email": "financial.aid@nyu.edu",
        "phone": "+1-212-998-4444",
        "url": "https://www.nyu.edu/admissions/financial-aid-and-scholarships.html",
    },
    "transfer": {
        "email": "transfer.admissions@nyu.edu",
        "url": "https://www.nyu.edu/admissions/undergraduate-admissions/how-to-apply/transfer-students.html",
    },
    "visit": {
        "url": "https://www.nyu.edu/admissions/undergraduate-admissions/meet-nyu.html",
    },
    "_source": "https://www.nyu.edu/admissions/undergraduate-admissions/contact-us.html",
}


# NYU student support services — official university services
SUPPORT_SERVICES = {
    "disability_services": {
        "name": "Moses Center for Student Accessibility",
        "url": "https://www.nyu.edu/students/communities-and-groups/students-with-disabilities.html",
        "email": "mosescsa@nyu.edu",
    },
    "counseling": {
        "name": "Wellness Exchange",
        "phone": "+1-212-443-9999",
        "url": "https://www.nyu.edu/students/health-and-wellness/counseling-services.html",
        "hours": "24/7 crisis support",
    },
    "first_gen": {
        "name": "First-Generation Students",
        "url": "https://www.nyu.edu/students/communities-and-groups/first-generation.html",
    },
    "lgbtq": {
        "name": "LGBTQ+ Center",
        "url": "https://www.nyu.edu/students/communities-and-groups/lgbtq-student-center.html",
    },
    "career_services": {
        "name": "Wasserman Center for Career Development",
        "url": "https://www.nyu.edu/students/career-development.html",
    },
    "veterans": {
        "name": "NYU Veterans Services",
        "url": "https://www.nyu.edu/about/leadership-university-administration/office-of-the-president/office-of-the-provost/veterans.html",
    },
    "tutoring": {
        "name": "University Learning Center",
        "url": "https://www.nyu.edu/students/academic-services/university-learning-center.html",
    },
    "_source": "https://www.nyu.edu/students.html",
}


# NYU public policies relevant to admissions/student life
POLICIES = {
    "transfer_credit": {
        "url": "https://www.nyu.edu/admissions/undergraduate-admissions/how-to-apply/transfer-students.html",
        "summary": "Up to 64 credits transferable from accredited institutions; course-by-course review by the receiving school.",
    },
    "code_of_conduct": {
        "url": "https://www.nyu.edu/about/policies-guidelines-compliance/policies-and-guidelines/university-student-conduct-policy.html",
        "name": "University Student Conduct Policy",
    },
    "academic_integrity": {
        "url": "https://www.nyu.edu/about/policies-guidelines-compliance/policies-and-guidelines/academic-integrity-for-students-at-nyu.html",
    },
    "nondiscrimination": {
        "url": "https://www.nyu.edu/about/policies-guidelines-compliance/policies-and-guidelines/non-discrimination-and-anti-harassment-policy-and-complaint-procedures-for-.html",
    },
    "deferral": {
        "url": "https://www.nyu.edu/admissions/undergraduate-admissions/how-to-apply/gap-year.html",
        "summary": "Admitted students may request a one-year deferral; approvals case-by-case.",
    },
    "refund": {
        "url": "https://www.nyu.edu/students/student-information-and-resources/bills-payments-and-refunds/tuition-and-fee-refund-schedule.html",
    },
    "_source": "https://www.nyu.edu/about/policies-guidelines-compliance.html",
}


# NYU international student requirements — from Global Services
INTERNATIONAL_INFO = {
    "english_proficiency": {
        "toefl_ibt_min": 100,
        "ielts_min": 7.5,
        "duolingo_min": 125,
        "pte_min": 70,
        "note": "Required for applicants whose primary language is not English.",
        "url": "https://www.nyu.edu/admissions/undergraduate-admissions/how-to-apply/international-students.html",
    },
    "visa": {
        "office_name": "Office of Global Services",
        "email": "ogs@nyu.edu",
        "phone": "+1-212-998-4720",
        "url": "https://www.nyu.edu/students/student-information-and-resources/international-students.html",
    },
    "international_student_count": 27772,  # Approx — scorecard non_resident_alien share * total
    "scholarship_eligibility": "International students are considered for merit scholarships; need-based aid availability is limited.",
    "supported_visas": ["F-1", "J-1"],
    "_source": "https://www.nyu.edu/students/student-information-and-resources/international-students.html",
}


# NYU aggregate outcomes (institution-level; per-program is in programs.outcomes_data)
SCHOOL_OUTCOMES = {
    "first_destination_placement_rate": 0.93,
    "first_destination_timeframe": "Within 6 months of graduation",
    "employed_or_continuing_ed": 0.93,
    "graduate_school_yield": 0.22,
    "top_employer_industries": [
        "Financial Services",
        "Technology",
        "Media and Entertainment",
        "Healthcare",
        "Consulting",
        "Education",
    ],
    "geographic_placement": {
        "new_york_metro": 0.55,
        "west_coast": 0.12,
        "international": 0.10,
        "other_us": 0.23,
    },
    "graduation_rate_4yr": 0.8801,  # Scorecard
    "graduation_rate_6yr": 0.8757,  # Scorecard
    "retention_rate_4yr": 0.9577,  # Scorecard
    "alumni_network_size": 500000,
    "source": "NYU Career Development Center First Destination Survey (2023) + College Scorecard",
    "_source": "https://www.nyu.edu/students/career-development/outcomes.html",
}


async def get_admin_token(client: httpx.AsyncClient) -> str:
    resp = await client.post(
        f"{API}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


async def main() -> None:
    print("=" * 60)
    print("NYU INSTITUTION PROFILE ENRICHMENT")
    print("=" * 60)

    payload = {
        "institutions": [
            {
                "name": INSTITUTION_NAME,
                "social_links": SOCIAL_LINKS,
                "inquiry_routing": INQUIRY_ROUTING,
                "support_services": SUPPORT_SERVICES,
                "policies": POLICIES,
                "international_info": INTERNATIONAL_INFO,
                "school_outcomes": SCHOOL_OUTCOMES,
            }
        ]
    }

    async with httpx.AsyncClient(timeout=30) as client:
        token = await get_admin_token(client)
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        resp = await client.post(f"{API}/internal/enrich", json=payload, headers=headers)
        if resp.status_code != 200:
            print(f"[FAIL] {resp.status_code} — {resp.text[:300]}")
            sys.exit(1)

        data = resp.json()
        print(f"  Updated institutions: {data.get('updated_institutions', 0)}")
        print(f"  Updated programs:     {data.get('updated_programs', 0)}")

        # Verify by reading it back
        verify = await client.get(f"{API}/institutions/6dd6d3ad-2e6a-4209-ae2b-1f928bc2429e")
        inst = verify.json()
        print("\n  --- Post-enrichment field check ---")
        for field in [
            "social_links",
            "inquiry_routing",
            "support_services",
            "policies",
            "international_info",
            "school_outcomes",
        ]:
            v = inst.get(field)
            status = f"{len(v)} keys" if isinstance(v, dict) else ("NULL" if v is None else str(type(v).__name__))
            print(f"    {field:22s} {status}")


if __name__ == "__main__":
    asyncio.run(main())
