"""Canonical Northwestern University profile — the single source of truth.

Real, sourced data only (U.S. Dept. of Education College Scorecard, UNITID 147767 ·
NCES College Navigator / IPEDS · Northwestern's Common Data Set 2024-25 from the Office
of Institutional Research · Northwestern Career Advancement "Beyond Northwestern, Class
of 2024" first-destination survey · the FY2025 Annual Financial Update (endowment) · the
official QS / Times Higher Education / U.S. News rankings · each school's official
leadership / about page and the Northwestern catalog). ``apply(session)`` idempotently
enriches the Northwestern institution row, upserts its real degree-granting schools, and
builds Northwestern's program catalog across them.

Northwestern's academic structure: six schools that admit undergraduates (Weinberg
College of Arts and Sciences, the McCormick School of Engineering and Applied Science,
the Medill School of Journalism, the Bienen School of Music, the School of Communication
and the School of Education and Social Policy), the dean-led professional schools
(Kellogg School of Management, Northwestern Pritzker School of Law, Feinberg School of
Medicine), The Graduate School (TGS), and the School of Professional Studies (SPS, which
carries Northwestern's online / part-time degree programs). The institution row was
already enriched at the report-card + rankings + research/campus-life level by the
``instenrich1`` migration; this module deepens it to gold and adds the whole school +
program tree.

It **flushes but does not commit** — the caller (the Alembic data migration, the CLI
script, or the dev seed) owns the transaction. It is a **no-op** (returns ``False``)
when Northwestern is absent, so it is safe to run against a fresh or CI database.
Re-running is safe: schools key off ``(institution_id, name)`` and programs off ``slug``;
stale rows are reconciled without breaking foreign keys.

This mirrors ``mit_profile`` / ``yale_profile`` so the migration, the standalone script,
and the dev seed all agree (DRY). Every figure traces to a public, citable source;
anything that could not be verified from a first-party or two-independent-source basis is
**omitted** (recorded in the relevant ``_standard.omitted`` list), never guessed. Computer
Science (the McCormick B.S.) is the most-enriched flagship program, mirroring MIT Sloan's
MBAn in the reference instance.
"""
# ruff: noqa: E501

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Northwestern University"

# Date this profile was researched + verified; stamped into every node's _standard.
ENRICHED_AT = "2026-06-11"


def _standard(omitted: list[str] | None = None) -> dict:
    """The per-node provenance stamp the routine writes onto every enriched node."""
    return {
        "version": STANDARD_VERSION,
        "enriched_at": ENRICHED_AT,
        "omitted": omitted or [],
    }


# Institution-level fields that could NOT be verified from a citable source and are
# therefore honestly omitted rather than guessed.
_OMITTED_INSTITUTION: list[str] = [
    # Northwestern does not publish a single canonical headline Nobel-laureate count on an
    # official page; aggregate third-party counts vary by counting method, so the figure is
    # omitted rather than asserting a number Northwestern itself does not state.
    "school_outcomes.flagship.nobel_laureates",
]

# ── Institution-level data ────────────────────────────────────────────────
# Rankings mirror what the live ``instenrich1`` migration already set (ownership + Carnegie
# + accreditor + cited QS/THE/U.S. News 2026). Re-declared here so this module is the single
# source of truth; the shallow-merge is a no-op against the already-correct row.
RANKING_DATA: dict = {
    "ownership_type": "private",
    "accreditor": "Higher Learning Commission (HLC)",
    "carnegie_classification": "Research 1: Very High Research Spending and Doctorate Production",
    # QS World University Rankings 2026: Northwestern #42 worldwide.
    "qs_world_university_rankings": {
        "rank": 42,
        "year": 2026,
        "source_url": "https://www.topuniversities.com/universities/northwestern-university",
    },
    # THE World University Rankings 2026: #30 in the world.
    "times_higher_education": {
        "rank": 30,
        "year": 2026,
        "source_url": "https://www.timeshighereducation.com/world-university-rankings/northwestern-university",
    },
    # U.S. News Best Colleges (National Universities) 2026: #6 nationally (tied).
    "us_news_national": {
        "rank": 6,
        "year": 2026,
        "source_url": "https://www.usnews.com/best-colleges/northwestern-university-1739",
    },
}

# school_outcomes is shallow-merged into the existing JSONB; each sub-object below is
# complete, so a shallow merge is correct. Figures are the Northwestern Common Data Set
# 2024-25 (Office of Institutional Research), College Scorecard (UNITID 147767), NCES
# College Navigator (IPEDS), and Northwestern's official reports where each publishes a
# metric. The research/campus_life/scale blocks extend what ``instenrich1`` set.
SCHOOL_OUTCOMES: dict = {
    # CDS 2024-25 §C1: 3,806 admits / 49,474 first-year applicants = 7.69%.
    "admit_rate": 0.0769,
    # College Navigator (IPEDS) average annual net price, 2023-24.
    "avg_net_price": 26830,
    # College Scorecard institution-wide median earnings 10 years after entry.
    "median_earnings_10yr": 89363,
    # College Scorecard four-year completion rate (150% of normal time).
    "completion_rate_4yr_150pct": 0.9513,
    # NCES College Navigator (IPEDS): first-year retention = 98%.
    "retention_rate_first_year": 0.98,
    # Northwestern CDS 2024-25 §B / College Navigator: six-year graduation rate = 95%.
    "graduation_rate_6yr": 0.95,
    "financial_aid": {
        # College Navigator (IPEDS): 21% of full-time first-time undergraduates received a
        # Pell grant; 19% took federal student loans (2023-24).
        "pell_grant_rate": 0.21,
        "federal_loan_rate": 0.19,
        # College Navigator total cost of attendance (on campus), 2024-25.
        "cost_of_attendance": 94878,
    },
    # Undergraduate race/ethnicity (Northwestern CDS 2024-25 §B2, % of total undergraduates).
    "demographics": {
        "white": 0.302,
        "hispanic": 0.157,
        "asian": 0.213,
        "black": 0.083,
        "two_or_more": 0.079,
        "international": 0.118,
    },
    # SAT/ACT 25th-75th percentiles (IPEDS via Urban Institute Education Data API, 2022).
    "test_scores": {
        "sat_reading_25_75": [730, 770],
        "sat_math_25_75": [760, 800],
        "act_25_75": [33, 35],
    },
    # Northwestern Evanston campus (the lakefront campus north of Chicago).
    "location": {"lat": 42.0565, "lng": -87.6753},
    "campus_basics": {"location": "Evanston, Illinois"},
    "scale": {
        # Northwestern CDS 2024-25 §I1: 1,807 total instructional faculty (1,618 full-time +
        # 189 part-time) — the IPEDS "instructional faculty" definition the standard uses.
        "faculty_count": 1807,
        # Northwestern CDS 2024-25 §I2 / Quick Facts: 6:1 student-faculty ratio.
        "student_faculty_ratio": "6:1",
        # Quick Facts: 20 University-wide research centers + 90+ school-based centers.
        "research_centers": 90,
        # Northwestern FY2025 Annual Financial Update: endowment $15.17 billion (June 30, 2025).
        "endowment_usd": 15170000000,
    },
    # Northwestern Career Advancement "Beyond Northwestern, Class of 2024": within six months,
    # 72% employed + 25% in graduate/professional school or a fellowship = 97% employed or
    # continuing education (knowledge rate 77%; 1,593 of 2,080 graduates responding).
    "employed_or_continuing_ed": 0.97,
    # "Beyond Northwestern, Class of 2024" — top industries by share of employed graduates.
    "top_employer_industries": [
        "Business / Financial Services / Investment Banking",
        "Engineering",
        "Consulting",
        "Communications / Marketing / Media",
        "Biotech / Healthcare / Pharmaceuticals",
    ],
    "research": {
        "areas": [
            "Nanotechnology",
            "Sustainability and energy",
            "Clinical and translational sciences",
            "Social policy research",
            "Bioelectronics",
            "Complex systems and network science",
        ],
        "labs": [
            "International Institute for Nanotechnology",
            "Institute for Policy Research",
            "Paula M. Trienens Institute for Sustainability and Energy",
            "Querrey Simpson Institute for Bioelectronics",
            "Northwestern Institute on Complex Systems",
            "Chemistry of Life Processes Institute",
            "Robert H. Lurie Comprehensive Cancer Center",
            "Northwestern University Clinical and Translational Sciences (NUCATS) Institute",
            "Buffett Institute for Global Affairs",
        ],
        "lab_links": {
            "International Institute for Nanotechnology": "https://www.iinano.org/",
            "Institute for Policy Research": "https://www.ipr.northwestern.edu/",
            "Paula M. Trienens Institute for Sustainability and Energy": "https://trienens-institute.northwestern.edu/",
            "Querrey Simpson Institute for Bioelectronics": "https://bioelectronics.northwestern.edu/",
            "Northwestern Institute on Complex Systems": "https://www.nico.northwestern.edu/",
            "Chemistry of Life Processes Institute": "https://clp.northwestern.edu/",
            "Robert H. Lurie Comprehensive Cancer Center": "https://www.cancer.northwestern.edu/",
            "Northwestern University Clinical and Translational Sciences (NUCATS) Institute": "https://www.nucats.northwestern.edu/",
            "Buffett Institute for Global Affairs": "https://buffett.northwestern.edu/",
        },
    },
    "campus_life": {
        "athletics_division": "NCAA Division I (Big Ten)",
        "mascot": "Northwestern Wildcats (Willie the Wildcat)",
        "student_orgs": 500,
        "varsity_sports": 19,
        "resources": [
            {"label": "Northwestern Athletics (Wildcats)", "url": "https://nusports.com/"},
            {
                "label": "Student Organizations & Activities",
                "url": "https://www.northwestern.edu/studentorgs/",
            },
            {"label": "Norris University Center", "url": "https://www.northwestern.edu/norris/"},
            {"label": "Residential Services", "url": "https://www.northwestern.edu/living/"},
        ],
    },
    "flagship": {
        # Northwestern CDS 2024-25 §B1: 23,431 total students (9,060 undergraduate + 14,371
        # graduate and professional).
        "enrollment_total": 23431,
        # Northwestern CDS 2024-25 §C1 first-year admissions cycle (entering class fall 2024).
        "applicants": 49474,
        "admits": 3806,
        "admissions_cycle": "Entering class fall 2024 (Northwestern Common Data Set 2024-25)",
        # Chartered in 1851.
        "founded_year": 1851,
    },
    "sources": [
        {
            "label": "U.S. Dept. of Education — College Scorecard (Northwestern, UNITID 147767)",
            "url": "https://collegescorecard.ed.gov/school/?147767",
        },
        {
            "label": "NCES College Navigator — Northwestern University (IPEDS)",
            "url": "https://nces.ed.gov/collegenavigator/?id=147767",
        },
        {
            "label": "Northwestern Office of Institutional Research — Common Data Set 2024-25",
            "url": "https://enrollment.northwestern.edu/data/2024-2025.pdf",
        },
        {
            "label": "Northwestern University — Quick Facts",
            "url": "https://www.northwestern.edu/about/facts.html",
        },
        {
            "label": "Northwestern — Annual Financial Update for 2025 (endowment $15.17B)",
            "url": "https://www.northwestern.edu/leadership-notes/2025/annual-financial-update-for-2025.html",
        },
        {
            "label": "Northwestern Career Advancement — Beyond Northwestern, Class of 2024",
            "url": "https://www.northwestern.edu/careers/images/beyond-northwestern-2024-final.pdf",
        },
        {
            "label": "QS World University Rankings 2026 — Northwestern University",
            "url": "https://www.topuniversities.com/universities/northwestern-university",
        },
        {
            "label": "Times Higher Education World University Rankings 2026 — Northwestern University",
            "url": "https://www.timeshighereducation.com/world-university-rankings/northwestern-university",
        },
        {
            "label": "U.S. News Best Colleges 2026 — Northwestern University",
            "url": "https://www.usnews.com/best-colleges/northwestern-university-1739",
        },
    ],
}

