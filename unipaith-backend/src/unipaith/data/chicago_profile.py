"""Canonical University of Chicago profile — the single source of truth.

Real, sourced data only (U.S. Dept. of Education College Scorecard, UNITID 144050 ·
NCES College Navigator / IPEDS · the University of Chicago Common Data Set 2024-25 · the
official "University Facts — At a Glance" data portal (data.uchicago.edu) · UChicago News
(endowment) · the official QS / Times Higher Education / U.S. News rankings · each unit's
official leadership page (Office of the Provost) · the Office of the Bursar / each school's
tuition page · UChicago Career Advancement post-college outcomes · the Chicago Booth
Full-Time MBA Employment Report, Class of 2025 · the College Scorecard Field-of-Study
earnings by CIP). ``apply(session)`` idempotently enriches the University of Chicago
institution row, upserts its real degree-granting schools and divisions, and builds its
program catalog across them.

UChicago's academic structure: the undergraduate College plus the four graduate divisions
(Biological Sciences, Humanities, Physical Sciences, Social Sciences) and a set of
dean-led professional schools. We model the units that own the degree programs in the
canonical College Scorecard Field-of-Study list for UNITID 144050 onto the platform's
``School`` model:
  - The College (undergraduate B.A./B.S. majors)
  - The University of Chicago Booth School of Business (the MBA — the most-enriched flagship)
  - Division of the Social Sciences (MAPSS, the Committee on International Relations)
  - Physical Sciences Division (the M.S. in Computer Science / MPCS, the M.S. in Statistics)
  - Crown Family School of Social Work, Policy, and Practice (the A.M. in Social Work)
  - Graham School of Continuing Liberal and Professional Studies (the Master of Liberal Arts)

It **flushes but does not commit** — the caller (the Alembic data migration, the CLI
script, or the dev seed) owns the transaction. It is a **no-op** (returns ``False``) when
UChicago is absent, so it is safe to run against a fresh or CI database. Re-running is
safe: schools key off ``(institution_id, name)`` and programs off ``slug``; stale rows are
reconciled without breaking foreign keys.

This mirrors ``mit_profile`` / ``yale_profile`` so the migration, the standalone script,
and the dev seed all agree (DRY). Every figure traces to a public, citable source;
anything that could not be verified from a first-party or two-independent-source basis is
**omitted** (recorded in the relevant ``_standard.omitted`` list), never guessed. The
Booth Full-Time MBA is the most-enriched flagship program (its real curriculum, faculty,
class profile, employment distribution and aggregated reviews), mirroring MIT Sloan's MBAn
in the reference instance — with the honest caveats that UChicago is test-optional for
first-year admission, that program-specific graduate tuition for the divisional master's
(MAPSS, International Relations, M.S. Statistics, Master of Liberal Arts) is published only
on the JavaScript-rendered Bursar pages and so is recorded as omitted rather than guessed,
and that three undergraduate majors whose one-year Field-of-Study earnings the federal
College Scorecard suppresses fall back to the institution-wide median.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "University of Chicago"

# Date this profile was researched + verified; stamped into every node's _standard.
ENRICHED_AT = "2026-06-10"


def _standard(omitted: list[str] | None = None) -> dict:
    """The per-node provenance stamp the routine writes onto every enriched node."""
    return {
        "version": STANDARD_VERSION,
        "enriched_at": ENRICHED_AT,
        "omitted": omitted or [],
    }


# Institution-level fields that could NOT be verified from a citable source and are
# therefore honestly omitted rather than guessed. (None at present — every required
# institution field is verified below.)
_OMITTED_INSTITUTION: list[str] = []

# ── Institution-level data ────────────────────────────────────────────────
# Rankings are stored as {rank, year} objects (the page renders any ranking_data entry
# that is an object with a numeric `rank`). All three ranks are quoted from the official
# ranking bodies for the 2026 editions.
RANKING_DATA: dict = {
    "ownership_type": "private",
    # UChicago is accredited by the Higher Learning Commission (HLC).
    "accreditor": "HLC",
    # Carnegie basic classification (R1).
    "carnegie_classification": "Doctoral Universities: Very High Research Activity",
    # QS World University Rankings 2026: UChicago is ranked #13 worldwide.
    "qs_world_university_rankings": {"rank": 13, "year": 2026},
    # THE World University Rankings 2026: #15 in the world.
    "times_higher_education": {"rank": 15, "year": 2026},
    # U.S. News Best Colleges (National Universities) 2026: #6 nationally.
    "us_news_national": {"rank": 6, "year": 2026},
}

# school_outcomes is shallow-merged into the existing JSONB; each sub-object below is
# complete, so a shallow merge is correct. Figures are College Scorecard (UNITID 144050)
# cross-checked against UChicago's Common Data Set 2024-25, NCES College Navigator
# (IPEDS), and the official "University Facts — At a Glance" page where each publishes a
# metric.
SCHOOL_OUTCOMES: dict = {
    # CDS 2024-25: 1,955 admits / 43,612 first-year applicants = 4.48% (Scorecard 0.0448).
    "admit_rate": 0.0448,
    # College Scorecard average annual net price.
    "avg_net_price": 14860,
    # College Scorecard institution-wide median earnings 10 years after entry.
    "median_earnings_10yr": 91885,
    # College Scorecard four-year completion rate (150% of normal time).
    "completion_rate_4yr_150pct": 0.9585,
    # CDS 2024-25 (item B22): first-year retention (Fall 2023 cohort) = 99.0%.
    "retention_rate_first_year": 0.99,
    # CDS 2024-25: six-year graduation rate (Fall 2018 cohort) = 95.9%.
    "graduation_rate_6yr": 0.959,
    "financial_aid": {
        # NCES College Navigator (IPEDS), 2023-24 full-time beginning undergraduates: 16%
        # received a Pell grant; 4% took federal student loans. UChicago's No Barriers
        # program meets full demonstrated need.
        "pell_grant_rate": 0.16,
        "federal_loan_rate": 0.04,
        # College Scorecard average annual cost of attendance.
        "cost_of_attendance": 90360,
    },
    # Undergraduate race/ethnicity (UChicago CDS 2024-25, item B2, degree-seeking
    # undergraduates, n=7,503; shares rounded to whole percents).
    "demographics": {
        "white": 0.30,
        "black": 0.07,
        "hispanic": 0.17,
        "asian": 0.19,
        "two_or_more": 0.07,
        "international": 0.18,
    },
    # SAT/ACT 25th-75th percentiles of enrolled first-years (UChicago CDS 2024-25, item
    # C9). UChicago is test-optional, so percentiles reflect only score-submitters.
    "test_scores": {
        "sat_reading_25_75": [740, 780],
        "sat_math_25_75": [770, 800],
        "act_25_75": [34, 35],
    },
    # Main campus, Hyde Park, Chicago, Illinois.
    "location": {"lat": 41.78972, "lng": -87.59972},
    "campus_basics": {"location": "Hyde Park, Chicago, Illinois"},
    "scale": {
        # data.uchicago.edu "At a Glance" (Fall 2024): tenure-track faculty (1,158) plus
        # BSD clinical faculty (1,030) = 2,188 faculty (excludes the 1,430 other academic
        # appointees the same page lists separately).
        "faculty_count": 2188,
        # data.uchicago.edu / CDS 2024-25 (item I2): 5-to-1 student-faculty ratio.
        "student_faculty_ratio": "5:1",
        # UChicago News: endowment $10.4 billion at fiscal year-end June 30, 2024 (FY24,
        # 8.4% net return).
        "endowment_usd": 10400000000,
    },
    # UChicago Career Advancement, Class of 2025: 98% of graduates secured a post-college
    # offer (employment, graduate school, or other opportunity), 71% employment and 29%
    # graduate/professional school.
    "employed_or_continuing_ed": 0.98,
    # The sectors UChicago Career Advancement reports graduates most commonly enter
    # (Career Advancement groups outcomes into these fields); not ranked by a published
    # percentage.
    "top_employer_industries": [
        "Financial services",
        "Consulting",
        "Technology",
        "Government & public policy",
        "Healthcare",
        "Science & research",
    ],
    "research": {
        "labs": [
            "Argonne National Laboratory (DOE lab; UChicago prime contractor since 1946)",
            "Fermi National Accelerator Laboratory (Fermilab; UChicago co-contractor)",
            "Marine Biological Laboratory (Woods Hole; UChicago affiliate)",
            "Enrico Fermi Institute (nuclear, particle & astrophysics)",
            "James Franck Institute (condensed-matter & materials science)",
            "Kavli Institute for Cosmological Physics",
        ],
        "areas": [
            "Physical sciences, cosmology & particle physics",
            "Economics & the social sciences",
            "Molecular engineering & materials",
            "Biomedicine & molecular biology",
            "Public policy & global conflict",
            "Law, philosophy & the humanities",
        ],
        "lab_links": {
            "Argonne National Laboratory (DOE lab; UChicago prime contractor since 1946)": (
                "https://www.anl.gov/"
            ),
            "Fermi National Accelerator Laboratory (Fermilab; UChicago co-contractor)": (
                "https://www.fnal.gov/"
            ),
            "Marine Biological Laboratory (Woods Hole; UChicago affiliate)": (
                "https://www.mbl.edu/"
            ),
        },
    },
    "campus_life": {
        # The Maroons compete in NCAA Division III as a charter member of the University
        # Athletic Association (UAA).
        "athletics_division": "NCAA Division III (University Athletic Association)",
        "mascot": "Chicago Maroons (Phil the Phoenix)",
        "housing": "Seven residential houses-in-commons across the Hyde Park campus",
        "resources": [
            {"label": "UChicago Athletics (Maroons)", "url": "https://athletics.uchicago.edu/"},
            {
                "label": "UChicago Affiliated Laboratories",
                "url": "https://www.uchicago.edu/en/education-and-research/affliated-laboratories",
            },
        ],
    },
    "flagship": {
        # data.uchicago.edu "At a Glance": 19,287 total students — 7,569 undergraduate +
        # 10,968 graduate, professional and other.
        "enrollment_total": 19287,
        # Common Data Set 2024-25 first-year admissions cycle (item C1).
        "applicants": 43612,
        "admits": 1955,
        "admissions_cycle": "Entering class fall 2024 (UChicago Common Data Set 2024-25)",
        # Incorporated in 1890 by John D. Rockefeller and the American Baptist Education
        # Society; instruction began in 1892.
        "founded_year": 1890,
        # UChicago official "Nobel Prizes" page: 101 Nobel laureates have been affiliated
        # with the University as faculty, students or researchers.
        "nobel_laureates": 101,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (UChicago, UNITID 144050)",
            "url": "https://collegescorecard.ed.gov/school/?144050-University-of-Chicago",
        },
        {
            "label": "NCES College Navigator — University of Chicago (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=144050",
        },
        {
            "label": "University of Chicago — Common Data Set 2024-25",
            "url": "https://data.uchicago.edu/common-data-set/",
        },
        {
            "label": "University of Chicago — University Facts (At a Glance)",
            "url": "https://data.uchicago.edu/data-at-a-glance/",
        },
        {
            "label": "University of Chicago endowment ended FY24 at $10.4 billion (UChicago News)",
            "url": "https://news.uchicago.edu/story/university-chicago-endowment-ended-fy24-104-billion",
        },
        {
            "label": "QS World University Rankings 2026 — University of Chicago",
            "url": "https://www.topuniversities.com/universities/university-chicago",
        },
        {
            "label": (
                "Times Higher Education World University Rankings 2026 — University of Chicago"
            ),
            "url": "https://www.timeshighereducation.com/world-university-rankings/university-chicago",
        },
        {
            "label": (
                "U.S. News Best Colleges 2026 — University of Chicago (#6 National Universities)"
            ),
            "url": "https://www.usnews.com/best-colleges/university-of-chicago-1774",
        },
        {
            "label": "University of Chicago Career Advancement — Post-College Outcomes",
            "url": "https://careeradvancement.uchicago.edu/about-us/post-college-outcomes/",
        },
        {
            "label": "University of Chicago — Nobel Laureates",
            "url": "https://www.uchicago.edu/en/who-we-are/global-impact/accolades/nobel-laureates",
        },
    ],
}

# student_body_size is the undergraduate count (the page labels it "Undergraduates"); the
# total (19,287) lives in flagship.enrollment_total and renders as "Total enrollment".
# 7,569 = data.uchicago.edu "At a Glance" undergraduate enrollment.
UNDERGRAD_COUNT = 7569

DESCRIPTION = (
    "Incorporated in 1890 by John D. Rockefeller and the American Baptist Education "
    "Society and opened for instruction in 1892, the University of Chicago is a private "
    "research university in the Hyde Park neighborhood of Chicago. It enrolls about 7,600 "
    "undergraduates in the College and roughly 11,000 graduate and professional students, "
    "some 19,300 in all, and is known for an intense, discussion-driven intellectual "
    "culture — the Core, the Chicago school of economics, and a faculty of 2,188 that "
    "sustains a 5-to-1 student-faculty ratio.\n\n"
    "The College awards the B.A. and B.S. across roughly fifty majors, and the university "
    "is organized into four graduate divisions (Biological Sciences, Humanities, Physical "
    "Sciences and Social Sciences) and a set of renowned professional schools — among them "
    "the Booth School of Business, the Law School, the Pritzker School of Medicine, the "
    "Harris School of Public Policy, the Crown Family School of Social Work, Policy, and "
    "Practice, the Divinity School and the Pritzker School of Molecular Engineering. Its "
    "research reaches well beyond campus through stewardship of Argonne National "
    "Laboratory and Fermilab and an affiliation with the Marine Biological Laboratory.\n\n"
    "Chicago ranks among the very best universities in the world: No. 6 among national "
    "universities by U.S. News, No. 15 in the world by Times Higher Education, and No. 13 "
    "by QS. It admits under 5% of first-year applicants, and 101 Nobel laureates have been "
    "affiliated with the university over its history.\n\n"
    "UChicago is need-blind for domestic applicants and, through its No Barriers program, "
    "meets 100% of demonstrated financial need: the average net price is about $14,900 a "
    "year, 16% of undergraduates receive Pell grants, and only 4% take federal student "
    "loans. Among the Class of 2025, 98% of graduates secured a post-college outcome — "
    "71% in employment and 29% in graduate or professional school."
)

# ── The real degree-granting schools / divisions (display order) ───────────
_COLLEGE = "The College"
_BOOTH = "University of Chicago Booth School of Business"
_SOCIAL = "Division of the Social Sciences"
_PHYSICAL = "Physical Sciences Division"
_CROWN = "Crown Family School of Social Work, Policy, and Practice"
_GRAHAM = "Graham School of Continuing Liberal and Professional Studies"

SCHOOLS: list[dict] = [
    {
        "name": _COLLEGE,
        "sort_order": 1,
        "description": (
            "The College, opened in 1892, is the University of Chicago's undergraduate "
            "school. Built around the Core — a rigorous shared curriculum in the "
            "humanities, social sciences and natural sciences — it awards the B.A. and "
            "B.S. across roughly fifty majors and is the historic heart of the "
            "university's discussion-driven intellectual culture."
        ),
    },
    {
        "name": _BOOTH,
        "sort_order": 2,
        "description": (
            "Founded in 1898, the University of Chicago Booth School of Business is the "
            "second-oldest business school in the United States and the birthplace of "
            "much of modern finance and economics. It awards the Full-Time, Evening, "
            "Weekend and Executive MBA, specialized master's degrees and the Ph.D., and "
            "is known for an evidence-based, discipline-driven approach and a famously "
            "flexible curriculum."
        ),
    },
    {
        "name": _SOCIAL,
        "sort_order": 3,
        "description": (
            "Established in 1930, the Division of the Social Sciences is home to the "
            "departments of economics, political science, sociology, anthropology, "
            "psychology and history and to the 'Chicago school' traditions across them. "
            "It awards doctoral degrees and master's degrees including the Master of Arts "
            "Program in the Social Sciences (MAPSS) and the Committee on International "
            "Relations."
        ),
    },
    {
        "name": _PHYSICAL,
        "sort_order": 4,
        "description": (
            "Established in 1930, the Physical Sciences Division spans astronomy and "
            "astrophysics, chemistry, computer science, geophysical sciences, mathematics, "
            "physics and statistics. Alongside its doctoral programs it awards "
            "professional master's degrees including the Master's Program in Computer "
            "Science (MPCS) and the M.S. in Statistics."
        ),
    },
    {
        "name": _CROWN,
        "sort_order": 5,
        "description": (
            "Tracing to 1908 and a graduate school of the university since 1920 (as the "
            "School of Social Service Administration, renamed the Crown Family School in "
            "2021), it is one of the oldest schools of social work in the country. It "
            "awards the A.M. in social work, the Master of Arts in social sector "
            "leadership, and the Ph.D."
        ),
    },
    {
        "name": _GRAHAM,
        "sort_order": 6,
        "description": (
            "The Graham School of Continuing Liberal and Professional Studies extends the "
            "university's teaching to working adults and lifelong learners. It awards the "
            "Master of Liberal Arts and a range of professional and continuing-education "
            "credentials grounded in UChicago's liberal-arts tradition."
        ),
    },
]

# Each school's official website (verified to resolve at author time).
_SCHOOL_WEBSITE: dict[str, str] = {
    _COLLEGE: "https://college.uchicago.edu/",
    _BOOTH: "https://www.chicagobooth.edu/",
    _SOCIAL: "https://socialsciences.uchicago.edu/",
    _PHYSICAL: "https://physicalsciences.uchicago.edu/",
    _CROWN: "https://crownschool.uchicago.edu/",
    _GRAHAM: "https://graham.uchicago.edu/",
}

# Rich, sourced About-tab content per unit. Deans + titles are quoted from the official
# Office of the Provost "Deans and Department Chairs" directory (verified 2026-06-10).
# Founding years come from each unit's official history. Notable-faculty rosters are not
# published uniformly per unit and are omitted rather than hand-picked (recorded in
# _ABOUT_OMITTED).
_DEAN_SOURCE = {
    "label": "University of Chicago — Office of the Provost, Deans and Department Chairs",
    "url": "https://provost.uchicago.edu/deans-and-department-chairs",
}
_ABOUT_DETAIL: dict[str, dict] = {
    _COLLEGE: {
        "founded": 1892,
        "leadership": "Melina Hale — Dean of the College",
        "research_centers": [
            "The Core (the College's signature shared curriculum)",
            "College Center for Research and Fellowships",
            "Chicago Studies program",
        ],
        "source": _DEAN_SOURCE,
    },
    _BOOTH: {
        "founded": 1898,
        "leadership": (
            "Madhav V. Rajan — Dean and George Pratt Shultz Professor of Accounting"
        ),
        "research_centers": [
            "Becker Friedman Institute for Economics",
            "Polsky Center for Entrepreneurship and Innovation",
            "Kilts Center for Marketing",
            "Fama-Miller Center for Research in Finance",
        ],
        "named_for": "David G. Booth (alumnus; 2008 naming gift)",
        "source": _DEAN_SOURCE,
    },
    _SOCIAL: {
        "founded": 1930,
        "leadership": "Amanda Woodward — Dean of the Division of the Social Sciences",
        "research_centers": [
            "NORC at the University of Chicago",
            "Pearson Institute for the Study and Resolution of Global Conflicts",
            "Center for the Study of Race, Politics, and Culture",
        ],
        "source": _DEAN_SOURCE,
    },
    _PHYSICAL: {
        "founded": 1930,
        "leadership": "Ka Yee C. Lee — Dean of the Physical Sciences Division",
        "research_centers": [
            "Enrico Fermi Institute",
            "James Franck Institute",
            "Kavli Institute for Cosmological Physics",
        ],
        "source": _DEAN_SOURCE,
    },
    _CROWN: {
        "founded": 1920,
        "leadership": (
            "Deborah Gorman-Smith — Dean and Emily Klein Gidwitz Professor"
        ),
        "named_for": "the Crown family (2021 naming gift)",
        "source": _DEAN_SOURCE,
    },
    _GRAHAM: {
        "leadership": (
            "Seth Green — Dean of the Graham School of Continuing Liberal and "
            "Professional Studies"
        ),
        "source": _DEAN_SOURCE,
    },
}

# About-detail fields omitted per unit (verified-unavailable), recorded in each unit's
# _standard.omitted. Notable-faculty rosters are omitted for every unit; Crown and the
# Graham School omit a distinct, school-owned research-center list (only affiliated or
# university-wide centers could be verified); the Graham School additionally omits a
# single canonical founding year.
_FACULTY_OMIT = ["about_detail.faculty"]
_ABOUT_OMITTED: dict[str, list[str]] = {
    _COLLEGE: list(_FACULTY_OMIT),
    _BOOTH: list(_FACULTY_OMIT),
    _SOCIAL: list(_FACULTY_OMIT),
    _PHYSICAL: list(_FACULTY_OMIT),
    _CROWN: [*_FACULTY_OMIT, "about_detail.research_centers"],
    _GRAHAM: [*_FACULTY_OMIT, "about_detail.research_centers", "about_detail.founded"],
}

# ── Channel feeds + official social links ──────────────────────────────────
# Institution-wide socials (official UChicago handles) + news page.
_INSTITUTION_CONTENT: dict = {
    "news_url": "https://news.uchicago.edu",
    "social": {
        "instagram": "https://www.instagram.com/uchicago/",
        "linkedin": "https://www.linkedin.com/school/university-of-chicago/",
        "x": "https://x.com/UChicago",
        "youtube": "https://www.youtube.com/user/uchicago",
        "facebook": "https://www.facebook.com/uchicago",
    },
}

# Booth MBA keyword-relevant feed (the flagship program), inheriting the institution
# socials (Booth surfaces its news through Chicago Booth Review and Booth News).
_MBA_CONTENT: dict = {
    "news_url": "https://www.chicagobooth.edu/review",
    "keywords": ["chicago booth", "mba", "finance", "economics", "entrepreneurship"],
    "social": {
        "instagram": "https://www.instagram.com/chicagobooth/",
        "linkedin": "https://www.linkedin.com/school/chicago-booth/",
        "x": "https://x.com/ChicagoBooth",
        "youtube": "https://www.youtube.com/user/ChicagoBooth",
        "facebook": "https://www.facebook.com/ChicagoBooth",
    },
}

# ── The program catalog (real majors/degrees, organized by unit) ───────────
# slug = idempotency key. Every program is mapped to its owning unit from UChicago's
# official structure. The program set is the College Scorecard Field-of-Study list for
# UNITID 144050 (the deterministic federal view); two federal computing CIP rows
# (11.07 / 11.02) and two statistics rows (27.05 at the bachelor's and master's level)
# map onto single named degrees and are not double-counted. Graduate degrees use the
# generic ``masters`` type with the real degree name carried in the program name.
PROGRAMS: list[dict] = [
    # ── The College (undergraduate B.A./B.S. majors) ──
    {
        "slug": "chicago-economics-bs",
        "school": _COLLEGE,
        "program_name": "Economics",
        "degree_type": "bachelors",
        "cip": "45.06",
        "duration_months": 48,
        "description": (
            "Economics — the home of the 'Chicago school', spanning price theory, "
            "econometrics, macroeconomics and applied microeconomics."
        ),
    },
    {
        "slug": "chicago-computer-science-bs",
        "school": _COLLEGE,
        "program_name": "Computer Science",
        "degree_type": "bachelors",
        "cip": "11.07",
        "duration_months": 48,
        "description": (
            "Computer science — offered as the B.A. and B.S. across algorithms, systems, "
            "machine learning, and the theory and applications of computation."
        ),
    },
    {
        "slug": "chicago-mathematics-bs",
        "school": _COLLEGE,
        "program_name": "Mathematics",
        "degree_type": "bachelors",
        "cip": "27.01",
        "duration_months": 48,
        "description": "Mathematics — analysis, algebra, geometry and number theory.",
    },
    {
        "slug": "chicago-statistics-bs",
        "school": _COLLEGE,
        "program_name": "Statistics",
        "degree_type": "bachelors",
        "cip": "27.05",
        "duration_months": 48,
        "description": (
            "Statistics — probability, statistical inference and data-driven computation."
        ),
    },
    {
        "slug": "chicago-biology-bs",
        "school": _COLLEGE,
        "program_name": "Biological Sciences",
        "degree_type": "bachelors",
        "cip": "26.01",
        "duration_months": 48,
        "description": (
            "Biological sciences — molecular, cellular and organismal biology, genetics "
            "and ecology."
        ),
    },
    {
        "slug": "chicago-political-science-bs",
        "school": _COLLEGE,
        "program_name": "Political Science",
        "degree_type": "bachelors",
        "cip": "45.10",
        "duration_months": 48,
        "description": (
            "Political science — American, comparative and international politics and "
            "political theory."
        ),
    },
    {
        "slug": "chicago-psychology-bs",
        "school": _COLLEGE,
        "program_name": "Psychology",
        "degree_type": "bachelors",
        "cip": "42.27",
        "duration_months": 48,
        "description": "Psychology — cognitive, developmental, social and biological science.",
    },
    {
        "slug": "chicago-public-policy-bs",
        "school": _COLLEGE,
        "program_name": "Public Policy Studies",
        "degree_type": "bachelors",
        "cip": "44.05",
        "duration_months": 48,
        "description": (
            "Public policy studies — an interdisciplinary major in policy analysis, "
            "economics, statistics and ethics."
        ),
    },
    {
        "slug": "chicago-chemistry-bs",
        "school": _COLLEGE,
        "program_name": "Chemistry",
        "degree_type": "bachelors",
        "cip": "40.05",
        "duration_months": 48,
        "description": "Chemistry — organic, inorganic, physical and biological chemistry.",
    },
    {
        "slug": "chicago-history-bs",
        "school": _COLLEGE,
        "program_name": "History",
        "degree_type": "bachelors",
        "cip": "54.01",
        "duration_months": 48,
        "description": "History — the study of the human past across periods and regions.",
    },
    {
        "slug": "chicago-philosophy-bs",
        "school": _COLLEGE,
        "program_name": "Philosophy",
        "degree_type": "bachelors",
        "cip": "38.01",
        "duration_months": 48,
        "description": "Philosophy — logic, ethics, metaphysics and the history of philosophy.",
    },
    {
        "slug": "chicago-neuroscience-bs",
        "school": _COLLEGE,
        "program_name": "Neuroscience",
        "degree_type": "bachelors",
        "cip": "26.15",
        "duration_months": 48,
        "description": (
            "Neuroscience — the molecular, cellular, systems and cognitive study of the "
            "brain and nervous system."
        ),
    },
    {
        "slug": "chicago-english-bs",
        "school": _COLLEGE,
        "program_name": "English Language and Literature",
        "degree_type": "bachelors",
        "cip": "23.01",
        "duration_months": 48,
        "description": "English — literature in English, criticism and creative writing.",
    },
    {
        "slug": "chicago-environmental-science-bs",
        "school": _COLLEGE,
        "program_name": "Environmental Science",
        "degree_type": "bachelors",
        "cip": "03.01",
        "duration_months": 48,
        "description": (
            "Environmental science — the natural-science study of Earth's environment, "
            "ecosystems and human impact."
        ),
    },
    # ── Booth School of Business (the flagship) ──
    {
        "slug": "chicago-mba",
        "school": _BOOTH,
        "program_name": "Full-Time MBA",
        "degree_type": "masters",
        "cip": "52.13",
        "duration_months": 21,
        "description": (
            "Chicago Booth's flagship full-time, 21-month MBA — a discipline-driven, "
            "famously flexible program with a single required course (LEAD), built on the "
            "school's strengths in finance, economics, accounting and entrepreneurship."
        ),
    },
    # ── Division of the Social Sciences ──
    {
        "slug": "chicago-mapss-ma",
        "school": _SOCIAL,
        "program_name": "Master of Arts Program in the Social Sciences (MAPSS)",
        "degree_type": "masters",
        "cip": "45.01",
        "duration_months": 12,
        "description": (
            "MAPSS — a one-year, interdisciplinary social-sciences master's with a "
            "personal preceptor, spanning economics, sociology, political science, "
            "anthropology, psychology and history."
        ),
    },
    {
        "slug": "chicago-international-relations-ma",
        "school": _SOCIAL,
        "program_name": "Master of Arts in International Relations (CIR)",
        "degree_type": "masters",
        "cip": "45.09",
        "duration_months": 12,
        "description": (
            "The Committee on International Relations — the oldest graduate program in "
            "international relations in the United States, awarding the M.A. in "
            "international relations."
        ),
    },
    # ── Physical Sciences Division ──
    {
        "slug": "chicago-computer-science-ms",
        "school": _PHYSICAL,
        "program_name": "Master's Program in Computer Science (MPCS)",
        "degree_type": "masters",
        "cip": "11.07",
        "duration_months": 12,
        "description": (
            "The Master's Program in Computer Science — a professional, project-oriented "
            "M.S. with specializations in software engineering, data analytics, "
            "high-performance computing and application development."
        ),
    },
    {
        "slug": "chicago-statistics-ms",
        "school": _PHYSICAL,
        "program_name": "Master of Science in Statistics",
        "degree_type": "masters",
        "cip": "27.05",
        "duration_months": 12,
        "description": (
            "The M.S. in Statistics — graduate training in statistical theory, "
            "computation and applied data analysis."
        ),
    },
    # ── Crown Family School of Social Work, Policy, and Practice ──
    {
        "slug": "chicago-social-work-am",
        "school": _CROWN,
        "program_name": "Master of Arts (A.M.) in Social Work",
        "degree_type": "masters",
        "cip": "44.07",
        "duration_months": 24,
        "description": (
            "The two-year A.M. in social work — clinical and social-administration "
            "training that combines coursework with supervised field placements."
        ),
    },
    # ── Graham School of Continuing Liberal and Professional Studies ──
    {
        "slug": "chicago-liberal-arts-mla",
        "school": _GRAHAM,
        "program_name": "Master of Liberal Arts (MLA)",
        "degree_type": "masters",
        "cip": "24.01",
        "duration_months": 12,
        "description": (
            "The Master of Liberal Arts — an interdisciplinary graduate degree in the "
            "liberal arts for working adults and lifelong learners."
        ),
    },
]

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

# Full official program names (program-page title); equal to the program name here.
_FULL_NAME_BY_SLUG: dict[str, str] = {p["slug"]: p["program_name"] for p in PROGRAMS}

# Official program/department/school home pages.
_WEBSITE_BY_SLUG: dict[str, str] = {
    "chicago-economics-bs": "http://collegecatalog.uchicago.edu/thecollege/economics/",
    "chicago-computer-science-bs": "https://cs.uchicago.edu/academics/undergraduate/",
    "chicago-mathematics-bs": "http://collegecatalog.uchicago.edu/thecollege/mathematics/",
    "chicago-statistics-bs": "http://collegecatalog.uchicago.edu/thecollege/statistics/",
    "chicago-biology-bs": "http://collegecatalog.uchicago.edu/thecollege/biologicalsciences/",
    "chicago-political-science-bs": (
        "http://collegecatalog.uchicago.edu/thecollege/politicalscience/"
    ),
    "chicago-psychology-bs": "http://collegecatalog.uchicago.edu/thecollege/psychology/",
    "chicago-public-policy-bs": (
        "http://collegecatalog.uchicago.edu/thecollege/publicpolicystudies/"
    ),
    "chicago-chemistry-bs": "http://collegecatalog.uchicago.edu/thecollege/chemistry/",
    "chicago-history-bs": "http://collegecatalog.uchicago.edu/thecollege/history/",
    "chicago-philosophy-bs": "http://collegecatalog.uchicago.edu/thecollege/philosophy/",
    "chicago-neuroscience-bs": "http://collegecatalog.uchicago.edu/thecollege/neuroscience/",
    "chicago-english-bs": (
        "http://collegecatalog.uchicago.edu/thecollege/englishlanguageandliterature/"
    ),
    "chicago-environmental-science-bs": (
        "http://collegecatalog.uchicago.edu/thecollege/environmentalscience/"
    ),
    "chicago-mba": "https://www.chicagobooth.edu/programs/full-time",
    "chicago-mapss-ma": "https://mapss.uchicago.edu/",
    "chicago-international-relations-ma": "https://cir.uchicago.edu/",
    "chicago-computer-science-ms": "https://masters.cs.uchicago.edu/",
    "chicago-statistics-ms": "https://stat.uchicago.edu/",
    "chicago-social-work-am": "https://crownschool.uchicago.edu/academic-programs/am-program",
    "chicago-liberal-arts-mla": (
        "https://graham.uchicago.edu/credit-programs/master-of-liberal-arts"
    ),
}

# ── Who-it's-for + highlights (catalog baselines) ──────────────────────────
_WHO_BASELINE = (
    "Intellectually ambitious students who want a rigorous, discussion-driven education "
    "anchored by the Core, with full-need financial aid and the depth of a major research "
    "university."
)
_HL_BASELINE = ["The Core curriculum", "5:1 student-faculty ratio", "Need-met financial aid"]
_WHO_GRAD_BASELINE = (
    "Graduate and professional students seeking a rigorous UChicago degree with the "
    "resources of a major research university and an internationally recognized faculty."
)
_HL_GRAD_BASELINE = [
    "Top-ranked UChicago graduate degree",
    "World-class faculty",
    "Hyde Park, Chicago",
]

_WHO_BY_SLUG = {
    "chicago-mba": (
        "Aspiring leaders who want an analytical, discipline-driven MBA with an unusually "
        "flexible curriculum and deep strength in finance, economics and entrepreneurship."
    ),
    "chicago-economics-bs": (
        "Students drawn to rigorous economic theory and empirical analysis at the home of "
        "the Chicago school of economics."
    ),
}
_HL_BY_SLUG = {
    "chicago-mba": [
        "Flexible curriculum (one required course)",
        "Top-ranked U.S. MBA",
        "Finance, economics & entrepreneurship",
    ],
    "chicago-economics-bs": [
        "Home of the Chicago school",
        "Price theory & econometrics",
        "Strong finance & consulting placement",
    ],
}

# ── Curriculum / concentrations, where published (the flagship) ────────────
# Booth publishes 13 functional concentrations; quoted from the official Full-Time MBA
# curriculum/academics pages.
_TRACKS_BY_SLUG: dict[str, dict] = {
    "chicago-mba": {
        "label": "Booth MBA concentrations",
        "note": (
            "Booth's curriculum is famously flexible: a single required course (LEAD) "
            "and a set of foundational requirements, after which students build their own "
            "path and can earn any number of the school's functional concentrations."
        ),
        "items": [
            {"name": "Accounting"},
            {"name": "Analytic Finance"},
            {"name": "Behavioral Science"},
            {"name": "Business Analytics"},
            {"name": "Econometrics & Statistics"},
            {"name": "Economics"},
            {"name": "Entrepreneurship"},
            {"name": "Finance"},
            {"name": "General Management"},
            {"name": "International Business"},
            {"name": "Marketing Management"},
            {"name": "Operations Management"},
            {"name": "Strategic Management"},
        ],
        "source": "Chicago Booth — Full-Time MBA Academics & Curriculum",
        "source_url": "https://www.chicagobooth.edu/mba/full-time/academics",
    },
}

# ── Program-specific cost ──────────────────────────────────────────────────
# The College undergraduate cost: tuition is the official 2025-26 Bursar figure; cost of
# attendance and average net price are College Scorecard (UNITID 144050).
_TUITION_UG = 73266
_UNDERGRAD_COA = 90360
_AVG_NET_PRICE = 14860

# Per-program graduate cost. Where the program-specific tuition is published only on the
# JavaScript-rendered Bursar pages and could not be verified from a static first-party
# source, the tuition figure is OMITTED (recorded in the program's _standard.omitted) and
# only the source pointer is kept. The four divisional master's (MAPSS, International
# Relations, M.S. Statistics, Master of Liberal Arts) are in that omitted state.
_COST_BY_SLUG: dict[str, dict] = {
    "chicago-mba": {
        "tuition_usd": 89976,
        "total_cost_of_attendance": 132449,
        "funded": False,
        "breakdown": {
            "tuition": 89976,
            "total_cost_of_attendance": 132449,
        },
        "note": (
            "Full-Time MBA first-year tuition for 2026-27 (Class of 2028); the estimated "
            "nine-month single-student cost of attendance is shown as total cost."
        ),
        "source": "Chicago Booth — Full-Time MBA Cost (2026-27)",
        "source_url": "https://www.chicagobooth.edu/mba/full-time/admissions/cost",
        "year": "2026-27",
    },
    "chicago-computer-science-ms": {
        "tuition_usd": 66762,
        "funded": False,
        "breakdown": {"tuition": 66762},
        "note": (
            "Estimated total tuition for the nine-course M.S. in Computer Science at "
            "$7,415 per course (2026-27 rate)."
        ),
        "source": "University of Chicago — Masters Program in Computer Science, Tuition & Fees",
        "source_url": "https://masters.cs.uchicago.edu/mpcs-admissions/tuition-fees/",
        "year": "2026-27",
    },
    "chicago-social-work-am": {
        "tuition_usd": 53721,
        "total_cost_of_attendance": 91041,
        "funded": False,
        "breakdown": {
            "tuition": 53721,
            "total_cost_of_attendance": 91041,
        },
        "note": (
            "Full-time A.M. tuition for the 2025-26 academic year; the estimated total "
            "student budget is shown as total cost. 95% of master's students receive "
            "scholarship aid."
        ),
        "source": "University of Chicago — Crown Family School, Tuition, Fees & Financial Aid",
        "source_url": "https://crownschool.uchicago.edu/admissions/tuition-fees-financial-aid",
        "year": "2025-26",
    },
    # Divisional master's — tuition omitted (Bursar pages are JavaScript-rendered; the
    # exact figure could not be verified from a static first-party source). Source pointer
    # retained so the costs section is present and the omission is honestly recorded.
    "chicago-mapss-ma": {
        "funded": False,
        "note": (
            "Tuition is set on the Office of the Bursar's Social Sciences Division page; "
            "the exact 2025-26 figure could not be verified from a static source and is "
            "omitted rather than estimated."
        ),
        "source": "University of Chicago — Office of the Bursar (Social Sciences Division)",
        "source_url": (
            "https://bursar.uchicago.edu/tuition-and-fees/tuition-and-fees-2025-26/"
            "tuition-and-fees-2025-26-social-sciences-division"
        ),
    },
    "chicago-international-relations-ma": {
        "funded": False,
        "note": (
            "Tuition is set on the Office of the Bursar's Social Sciences Division page; "
            "the exact 2025-26 figure could not be verified from a static source and is "
            "omitted rather than estimated."
        ),
        "source": "University of Chicago — Office of the Bursar (Social Sciences Division)",
        "source_url": (
            "https://bursar.uchicago.edu/tuition-and-fees/tuition-and-fees-2025-26/"
            "tuition-and-fees-2025-26-social-sciences-division"
        ),
    },
    "chicago-statistics-ms": {
        "funded": False,
        "note": (
            "Tuition is set on the Office of the Bursar's Physical Sciences Division page; "
            "the exact 2025-26 figure could not be verified from a static source and is "
            "omitted rather than estimated."
        ),
        "source": "University of Chicago — Office of the Bursar (Physical Sciences Division)",
        "source_url": (
            "https://bursar.uchicago.edu/tuition-and-fees/tuition-and-fees-2025-26/"
            "tuition-and-fees-2025-26-physical-sciences-division"
        ),
    },
    "chicago-liberal-arts-mla": {
        "funded": False,
        "note": (
            "Tuition is set on the Graham School / Office of the Bursar pages; the exact "
            "2025-26 figure could not be verified from a static source and is omitted "
            "rather than estimated."
        ),
        "source": "University of Chicago — Graham School, Master of Liberal Arts",
        "source_url": "https://graham.uchicago.edu/credit-programs/master-of-liberal-arts",
    },
}

# Programs whose program tuition is omitted (recorded per program in _standard.omitted).
_TUITION_OMITTED_SLUGS = {
    slug
    for slug, cost in _COST_BY_SLUG.items()
    if cost.get("tuition_usd") is None
}

# ── Program-specific outcomes (College Scorecard Field of Study, by CIP) ────
# Where the federal College Scorecard publishes a Field-of-Study median earnings (one
# year after completion) for an awarded CIP + credential level at UNITID 144050, we use it
# (program scope). Programs whose CIP earnings are suppressed fall back to the institution
# 10-year median. The Booth MBA (flagship) instead carries its own published employment
# distribution (below) and is not in this table. Tuples are (median_earnings_1yr, cip).
_FOS_OUTCOMES: dict[str, tuple[int, str]] = {
    "chicago-economics-bs": (92075, "45.06"),
    "chicago-computer-science-bs": (117578, "11.07"),
    "chicago-mathematics-bs": (100421, "27.01"),
    "chicago-statistics-bs": (82681, "27.05"),
    "chicago-biology-bs": (35275, "26.01"),
    "chicago-political-science-bs": (56022, "45.10"),
    "chicago-psychology-bs": (31986, "42.27"),
    "chicago-public-policy-bs": (60057, "44.05"),
    "chicago-history-bs": (46616, "54.01"),
    "chicago-neuroscience-bs": (37246, "26.15"),
    "chicago-english-bs": (44397, "23.01"),
    "chicago-mapss-ma": (53788, "45.01"),
    "chicago-international-relations-ma": (66182, "45.09"),
    "chicago-computer-science-ms": (135918, "11.07"),
    "chicago-statistics-ms": (115925, "27.05"),
    "chicago-social-work-am": (52551, "44.07"),
    "chicago-liberal-arts-mla": (26094, "24.01"),
}

# Verbatim methodology for the program-scope Scorecard FOS earnings figure.
_FOS_CONDITIONS = (
    "Median earnings of graduates who received federal financial aid, measured "
    "approximately one year after program completion; reported by the U.S. Department of "
    "Education College Scorecard Field of Study by 4-digit CIP code and credential level. "
    "Programs with too few completers are suppressed."
)

# Institution-wide outcomes fallback (College Scorecard, UNITID 144050), used for degree
# programs whose program-level one-year earnings are suppressed (Chemistry, Philosophy,
# Environmental Science).
_OUTCOMES_INSTITUTION = {
    "median_salary": 91885,
    "scope": "institution",
    "conditions": (
        "UChicago institution-wide median earnings ten years after entry (College "
        "Scorecard, UNITID 144050); a program-level one-year earnings figure is not "
        "published (suppressed) for this field of study."
    ),
    "source": "U.S. Dept. of Education College Scorecard (UNITID 144050)",
    "source_url": "https://collegescorecard.ed.gov/school/?144050-University-of-Chicago",
}

# ── The flagship: Booth Full-Time MBA employment distribution ──────────────
# Chicago Booth Full-Time MBA Employment Report, Class of 2025 (the official 2024-2025
# Employment Statistics workbook). Percentages and counts are quoted from that report.
_MBA_OUTCOMES = {
    "median_salary": 175000,
    "median_signing_bonus": 30000,
    "employment_rate": 0.878,
    "employment_timeframe": "accepted an offer within 3 months of graduation",
    "class_size": 663,
    "scope": "program",
    "cip": "52.13",
    "top_industries": [
        "Consulting — 36.7%",
        "Technology — 14.1%",
        "Diversified financial services — 9.0%",
        "Investment banking/brokerage — 8.3%",
        "Investment management/research — 5.3%",
        "Private equity — 5.3%",
    ],
    "top_employers": [
        "Boston Consulting Group (52 hires)",
        "McKinsey & Company (35)",
        "Bain & Company (30)",
        "Amazon (20)",
        "Goldman Sachs (11)",
        "JPMorgan Chase (11)",
    ],
    "conditions": [
        "Chicago Booth Full-Time MBA Employment Report, Class of 2025 (graduates of "
        "Aug. 2024, Dec. 2024, Mar. 2025 and Jun. 2025).",
        "Of 534 graduates seeking employment, 89.1% received and 87.8% accepted a "
        "full-time offer within three months of graduation.",
        "Median base salary and median sign-on bonus are across all reported accepted "
        "offers (n=469); compensation is self-reported and 90% of reporting graduates "
        "included salary; 65% of accepted offers reported a sign-on bonus.",
        "Base salary range across accepted offers: $70,000 minimum to $400,000 maximum.",
    ],
    "source": "Chicago Booth Full-Time MBA Employment Report, Class of 2025",
    "source_url": "https://www.chicagobooth.edu/employmentreport",
}


def _outcomes_for(slug: str) -> dict:
    """The outcomes_data payload (without _standard) for a program slug.

    Precedence: Booth MBA flagship distribution → Scorecard FOS (program) → institution
    median fallback. Used by both ``apply()`` and the conformance test (DRY).
    """
    if slug == "chicago-mba":
        return dict(_MBA_OUTCOMES)
    fos = _FOS_OUTCOMES.get(slug)
    if fos is not None:
        salary, cip = fos
        return {
            "median_salary": salary,
            "scope": "program",
            "cip": cip,
            "earnings_timeframe": "median earnings 1 year after completion",
            "conditions": _FOS_CONDITIONS,
            "source": "U.S. Dept. of Education College Scorecard — Field of Study",
            "source_url": (
                "https://collegescorecard.ed.gov/school/?144050-University-of-Chicago"
            ),
        }
    return dict(_OUTCOMES_INSTITUTION)


# ── Class profile, where published (the flagship) ──────────────────────────
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {
    "chicago-mba": {
        "cohort_size": "663 graduates (Full-Time MBA, Class of 2025)",
        "international_pct": 36,
        "note": (
            "Class of 2025: 663 graduating Full-Time MBA students; 42% women and 36% "
            "international; mean age 28 with a mean of five years of work experience "
            "(demographics based on the cohort matriculating September 2023)."
        ),
        "source": "Chicago Booth Full-Time MBA Employment Report, Class of 2025",
        "source_url": "https://www.chicagobooth.edu/employmentreport",
    },
}

# ── Faculty (lead + directory link), where confidently sourced (the flagship) ──
_FACULTY_BY_SLUG: dict[str, dict] = {
    "chicago-mba": {
        "lead": [
            {
                "name": "Eugene F. Fama",
                "title": (
                    "Robert R. McCormick Distinguished Service Professor of Finance; "
                    "2013 Nobel laureate in Economic Sciences"
                ),
            },
            {
                "name": "Douglas W. Diamond",
                "title": (
                    "Merton H. Miller Distinguished Service Professor of Finance; "
                    "2022 Nobel laureate in Economic Sciences"
                ),
            },
        ],
        "note": (
            "Booth's finance faculty includes multiple Nobel laureates — among them "
            "Eugene Fama (2013) and Douglas Diamond (2022)."
        ),
        "directory_url": "https://www.chicagobooth.edu/faculty/directory",
    },
}

# ── Aggregated, cited student-review themes (≥2 third-party sources, the flagship) ──
_REVIEWS_BY_SLUG: dict[str, dict] = {
    "chicago-mba": {
        "summary": (
            "Students and third-party guides describe Chicago Booth as analytically "
            "rigorous and discipline-driven, with an unusually flexible curriculum that "
            "lets students tailor their path, world-class finance and economics faculty, "
            "and strong placement into consulting and finance. Booth is consistently "
            "ranked among the very top U.S. MBA programs. Common cautions are that the "
            "quantitative rigor is demanding and that the flexible, build-your-own "
            "structure rewards self-direction over a fixed cohort experience."
        ),
        "themes": [
            {
                "label": "Flexible, build-your-own curriculum",
                "sentiment": "positive",
                "detail": "A single required course lets students design their own MBA.",
            },
            {
                "label": "Analytical & finance strength",
                "sentiment": "positive",
                "detail": "Deep, evidence-based teaching in finance, economics and analytics.",
            },
            {
                "label": "Consulting & finance placement",
                "sentiment": "positive",
                "detail": "Strong recruiting into top consulting firms and financial services.",
            },
            {
                "label": "Quantitative rigor",
                "sentiment": "caution",
                "detail": "The data-driven curriculum is demanding and quant-heavy.",
            },
            {
                "label": "Self-directed structure",
                "sentiment": "caution",
                "detail": "Flexibility rewards students who drive their own experience.",
            },
        ],
        "sources": [
            {
                "label": "Poets&Quants — University of Chicago (Booth)",
                "url": "https://poetsandquants.com/school/university-of-chicago-booth-school-of-business/",
            },
            {
                "label": "U.S. News — Booth School of Business (Best Business Schools)",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/university-of-chicago-01207",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not individual "
            "verbatim reviews."
        ),
    },
}

# ── Application requirements ─────────────────────────────────────────────────
_INTL_VISA = {
    "types": ["F-1", "J-1"],
    "note": "International students are issued an I-20 (F-1) or DS-2019 (J-1) after admission.",
}
# Undergraduate (the College) admission via the Common Application or Coalition (Scoir).
# UChicago is test-optional: SAT/ACT scores are not required but are considered if
# submitted (CDS 2024-25 item C8).
_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Common Application or Coalition Application (Scoir)", "required": True},
        {"name": "UChicago Supplement (the 'uncommon' essays)", "required": True},
        {"name": "Secondary-school transcript / school report", "required": True},
        {"name": "Counselor recommendation", "required": True},
        {"name": "Two teacher recommendations", "required": True},
        {"name": "$75 application fee; need-based fee waivers available", "required": True},
        {
            "name": "Standardized test scores (optional)",
            "required": False,
            "note": (
                "UChicago is test-optional: SAT/ACT scores are not required for "
                "admission but are considered if submitted."
            ),
        },
    ],
    "deadlines": [
        {"round": "Early Action / Early Decision I", "date": "November 1"},
        {"round": "Early Decision II / Regular Decision", "date": "January 2"},
    ],
    "recommendations": {
        "required": 3,
        "note": "Two teacher recommendations plus a counselor recommendation.",
    },
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "Duolingo English Test"],
            "required": False,
            "note": "English-proficiency proof may be required for non-native speakers.",
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "UChicago College Admissions — How to Apply",
                "url": "https://collegeadmissions.uchicago.edu/apply",
            }
        ],
    },
    "source": "University of Chicago College Admissions",
    "source_url": "https://collegeadmissions.uchicago.edu/apply/first-year-applicants",
}

# Graduate (Booth Full-Time MBA) admission via the Booth application.
_REQ_MBA = {
    "materials": [
        {"name": "Chicago Booth online application", "required": True},
        {"name": "Two written essays + a short-answer set", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Two letters of recommendation", "required": True},
        {"name": "Résumé", "required": True},
        {
            "name": "GMAT or GRE scores",
            "required": True,
            "note": "GMAT or GRE accepted; a test waiver may be requested in some cases.",
        },
        {"name": "Interview (by invitation)", "required": False},
        {"name": "$250 application fee", "required": True},
    ],
    "deadlines": [
        {"round": "Round 1", "date": "Late September"},
        {"round": "Round 2", "date": "Early January"},
        {"round": "Round 3", "date": "Early April"},
    ],
    "recommendations": {
        "required": 2,
        "note": "Two professional recommendations submitted through the Booth application.",
    },
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "PTE"],
            "required": False,
            "note": (
                "An English-proficiency test may be required for applicants whose native "
                "language is not English."
            ),
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "Chicago Booth — Full-Time MBA Admissions",
                "url": "https://www.chicagobooth.edu/mba/full-time/admissions",
            }
        ],
    },
    "source": "Chicago Booth — Full-Time MBA Admissions",
    "source_url": "https://www.chicagobooth.edu/mba/full-time/admissions",
}

# Generic UChicago graduate / professional admission set. Each division and professional
# school administers its own admissions; the materials below are common across UChicago
# graduate programs, and deadlines vary by program (commonly winter) — applicants are
# pointed to the program's own admissions page via the program website.
_REQ_GRAD_GENERIC = {
    "materials": [
        {"name": "Program online application", "required": True},
        {"name": "Transcripts from all post-secondary institutions", "required": True},
        {"name": "Statement of purpose / personal statement", "required": True},
        {"name": "Résumé / CV", "required": True},
        {
            "name": "Letters of recommendation",
            "required": True,
            "note": "Most UChicago graduate programs require two to three letters.",
        },
        {
            "name": "Standardized test scores (GRE)",
            "required": False,
            "note": "Test requirements vary by program (required, optional or not accepted).",
        },
    ],
    "deadlines": [
        {"round": "Application deadline", "date": "Varies by program — see the program page"},
    ],
    "recommendations": {
        "required": 3,
        "note": (
            "Most UChicago graduate programs require three letters of recommendation "
            "(some require two)."
        ),
    },
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS"],
            "required": True,
            "note": (
                "Required for applicants whose native language is not English; an "
                "exemption applies to degrees earned where English is the language of "
                "instruction."
            ),
        },
        "visa": _INTL_VISA,
        "sources": [
            {
                "label": "UChicago Graduate Admissions",
                "url": "https://grad.uchicago.edu/admissions/",
            }
        ],
    },
    "source": "University of Chicago graduate & professional admissions",
    "source_url": "https://grad.uchicago.edu/admissions/",
}


def _requirements_for(spec: dict) -> dict:
    """Pick the admissions requirement set for a program by slug / degree type."""
    if spec["slug"] == "chicago-mba":
        return dict(_REQ_MBA)
    if spec["degree_type"] == "masters":
        return dict(_REQ_GRAD_GENERIC)
    return dict(_REQ_UNDERGRAD)


# Real University of Chicago campus photo (aerial of the Hyde Park campus with the city
# skyline beyond) — Wikimedia Commons, hotlinkable landscape JPG (verified HTTP 200).
# Leads the institution hero.
_CAMPUS_PHOTO = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/"
    "Alex_MacLean_2005_campus_with_cityscape.jpg/"
    "1920px-Alex_MacLean_2005_campus_with_cityscape.jpg"
)


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich UChicago to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when UChicago is absent — safe on fresh/CI databases.
    """
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    # Shallow-merge JSONB: every sub-object we provide is complete.
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
    # Drop any stale value for a path we explicitly declare omitted, so the merge can't
    # keep serving a figure the enrichment run refused to assert.
    for _path in _OMITTED_INSTITUTION:
        if _path.startswith("school_outcomes."):
            rest = _path.split(".", 1)[1]
            if "." not in rest:
                school_outcomes.pop(rest, None)
            else:
                head, leaf = rest.split(".", 1)
                if isinstance(school_outcomes.get(head), dict):
                    school_outcomes[head].pop(leaf, None)
    school_outcomes["_standard"] = _standard(_OMITTED_INSTITUTION)
    inst.school_outcomes = school_outcomes
    inst.description_text = DESCRIPTION
    inst.student_body_size = UNDERGRAD_COUNT
    inst.founded_year = 1890
    inst.campus_setting = "urban"
    if not inst.website_url:
        inst.website_url = "https://www.uchicago.edu"
    # Lead the gallery with a real campus photo (dedupe + prepend; idempotent).
    _gallery = [u for u in (inst.media_gallery or []) if u != _CAMPUS_PHOTO]
    inst.media_gallery = [_CAMPUS_PHOTO, *_gallery]
    inst.content_sources = _INSTITUTION_CONTENT
    session.flush()
    school_by_name = _apply_schools(session, inst)
    _apply_programs(session, inst, school_by_name)
    session.flush()
    return True


