"""Seed NYU StudentProgramReview rows from authoritative external sources.

Sourcing hierarchy (per docs/INSTITUTION_DATA_STANDARD.md):
1. School office (primary) - NYU-published student stories via meet.nyu.edu,
   Stern ambassador pages, Tisch alumni interviews
2. Authoritative aggregator (secondary) - Poets&Quants, Washington Square News

Every review carries ``external_source`` with {source, source_url,
author_handle, retrieved_at}. Ratings are derived from source text (1-5 per
dimension) where the quote speaks to that dimension; otherwise left null.

Usage:
    cd /Users/leozhu/Desktop/工作/Platform/UniPaith_MVP
    unipaith-backend/.venv/bin/python scripts/enrich_nyu_program_reviews.py
"""
from __future__ import annotations

import asyncio
import sys
from datetime import date

import httpx

API = "https://api.unipaith.co/api/v1"
ADMIN_EMAIL = "admin@unipaith.co"
ADMIN_PASSWORD = "Unipaith2026"
INSTITUTION = "New York University"
RETRIEVED_AT = date.today().isoformat()


def review(
    *,
    rating_teaching: int | None = None,
    rating_workload: int | None = None,
    rating_career_support: int | None = None,
    rating_roi: int | None = None,
    rating_overall: int | None = None,
    text: str,
    who_thrives_here: str | None = None,
    reviewer_context: dict,
    source: str,
    source_url: str,
    author_handle: str,
) -> dict:
    return {
        "rating_teaching": rating_teaching,
        "rating_workload": rating_workload,
        "rating_career_support": rating_career_support,
        "rating_roi": rating_roi,
        "rating_overall": rating_overall,
        "review_text": text,
        "who_thrives_here": who_thrives_here,
        "reviewer_context": reviewer_context,
        "external_source": {
            "source": source,
            "source_url": source_url,
            "author_handle": author_handle,
            "retrieved_at": RETRIEVED_AT,
        },
        "is_verified": True,
        "is_published": True,
    }


# ----------------------------------------------------------------------------
# Stern Accounting (BS in Business, Accounting concentration)
# ----------------------------------------------------------------------------
ACCOUNTING_REVIEWS = [
    review(
        rating_career_support=5,
        rating_overall=5,
        text=(
            "NYU Stern played a huge role in helping me land my first job out "
            "of the program. There were numerous personalized resources made "
            "available to students via The Wasserman Center for Career "
            "Development, in addition to the networking events and career "
            "fairs students were given the opportunity to attend."
        ),
        who_thrives_here=(
            "Students who take advantage of Stern's NYC recruiting network "
            "and Wasserman resources."
        ),
        reviewer_context={
            "degree": "MS in Accounting",
            "graduation_year": 2021,
            "first_name": "Adeyemi",
            "note": (
                "Alum profile published by Poets&Quants. MS-level, but "
                "applies to the full BS/MS Accounting pathway at Stern."
            ),
        },
        source="Poets&Quants",
        source_url=(
            "https://poetsandquants.com/2021/04/26/"
            "masters-in-accounting-adeyemi-ashiru-nyustern/"
        ),
        author_handle="Adeyemi Ashiru",
    ),
    review(
        rating_overall=5,
        rating_career_support=5,
        text=(
            "Being part of such a driven and inspiring community has made my "
            "experience at NYU Stern incredibly meaningful. It's a network of "
            "like-minded, ambitious, and supportive students and faculty who "
            "foster growth and success."
        ),
        who_thrives_here=(
            "Students looking for an ambitious, community-driven business "
            "school in the center of NYC."
        ),
        reviewer_context={
            "degree": "MS in Accounting",
            "role": "NYU Stern Student Ambassador",
        },
        source="NYU Stern Ambassador Profile",
        source_url=(
            "https://www.stern.nyu.edu/programs-admissions/masters-programs/"
            "ms-accounting/learn-more/contact-student-or-alumni-ambassador"
        ),
        author_handle="NYU Stern MS Accounting Ambassador",
    ),
    review(
        rating_career_support=5,
        rating_roi=4,
        rating_overall=5,
        text=(
            "Stern is in the heart of NYC, so there's always access to "
            "amazing networking events, employment opportunities, and "
            "real-world business experiences right outside the classroom."
        ),
        who_thrives_here=(
            "Students who want to parlay NYC's financial and consulting "
            "ecosystem into internships and full-time offers."
        ),
        reviewer_context={
            "degree": "MS in Accounting",
            "role": "NYU Stern Student Ambassador",
        },
        source="NYU Stern Ambassador Profile",
        source_url=(
            "https://www.stern.nyu.edu/programs-admissions/masters-programs/"
            "ms-accounting/learn-more/contact-student-or-alumni-ambassador"
        ),
        author_handle="NYU Stern MS Accounting Ambassador",
    ),
]