# student_body_size is the undergraduate count (the page labels it "Undergraduates"); the
# total (23,431) lives in flagship.enrollment_total and renders as "Total enrollment".
UNDERGRAD_COUNT = 9060

DESCRIPTION = (
    "Northwestern University is a private research university in Evanston, Illinois, "
    "founded in 1851 on the shore of Lake Michigan just north of Chicago. A founding "
    "member of the Big Ten Conference and a member of the Association of American "
    "Universities, it enrolls about 9,100 undergraduates and roughly 14,400 graduate and "
    "professional students — some 23,400 in all — across twelve schools and colleges, with "
    "a 6:1 student-faculty ratio.\n\n"
    "Undergraduates enroll in one of six schools — the Weinberg College of Arts and "
    "Sciences, the McCormick School of Engineering and Applied Science, the Medill School "
    "of Journalism, the Bienen School of Music, the School of Communication, and the "
    "School of Education and Social Policy — while Northwestern's professional schools "
    "include the Kellogg School of Management, the Pritzker School of Law and the Feinberg "
    "School of Medicine, alongside The Graduate School and the School of Professional "
    "Studies. Its research enterprise, topping $1 billion in annual funding, is anchored by "
    "the International Institute for Nanotechnology — the first institute of its kind in the "
    "United States — the Institute for Policy Research, and the Robert H. Lurie "
    "Comprehensive Cancer Center.\n\n"
    "Northwestern ranks among the nation's best universities: No. 6 among national "
    "universities by U.S. News, No. 30 in the world by Times Higher Education, and No. 42 "
    "by QS. It admits under 8% of first-year applicants, graduates 95% of entering "
    "students within six years, and backs a $15.2 billion endowment as of June 2025.\n\n"
    "Among the Class of 2024, within six months of graduation 72% were employed and 25% "
    "had entered graduate or professional school. The average annual net price is about "
    "$26,800, 21% of undergraduates receive Pell grants, and Northwestern meets full "
    "demonstrated financial need."
)

# ── The real degree-granting schools (display order) ───────────────────────
_WEINBERG = "Weinberg College of Arts and Sciences"
_MCCORMICK = "McCormick School of Engineering and Applied Science"
_MEDILL = "Medill School of Journalism, Media, Integrated Marketing Communications"
_BIENEN = "Bienen School of Music"
_COMM = "School of Communication"
_SESP = "School of Education and Social Policy"
_KELLOGG = "Kellogg School of Management"
_LAW = "Northwestern Pritzker School of Law"
_FEINBERG = "Feinberg School of Medicine"
_TGS = "The Graduate School"
_SPS = "School of Professional Studies"

SCHOOLS: list[dict] = [
    {
        "name": _WEINBERG,
        "sort_order": 1,
        "description": (
            "Weinberg College of Arts and Sciences, founded with the university in 1851, is "
            "Northwestern's largest school and the academic heart of its undergraduate "
            "education. It awards the Bachelor of Arts across the humanities, the natural "
            "and social sciences and mathematics, and — through The Graduate School — "
            "doctoral and master's degrees in those disciplines."
        ),
    },
    {
        "name": _MCCORMICK,
        "sort_order": 2,
        "description": (
            "The McCormick School of Engineering and Applied Science, founded in 1909, "
            "educates engineers in a 'whole-brain' tradition that pairs technical depth with "
            "design and entrepreneurship. It awards the B.S. across the engineering "
            "disciplines and computer science, research master's and Ph.D. degrees, and a "
            "broad set of professional master's degrees in engineering management, design, "
            "AI and analytics."
        ),
    },
    {
        "name": _MEDILL,
        "sort_order": 3,
        "description": (
            "The Medill School of Journalism, Media, Integrated Marketing Communications, "
            "founded in 1921, is one of the country's foremost journalism schools. It awards "
            "the Bachelor of Science in Journalism, the master's in journalism (MSJ) and the "
            "master's in integrated marketing communications (IMC), offered on campus and "
            "online."
        ),
    },
    {
        "name": _BIENEN,
        "sort_order": 4,
        "description": (
            "The Henry and Leigh Bienen School of Music, founded in 1895, is a conservatory "
            "within a major research university. It awards the Bachelor of Music, the Master "
            "of Music, the Doctor of Musical Arts and the Ph.D. across performance, "
            "composition, conducting, music education, musicology, and music theory and "
            "cognition."
        ),
    },
    {
        "name": _COMM,
        "sort_order": 5,
        "description": (
            "The School of Communication, with roots in the university's 1878 program in "
            "oratory, spans communication studies, performance, film and media, theatre and "
            "dance, and communication sciences and disorders. It awards undergraduate, "
            "master's, M.F.A., clinical doctoral and Ph.D. degrees."
        ),
    },
    {
        "name": _SESP,
        "sort_order": 6,
        "description": (
            "The School of Education and Social Policy, founded in 1926, studies human "
            "development and learning across the lifespan and the design of social policy. "
            "It awards undergraduate degrees in social policy, learning sciences, human "
            "development and learning and organizational change, plus master's, Ed.D. and "
            "Ph.D. degrees."
        ),
    },
    {
        "name": _KELLOGG,
        "sort_order": 7,
        "description": (
            "The Kellogg School of Management, founded in 1908, is one of the world's "
            "leading business schools. It awards the Full-Time, Evening & Weekend and "
            "Executive MBA, the joint MMM and JD-MBA degrees, the Master in Management and a "
            "research Ph.D. across eight fields of study."
        ),
    },
    {
        "name": _LAW,
        "sort_order": 8,
        "description": (
            "Northwestern Pritzker School of Law, founded in 1859, is one of the oldest law "
            "schools in the country, known for its empirical and interdisciplinary approach "
            "and its accelerated and joint degrees. It awards the J.D., the JD-MBA with "
            "Kellogg, the LL.M., the Master of Science in Law and the doctoral S.J.D."
        ),
    },
    {
        "name": _FEINBERG,
        "sort_order": 9,
        "description": (
            "The Feinberg School of Medicine, founded in 1859, is Northwestern's medical "
            "school on its Chicago campus. It awards the M.D., the M.D.-Ph.D. (Medical "
            "Scientist Training Program), clinical doctorates in physical therapy, and a "
            "range of health-sciences master's degrees in fields such as genetic counseling, "
            "clinical investigation, public health and prosthetics-orthotics."
        ),
    },
    {
        "name": _TGS,
        "sort_order": 10,
        "description": (
            "The Graduate School administers Northwestern's Ph.D. and research master's "
            "degrees across more than seventy fields in the arts and sciences and "
            "interdisciplinary programs, in partnership with the disciplinary departments "
            "and the professional schools."
        ),
    },
    {
        "name": _SPS,
        "sort_order": 11,
        "description": (
            "The School of Professional Studies, founded in 1933, is Northwestern's school "
            "for adult, part-time and online learners. It awards part-time bachelor's "
            "completion degrees and a broad set of master's degrees — many offered fully "
            "online — in data science, information systems, public policy, health "
            "informatics, writing and related professional fields."
        ),
    },
]