def _apply_schools(session: Session, inst: Institution) -> dict[str, School]:
    existing = {
        s.name: s for s in session.scalars(select(School).where(School.institution_id == inst.id))
    }
    canonical_names = {s["name"] for s in SCHOOLS}
    by_name: dict[str, School] = {}
    for spec in SCHOOLS:
        sc = existing.get(spec["name"])
        if sc is None:
            sc = School(institution_id=inst.id, name=spec["name"])
            session.add(sc)
        sc.description_text = spec["description"]
        sc.sort_order = spec["sort_order"]
        sc.catalog_source = "curated"
        sc.website_url = _SCHOOL_WEBSITE.get(spec["name"])
        about = _ABOUT_DETAIL.get(spec["name"])
        if about is not None:
            about = dict(about)
            about["_standard"] = _standard(_ABOUT_OMITTED.get(spec["name"], []))
            sc.about_detail = about
        # No unit carries its own keyword-relevant feed (only the flagship program does);
        # always assign None so a stale value on a pre-existing row is cleared.
        sc.content_sources = None
        by_name[spec["name"]] = sc
    # Drop legacy schools — programs.school_id is ON DELETE SET NULL, so this is FK-safe.
    for name, sc in existing.items():
        if name not in canonical_names:
            session.delete(sc)
    session.flush()
    return by_name


