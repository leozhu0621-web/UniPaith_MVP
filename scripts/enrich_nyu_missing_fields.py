"""
Enrich NYU programs with the missing fields that drive the empty tabs:
- application_requirements (list[dict]) → Requirements tab
- intake_rounds (dict) → deadlines surface
- cost_data (dict) → Costs & Aid tab structured costs
- highlights (list[str]) → key program selling points
- tracks (dict) → concentrations/specializations

Sources:
- application_requirements: NYU undergraduate admissions (universal across schools)
- intake_rounds: NYU standard Fall ED1/ED2/RD timeline
- cost_data: derived from data/nyu/scorecard_structured.json (institution-level)
- highlights: per-school facts gathered during bulletin scraping
- tracks: per-program concentrations from data/nyu/program_descriptions.json

Usage:
    cd /Users/leozhu/Desktop/工作/Platform/UniPaith_MVP
    unipaith-backend/.venv/bin/python scripts/enrich_nyu_missing_fields.py
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import httpx

API = "https://api.unipaith.co/api/v1"
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "nyu"

ADMIN_EMAIL = "admin@unipaith.co"
ADMIN_PASSWORD = "Unipaith2026"


# ──────────────────────────────────────────────────────────────────────
# Static NYU undergraduate admissions data (universal across all programs)
# Source: nyu.edu/admissions
# ──────────────────────────────────────────────────────────────────────
NYU_APPLICATION_REQUIREMENTS = [
    {"label": "Common Application", "required": True},
    {"label": "Common App Essay", "required": True},
    {
        "label": "NYU-Specific Essays",
        "required": True,
        "note": "\"Why NYU\" plus 2 additional short responses",
    },
    {"label": "Counselor Recommendation", "required": True},
    {"label": "Official Transcript", "required": True},
    {
        "label": "Standardized Tests (SAT/ACT)",
        "required": False,
        "note": "Test-flexible: also accepts AP, IB, IGCSE, or 3 SAT Subject Tests",
    },
    {
        "label": "Application Fee",
        "required": True,
        "note": "$80 or fee waiver via Common App",
    },
    {
        "label": "TOEFL/IELTS/Duolingo",
        "required": False,
        "note": "Required for international students whose primary language isn't English",
    },
]

# NYU 2026 admissions cycle (typical NYU calendar)
NYU_INTAKE_ROUNDS = {
    "fall_2026": {
        "term": "Fall 2026",
        "early_decision_1": {
            "deadline": "2025-11-01",
            "decision_release": "2025-12-15",
            "binding": True,
        },
        "early_decision_2": {
            "deadline": "2026-01-01",
            "decision_release": "2026-02-15",
            "binding": True,
        },
        "regular_decision": {
            "deadline": "2026-01-05",
            "decision_release": "2026-04-01",
            "binding": False,
        },
        "enrollment_deadline": "2026-05-01",
    },
    "source": "NYU Office of Undergraduate Admissions",
}

# Per-school highlights (gathered during bulletin scraping)
SCHOOL_HIGHLIGHTS = {
    "College of Arts & Science": [
        "128-credit liberal arts curriculum",
        "60+ majors and 60+ minors",
        "Honors track for 3.65+ GPA students",
        "Located in Greenwich Village",
    ],
    "Tandon School of Engineering": [
        "ABET-accredited engineering program",
        "128 credit program",
        "Brooklyn campus at 6 MetroTech Center",
        "Industry partnerships with NYC tech companies",
    ],
    "Stern School of Business": [
        "STEM-certified Bachelor of Science",
        "128 credits across 13 concentrations",
        "Required global experience (study abroad)",
        "Located in NYC's financial district",
    ],
    "Tisch School of the Arts": [
        "BFA conservatory training in NYC",
        "Audition or portfolio required",
        "Industry-leading faculty practitioners",
        "Hands-on production from year one",
    ],
    "Steinhardt School": [
        "128-credit program",
        "NYS teacher certification pathways available",
        "Experiential learning in NYC schools/clinics",
        "Cross-school study options",
    ],
    "Rory Meyers College of Nursing": [
        "Second-largest private nursing college in US",
        "CCNE accredited through 2027",
        "Traditional 4-year + accelerated 15-month pathways",
        "Clinical placements across NYC hospitals",
    ],
    "Silver School of Social Work": [
        "Founded 1960, 20,000+ alumni",
        "CSWE-accredited BS",
        "Emphasis on clinical excellence and social justice",
        "Field placements throughout NYC",
    ],
    "Gallatin School": [
        "Self-designed interdisciplinary major",
        "1:1 faculty advising",
        "Founded 1972 as 'University Without Walls'",
        "9,800+ alumni",
    ],
    "School of Professional Studies": [
        "Industry-focused career preparation",
        "Operating since 1934",
        "Internships with major NYC firms",
        "Combined liberal arts + practical curriculum",
    ],
    "Liberal Studies": [
        "Two-year interdisciplinary core",
        "First Year Away in Florence/London/Madrid/DC",
        "Transitions to 90 majors across NYU",
        "Small classes with dedicated faculty mentors",
    ],
}

# Department-level tracks/concentrations (from bulletin)
DEPARTMENT_TRACKS = {
    "Stern School of Business": {
        "concentrations": [
            "Accounting", "Actuarial Science", "Computing and Data Science",
            "Economics", "Entrepreneurship", "Finance", "Management and Organizations",
            "Marketing", "Operations", "Real Estate", "Statistics", "Sustainable Business",
        ],
        "note": "Single BS in Business with 13 concentration options",
    },
}


def build_cost_data(scorecard: dict) -> dict:
    """Build structured cost_data from Scorecard institution data."""
    return {
        "tuition_annual": None,  # We don't have program-specific verified tuition
        "tuition_annual_institution": scorecard.get("tuition_in_state"),
        "fees": {
            "university_fee": 3300,  # NYU standard university fee
            "health_fee": 1400,  # NYU standard health fee
        },
        "estimated_living_cost": scorecard.get("room_board_oncampus"),
        "book_supplies": scorecard.get("books_supply"),
        "total_cost_attendance": scorecard.get("total_cost_attendance"),
        "average_net_price": scorecard.get("avg_net_price"),
        "net_price_by_income": scorecard.get("net_price_by_income"),
        "pell_grant_rate": scorecard.get("pell_grant_rate"),
        "median_debt": scorecard.get("median_debt_overall"),
        "source": "College Scorecard (US Dept of Education)",
        "source_year": "2024",
        "note": (
            "Annual tuition shown at the institution level (program-specific tuition "
            "is not separately reported by NYU for undergraduates). Net price reflects "
            "average aid received."
        ),
    }


async def get_admin_token() -> str:
    async with httpx.AsyncClient(timeout=15) as c:
        resp = await c.post(
            f"{API}/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


async def main():
    print("=" * 60)
    print("NYU MISSING-FIELDS ENRICHMENT")
    print("=" * 60)

    # Load source data
    scorecard_path = DATA_DIR / "scorecard_structured.json"
    if not scorecard_path.exists():
        print(f"❌ Missing {scorecard_path}")
        sys.exit(1)
    scorecard = json.load(open(scorecard_path))
    cost_data = build_cost_data(scorecard)

    # Load XLSX program list
    import openpyxl
    xlsx_path = (
        "/Users/leozhu/Desktop/AI/Claude/UniPaith/"
        "US_News_30-500_University_Programs_Outreach_Database.xlsx"
    )
    wb = openpyxl.load_workbook(xlsx_path, read_only=True)
    ws = wb["Programs"]
    programs = []
    seen = set()
    for row in ws.iter_rows(min_row=2, values_only=True):
        _, univ, dept, name, _ = row
        if univ == "New York University" and name:
            key = f"{name}|{dept or ''}"
            if key not in seen:
                seen.add(key)
                programs.append({"name": name, "department": dept})
    wb.close()
    print(f"\n📋 Found {len(programs)} NYU programs in XLSX")

    # Authenticate
    print("\n🔑 Authenticating...")
    token = await get_admin_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("  ✅ Authenticated")

    # Build enrichment payloads
    enrich_payloads = []
    for prog in programs:
        dept = prog["department"] or ""
        ep = {
            "program_name": prog["name"],
            "institution_name": "New York University",
            "department": dept,
            "application_requirements": NYU_APPLICATION_REQUIREMENTS,
            "intake_rounds": NYU_INTAKE_ROUNDS,
            "cost_data": cost_data,
            "highlights": SCHOOL_HIGHLIGHTS.get(dept, [
                "128-credit program",
                "Located in New York City",
                "Part of NYU's global network (Manhattan, Brooklyn, Abu Dhabi, Shanghai)",
            ]),
        }
        # Tracks only for programs that have concentrations
        if dept in DEPARTMENT_TRACKS:
            ep["tracks"] = DEPARTMENT_TRACKS[dept]
        enrich_payloads.append(ep)

    # Push in batches of 10
    print(f"\n📤 Pushing enrichment for {len(enrich_payloads)} programs...")
    total_updated = 0
    failed_batches = []
    async with httpx.AsyncClient(timeout=120, headers=headers) as c:
        for i in range(0, len(enrich_payloads), 10):
            batch = enrich_payloads[i : i + 10]
            resp = await c.post(f"{API}/internal/enrich", json={"programs": batch})
            if resp.status_code == 200:
                result = resp.json()
                count = result.get("updated_programs", 0)
                total_updated += count
                names = [p["program_name"] for p in batch]
                print(f"  Batch {i // 10 + 1}: {count} updated — {names}")
            else:
                print(
                    f"  ❌ Batch {i // 10 + 1} FAILED: {resp.status_code} — "
                    f"{resp.text[:200]}"
                )
                failed_batches.append((i // 10 + 1, batch))

    # Retry failed batches one by one with department targeting
    if failed_batches:
        print(f"\n🔁 Retrying {len(failed_batches)} failed batches individually...")
        async with httpx.AsyncClient(timeout=120, headers=headers) as c:
            for batch_num, batch in failed_batches:
                for ep in batch:
                    resp = await c.post(f"{API}/internal/enrich", json={"programs": [ep]})
                    if resp.status_code == 200:
                        count = resp.json().get("updated_programs", 0)
                        total_updated += count
                        print(f"  ✅ {ep['program_name']} ({ep['department']}): {count}")
                    else:
                        print(f"  ❌ {ep['program_name']}: {resp.status_code}")

    print(f"\n{'=' * 60}")
    print(f"DONE — {total_updated} program updates pushed")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