# Official school home pages.
_SCHOOL_WEBSITE: dict[str, str] = {
    _WEINBERG: "https://www.weinberg.northwestern.edu/",
    _MCCORMICK: "https://www.mccormick.northwestern.edu/",
    _MEDILL: "https://www.medill.northwestern.edu/",
    _BIENEN: "https://www.music.northwestern.edu/",
    _COMM: "https://www.communication.northwestern.edu/",
    _SESP: "https://www.sesp.northwestern.edu/",
    _KELLOGG: "https://www.kellogg.northwestern.edu/",
    _LAW: "https://www.law.northwestern.edu/",
    _FEINBERG: "https://www.feinberg.northwestern.edu/",
    _TGS: "https://www.tgs.northwestern.edu/",
    _SPS: "https://sps.northwestern.edu/",
}

# Per-school About tab (founded · current 2025-26 leadership · notable current faculty ·
# named research centers · source). Each value individually verified against the school's
# own official page; deans verified individually (Pritzker Law changed: Clopton, 2026).
_ABOUT_DETAIL: dict[str, dict] = {
    _WEINBERG: {
        "founded": 1851,
        "leadership": "Adrian Randolph, Dean",
        "faculty": [
            "Shana Kelley (Chemistry)",
            "Dan P. McAdams (Psychology)",
            "Shalini Shankar (Anthropology)",
        ],
        "research_centers": [
            "Weinberg College Center for International & Area Studies",
            "Program in Environmental Policy & Culture",
        ],
        "named_for": "Marjorie I. and Harvey Kapnick / John Evans benefactors — named for Judd A. and Marjorie Weinberg (1998)",
        "source": "https://weinberg.northwestern.edu/about/college-facts/history.html",
    },
    _MCCORMICK: {
        "founded": 1909,
        "leadership": "Christopher A. Schuh, Dean",
        "faculty": [
            "Samuel I. Stupp (Materials Science & Engineering)",
            "John A. Rogers (Biomedical Engineering / Bio-Integrated Electronics)",
        ],
        "research_centers": [
            "Segal Design Institute",
            "Farley Center for Entrepreneurship & Innovation",
            "Northwestern Institute on Complex Systems (NICO)",
            "Northwestern University Transportation Center",
        ],
        "named_for": "Robert R. McCormick (1989)",
        "source": "https://www.mccormick.northwestern.edu/about/history.html",
    },
    _MEDILL: {
        "founded": 1921,
        "leadership": "Charles Whitaker, Dean",
        "faculty": [
            "Steven W. Thrasher (Daniel H. Renberg Chair)",
            "Mei-Ling Hopgood (Journalism)",
        ],
        "research_centers": [
            "Spiegel Research Center",
            "Medill Local News Initiative",
            "Medill Intent Lab",
        ],
        "named_for": "Joseph Medill",
        "source": "https://www.medill.northwestern.edu/about-us/our-history.html",
    },
    _BIENEN: {
        "founded": 1895,
        "leadership": "Jonathan Bailey Holland, Dean",
        "faculty": [
            "Nancy Gustafson (Voice & Opera)",
            "David McGill (Bassoon)",
            "Vasili Byros (Music Theory & Cognition)",
        ],
        "research_centers": [
            "Institute for New Music",
            "Mary B. Galvin Recital Hall / Ryan Center for the Musical Arts",
        ],
        "named_for": "Henry and Leigh Bienen",
        "source": "https://music.northwestern.edu/about",
    },
    _COMM: {
        "founded": 1878,
        "leadership": "E. Patrick Johnson, Dean",
        "faculty": [
            "Mary Zimmerman (Performance Studies)",
            "Nina Kraus (Auditory Neuroscience / Brainvolts)",
            "Pablo Boczkowski (Communication Studies)",
        ],
        "research_centers": [
            "Center for Human-Computer Interaction + Design (HCI+D)",
            "Center for Latinx Digital Media",
            "Northwestern University Center for Audiology, Speech, Language and Learning",
        ],
        "source": "https://communication.northwestern.edu/about/leadership.html",
    },
    _SESP: {
        "founded": 1926,
        "leadership": "Bryan McKinley Jones Brayboy, Dean",
        "faculty": [
            "C. Kirabo Jackson (Economics of Education)",
            "Nichole Pinkard (Learning Sciences)",
            "Brian J. Reiser (Learning Sciences)",
        ],
        "research_centers": [
            "Center for Connected Learning and Computer-Based Modeling",
            "Office of STEM Education Partnerships",
            "Center for Talent Development",
        ],
        "source": "https://sesp.northwestern.edu/about/why-sesp/our-history.html",
    },
    _KELLOGG: {
        "founded": 1908,
        "leadership": "Francesca Cornelli, Dean",
        "faculty": [
            "Sergio Rebelo (Finance)",
            "Sunil Chopra (Operations / Deputy Dean)",
        ],
        "research_centers": [
            "Heizer Center for Private Equity & Venture Capital",
            "Zell Center for Risk Research",
        ],
        "named_for": "John L. Kellogg (1979)",
        "source": "https://www.kellogg.northwestern.edu/academics-research/research-centers/",
    },
    _LAW: {
        "founded": 1859,
        "leadership": "Zachary D. Clopton, Dean (effective February 1, 2026)",
        "faculty": [
            "Bernard S. Black (Nicholas J. Chabraja Professor)",
            "Hari M. Osofsky (former dean; Energy Innovation)",
        ],
        "research_centers": [
            "Bluhm Legal Clinic",
            "Center on Wrongful Convictions",
            "Center for International Human Rights",
            "Donald Pritzker Entrepreneurship Law Center",
        ],
        "named_for": "J.B. and M.K. Pritzker family (2015)",
        "source": "https://news.law.northwestern.edu/news/zachary-clopton-named-dean-of-northwestern-pritzker-school-of-law/",
    },
    _FEINBERG: {
        "founded": 1859,
        "leadership": "Eric G. Neilson, MD, Vice President for Medical Affairs and Lewis Landsberg Dean",
        "faculty": [
            "Clyde W. Yancy (Cardiology)",
            "Ankit Bharat (Thoracic Surgery)",
        ],
        "research_centers": [
            "Robert H. Lurie Comprehensive Cancer Center",
            "Bluhm Cardiovascular Institute",
            "Institute for Public Health and Medicine (IPHAM)",
            "Institute for Artificial Intelligence in Medicine (iAIM)",
        ],
        "named_for": "Reva and David Logan / Joseph and Bessie Feinberg (2002)",
        "source": "https://www.feinberg.northwestern.edu/about/dean/index.html",
    },
    _TGS: {
        "leadership": "Kelly E. Mayo, PhD, Dean",
        "source": "https://www.tgs.northwestern.edu/about/our-people/staff/kelly-mayo.html",
    },
    _SPS: {
        "founded": 1933,
        "leadership": "Thomas F. Gibbons, Dean",
        "source": "https://sps.northwestern.edu/main/about.html",
    },
}

# Fields each school legitimately omits (recorded in its _standard.omitted).
_ABOUT_OMITTED: dict[str, list[str]] = {
    # The Graduate School is an umbrella school: founding year is not confirmed on an
    # official NU page, and faculty + research centers belong to the disciplinary
    # departments, not to TGS itself.
    _TGS: ["about_detail.founded", "about_detail.faculty", "about_detail.research_centers"],
    # SPS publishes no notable-faculty roster (instruction is largely part-time lecturers)
    # and runs program units rather than named research centers.
    _SPS: ["about_detail.faculty", "about_detail.research_centers"],
}