def _program_has_dependents(session: Session, program_id) -> bool:
    """True if any FK in the schema references this programs row (delete unsafe)."""
    fks = session.execute(
        text("""
        SELECT tc.table_name, kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
         AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
          ON tc.constraint_name = ccu.constraint_name
         AND tc.table_schema = ccu.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND ccu.table_name = 'programs'
          AND ccu.column_name = 'id'
          AND tc.table_name <> 'programs'
        """)
    ).fetchall()
    for table, col in fks:
        hit = session.execute(
            text(f'SELECT 1 FROM "{table}" WHERE "{col}" = :pid LIMIT 1'),
            {"pid": program_id},
        ).first()
        if hit:
            return True
    return False


def _program_standard(slug: str) -> dict:
    """Per-program omitted-field list (verified-unavailable), for _standard."""
    omitted: list[str] = []
    # Only the Booth MBA flagship carries a per-program employment rate and industry
    # breakdown. Every other program reports a program-scope median earnings (Scorecard
    # FOS) and honestly omits the program-level employment rate and top industries.
    if slug != "chicago-mba":
        omitted += [
            "outcomes_data.employment_rate",
            "outcomes_data.top_industries",
        ]
    if slug not in _TRACKS_BY_SLUG:
        omitted.append("tracks")
    if slug not in _CLASS_PROFILE_BY_SLUG:
        omitted.append("class_profile.cohort_size")
    if slug not in _FACULTY_BY_SLUG:
        omitted.append("faculty_contacts.lead")
    if slug not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    if slug != "chicago-mba":
        # Only the flagship carries its own keyword-relevant feed; catalog programs
        # surface the institution feed rather than a per-program one.
        omitted.append("content_sources")
    if slug in _TUITION_OMITTED_SLUGS:
        # Divisional master's whose program tuition is published only on the
        # JavaScript-rendered Bursar pages (omitted rather than guessed).
        omitted.append("cost_data.tuition_usd")
    return _standard(omitted)


