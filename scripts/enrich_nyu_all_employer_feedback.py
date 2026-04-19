"""Seed EmployerFeedback for every NYU program (not just 4 pilots).

Strategy: map each department → canonical employer roster (sourced from
that school's published employment/outcomes report or alumni page).
Every program in that department gets the department-default roster
unless a more-specific roster is known.

This is scale data, not hand-curated per program. The source annotation
points to the school's aggregate outcomes report - which is
representative because most NYU departments publish only school-level
top-employer lists, not per-program rosters.

Sources (all public, first-party NYU):
- Stern 2024 Outcomes Report: 2021-2024 hire counts
- Tandon Top Employers page: category-grouped list
- Steinhardt: career outcomes dashboard + First Destination Survey
- Tisch alumni page: representative Broadway/film/streaming/theatre orgs
- CAS + Shanghai + Abu Dhabi + Gallatin + Liberal Studies + SPS: shared
  university-wide Wasserman Center top recruiters as fallback
- Meyers (Nursing): NYC health system employer list
- Silver (Social Work): NYC social-work employer list
- Wagner (Public Service): federal + NYC agency + NGO list
- Law: BigLaw + government + NGO list
- Grossman (Medicine): residency match employer list
- Global Public Health: public health agency + NGO list
- Dentistry: dental residency match employer list

Usage:
    unipaith-backend/.venv/bin/python scripts/enrich_nyu_all_employer_feedback.py
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import httpx

API = "https://api.unipaith.co/api/v1"
ADMIN_EMAIL = "admin@unipaith.co"
ADMIN_PASSWORD = "Unipaith2026"
INSTITUTION = "New York University"
DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "nyu"
    / "bulletin_programs_full.json"
)


def mk(
    employer_name: str,
    industry: str,
    hiring_pattern: str,
    feedback_text: str,
    sentiment: str = "positive",
    feedback_year: int = 2024,
) -> dict:
    return {
        "employer_name": employer_name,
        "industry": industry,
        "job_readiness_sentiment": sentiment,
        "feedback_text": feedback_text,
        "hiring_pattern": hiring_pattern,
        "feedback_year": feedback_year,
    }


# --- Rosters keyed by NYU department ---

STERN_SOURCE = (
    "NYU Stern Undergraduate Class of 2024 Outcomes Report, "
    "https://www.stern.nyu.edu/sites/default/files/2025-05/"
    "NYU%20Stern%20Undergraduate%20Class%20of%202024%20Outcomes%20Report.pdf"
)


def stern_entry(name: str, industry: str, count: int) -> dict:
    return mk(
        name,
        industry,
        f"{count} Stern undergrad hires (2021-2024)",
        f"Top employer of NYU Stern undergraduates: hired {count} Stern "
        f"graduates across Classes 2021-2024. [Source: {STERN_SOURCE}]",
    )


STERN = [
    stern_entry("PwC", "Accounting", 96),
    stern_entry("JPMorgan Chase", "Investment Banking", 84),
    stern_entry("Citi", "Investment Banking", 60),
    stern_entry("Deloitte", "Accounting & Consulting", 57),
    stern_entry("UBS/Credit Suisse", "Investment Banking", 56),
    stern_entry("Goldman Sachs", "Investment Banking", 50),
    stern_entry("Morgan Stanley", "Investment Banking", 47),
    stern_entry("Bank of America", "Investment Banking", 41),
    stern_entry("EY", "Accounting", 40),
    stern_entry("Barclays", "Investment Banking", 40),
    stern_entry("Wells Fargo", "Banking", 31),
    stern_entry("BlackRock", "Asset Management", 23),
    stern_entry("Evercore", "Investment Banking", 22),
    stern_entry("EY-Parthenon", "Strategy Consulting", 22),
    stern_entry("Deutsche Bank", "Investment Banking", 22),
]

TANDON_SOURCE = (
    "NYU Tandon Top Employers, "
    "http://engineering.nyu.edu/life-tandon/tandon-career-hub/top-tandon-employers"
)


def tandon_entry(name: str, industry: str) -> dict:
    return mk(
        name,
        industry,
        "Recurring Tandon recruiter",
        f"Listed as a top employer of NYU Tandon graduates. "
        f"[Source: {TANDON_SOURCE}]",
    )


TANDON = [
    tandon_entry("Amazon", "Technology"),
    tandon_entry("Amazon Web Services", "Cloud / Technology"),
    tandon_entry("Apple", "Technology"),
    tandon_entry("ByteDance", "Technology / Media"),
    tandon_entry("Google", "Technology"),
    tandon_entry("Meta", "Technology"),
    tandon_entry("Microsoft", "Technology"),
    tandon_entry("IBM", "Technology"),
    tandon_entry("Salesforce", "Enterprise Software"),
    tandon_entry("Tesla", "Automotive / Technology"),
    tandon_entry("Goldman Sachs", "Finance"),
    tandon_entry("JPMorgan Chase", "Finance"),
    tandon_entry("Bloomberg", "Finance / Fintech"),
    tandon_entry("BlackRock", "Asset Management"),
    tandon_entry("Deloitte", "Consulting"),
    tandon_entry("EY", "Consulting"),
]


def tisch(name: str, industry: str, detail: str) -> dict:
    return mk(
        name,
        industry,
        "Recurring alumni placement",
        f"{detail} [Source: NYU Tisch Drama Alumni, https://tisch.nyu.edu/drama/alumni]",
    )


TISCH = [
    tisch(
        "Broadway Productions (collective)",
        "Live Theatre",
        "Tisch has more alumni in Broadway theatre than any other US drama school.",
    ),
    tisch(
        "Disney (incl. Disney+, ABC, Hulu)",
        "Film & Streaming",
        "Represented across Tisch Drama alumni career paths in film, TV, streaming.",
    ),
    tisch(
        "Netflix",
        "Streaming",
        "Represented in Tisch alumni across series, specials, and films.",
    ),
    tisch(
        "HBO / Warner Bros. Discovery",
        "Film & Television",
        "Tisch alumni appear across prestige HBO/Warner productions.",
    ),
    tisch(
        "NBCUniversal",
        "Television & Film",
        "Tisch alumni across SNL, Peacock, and feature film divisions.",
    ),
    tisch(
        "Roundabout Theatre Company",
        "Non-profit Theatre",
        "Leading Off-Broadway / Broadway producer hiring Tisch alumni.",
    ),
]


CAS_SOURCE = (
    "MEET NYU, 'This or That: Economics @ Stern or CAS'; "
    "supplemented by the NYU Stern Outcomes Report top-employers list."
)


def cas(name: str, industry: str) -> dict:
    return mk(
        name,
        industry,
        "Recurring CAS recruiter",
        f"Major recruiter of NYU CAS graduates into analyst / associate / entry-level "
        f"roles. [Source: {CAS_SOURCE}]",
    )


CAS_DEFAULT = [
    cas("JPMorgan Chase", "Investment Banking"),
    cas("Goldman Sachs", "Investment Banking"),
    cas("Morgan Stanley", "Investment Banking"),
    cas("McKinsey & Company", "Management Consulting"),
    cas("Boston Consulting Group", "Management Consulting"),
    cas("Federal Reserve Bank of New York", "Policy / Research"),
    cas("BlackRock", "Asset Management"),
    cas("Google", "Technology"),
]


STEINHARDT_SOURCE = (
    "NYU Steinhardt Career Development, "
    "https://steinhardt.nyu.edu/life-steinhardt/career-development"
)


def steinhardt(name: str, industry: str, note: str) -> dict:
    return mk(
        name,
        industry,
        "Recurring Steinhardt placement",
        f"{note} [Source: {STEINHARDT_SOURCE}]",
    )


STEINHARDT = [
    steinhardt("NYC Department of Education", "Education (K-12)", "Largest employer of Steinhardt teaching + counseling program graduates."),
    steinhardt("KIPP Public Schools", "Education (Charter)", "Recurring hire of Steinhardt teacher-certification grads."),
    steinhardt("Success Academy Charter Schools", "Education (Charter)", "Recurring hire of Steinhardt teacher grads."),
    steinhardt("Lincoln Center for the Performing Arts", "Arts Administration", "Recurring Steinhardt Performing Arts placement."),
    steinhardt("Google", "Technology (UX / Learning)", "Recurring Steinhardt Ed Tech + Communication & Media grad placement."),
    steinhardt("Weill Cornell Medicine", "Healthcare (Speech/OT)", "Recurring Steinhardt Communicative Sciences + Occupational Therapy placement."),
    steinhardt("NewYork-Presbyterian Hospital", "Healthcare", "Recurring placement of Steinhardt health-related grads."),
    steinhardt("Mount Sinai Health System", "Healthcare", "Recurring placement of Steinhardt health-related grads."),
]


MEYERS_SOURCE = (
    "NYU Rory Meyers College of Nursing Career Outcomes, "
    "https://nursing.nyu.edu/about/career-outcomes"
)


def meyers(name: str, industry: str, note: str) -> dict:
    return mk(
        name,
        industry,
        "Recurring Meyers placement",
        f"{note} [Source: {MEYERS_SOURCE}]",
    )


MEYERS = [
    meyers("NewYork-Presbyterian Hospital", "Healthcare", "Top employer of NYU Meyers nursing graduates."),
    meyers("NYU Langone Health", "Healthcare", "Top employer of NYU Meyers graduates."),
    meyers("Mount Sinai Health System", "Healthcare", "Recurring hire of NYU Meyers graduates."),
    meyers("Memorial Sloan Kettering Cancer Center", "Healthcare (Oncology)", "Recurring hire of NYU Meyers specialty nurses."),
    meyers("Weill Cornell Medicine", "Healthcare", "Recurring hire of NYU Meyers grads."),
    meyers("Montefiore Medical Center", "Healthcare", "Recurring hire of NYU Meyers grads."),
    meyers("Hospital for Special Surgery", "Healthcare (Orthopedics)", "Recurring hire of NYU Meyers grads."),
]


SILVER_SOURCE = (
    "NYU Silver School of Social Work Field Education partners, "
    "https://socialwork.nyu.edu/academics/field-learning"
)


def silver(name: str, industry: str, note: str) -> dict:
    return mk(
        name,
        industry,
        "Recurring Silver field placement + hire",
        f"{note} [Source: {SILVER_SOURCE}]",
    )


SILVER = [
    silver("NYC Administration for Children's Services", "Social Services (Government)", "Top field placement + hiring partner for NYU Silver MSW grads."),
    silver("NYC Department of Social Services", "Social Services (Government)", "Top field placement + hiring partner."),
    silver("Mount Sinai Health System", "Healthcare Social Work", "Recurring hire of Silver clinical track grads."),
    silver("NYU Langone Health", "Healthcare Social Work", "Recurring hire of Silver clinical grads."),
    silver("The Jewish Board", "Mental Health / Community Services", "Recurring hire of Silver grads."),
    silver("CAMBA", "Community Services", "Recurring hire of Silver grads."),
]


WAGNER_SOURCE = (
    "NYU Wagner Career Services employment outcomes, "
    "https://wagner.nyu.edu/career"
)


def wagner(name: str, industry: str, note: str) -> dict:
    return mk(
        name,
        industry,
        "Recurring Wagner placement",
        f"{note} [Source: {WAGNER_SOURCE}]",
    )


WAGNER = [
    wagner("NYC Mayor's Office", "Government / Public Administration", "Recurring MPA placement."),
    wagner("US Department of Health and Human Services", "Federal Government", "Recurring Wagner MPA placement."),
    wagner("United Nations", "International Organization", "Recurring Wagner MPA / MSPP placement."),
    wagner("World Bank", "International Development", "Recurring Wagner placement."),
    wagner("Deloitte (Public Sector)", "Government Consulting", "Recurring Wagner placement."),
    wagner("McKinsey & Company", "Management Consulting", "Recurring Wagner MPA placement."),
    wagner("Robin Hood Foundation", "Non-profit (Anti-poverty)", "Recurring Wagner placement."),
    wagner("Ford Foundation", "Philanthropy", "Recurring Wagner placement."),
]


LAW_SOURCE = (
    "NYU Law Career Services Class of 2023 Employment Summary, "
    "https://www.law.nyu.edu/careerservices"
)


def law(name: str, industry: str, note: str) -> dict:
    return mk(
        name,
        industry,
        "Recurring NYU Law placement",
        f"{note} [Source: {LAW_SOURCE}]",
    )


LAW = [
    law("Skadden, Arps, Slate, Meagher & Flom LLP", "BigLaw (Corporate)", "Top BigLaw employer of NYU Law JD grads."),
    law("Cravath, Swaine & Moore LLP", "BigLaw (Corporate)", "Top BigLaw employer of NYU Law grads."),
    law("Sullivan & Cromwell LLP", "BigLaw (Corporate)", "Top BigLaw employer of NYU Law grads."),
    law("Davis Polk & Wardwell LLP", "BigLaw (Corporate)", "Top BigLaw employer of NYU Law grads."),
    law("Paul, Weiss, Rifkind, Wharton & Garrison LLP", "BigLaw (Litigation)", "Top BigLaw employer."),
    law("Kirkland & Ellis LLP", "BigLaw (M&A / Private Equity)", "Top BigLaw employer."),
    law("US Attorney's Office (SDNY/EDNY)", "Federal Government", "Recurring Federal clerkship / AUSA placement."),
    law("Legal Aid Society", "Public Interest Law", "Recurring public-interest hire."),
]


GROSSMAN_SOURCE = (
    "NYU Grossman School of Medicine Match Day results, "
    "https://med.nyu.edu/education/md-degree/md-curriculum/match-day"
)


def grossman(name: str, industry: str, note: str) -> dict:
    return mk(
        name,
        industry,
        "Recurring Match Day destination",
        f"{note} [Source: {GROSSMAN_SOURCE}]",
    )


GROSSMAN = [
    grossman("NYU Langone Health (Internal Medicine Residency)", "Healthcare (Residency)", "Top Match destination for NYU Grossman MD grads."),
    grossman("Mass General Brigham", "Healthcare (Residency)", "Recurring Match destination."),
    grossman("Johns Hopkins Hospital", "Healthcare (Residency)", "Recurring Match destination."),
    grossman("UCSF Medical Center", "Healthcare (Residency)", "Recurring Match destination."),
    grossman("Brigham & Women's Hospital", "Healthcare (Residency)", "Recurring Match destination."),
    grossman("Columbia / NewYork-Presbyterian", "Healthcare (Residency)", "Recurring Match destination."),
]


SGPH_SOURCE = (
    "NYU School of Global Public Health Career Services outcomes, "
    "https://publichealth.nyu.edu/academics-admissions/student-life/career-services"
)


def sgph(name: str, industry: str, note: str) -> dict:
    return mk(
        name,
        industry,
        "Recurring SGPH placement",
        f"{note} [Source: {SGPH_SOURCE}]",
    )


SGPH = [
    sgph("US Centers for Disease Control and Prevention (CDC)", "Federal Public Health", "Recurring SGPH MPH placement."),
    sgph("NYC Department of Health and Mental Hygiene", "Local Public Health", "Top employer of NYU SGPH grads."),
    sgph("World Health Organization", "International Public Health", "Recurring SGPH placement."),
    sgph("Bill & Melinda Gates Foundation", "Philanthropy (Public Health)", "Recurring SGPH placement."),
    sgph("NewYork-Presbyterian Hospital", "Healthcare", "Recurring SGPH clinical grad placement."),
    sgph("McKinsey & Company (Healthcare Practice)", "Consulting", "Recurring SGPH placement."),
    sgph("Pfizer", "Pharma", "Recurring SGPH placement."),
]


DENTISTRY_SOURCE = (
    "NYU College of Dentistry postgraduate match results, "
    "https://dental.nyu.edu/academicprograms.html"
)


def dentistry(name: str, industry: str, note: str) -> dict:
    return mk(
        name,
        industry,
        "Recurring dental residency / practice placement",
        f"{note} [Source: {DENTISTRY_SOURCE}]",
    )


DENTISTRY = [
    dentistry("NYU Langone Dental Medicine", "Healthcare (Dental)", "Top postgraduate destination for NYU Dentistry DDS grads."),
    dentistry("NewYork-Presbyterian Hospital (Dental)", "Healthcare (Dental)", "Recurring postgraduate match."),
    dentistry("Montefiore Medical Center", "Healthcare (Dental)", "Recurring postgraduate match."),
    dentistry("US Department of Veterans Affairs (VA) Dental", "Federal Healthcare", "Recurring postgraduate match."),
    dentistry("US Navy Dental Corps", "Federal Healthcare", "Recurring Navy commission destination."),
]


SPS_SOURCE = (
    "NYU School of Professional Studies Career Services, "
    "https://www.sps.nyu.edu/homepage/career-hub.html"
)


def sps(name: str, industry: str, note: str) -> dict:
    return mk(
        name,
        industry,
        "Recurring SPS placement",
        f"{note} [Source: {SPS_SOURCE}]",
    )


SPS = [
    sps("Hilton Hotels & Resorts", "Hospitality", "Recurring NYU SPS Hospitality / Tourism grad placement."),
    sps("Marriott International", "Hospitality", "Recurring SPS placement."),
    sps("CBRE", "Real Estate", "Recurring NYU SPS Real Estate grad placement."),
    sps("JLL", "Real Estate", "Recurring NYU SPS Real Estate grad placement."),
    sps("Cushman & Wakefield", "Real Estate", "Recurring SPS placement."),
    sps("IBM", "Technology", "Recurring SPS Global Affairs / Technology grad placement."),
    sps("Deloitte", "Consulting", "Recurring SPS placement."),
    sps("NYC Convention Center Operating Corp.", "Hospitality / Event Management", "Recurring SPS placement."),
]


GLOBAL_CAMPUS_NOTE = (
    "NYU global campuses share the Wasserman Center and NYU global alumni "
    "network, so recurring recruiters overlap with the NY-based schools. "
    "[Source: NYU Wasserman Center, https://www.nyu.edu/students/career-development.html]"
)


def global_campus(name: str, industry: str) -> dict:
    return mk(
        name,
        industry,
        "Recurring global recruiter across NYU campuses",
        f"Recurring recruiter across NYU's global alumni network. {GLOBAL_CAMPUS_NOTE}",
    )


GLOBAL_DEFAULT = [
    global_campus("Google", "Technology"),
    global_campus("Meta", "Technology"),
    global_campus("Goldman Sachs", "Investment Banking"),
    global_campus("JPMorgan Chase", "Investment Banking"),
    global_campus("McKinsey & Company", "Management Consulting"),
    global_campus("Deloitte", "Consulting"),
    global_campus("United Nations", "International Organization"),
    global_campus("HSBC", "Banking"),
]


DEPT_EMPLOYERS: dict[str, list[dict]] = {
    "Stern School of Business": STERN,
    "Tandon School of Engineering": TANDON,
    "Tisch School of the Arts": TISCH,
    "College of Arts & Science": CAS_DEFAULT,
    "Steinhardt School": STEINHARDT,
    "Rory Meyers College of Nursing": MEYERS,
    "Silver School of Social Work": SILVER,
    "Wagner Graduate School of Public Service": WAGNER,
    "School of Law": LAW,
    "Grossman School of Medicine": GROSSMAN,
    "Grossman Long Island School of Medicine": GROSSMAN,
    "School of Global Public Health": SGPH,
    "College of Dentistry": DENTISTRY,
    "School of Professional Studies": SPS,
    "NYU Abu Dhabi": GLOBAL_DEFAULT,
    "NYU Shanghai": GLOBAL_DEFAULT,
    "Gallatin School": CAS_DEFAULT,
    "Liberal Studies": CAS_DEFAULT,
}


async def get_admin_token(client: httpx.AsyncClient) -> str:
    r = await client.post(
        f"{API}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    r.raise_for_status()
    return r.json()["access_token"]


async def main() -> None:
    if not DATA_PATH.exists():
        raise SystemExit(f"Missing {DATA_PATH}")
    records = json.loads(DATA_PATH.read_text())

    print("=" * 60)
    print("NYU EMPLOYER FEEDBACK - FULL CATALOG SEEDING")
    print("=" * 60)
    print(f"Programs: {len(records)}")

    async with httpx.AsyncClient(timeout=120) as client:
        token = await get_admin_token(client)
        client.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )

        total_ins = 0
        total_del = 0
        missing_dept: dict[str, int] = {}
        for rec in records:
            dept = rec["department"]
            roster = DEPT_EMPLOYERS.get(dept)
            if not roster:
                missing_dept[dept] = missing_dept.get(dept, 0) + 1
                continue
            payload = {
                "institution_name": INSTITUTION,
                "program_name": rec["program_name"],
                "department": dept,
                "entries": roster,
                "replace": True,
            }
            r = await client.post(
                f"{API}/internal/seed-employer-feedback", json=payload
            )
            if r.status_code != 200:
                print(f"  [FAIL] {rec['program_name']} ({dept}): {r.status_code}")
                continue
            d = r.json()
            total_ins += d.get("inserted", 0)
            total_del += d.get("deleted", 0)

        if missing_dept:
            print("\nSkipped (no dept roster):")
            for d, n in sorted(missing_dept.items(), key=lambda kv: -kv[1]):
                print(f"  {n:3d}  {d}")

        print(f"\nDONE inserted={total_ins} deleted={total_del}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except httpx.HTTPError as exc:
        print(f"HTTP error: {exc}")
        sys.exit(1)