# ── Channel feeds + official social links ──────────────────────────────────
# The daily content-ingest reads ``news_rss`` (an RSS feed), an optional ``events_feed``
# (an iCalendar URL), ``keywords`` (word-boundary relevance filter) and ``news_curated``
# from each node's content_sources. Without a real ``news_rss`` a node's Events & Updates
# tab is empty — so every school and program below carries one. Feeds verified 2026-06-11:
#   • Northwestern Now all-stories RSS: https://news.northwestern.edu/feeds/allStories (items
#     carry <enclosure> cover images the ingest captures)
#   • Northwestern events iCalendar (PlanItPurple all-university): /feed/ical/124
#   • Weinberg + Feinberg run their own school RSS (verified live); other schools use the
#     university feed filtered by school keywords (the MIT/MBAn pattern).
_NU_NEWS_RSS = "https://news.northwestern.edu/feeds/allStories"
_NU_EVENTS_ICS = {"url": "https://planitpurple.northwestern.edu/feed/ical/124", "type": "ical"}
_WEINBERG_RSS = "https://news.weinberg.northwestern.edu/feed/"
_FEINBERG_RSS = "https://news.feinberg.northwestern.edu/feed/"

# Official university social handles (verified 2026-06-11).
_SOCIAL_NU = {
    "instagram": "https://instagram.com/northwesternu",
    "facebook": "https://www.facebook.com/NorthwesternU",
    "x": "https://x.com/northwesternu",
    "youtube": "https://www.youtube.com/user/NorthwesternU",
    "linkedin": "https://www.linkedin.com/school/northwestern-university/",
}

# Per-school feed config: an own-RSS school uses it; the rest use the university all-stories
# RSS filtered to school-relevant items by ``keywords``. (school_name -> {rss, keywords}).
_SCHOOL_FEED_SPEC: dict[str, dict] = {
    _WEINBERG: {"rss": _WEINBERG_RSS, "keywords": ["Weinberg", "arts and sciences"]},
    _MCCORMICK: {"rss": _NU_NEWS_RSS, "keywords": ["McCormick", "engineering"]},
    _MEDILL: {"rss": _NU_NEWS_RSS, "keywords": ["Medill", "journalism"]},
    _BIENEN: {"rss": _NU_NEWS_RSS, "keywords": ["Bienen", "music"]},
    _COMM: {"rss": _NU_NEWS_RSS, "keywords": ["School of Communication", "communication"]},
    _SESP: {"rss": _NU_NEWS_RSS, "keywords": ["education and social policy", "SESP"]},
    _KELLOGG: {"rss": _NU_NEWS_RSS, "keywords": ["Kellogg", "business", "MBA"]},
    _LAW: {"rss": _NU_NEWS_RSS, "keywords": ["Pritzker School of Law", "law school"]},
    _FEINBERG: {"rss": _FEINBERG_RSS, "keywords": ["Feinberg", "medicine", "medical"]},
    _TGS: {"rss": _NU_NEWS_RSS, "keywords": ["graduate school", "doctoral", "PhD"]},
    _SPS: {"rss": _NU_NEWS_RSS, "keywords": ["professional studies", "SPS"]},
}


def _school_content(name: str) -> dict:
    """Build a school's content_sources from its verified RSS + keywords + university socials."""
    spec = _SCHOOL_FEED_SPEC[name]
    return {
        "news_rss": spec["rss"],
        "news_curated": spec["rss"] != _NU_NEWS_RSS,
        "events_feed": dict(_NU_EVENTS_ICS),
        "keywords": list(spec["keywords"]),
        "social": _SOCIAL_NU,
    }


def _program_content(school_name: str, keywords: list[str]) -> dict:
    """Build a program's content_sources from its school feed, refined by program keywords."""
    base = _school_content(school_name)
    base["keywords"] = list(keywords)
    return base


# Institution-wide feed: the all-stories Northwestern Now RSS (curated) + the PlanItPurple
# events calendar, with the official university social handles.
_INSTITUTION_CONTENT: dict = {
    "news_rss": _NU_NEWS_RSS,
    "news_url": "https://news.northwestern.edu",
    "news_curated": True,
    "events_feed": dict(_NU_EVENTS_ICS),
    "social": _SOCIAL_NU,
}

# Real Northwestern campus photo (University Hall, the oldest building) — Wikimedia Commons,
# CC BY-SA 3.0, hotlinkable landscape JPG (verified HTTP 200). Leads the institution hero.
_CAMPUS_PHOTO = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/49/"
    "University_Hall_Northwestern.jpg/1280px-University_Hall_Northwestern.jpg"
)


# ── Full catalog (breadth) ─────────────────────────────────────────────────
# Northwestern's published degree catalog, enumerated from each school's official pages
# and the Northwestern catalog (catalogs.northwestern.edu) and cross-checked against the
# College Scorecard Field-of-Study list for UNITID 147767. Every program carries verified
# BASICS (full name, degree, delivery_format, owning school, factual description); deeper
# fields (tracks/outcomes/faculty/reviews) are layered on the flagship and recorded as
# omitted-pending elsewhere per _program_standard, and deepened on resume runs. Sources are
# each school's official degree page (cited per school in _ABOUT_DETAIL / the research log):
#   • Weinberg majors: weinberg.northwestern.edu/undergraduate/major-minor/explore/
#   • McCormick: mccormick.northwestern.edu/academics/{undergraduate,graduate}/
#   • Medill: medill.northwestern.edu · Bienen: music.northwestern.edu/academics/degrees
#   • Communication: communication.northwestern.edu/academics/graduate-programs/
#   • SESP: sesp.northwestern.edu/graduate-professional/ · Kellogg: kellogg.northwestern.edu/programs/
#   • Pritzker Law: law.northwestern.edu/academics/degree-programs/
#   • Feinberg: feinberg.northwestern.edu/education.html · TGS: tgs.northwestern.edu/academics/programs/
#   • SPS: sps.northwestern.edu/masters/ + /part-time-undergraduate/

_SLUG_REPL = {"&": "and", "—": " ", "/": " ", "'": "", ".": "", ",": "", "(": "", ")": "", ":": ""}


def _slugify(text: str) -> str:
    s = text.lower()
    for a, b in _SLUG_REPL.items():
        s = s.replace(a, b)
    return "-".join(s.split())


_DUR_DEFAULT = {"bachelors": 48, "masters": 18, "phd": 60, "professional": 36}
_DEG_WORD = {
    "bachelors": "undergraduate",
    "masters": "master's",
    "phd": "doctoral (Ph.D.)",
    "professional": "professional",
}

# Undergraduate majors (all Weinberg majors award the Bachelor of Arts; all McCormick majors
# award the Bachelor of Science). (name, suffix).
_WEINBERG_BA = [
    "American Studies", "Anthropology", "Art History", "Art Theory and Practice",
    "Asian American Studies", "Asian Languages and Cultures", "Biological Sciences",
    "Black Studies", "Chemistry", "Classics", "Cognitive Science",
    "Comparative Literary Studies", "Computer Science", "Earth and Planetary Sciences",
    "Environmental Science", "Economics", "Creative Writing", "Literature", "French",
    "Italian", "Gender and Sexuality Studies", "German", "History", "Integrated Science",
    "Jewish Studies", "Latina and Latino Studies", "Legal Studies", "Linguistics",
    "Mathematics", "Middle East and North African Studies", "Neuroscience", "Philosophy",
    "Physics", "Political Science", "Psychology", "Religious Studies",
    "Russian Language, Literature and Culture", "Russian and East European Studies",
    "Sociology", "Spanish", "Statistics", "Data Science",
]
_MCCORMICK_BS = [
    "Applied Mathematics", "Biomedical Engineering", "Chemical Engineering",
    "Civil Engineering", "Computer Engineering", "Computer Science",
    "Electrical Engineering", "Environmental Engineering", "Industrial Engineering",
    "Manufacturing and Design Engineering", "Materials Science and Engineering",
    "Mechanical Engineering",
]