def _apply_programs(session: Session, inst: Institution, school_by_name: dict[str, School]) -> None:
    existing = {
        p.slug: p
        for p in session.scalars(select(Program).where(Program.institution_id == inst.id))
        if p.slug
    }
    canonical = set(PROGRAM_SLUGS)
    for spec in PROGRAMS:
        slug = spec["slug"]
        p = existing.get(slug)
        if p is None:
            p = Program(
                institution_id=inst.id,
                program_name=spec["program_name"],
                degree_type=spec["degree_type"],
                slug=slug,
            )
            session.add(p)
        p.program_name = _FULL_NAME_BY_SLUG.get(slug) or spec["program_name"]
        p.degree_type = spec["degree_type"]
        p.duration_months = spec.get("duration_months")
        p.description_text = spec["description"]
        # Website: verified program/department page where available, else the owning
        # unit's site.
        p.website_url = _WEBSITE_BY_SLUG.get(slug) or _SCHOOL_WEBSITE.get(spec["school"])
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec.get("delivery_format", "in_person")
        # Only the flagship carries its own feed (content_sources omitted for the rest).
        p.content_sources = _MBA_CONTENT if slug == "chicago-mba" else None
        # Cost: graduate programs use verified per-program cost where available;
        # undergraduate uses the published College rates.
        cost_override = _COST_BY_SLUG.get(slug)
        if cost_override is not None:
            p.tuition = cost_override.get("tuition_usd")
            p.cost_data = dict(cost_override)
        else:
            p.tuition = _TUITION_UG
            p.cost_data = {
                "tuition_usd": _TUITION_UG,
                "total_cost_of_attendance": _UNDERGRAD_COA,
                "avg_net_price": _AVG_NET_PRICE,
                "breakdown": {
                    "tuition": _TUITION_UG,
                    "total_cost_of_attendance": _UNDERGRAD_COA,
                },
                "funded": False,
                "note": (
                    "Published 2025-26 College tuition with the College Scorecard cost of "
                    "attendance and average net price. UChicago is need-blind for domestic "
                    "applicants and, through its No Barriers program, meets 100% of "
                    "demonstrated need, so most families pay far less than the sticker "
                    "price (average net price ≈ $14,900)."
                ),
                "source": (
                    "UChicago Office of the Bursar (2025-26) + College Scorecard (UNITID 144050)"
                ),
                "source_url": "https://collegescorecard.ed.gov/school/?144050-University-of-Chicago",
                "year": "2025-26",
            }
        # Admissions: undergraduate, MBA or generic graduate set by slug / degree type.
        p.application_requirements = _requirements_for(spec)
        # Outcomes precedence: Booth flagship → Scorecard FOS (program) → institution median.
        outcomes = _outcomes_for(slug)
        outcomes["_standard"] = _program_standard(slug)
        p.outcomes_data = outcomes
        if spec["degree_type"] == "masters":
            p.who_its_for = _WHO_BY_SLUG.get(slug) or _WHO_GRAD_BASELINE
            p.highlights = _HL_BY_SLUG.get(slug) or _HL_GRAD_BASELINE
        else:
            p.who_its_for = _WHO_BY_SLUG.get(slug) or _WHO_BASELINE
            p.highlights = _HL_BY_SLUG.get(slug) or _HL_BASELINE
        # Always assign so a stale value on a pre-existing row is cleared (tracks is
        # recorded as omitted where unverified, and match_service reads program.tracks).
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        # Application deadline (upcoming undergraduate Regular Decision closes Jan 2).
        p.application_deadline = (
            None if spec["degree_type"] == "masters" and slug != "chicago-mba"
            else date(2026, 1, 6) if slug == "chicago-mba"
            else date(2027, 1, 2)
        )
    session.flush()
    # Reconcile legacy UChicago programs (slug not in the canonical set): delete when
    # unreferenced, otherwise unpublish so the catalog stays clean without breaking any
    # application/match rows that point at them.
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