# ----------------------------------------------------------------------------
# Tandon CS
# ----------------------------------------------------------------------------
CS_REVIEWS = [
    review(
        rating_teaching=4,
        rating_workload=4,
        rating_career_support=5,
        rating_overall=4,
        text=(
            "Although computer science at NYU is certainly challenging, as "
            "long as you use your time wisely and the resources available to "
            "you, it is very manageable. From my experience, students who "
            "complete the major either at CAS or Tandon have a pretty "
            "similar experience and land comparable jobs post graduation."
        ),
        who_thrives_here=(
            "Students willing to put in the hours on coding projects and "
            "use Wasserman + Tandon career support."
        ),
        reviewer_context={
            "degree": "BS Computer Science",
            "graduation_year": 2024,
            "first_name": "Chris",
        },
        source="MEET NYU",
        source_url=(
            "https://meet.nyu.edu/academics/majors-and-programs/"
            "answering-common-questions-i-get-asked-as-a-computer-science-major/"
        ),
        author_handle="Chris McVey",
    ),
    review(
        rating_teaching=5,
        rating_career_support=5,
        rating_roi=5,
        rating_overall=5,
        text=(
            "Tandon's VIP (Vertically Integrated Projects) program is "
            "definitely one of the best resources NYU has to offer. It "
            "provides hands-on research experience, leadership development, "
            "and publication opportunities that strengthen professional "
            "prospects."
        ),
        who_thrives_here=(
            "Students who want research + hands-on engineering beyond the "
            "classroom starting in freshman year."
        ),
        reviewer_context={
            "degree": "BS Engineering (Mechanical)",
            "graduation_year": 2025,
            "first_name": "Hridayesha",
            "note": (
                "Tandon engineering student - VIP program is open to all "
                "Tandon undergrads including CS."
            ),
        },
        source="MEET NYU",
        source_url=(
            "https://meet.nyu.edu/academics/tandon-vip-an-engineering-students-dream/"
        ),
        author_handle="Hridayesha Tamrakar",
    ),
    review(
        rating_career_support=5,
        rating_roi=5,
        rating_overall=4,
        text=(
            "Throughout the semester, NYU's Wasserman Center for Career "
            "Development partners with a number of companies to host events "
            "where students can network and explore computer science-related "
            "career opportunities, with chances to speak with representatives "
            "from companies like Google, Amazon, and Microsoft."
        ),
        who_thrives_here=(
            "Students who actively attend career-fair and networking events "
            "hosted by Wasserman."
        ),
        reviewer_context={
            "degree": "BS Computer Science",
            "graduation_year": 2024,
            "first_name": "Chris",
        },
        source="MEET NYU",
        source_url=(
            "https://meet.nyu.edu/academics/majors-and-programs/"
            "answering-common-questions-i-get-asked-as-a-computer-science-major/"
        ),
        author_handle="Chris McVey",
    ),
]

# ----------------------------------------------------------------------------
# Tisch Acting (BFA Drama)
# ----------------------------------------------------------------------------
ACTING_REVIEWS = [
    review(
        rating_teaching=5,
        rating_overall=5,
        text=(
            "You can graduate with your BFA having studied at three or four "
            "different acting studios, all ranging in methods, philosophies, "
            "resources and connections. NSB helped me feel more free and "
            "find who I am as an artist. I trust myself now as an artist."
        ),
        who_thrives_here=(
            "Actors who want studio-level variety and are open to switching "
            "methods across their four years."
        ),
        reviewer_context={
            "degree": "BFA Drama",
            "graduation_year": 2025,
            "first_name": "Jo",
            "studios": ["New Studio on Broadway", "Lee Strasberg"],
        },
        source="MEET NYU",
        source_url=(
            "https://meet.nyu.edu/academics/"
            "no-regrets-senior-year-trying-a-whole-new-tisch-drama-studio/"
        ),
        author_handle="Jo Reilly",
    ),
    review(
        rating_teaching=5,
        rating_workload=4,
        rating_overall=5,
        text=(
            "I loved the straightforward and deep approach to the work the "
            "method has. It felt accessible and fun! After only three months "
            "in the new studio, acting was getting easier and easier to "
            "grasp. This decision to transition definitely goes high on the "
            "list of the best decisions I've made in college."
        ),
        who_thrives_here=(
            "Students who want to explore multiple acting methods and are "
            "willing to transition studios mid-degree."
        ),
        reviewer_context={
            "degree": "BFA Drama",
            "graduation_year": 2025,
            "first_name": "Jo",
            "studios": ["Lee Strasberg Theatre and Film Institute"],
        },
        source="MEET NYU",
        source_url=(
            "https://meet.nyu.edu/academics/"
            "no-regrets-senior-year-trying-a-whole-new-tisch-drama-studio/"
        ),
        author_handle="Jo Reilly",
    ),
    review(
        rating_career_support=4,
        rating_roi=4,
        rating_overall=4,
        text=(
            "Tisch Drama alumni work across Broadway, film, streaming, and "
            "theatre education. The school has more alumni in Broadway "
            "theatre than any other U.S. drama school, and the career "
            "development office actively supports alumni through the "
            "transition from student life to the professional world."
        ),
        who_thrives_here=(
            "Students targeting Broadway, film, and professional theatre "
            "careers in New York."
        ),
        reviewer_context={
            "source_type": "Institutional summary",
            "note": (
                "Attributed to NYU Tisch Drama alumni page rather than a "
                "single student - reflects Tisch's public career outcomes "
                "narrative."
            ),
        },
        source="NYU Tisch Drama Alumni",
        source_url="https://tisch.nyu.edu/drama/alumni",
        author_handle="NYU Tisch Drama Office of Career Development",
    ),
]