# Graduate / professional / named-bachelor programs:
# (name, degree_type, school, delivery_format, suffix, duration_months_or_None)
_GRAD: list[tuple] = [
    # ── McCormick Engineering — PhD ──
    ("Biomedical Engineering", "phd", _MCCORMICK, "in_person", "phd", None),
    ("Chemical and Biological Engineering", "phd", _MCCORMICK, "in_person", "phd", None),
    ("Civil and Environmental Engineering", "phd", _MCCORMICK, "in_person", "phd", None),
    ("Computer Science", "phd", _MCCORMICK, "in_person", "phd", None),
    ("Computer Engineering", "phd", _MCCORMICK, "in_person", "phd", None),
    ("Electrical Engineering", "phd", _MCCORMICK, "in_person", "phd", None),
    ("Industrial Engineering and Management Sciences", "phd", _MCCORMICK, "in_person", "phd", None),
    ("Materials Science and Engineering", "phd", _MCCORMICK, "in_person", "phd", None),
    ("Mechanical Engineering", "phd", _MCCORMICK, "in_person", "phd", None),
    ("Theoretical and Applied Mechanics", "phd", _MCCORMICK, "in_person", "phd", None),
    ("Engineering Sciences and Applied Mathematics", "phd", _MCCORMICK, "in_person", "phd", None),
    # ── McCormick — research MS ──
    ("Biomedical Engineering", "masters", _MCCORMICK, "in_person", "ms", 24),
    ("Chemical and Biological Engineering", "masters", _MCCORMICK, "in_person", "ms", 24),
    ("Civil and Environmental Engineering", "masters", _MCCORMICK, "in_person", "ms", 24),
    ("Computer Science", "masters", _MCCORMICK, "in_person", "ms", 24),
    ("Computer Engineering", "masters", _MCCORMICK, "in_person", "ms", 24),
    ("Electrical Engineering", "masters", _MCCORMICK, "in_person", "ms", 24),
    ("Materials Science and Engineering", "masters", _MCCORMICK, "in_person", "ms", 24),
    ("Mechanical Engineering", "masters", _MCCORMICK, "in_person", "ms", 24),
    ("Engineering Sciences and Applied Mathematics", "masters", _MCCORMICK, "in_person", "ms", 24),
    ("Energy and Sustainability", "masters", _MCCORMICK, "in_person", "ms", 24),
    # ── McCormick — professional master's ──
    ("Master of Engineering Management (MEM)", "masters", _MCCORMICK, "in_person", "mem", 24),
    ("Master of Project Management (MPM)", "masters", _MCCORMICK, "in_person", "mpm", 24),
    ("Master of Science in Artificial Intelligence (MSAI)", "masters", _MCCORMICK, "in_person", "msai", 15),
    ("Master of Science in Machine Learning and Data Science (MLDS)", "masters", _MCCORMICK, "in_person", "mlds", 15),
    ("Master of Science in Robotics (MSR)", "masters", _MCCORMICK, "in_person", "msr", 12),
    ("Master of Science in Biotechnology (MBP)", "masters", _MCCORMICK, "in_person", "mbp", 15),
    ("Master of Science in Information Technology (MSIT)", "masters", _MCCORMICK, "in_person", "msit", 24),
    ("Master of Science in Executive Management for Design and Construction (EMDC)", "masters", _MCCORMICK, "hybrid", "emdc", 24),
    ("Master of Engineering Design Innovation (EDI)", "masters", _MCCORMICK, "in_person", "edi", 15),
    ("Master of Product Design and Development Management (MPD2)", "masters", _MCCORMICK, "in_person", "mpd2", 24),
    ("Master of Science in Advanced Manufacturing", "masters", _MCCORMICK, "in_person", "ms-mfg", 24),
    # ── Medill ──
    ("Bachelor of Science in Journalism (BSJ)", "bachelors", _MEDILL, "in_person", "bsj", 48),
    ("Master of Science in Journalism (MSJ)", "masters", _MEDILL, "in_person", "msj", 12),
    ("Master of Science in Integrated Marketing Communications — Full-Time", "masters", _MEDILL, "in_person", "imc-ft", 15),
    ("Master of Science in Integrated Marketing Communications — Professional (Online)", "masters", _MEDILL, "online", "imc-online", 18),
    # ── Bienen Music ──
    ("Bachelor of Music in Composition", "bachelors", _BIENEN, "in_person", "bmus", 48),
    ("Bachelor of Music in Jazz Studies", "bachelors", _BIENEN, "in_person", "bmus", 48),
    ("Bachelor of Music in Music Education", "bachelors", _BIENEN, "in_person", "bmus", 48),
    ("Bachelor of Music in Musicology", "bachelors", _BIENEN, "in_person", "bmus", 48),
    ("Bachelor of Music in Music Theory", "bachelors", _BIENEN, "in_person", "bmus", 48),
    ("Bachelor of Music in Music Cognition", "bachelors", _BIENEN, "in_person", "bmus", 48),
    ("Bachelor of Music in Performance", "bachelors", _BIENEN, "in_person", "bmus", 48),
    ("Bachelor of Arts and Bachelor of Music (Dual Degree)", "bachelors", _BIENEN, "in_person", "ba-bmus", 60),
    ("Master of Music in Performance", "masters", _BIENEN, "in_person", "mm", 24),
    ("Master of Music in Conducting", "masters", _BIENEN, "in_person", "mm", 24),
    ("Master of Music in Collaborative Piano", "masters", _BIENEN, "in_person", "mm", 24),
    ("Master of Music in Jazz Studies", "masters", _BIENEN, "in_person", "mm", 24),
    ("Master of Music in Music Education", "masters", _BIENEN, "in_person", "mm", 24),
    ("Master of Music in Music Theory", "masters", _BIENEN, "in_person", "mm", 24),
    ("Master of Music in Musicology", "masters", _BIENEN, "in_person", "mm", 24),
    ("Doctor of Musical Arts in Performance", "professional", _BIENEN, "in_person", "dma", 36),
    ("Doctor of Musical Arts in Conducting", "professional", _BIENEN, "in_person", "dma", 36),
    ("Doctor of Musical Arts in Piano Performance and Pedagogy", "professional", _BIENEN, "in_person", "dma", 36),
    ("Doctor of Philosophy in Music (Musicology)", "phd", _BIENEN, "in_person", "phd", None),
    ("Doctor of Philosophy in Music (Music Theory and Cognition)", "phd", _BIENEN, "in_person", "phd", None),
    ("Doctor of Philosophy in Music (Music Education)", "phd", _BIENEN, "in_person", "phd", None),
    ("Doctor of Philosophy in Music (Composition and Music Technology)", "phd", _BIENEN, "in_person", "phd", None),
    # ── School of Communication — undergrad majors ──
    ("Communication Studies", "bachelors", _COMM, "in_person", "ba", 48),
    ("Radio/Television/Film", "bachelors", _COMM, "in_person", "ba", 48),
    ("Theatre", "bachelors", _COMM, "in_person", "ba", 48),
    ("Dance", "bachelors", _COMM, "in_person", "ba", 48),
    ("Human Communication Sciences", "bachelors", _COMM, "in_person", "bs", 48),
    ("Performance Studies", "bachelors", _COMM, "in_person", "ba", 48),
    # ── School of Communication — graduate ──
    ("Master of Science in Communication", "masters", _COMM, "in_person", "ms", 15),
    ("Master of Science in Leadership for Creative Enterprises", "masters", _COMM, "in_person", "ms", 15),
    ("Master of Arts in Sound Arts and Industries", "masters", _COMM, "in_person", "ma", 15),
    ("Master of Science in Speech, Language, and Learning", "masters", _COMM, "in_person", "ms", 24),
    ("Master of Fine Arts in Acting", "masters", _COMM, "in_person", "mfa", 36),
    ("Master of Fine Arts in Directing", "masters", _COMM, "in_person", "mfa", 36),
    ("Master of Fine Arts in Stage Design", "masters", _COMM, "in_person", "mfa", 36),
    ("Master of Fine Arts in Documentary Media", "masters", _COMM, "in_person", "mfa", 24),
    ("Master of Fine Arts in Writing for the Screen and Stage", "masters", _COMM, "in_person", "mfa", 24),
    ("Doctor of Audiology (AuD)", "professional", _COMM, "in_person", "aud", 48),
    ("Doctor of Speech-Language Pathology (SLPD)", "professional", _COMM, "in_person", "slpd", 36),
    ("Doctor of Philosophy in Communication Sciences and Disorders", "phd", _COMM, "in_person", "phd", None),
    ("Doctor of Philosophy in Rhetoric, Media, and Publics", "phd", _COMM, "in_person", "phd", None),
    ("Doctor of Philosophy in Performance Studies", "phd", _COMM, "in_person", "phd", None),
    ("Doctor of Philosophy in Screen Cultures", "phd", _COMM, "in_person", "phd", None),
    ("Doctor of Philosophy in Theatre and Drama", "phd", _COMM, "in_person", "phd", None),
    ("Doctor of Philosophy in Technology and Social Behavior", "phd", _COMM, "in_person", "phd", None),
    ("Doctor of Philosophy in Media, Technology, and Society", "phd", _COMM, "in_person", "phd", None),
    # ── SESP — undergrad concentrations (BS in Education and Social Policy) ──
    ("Social Policy", "bachelors", _SESP, "in_person", "bsed", 48),
    ("Human Development in Context", "bachelors", _SESP, "in_person", "bsed", 48),
    ("Learning and Organizational Change", "bachelors", _SESP, "in_person", "bsed", 48),
    ("Learning Sciences", "bachelors", _SESP, "in_person", "bsed", 48),
    ("Elementary Teaching", "bachelors", _SESP, "in_person", "bsed", 48),
    ("Secondary Teaching", "bachelors", _SESP, "in_person", "bsed", 48),
    # ── SESP — graduate ──
    ("Master of Science in Education — Elementary Teaching (MSEd)", "masters", _SESP, "in_person", "msed-elem", 12),
    ("Master of Science in Education — Secondary Teaching (MSEd)", "masters", _SESP, "in_person", "msed-sec", 12),
    ("Master of Science in Education — Educational Studies (MSEd)", "masters", _SESP, "in_person", "msed-eds", 12),
    ("Master of Science in Education — Learning Sciences (MSEd)", "masters", _SESP, "in_person", "msed-ls", 12),
    ("Master of Science in Learning and Organizational Change (MSLOC)", "masters", _SESP, "hybrid", "msloc", 18),
    ("Master of Science in Higher Education Administration and Policy (MSHE)", "masters", _SESP, "in_person", "mshe", 12),
    ("Doctor of Philosophy in Human Development and Social Policy", "phd", _SESP, "in_person", "phd", None),
    ("Doctor of Philosophy in Learning Sciences", "phd", _SESP, "in_person", "phd", None),
    ("Doctor of Philosophy in Computer Science and Learning Sciences", "phd", _SESP, "in_person", "phd", None),
    # ── Kellogg ──
    ("Full-Time MBA", "masters", _KELLOGG, "in_person", "mba", 21),
    ("MMM Program (MBA + MS in Design Innovation)", "masters", _KELLOGG, "in_person", "mmm", 24),
    ("MBAi Program (MBA + Artificial Intelligence)", "masters", _KELLOGG, "in_person", "mbai", 21),
    ("Evening & Weekend MBA", "masters", _KELLOGG, "in_person", "ew-mba", 30),
    ("Executive MBA (EMBA)", "masters", _KELLOGG, "in_person", "emba", 24),
    ("Master in Management (MiM)", "masters", _KELLOGG, "in_person", "mim", 10),
    ("Doctor of Philosophy in Management", "phd", _KELLOGG, "in_person", "phd", None),
    # ── Pritzker Law ──
    ("Juris Doctor (JD)", "professional", _LAW, "in_person", "jd", 36),
    ("JD-MBA", "professional", _LAW, "in_person", "jd-mba", 36),
    ("JD-PhD", "professional", _LAW, "in_person", "jd-phd", 72),
    ("Master of Laws (LLM)", "masters", _LAW, "in_person", "llm", 12),
    ("Master of Laws in Taxation (LLM Tax)", "masters", _LAW, "in_person", "llm-tax", 12),
    ("Executive LLM (International)", "masters", _LAW, "in_person", "exec-llm", 18),
    ("Master of Science in Law (MSL)", "masters", _LAW, "in_person", "msl", 12),
    ("Master of Science in Law (MSL) — Online", "masters", _LAW, "online", "msl-online", 24),
    # ── Feinberg ──
    ("Doctor of Medicine (MD)", "professional", _FEINBERG, "in_person", "md", 48),
    ("Medical Scientist Training Program (MD-PhD)", "professional", _FEINBERG, "in_person", "mdphd", 96),
    ("Physician Assistant Program (MMS)", "masters", _FEINBERG, "in_person", "pa", 27),
    ("Doctor of Physical Therapy (DPT)", "professional", _FEINBERG, "in_person", "dpt", 32),
    ("Master of Prosthetics and Orthotics (MPO)", "masters", _FEINBERG, "hybrid", "mpo", 21),
    ("Master of Public Health (MPH)", "masters", _FEINBERG, "in_person", "mph", 24),
    ("Master of Science in Healthcare Quality and Patient Safety", "masters", _FEINBERG, "hybrid", "hqps", 18),
    ("Master of Science in Health and Biomedical Informatics", "masters", _FEINBERG, "in_person", "hbmi", 24),
    ("Master of Science in Reproductive Science and Medicine", "masters", _FEINBERG, "in_person", "rsm", 18),
    ("Master of Science in Genetic Counseling", "masters", _FEINBERG, "in_person", "gc", 21),
    ("Master of Science in Health Services and Outcomes Research", "masters", _FEINBERG, "hybrid", "hsor", 24),
    ("Master of Science in Biostatistics", "masters", _FEINBERG, "in_person", "biostat", 12),
    ("Master of Science in Epidemiology", "masters", _FEINBERG, "in_person", "epi", 12),
    ("Master of Science in Global Health (Online)", "masters", _FEINBERG, "online", "globalhealth", 24),
    ("Driskill Graduate Program in Life Sciences (DGP)", "phd", _FEINBERG, "in_person", "dgp-phd", None),
    ("Northwestern University Interdepartmental Neuroscience (NUIN)", "phd", _FEINBERG, "in_person", "nuin-phd", None),
    ("Health Sciences Integrated Program (HSIP)", "phd", _FEINBERG, "in_person", "hsip-phd", None),
    ("Clinical Psychology", "phd", _FEINBERG, "in_person", "phd", None),
    # ── The Graduate School — arts & sciences research degrees ──
    ("Anthropology", "phd", _TGS, "in_person", "phd", None),
    ("Applied Physics", "phd", _TGS, "in_person", "phd", None),
    ("Art History", "phd", _TGS, "in_person", "phd", None),
    ("Astronomy", "phd", _TGS, "in_person", "phd", None),
    ("Black Studies", "phd", _TGS, "in_person", "phd", None),
    ("Chemistry", "phd", _TGS, "in_person", "phd", None),
    ("Comparative Literary Studies", "phd", _TGS, "in_person", "phd", None),
    ("Earth and Planetary Sciences", "phd", _TGS, "in_person", "phd", None),
    ("Economics", "phd", _TGS, "in_person", "phd", None),
    ("English", "phd", _TGS, "in_person", "phd", None),
    ("French and Francophone Studies", "phd", _TGS, "in_person", "phd", None),
    ("German Literature and Critical Thought", "phd", _TGS, "in_person", "phd", None),
    ("History", "phd", _TGS, "in_person", "phd", None),
    ("Interdisciplinary Biological Sciences (IBiS)", "phd", _TGS, "in_person", "phd", None),
    ("Linguistics", "phd", _TGS, "in_person", "phd", None),
    ("Mathematics", "phd", _TGS, "in_person", "phd", None),
    ("Philosophy", "phd", _TGS, "in_person", "phd", None),
    ("Physics", "phd", _TGS, "in_person", "phd", None),
    ("Plant Biology and Conservation", "phd", _TGS, "in_person", "phd", None),
    ("Political Science", "phd", _TGS, "in_person", "phd", None),
    ("Psychology", "phd", _TGS, "in_person", "phd", None),
    ("Religious Studies", "phd", _TGS, "in_person", "phd", None),
    ("Slavic Languages and Literatures", "phd", _TGS, "in_person", "phd", None),
    ("Sociology", "phd", _TGS, "in_person", "phd", None),
    ("Spanish and Portuguese", "phd", _TGS, "in_person", "phd", None),
    ("Statistics and Data Science", "phd", _TGS, "in_person", "phd", None),
    ("Art Theory and Practice", "masters", _TGS, "in_person", "mfa", 24),
    ("Creative Writing (Litowitz MFA+MA)", "masters", _TGS, "in_person", "mfa", 24),
    ("Counseling", "masters", _TGS, "in_person", "ma", 24),
    ("Marriage and Family Therapy", "masters", _TGS, "in_person", "ms", 24),
    ("Neurobiology", "masters", _TGS, "in_person", "ms", 12),
    ("Plant Biology and Conservation", "masters", _TGS, "in_person", "ms", 24),
    ("Quantitative and Systems Biology", "masters", _TGS, "in_person", "ms", 12),
    # ── School of Professional Studies — online / part-time degrees ──
    ("Master of Science in Data Science", "masters", _SPS, "online", "ms", 24),
    ("Master of Science in Enterprise Risk Management", "masters", _SPS, "online", "ms", 24),
    ("Master of Science in Global Health", "masters", _SPS, "online", "ms", 24),
    ("Master of Science in Health Informatics", "masters", _SPS, "online", "ms", 24),
    ("Master of Science in Healthcare Administration", "masters", _SPS, "online", "ms", 24),
    ("Master of Science in Healthcare Data Science", "masters", _SPS, "online", "ms", 24),
    ("Master of Science in Information Design and Strategy", "masters", _SPS, "online", "ms", 24),
    ("Master of Science in Information Systems", "masters", _SPS, "online", "ms", 24),
    ("Master of Arts in Literature", "masters", _SPS, "online", "ma", 24),
    ("Master of Fine Arts in Prose and Poetry", "masters", _SPS, "hybrid", "mfa", 24),
    ("Master of Arts in Public Policy and Administration", "masters", _SPS, "hybrid", "ma", 24),
    ("Master of Science in Regulatory Compliance", "masters", _SPS, "online", "ms", 24),
    ("Master of Arts in Sports Administration", "masters", _SPS, "hybrid", "ma", 24),
    ("Master of Arts in Writing", "masters", _SPS, "hybrid", "ma", 24),
    ("Accelerated Master of Science in Data Science", "masters", _SPS, "hybrid", "ms-accel", 15),
    ("Accelerated Master of Science in Information Systems", "masters", _SPS, "hybrid", "ms-accel", 15),
    ("Accelerated Master of Arts in Public Policy and Administration", "masters", _SPS, "hybrid", "ma-accel", 15),
    ("Bachelor of Science in Enterprise Leadership", "bachelors", _SPS, "online", "bs", 48),
    ("Bachelor of Science in Health Sciences", "bachelors", _SPS, "online", "bs", 48),
    ("Bachelor of Science in Information Systems", "bachelors", _SPS, "online", "bs", 48),
    ("Bachelor of Science in Social Sciences", "bachelors", _SPS, "online", "bs", 48),
    ("Bachelor of Science in Strategic Communication", "bachelors", _SPS, "online", "bs", 48),
    ("Bachelor of Philosophy in Biological Sciences", "bachelors", _SPS, "in_person", "bphil", 48),
    ("Bachelor of Philosophy in Communication Studies", "bachelors", _SPS, "in_person", "bphil", 48),
    ("Bachelor of Philosophy in Economics", "bachelors", _SPS, "in_person", "bphil", 48),
    ("Bachelor of Philosophy in English (Writing)", "bachelors", _SPS, "in_person", "bphil", 48),
    ("Bachelor of Philosophy in Humanities", "bachelors", _SPS, "in_person", "bphil", 48),
    ("Bachelor of Philosophy in Organization Behavior", "bachelors", _SPS, "in_person", "bphil", 48),
    ("Bachelor of Philosophy in Psychology", "bachelors", _SPS, "in_person", "bphil", 48),
]


_UG_LABEL = {
    "ba": "Bachelor of Arts",
    "bs": "Bachelor of Science",
    "bmus": "Bachelor of Music",
    "ba-bmus": "dual Bachelor of Arts / Bachelor of Music",
    "bsj": "Bachelor of Science in Journalism",
    "bsed": "Bachelor of Science in Education and Social Policy",
    "bphil": "Bachelor of Philosophy",
}


def _auto_desc(name: str, dtype: str, school: str, suffix: str) -> str:
    word = _DEG_WORD[dtype]
    if dtype == "bachelors":
        label = _UG_LABEL.get(suffix, "undergraduate")
        if name.lower().startswith(("bachelor", "master", "doctor")):
            return f"{name} — an undergraduate degree program at Northwestern University's {school}."
        return (
            f"{name} — an undergraduate {label} program at Northwestern University's {school}."
        )
    if school == _TGS:
        return f"{name} — a {word} program administered by The Graduate School at Northwestern University, in partnership with the disciplinary departments."
    if name.lower().startswith(("bachelor", "master", "doctor", "juris", "full-time", "evening", "executive", "medical", "physician", "driskill", "northwestern", "health", "mmm", "mbai", "jd")):
        return f"{name}, a {word} program at Northwestern University's {school}."
    return f"{name} — a {word} program at Northwestern University's {school}."