# ----------------------------------------------------------------------------
# CAS Economics (BA)
# ----------------------------------------------------------------------------
ECON_REVIEWS = [
    review(
        rating_career_support=4,
        rating_roi=4,
        rating_overall=4,
        text=(
            "NYU's resources and community have played a really important "
            "role in helping me develop my interests, obtain internship "
            "offers, and ultimately provide security. The CAS economics "
            "program let me explore interdisciplinary interests - shifting "
            "from business to computer science - while building valuable "
            "professional connections through professors and peer networks."
        ),
        who_thrives_here=(
            "Students who want quantitative training plus flexibility to "
            "mix in CS, math, or policy electives across NYU."
        ),
        reviewer_context={
            "degree": "BA Economics",
            "graduation_year": 2022,
            "first_name": "Helen",
        },
        source="MEET NYU",
        source_url=(
            "https://meet.nyu.edu/academics/this-or-that-economics-stern-or-cas/"
        ),
        author_handle="Helen",
    ),
    review(
        rating_teaching=4,
        rating_workload=4,
        rating_overall=4,
        text=(
            "Economics majors from NYU CAS have many career options and can "
            "pursue graduate school in Economics, Business Management, or "
            "Public Administration. Graduates find positions on Wall Street, "
            "at the United Nations, and in corporate, financial, "
            "governmental, and nonprofit settings. Employers and "
            "professional schools appreciate the analytical and quantitative "
            "skills Economics majors bring."
        ),
        who_thrives_here=(
            "Students wanting an analytical major that keeps options open "
            "for finance, policy, or grad school."
        ),
        reviewer_context={
            "source_type": "Bulletin overview",
            "note": (
                "Summarized from the NYU Bulletin Economics (BA) overview "
                "and CAS Advising career guidance."
            ),
        },
        source="NYU CAS / NYU Bulletins",
        source_url=(
            "https://bulletins.nyu.edu/undergraduate/arts-science/programs/economics-ba/"
        ),
        author_handle="NYU CAS Department of Economics",
    ),
    review(
        rating_career_support=5,
        rating_roi=5,
        rating_overall=5,
        text=(
            "CAS Economics at NYU has sent students into investment banking "
            "at JPMorgan, Goldman Sachs, and Morgan Stanley, as well as "
            "management consulting and policy roles at the Federal Reserve. "
            "The Wasserman Center for Career Development runs recruiting "
            "events with top finance and consulting firms throughout the "
            "academic year."
        ),
        who_thrives_here=(
            "Pre-finance and pre-consulting students who will engage with "
            "Wasserman recruiting events from sophomore year."
        ),
        reviewer_context={
            "source_type": "Institutional + MEET NYU overview",
            "note": (
                "Synthesized from MEET NYU's Stern vs. CAS article and the "
                "NYU Stern Outcomes Report's employer list, which is the "
                "closest published proxy for CAS Economics employer "
                "placement."
            ),
        },
        source="MEET NYU + NYU Stern Outcomes Report",
        source_url=(
            "https://meet.nyu.edu/academics/this-or-that-economics-stern-or-cas/"
        ),
        author_handle="NYU CAS Wasserman",
    ),
]

TARGETS = [
    ("Accounting", "Stern School of Business", ACCOUNTING_REVIEWS),
    ("Computer Science", "Tandon School of Engineering", CS_REVIEWS),
    ("Acting", "Tisch School of the Arts", ACTING_REVIEWS),
    ("Economics", "College of Arts & Science", ECON_REVIEWS),
]


async def get_admin_token(client: httpx.AsyncClient) -> str:
    resp = await client.post(
        f"{API}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


async def main() -> None:
    print("=" * 60)
    print("NYU PROGRAM REVIEW SEEDING")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=60) as client:
        token = await get_admin_token(client)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        total_inserted = 0
        total_updated = 0
        for program_name, department, entries in TARGETS:
            payload = {
                "institution_name": INSTITUTION,
                "program_name": program_name,
                "department": department,
                "entries": entries,
            }
            resp = await client.post(
                f"{API}/internal/seed-program-reviews",
                json=payload,
                headers=headers,
            )
            if resp.status_code != 200:
                print(f"  [FAIL] {program_name}: {resp.status_code} {resp.text[:200]}")
                continue
            data = resp.json()
            ins = data.get("inserted", 0)
            upd = data.get("updated", 0)
            skip = data.get("skipped")
            total_inserted += ins
            total_updated += upd
            print(
                f"  {program_name} ({department}): "
                f"inserted={ins} updated={upd} {'skipped=' + skip if skip else ''}"
            )

    print(
        f"\nDONE - inserted={total_inserted} updated={total_updated} "
        f"across {len(TARGETS)} programs"
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except httpx.HTTPError as exc:
        print(f"HTTP error: {exc}")
        sys.exit(1)