PROGRAMS: list[dict] = []
_seen: set[str] = set()


def _add(name: str, dtype: str, school: str, fmt: str, suffix: str, dur: int) -> None:
    slug = f"northwestern-{_slugify(name)}-{suffix}"
    if slug in _seen:
        return
    _seen.add(slug)
    PROGRAMS.append(
        {
            "slug": slug,
            "school": school,
            "program_name": name,
            "degree_type": dtype,
            "duration_months": dur,
            "delivery_format": fmt,
            "description": _auto_desc(name, dtype, school, suffix),
        }
    )


for _n in _WEINBERG_BA:
    _add(_n, "bachelors", _WEINBERG, "in_person", "ba", 48)
for _n in _MCCORMICK_BS:
    _add(_n, "bachelors", _MCCORMICK, "in_person", "bs", 48)
for _name, _dt, _sch, _fmt, _suf, _dur in _GRAD:
    _add(_name, _dt, _sch, _fmt, _suf, _dur or _DUR_DEFAULT[_dt])

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_SPEC_BY_SLUG: dict[str, dict] = {p["slug"]: p for p in PROGRAMS}
_FULL_NAME_BY_SLUG: dict[str, str] = {p["slug"]: p["program_name"] for p in PROGRAMS}

# ── Flagship (deeply-enriched) program: the McCormick B.S. in Computer Science ──
_FLAGSHIP = "northwestern-computer-science-bs"

# Verified program/department home pages (else the owning school's site is used).
_WEBSITE_BY_SLUG: dict[str, str] = {
    _FLAGSHIP: "https://www.mccormick.northwestern.edu/computer-science/",
    "northwestern-computer-science-phd": "https://www.mccormick.northwestern.edu/computer-science/",
    "northwestern-computer-science-ms": "https://www.mccormick.northwestern.edu/computer-science/",
    "northwestern-computer-science-ba": "https://www.mccormick.northwestern.edu/computer-science/academics/undergraduate/",
    "northwestern-economics-ba": "https://economics.northwestern.edu/",
    "northwestern-full-time-mba-mba": "https://www.kellogg.northwestern.edu/programs/full-time-mba/",
    "northwestern-bachelor-of-science-in-journalism-bsj-bsj": "https://www.medill.northwestern.edu/journalism/undergraduate-journalism/",
}

# Program-specific feed keywords (else the program inherits its school's keywords).
_PROGRAM_KEYWORDS_BY_SLUG: dict[str, list[str]] = {
    _FLAGSHIP: ["computer science", "McCormick"],
    "northwestern-full-time-mba-mba": ["Kellogg", "MBA"],
    "northwestern-bachelor-of-science-in-journalism-bsj-bsj": ["Medill", "journalism"],
}

# Tracks / specialization areas — only where verified from the department's official page.
_TRACKS_BY_SLUG: dict[str, dict] = {
    _FLAGSHIP: {
        "label": "Research and specialization areas",
        "items": [
            {"name": "Artificial Intelligence"},
            {"name": "Systems"},
            {"name": "Theory"},
            {"name": "Human-Computer Interaction"},
            {"name": "Security and Privacy"},
            {"name": "Robotics"},
            {"name": "Graphics and Interactive Media"},
            {"name": "Programming Languages"},
        ],
        "note": (
            "Northwestern offers the B.S. in Computer Science through McCormick and a B.A. "
            "through Weinberg, with interdisciplinary 'CS+X' combinations; undergraduates "
            "can specialize through research across the department's areas."
        ),
        "source": "https://www.mccormick.northwestern.edu/computer-science/academics/undergraduate/",
    },
}

# Class profile — omitted for the flagship (Northwestern does not publish a CS-major-specific
# entering-cohort profile); recorded in _program_standard.
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {}

# Faculty contacts — verified department leadership where available.
_FACULTY_BY_SLUG: dict[str, dict] = {
    _FLAGSHIP: {
        "lead": "Samir Khuller, Peter and Adrienne Barris Chair of Computer Science",
        "directory_url": "https://www.mccormick.northwestern.edu/computer-science/people/",
    },
}

# External reviews — ≥2 independent authoritative sources.
_REVIEWS_BY_SLUG: dict[str, dict] = {
    _FLAGSHIP: {
        "summary": (
            "Northwestern's computer science program is regarded as one of the country's "
            "strong CS programs — distinguished by its interdisciplinary 'CS+X' breadth "
            "inside a top-ranked engineering school and by research strength in artificial "
            "intelligence, human-computer interaction, theory and systems."
        ),
        "themes": [
            "Interdisciplinary CS+X breadth",
            "Strong AI, HCI, theory and systems groups",
            "Highly selective, well-resourced department",
        ],
        "sources": [
            {
                "label": "U.S. News Best Colleges — Northwestern University",
                "url": "https://www.usnews.com/best-colleges/northwestern-university-1739",
            },
            {
                "label": "Niche — Northwestern University",
                "url": "https://www.niche.com/colleges/northwestern-university/",
            },
        ],
    },
}

# Who-it's-for + highlights (catalog baselines + flagship override).
_WHO_BASELINE = (
    "Academically exceptional students seeking a research-rich education at a private "
    "university that pairs a close, interdisciplinary undergraduate experience with the "
    "depth of a major research enterprise and Big Ten campus life."
)
_HL_BASELINE = ["Big Ten private research university", "6:1 student-faculty ratio", "Meets full demonstrated need"]
_WHO_GRAD_BASELINE = (
    "Graduate and professional students seeking a top-ranked Northwestern degree with the "
    "resources of a major research university and an internationally recognized faculty."
)
_HL_GRAD_BASELINE = ["Top-ranked Northwestern graduate degree", "World-class faculty", "Big Ten research university"]

_WHO_BY_SLUG: dict[str, str] = {
    _FLAGSHIP: (
        "Technically strong students who want a rigorous, interdisciplinary computer science "
        "education — offered as the McCormick B.S. or the Weinberg B.A. — at a top research "
        "university."
    ),
}
_HL_BY_SLUG: dict[str, list[str]] = {
    _FLAGSHIP: [
        "B.S. (McCormick) or B.A. (Weinberg) options",
        "CS+X interdisciplinary combinations",
        "AI, HCI, systems and theory research",
    ],
}

# ── Costs ──────────────────────────────────────────────────────────────────
_TUITION_UG = 68322  # Northwestern 2024-25 full-time undergraduate tuition (College Navigator).
_UNDERGRAD_COA = 94878  # Total cost of attendance (on campus), 2024-25 (College Navigator).
_AVG_NET_PRICE = 26830  # Average annual net price, 2023-24 (College Navigator).

# Full-time, full-tuition undergraduate schools (the six that admit first-years). SPS
# part-time / online bachelor's degrees are priced per unit, so they do NOT inherit the
# full-time rate (their per-program tuition is recorded omitted, never guessed).
_FULLTIME_UG_SCHOOLS = {_WEINBERG, _MCCORMICK, _MEDILL, _BIENEN, _COMM, _SESP}

# Verified per-program cost overrides (none verified this run; recorded omitted instead).
_COST_BY_SLUG: dict[str, dict] = {}

# ── Outcomes ───────────────────────────────────────────────────────────────
_FOS_CONDITIONS = (
    "Median earnings of federally aided graduates of this specific program measured one "
    "year after completion (U.S. Dept. of Education College Scorecard, Field of Study). "
    "Small cohorts may be suppressed; figures reflect only federally aided students."
)
# Program-level median earnings (1 yr after completion) for programs that match a College
# Scorecard Field-of-Study CIP for UNITID 147767. (slug -> (median_salary, cip)).
_FOS_OUTCOMES: dict[str, tuple[int, str]] = {
    _FLAGSHIP: (99981, "11.07"),
    "northwestern-economics-ba": (84932, "45.06"),
    "northwestern-psychology-ba": (44088, "42.01"),
    "northwestern-political-science-ba": (54737, "45.10"),
    "northwestern-neuroscience-ba": (35334, "26.15"),
}
_OUTCOMES_INSTITUTION = {
    "median_salary": 89363,
    "scope": "institution",
    "earnings_timeframe": "median earnings 10 years after entry (institution-wide)",
    "conditions": (
        "Institution-wide median earnings of federally aided students measured 10 years "
        "after entry (U.S. Dept. of Education College Scorecard); not specific to this "
        "program. Northwestern reports first-destination outcomes university-wide via "
        "Northwestern Career Advancement, not per program."
    ),
    "source": "U.S. Dept. of Education College Scorecard (UNITID 147767)",
    "source_url": "https://collegescorecard.ed.gov/school/?147767",
}

# ── Admissions requirement sets ────────────────────────────────────────────
_REQ_UNDERGRAD = {
    "materials": [
        "Common Application or Coalition Application",
        "Northwestern Writing Supplement",
        "Official secondary-school transcript",
        "School counselor recommendation and one teacher recommendation",
        "Standardized test scores optional (Northwestern is test-optional)",
    ],
    "deadlines": {
        "note": (
            "Early Decision in early November; Regular Decision in early January — see "
            "Northwestern Undergraduate Admission for the current cycle's exact dates."
        )
    },
    "recommendations": "One school counselor recommendation and one teacher recommendation",
    "international": "TOEFL, IELTS or Duolingo English Test for applicants whose first language is not English",
    "application_fee": "$75 (fee waivers available)",
    "source": "https://www.northwestern.edu/undergraduate-admission/",
}
_REQ_MBA = {
    "materials": [
        "Online application with essays",
        "Transcripts from all post-secondary institutions",
        "GMAT or GRE (waivers available for some programs)",
        "Two recommendations",
        "Résumé and video essays",
    ],
    "deadlines": {
        "note": "Kellogg admits in rounds; see the program's admissions page for current round deadlines."
    },
    "international": "TOEFL, IELTS or PTE for applicants whose first language is not English",
    "source": "https://www.kellogg.northwestern.edu/programs/",
}
_REQ_GRAD_GENERIC = {
    "materials": [
        "Online graduate application",
        "Transcripts from all post-secondary institutions",
        "Statement of purpose",
        "Letters of recommendation",
        "Standardized tests where required by the program",
    ],
    "deadlines": {
        "note": "See the program's official admissions page for the current cycle's deadlines."
    },
    "international": "English-proficiency testing (TOEFL/IELTS) for applicants whose first language is not English",
    "source": "https://www.northwestern.edu/academics/",
}


def _requirements_for(spec: dict) -> dict:
    school = spec["school"]
    dt = spec["degree_type"]
    if dt == "bachelors" and school in _FULLTIME_UG_SCHOOLS:
        return dict(_REQ_UNDERGRAD)
    if school == _KELLOGG and dt == "masters":
        return dict(_REQ_MBA)
    return dict(_REQ_GRAD_GENERIC)


def _has_undergrad_rate(spec: dict) -> bool:
    """A program inherits the published full-time undergraduate tuition only when it is a
    bachelor's degree from one of the six full-time undergraduate schools."""
    return spec["degree_type"] == "bachelors" and spec["school"] in _FULLTIME_UG_SCHOOLS


def _program_standard(slug: str) -> dict:
    """Per-program omitted-field list (verified-unavailable), for _standard."""
    omitted: list[str] = [
        # Northwestern reports first-destination outcomes university-wide (Northwestern Career
        # Advancement), not per program, so every program omits the program-level employment
        # rate and top-industries breakdown.
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
    spec = _SPEC_BY_SLUG.get(slug)
    # Tuition is set only from a verified override or the full-time undergraduate rate; every
    # other program (graduate/professional, and SPS part-time/online bachelor's degrees that
    # are priced per unit) omits tuition rather than guessing it.
    if spec is not None and slug not in _COST_BY_SLUG and not _has_undergrad_rate(spec):
        omitted.append("cost_data.tuition_usd")
    return _standard(omitted)


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich Northwestern to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when Northwestern is absent — safe on fresh/CI databases.
    """
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
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
    inst.founded_year = 1851
    inst.campus_setting = "suburban"
    if not inst.website_url:
        inst.website_url = "https://www.northwestern.edu"
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
        sc.content_sources = _school_content(spec["name"])
        by_name[spec["name"]] = sc
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
        p.website_url = _WEBSITE_BY_SLUG.get(slug) or _SCHOOL_WEBSITE.get(spec["school"])
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec.get("delivery_format", "in_person")
        _kw = _PROGRAM_KEYWORDS_BY_SLUG.get(slug) or list(
            _SCHOOL_FEED_SPEC[spec["school"]]["keywords"]
        )
        p.content_sources = _program_content(spec["school"], _kw)
        cost_override = _COST_BY_SLUG.get(slug)
        if cost_override is not None:
            p.tuition = cost_override.get("tuition_usd")
            p.cost_data = dict(cost_override)
        elif _has_undergrad_rate(spec):
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
                    "Published 2024-25 Northwestern full-time undergraduate tuition with the "
                    "College Navigator total cost of attendance and average net price. "
                    "Northwestern meets 100% of demonstrated financial need, so most families "
                    "pay well below the sticker price (average net price ≈ $26,800)."
                ),
                "source": "NCES College Navigator (UNITID 147767), 2024-25",
                "source_url": "https://nces.ed.gov/collegenavigator/?id=147767",
                "year": "2024-25",
            }
        else:
            p.tuition = None
            p.cost_data = {
                "note": (
                    "Tuition for this program varies and is published on the school's "
                    "official tuition page; a verified per-program figure is not yet "
                    "recorded here."
                ),
                "source": "Northwestern University — program tuition pages",
                "source_url": _SCHOOL_WEBSITE.get(spec["school"], "https://www.northwestern.edu"),
            }
        p.application_requirements = _requirements_for(spec)
        fos = _FOS_OUTCOMES.get(slug)
        if fos is not None:
            salary, cip = fos
            outcomes = {
                "median_salary": salary,
                "scope": "program",
                "cip": cip,
                "earnings_timeframe": "median earnings 1 year after completion",
                "conditions": _FOS_CONDITIONS,
                "source": "U.S. Dept. of Education College Scorecard — Field of Study",
                "source_url": "https://collegescorecard.ed.gov/school/?147767",
            }
        else:
            outcomes = dict(_OUTCOMES_INSTITUTION)
        outcomes["_standard"] = _program_standard(slug)
        p.outcomes_data = outcomes
        if spec["degree_type"] in ("masters", "phd", "professional"):
            p.who_its_for = _WHO_BY_SLUG.get(slug) or _WHO_GRAD_BASELINE
            p.highlights = _HL_BY_SLUG.get(slug) or _HL_GRAD_BASELINE
        else:
            p.who_its_for = _WHO_BY_SLUG.get(slug) or _WHO_BASELINE
            p.highlights = _HL_BY_SLUG.get(slug) or _HL_BASELINE
        p.tracks = _TRACKS_BY_SLUG.get(slug)
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(slug)
        p.faculty_contacts = _FACULTY_BY_SLUG.get(slug)
        p.external_reviews = _REVIEWS_BY_SLUG.get(slug)
        p.application_deadline = date(2027, 1, 2) if _has_undergrad_rate(spec) else None
    session.flush()
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
