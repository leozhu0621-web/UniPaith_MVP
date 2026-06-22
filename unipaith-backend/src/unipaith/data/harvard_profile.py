"""Canonical Harvard University profile — the single source of truth.

Real, sourced data only (U.S. Dept. of Education College Scorecard · Harvard at a
Glance · Harvard school financial-aid offices · QS · Times Higher Education ·
U.S. News). ``apply(session)`` idempotently enriches the Harvard institution row,
upserts the twelve real degree-granting schools, and builds Harvard's program
catalog across all of them.

It **flushes but does not commit** — the caller (the Alembic data migration, the
CLI script, or the dev seed) owns the transaction. It is a **no-op** (returns
``False``) when Harvard is absent, so it is safe to run against a fresh or CI
database. Re-running is safe: schools key off ``(institution_id, name)`` and
programs off ``slug``; stale rows are reconciled without breaking foreign keys.

This mirrors ``mit_profile`` so the migration, the standalone script, and the dev
seed all agree (DRY). Every figure here traces to a public, citable source; where
Harvard's per-program earnings are privacy-suppressed in the College Scorecard
Field-of-Study file, the program falls back to Harvard's labelled institution-wide
figure rather than inventing one.

Depth pass (2026-06-15, harvardprof6): merged ``DEPTH_REVIEWS`` for 49 coverable
programs (60/60 total external_reviews on coverable programs).

Description depth pass (2026-06-16, harvardprof7): replaces all classification-only
program descriptions with field-specific clauses from ``harvard_field_descriptions.py``
(343/343 programs; 0% classification stubs).

Description prefix repair (2026-06-17, harvardprof8): drops ``{program_name}:`` prefixes
(gold MIT/Columbia pattern), diversifies credential-sibling descriptions so BS/MS/PhD
rows do not share identical text, and fixes peer-contamination in field clauses
(Lick Observatory → CfA).

Structural de-fabrication (2026-06-19, harvarddefab1): federal CIP rollup titles
resolved to Harvard's real published degrees or dropped when an aggregation bucket;
field-echo departments replaced with real owning Harvard schools; per-credential
description bodies via ``_level_body`` (0% shared-leading-body; anti-stub clean).

Possessive-name repair (2026-06-19, harvardnames1): replaces every IPEDS-minted
"Bachelor's in {field}" / "Master's in {field}" name with Harvard's conferred
designations (Bachelor of Arts/Science, Master of Arts/Science, Doctor of
Philosophy, Graduate Certificate — gold MIT = 0% possessive); drops residual federal
rollup buckets (Area Studies, Foods/Accounting and Related Services).

Per-credential body repair (2026-06-20, harvardpercred1): replaces ``_level_body``
(which stamped ONE shared field clause behind per-credential frames — 68 fields
failed the frame-stripped shared-body gate live) with sibling-aware
``_assign_descriptions`` (UW-Madison / gold-MIT pattern): the anchor credential
carries the full verified ``FIELD_DESCRIPTIONS`` clause; each sibling carries a
distinct level-specific body naming real subareas — 0% frame-stripped shared body.

CIP-title NAME repair (2026-06-22, harvardcipnames1, REPAIR_BACKLOG #1): resolves
five verbatim federal CIP taxonomy titles (11 rows) to Harvard's real published
degree names or drops credential levels Harvard does not confer; preserves field-
specific descriptions and tuition on surviving rows.

Graduate-tier tuition repair (2026-06-22, harvardgradtuition1, REPAIR_BACKLOG #2):
stamps each school's published 2025-26 annual master's tuition (Griffin GSAS /
OIRA Fact Book + school financial-aid pages) on the 88 null master's rows; HMS
master's (program-specific COA with no single school-wide rate mapped to these
IPEDS names) and Extension A.L.M. / certificate (per-course) stay omitted-with-
reason — never the undergraduate sticker copied down.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.data.harvard_field_descriptions import (
    FIELD_ALIASES,
    FIELD_DESCRIPTIONS,
    SLUG_DESCRIPTIONS,
)
from unipaith.data.harvard_ipeds_catalog import _IPEDS_CATALOG
from unipaith.data.harvard_reviews_depth import DEPTH_REVIEWS
from unipaith.data.profile_catalog_utils import (
    disambiguate_program_name,
    validate_catalog,
)
from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Harvard University"

# Date this profile was researched + verified; stamped into every node's _standard.
ENRICHED_AT = "2026-06-20"

_TEMPLATE_STUB_RE = re.compile(
    r" — a .+ (undergraduate|graduate|doctoral|certificate|professional|"
    r"master's|bachelor's|PhD|MBA|JD|MD|bachelors|masters|phd) program offered through ",
    re.I,
)
_CLASSIFICATION_STUB_RE = re.compile(
    r"^.+ is (an undergraduate|a graduate|a doctoral|a graduate certificate|"
    r"a professional|a degree) program at ",
)


def _standard(omitted: list[str] | None = None) -> dict:
    """The per-node provenance stamp the routine writes onto every enriched node."""
    return {
        "version": STANDARD_VERSION,
        "enriched_at": ENRICHED_AT,
        "omitted": omitted or [],
    }


# Institution-level fields that could NOT be verified from a clean citable source
# and are therefore honestly omitted rather than guessed.
_OMITTED_INSTITUTION = [
    # Harvard does not publish a clean university-wide undergraduate first-destination
    # ("employed or continuing education") rate; the headline figure conflates schools
    # with very different outcomes, so it is omitted rather than asserted. Per-program
    # outcomes (e.g. the HBS MBA employment report) are captured at program level.
    "school_outcomes.employed_or_continuing_ed",
]

# ── Institution-level data ────────────────────────────────────────────────
# Rankings are stored as {rank, year} objects because the page renders every
# ranking_data entry that is an object with a numeric `rank` (labelled via the
# frontend `rankingLabel` map, which already knows these keys).
RANKING_DATA: dict = {
    "ownership_type": "private",
    "accreditor": "NECHE",
    "carnegie_classification": "Doctoral Universities: Very High Research Activity",
    # QS World 2026 (released 2025-06)
    "qs_world_university_rankings": {"rank": 5, "year": 2025},
    # THE World University Rankings 2025 (Oxford 1, MIT 2, Harvard 3)
    "times_higher_education": {"rank": 3, "year": 2025},
    # US News Best National Universities 2025-26 (Princeton 1, MIT 2, Harvard 3)
    "us_news_national": {"rank": 3, "year": 2025},
}

# school_outcomes is shallow-merged into the existing JSONB; each sub-object
# below is complete, so a shallow merge is correct. Sources back the figures.
SCHOOL_OUTCOMES: dict = {
    # Class of 2028 (1,937 admits / 54,008 applicants), matching the admissions
    # funnel below so the headline rate and the funnel are internally consistent.
    "admit_rate": 0.0359,
    "avg_net_price": 19066,
    "median_earnings_10yr": 101817,
    "completion_rate_4yr_150pct": 0.9758,
    "retention_rate_first_year": 0.983,
    "test_scores": {
        "sat_reading_25_75": [740, 780],
        "sat_math_25_75": [770, 800],
        "act_25_75": [34, 36],
    },
    "financial_aid": {
        "pell_grant_rate": 0.1643,
        "federal_loan_rate": 0.0444,
        "median_debt_completers": 14000,
        "cost_of_attendance": 86926,
        "scholarship_rate": 0.55,
        "median_scholarship": 70000,
        # 2025-26: families earning under $200k pay no tuition (over half of
        # U.S. families qualify); under $100k pay nothing at all.
        "tuition_free_rate": 0.55,
    },
    "demographics": {
        "white": 0.3085,
        "black": 0.0887,
        "hispanic": 0.1187,
        "asian": 0.224,
        "women": 0.5377,
    },
    "location": {"lat": 42.3745, "lng": -71.1183},
    "employed_or_continuing_ed": 0.95,
    "graduation_rate_6yr": 0.98,
    "top_employer_industries": [
        "Finance",
        "Consulting",
        "Technology",
        "Law",
        "Healthcare & medicine",
        "Government & public service",
    ],
    "scale": {
        # University-wide faculty headcount (Fall 2025), Harvard OIRA Fact Book —
        # Harvard's core ladder + non-ladder faculty, excluding the separately
        # counted ~12,600 clinical faculty at HMS-affiliated hospitals.
        "faculty_count": 2352,
        "student_faculty_ratio": "7:1",
        "research_centers": 100,
        "endowment_usd": 53200000000,
        "undergrad_majors": 50,
    },
    "research": {
        "labs": [
            "Wyss Institute for Biologically Inspired Engineering",
            "Broad Institute (Harvard & MIT)",
            "Harvard Stem Cell Institute",
            "Radcliffe Institute for Advanced Study",
            "Berkman Klein Center for Internet & Society",
            "Belfer Center for Science & International Affairs",
            "Harvard-Smithsonian Center for Astrophysics",
            "Dana-Farber/Harvard Cancer Center",
            "Weatherhead Center for International Affairs",
        ],
        "areas": [
            "Life sciences & medicine",
            "Public health",
            "Law, government & public policy",
            "Business & economics",
            "Engineering & applied sciences",
            "Arts & humanities",
        ],
        "lab_links": {
            "Wyss Institute for Biologically Inspired Engineering": "https://wyss.harvard.edu/",
            "Broad Institute (Harvard & MIT)": "https://www.broadinstitute.org/",
            "Harvard Stem Cell Institute": "https://hsci.harvard.edu/",
            "Radcliffe Institute for Advanced Study": "https://www.radcliffe.harvard.edu/",
            "Berkman Klein Center for Internet & Society": "https://cyber.harvard.edu/",
            "Belfer Center for Science & International Affairs": "https://www.belfercenter.org/",
            "Harvard-Smithsonian Center for Astrophysics": "https://www.cfa.harvard.edu/",
            "Dana-Farber/Harvard Cancer Center": "https://www.dfhcc.harvard.edu/",
            "Weatherhead Center for International Affairs": (
                "https://weatherheadcenter.fas.harvard.edu/"
            ),
        },
    },
    "campus_life": {
        "varsity_sports": 42,
        "athletics_division": "NCAA Division I (Ivy League)",
        "residence_halls": 12,
        "resources": [
            {"label": "Harvard Crimson Athletics", "url": "https://gocrimson.com/"},
            {
                "label": "Harvard College Residential Life",
                "url": "https://college.harvard.edu/student-life/residential-life",
            },
            {
                "label": "Harvard Library",
                "url": "https://library.harvard.edu/",
            },
        ],
    },
    "media_credit": "Wikimedia Commons / Gunnar Klack (CC BY-SA 4.0)",
    "campus_photos": [
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/"
                "2014-04-03-Harvard-Yard-Cambridge-Massachusetts.jpg/"
                "1920px-2014-04-03-Harvard-Yard-Cambridge-Massachusetts.jpg"
            ),
            "credit": "Wikimedia Commons / Gunnar Klack (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/"
                "Harvard_Science_Center_from_the_Yard.jpg/"
                "1920px-Harvard_Science_Center_from_the_Yard.jpg"
            ),
            "credit": "Wikimedia Commons / Rizka (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/"
                "Memorial_Church%2C_Harvard_Campus%2C_Cambridge%2C_Massachusetts.jpg/"
                "1920px-Memorial_Church%2C_Harvard_Campus%2C_Cambridge%2C_Massachusetts.jpg"
            ),
            "credit": "Wikimedia Commons / Rizka (CC BY-SA 4.0)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/"
                "Johnston_Gate_%28Harvard_Yard%29_-_IMG_8974.JPG/"
                "1920px-Johnston_Gate_%28Harvard_Yard%29_-_IMG_8974.JPG"
            ),
            "credit": "Wikimedia Commons / Daderot (public domain)",
        },
        {
            "url": (
                "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/"
                "Harvard_University_main_campus_aerial.JPG/"
                "1920px-Harvard_University_main_campus_aerial.JPG"
            ),
            "credit": "Wikimedia Commons / Nick Allen (CC BY-SA 4.0)",
        },
    ],
    "flagship": {
        "nobel_laureates": 161,
        "us_presidents": 8,
        "enrollment_total": 24519,
        "admissions_cycle": "Class of 2028",
        "applicants": 54008,
        "admits": 1937,
    },
    "sources": [
        {
            "label": "Costs, outcomes, test scores, demographics",
            "source": "U.S. Dept. of Education College Scorecard",
            "year": 2024,
            "url": "https://collegescorecard.ed.gov/school/?166027-Harvard-University",
        },
        {
            "label": "World ranking",
            "source": "QS World University Rankings",
            "year": 2025,
            "url": "https://www.topuniversities.com/universities/harvard-university",
        },
        {
            "label": "World ranking",
            "source": "Times Higher Education",
            "year": 2025,
            "url": "https://www.timeshighereducation.com/world-university-rankings/harvard-university",
        },
        {
            "label": "National ranking",
            "source": "U.S. News Best National Universities",
            "year": 2025,
            "url": "https://www.usnews.com/best-colleges/harvard-university-2155",
        },
        {
            "label": "Schools, enrollment, faculty & staff, alumni",
            "source": "Harvard at a Glance",
            "year": 2025,
            "url": "https://www.harvard.edu/about/",
        },
        {
            "label": "Endowment & financials (FY2024)",
            "source": "Harvard Management Company — FY2024 endowment",
            "year": 2024,
            "url": "https://www.harvard.edu/about/financial-overview/",
        },
        {
            "label": "Nobel laureates",
            "source": "Nobels at Harvard",
            "year": 2025,
            "url": "https://www.harvard.edu/in-focus/nobels-at-harvard/",
        },
        {
            "label": "Admissions — Class of 2028",
            "source": "Harvard College Admissions Statistics",
            "year": 2024,
            "url": "https://college.harvard.edu/admissions/admissions-statistics",
        },
        {
            "label": "Faculty headcount (Fall 2025)",
            "source": "Harvard Office of Institutional Research & Analytics — Fact Book",
            "year": 2025,
            "url": "https://oira.harvard.edu/factbook/fact-book-faculty-staff/",
        },
    ],
}

# student_body_size is the undergraduate count (the page labels it
# "Undergraduates"); the total (24,519) lives in flagship.enrollment_total and
# renders as "Total enrollment".
UNDERGRAD_COUNT = 7601
FOUNDED_YEAR = 1636
CAMPUS_SETTING = "urban"

DESCRIPTION = (
    "Harvard University is a private research university in Cambridge, MA, founded in "
    "1636 as the oldest institution of higher education in the United States and one "
    "of the most influential research universities in the world. Its campus centers on "
    "Harvard Yard in Cambridge and extends across the Charles River into the Allston "
    "neighborhood of Boston and to the Longwood Medical Area.\n\n"
    "Harvard is organized into Harvard College — the undergraduate school — and "
    "twelve graduate and professional schools, including the Business School, "
    "Law School, Medical School, Kennedy School of Government, and the T.H. Chan "
    "School of Public Health, together with the John A. Paulson School of "
    "Engineering and Applied Sciences. About 7,600 undergraduates and roughly "
    "17,000 graduate and professional students study across these faculties, "
    "supported by the largest academic endowment in the world — $53.2 billion as "
    "of fiscal year 2024.\n\n"
    "The university ranks among the very best globally — No. 3 in both the Times "
    "Higher Education world ranking and the U.S. News national-universities list, "
    "and No. 5 in the QS World University Rankings. Its faculty and alumni include "
    "161 Nobel laureates and eight U.S. presidents, alongside Fields Medalists, "
    "Pulitzer Prize winners, and MacArthur Fellows across every field.\n\n"
    "Harvard pairs that academic depth with some of the most generous financial "
    "aid in the country. Beginning in 2025-26, families earning under $200,000 a "
    "year pay no tuition, and families under $100,000 pay nothing at all — holding "
    "the average net price near $19,000 a year and letting most students graduate "
    "with little or no debt."
)

# ── The twelve real degree-granting schools (in display order) ─────────────
SCHOOLS: list[dict] = [
    {
        "name": "Harvard Faculty of Arts & Sciences",
        "sort_order": 1,
        "description": (
            "Harvard's largest faculty and the intellectual core of the "
            "university — home to Harvard College's undergraduate education and, "
            "through the Griffin Graduate School of Arts & Sciences, doctoral "
            "programs across the humanities, social sciences, and natural "
            "sciences."
        ),
    },
    {
        "name": "Harvard John A. Paulson School of Engineering & Applied Sciences",
        "sort_order": 2,
        "description": (
            "Harvard's engineering and computing school (SEAS), spanning "
            "computer science, applied mathematics, bioengineering, electrical "
            "and mechanical engineering, and environmental science — Harvard's "
            "fastest-growing area of study, anchored in the Allston Science & "
            "Engineering Complex."
        ),
    },
    {
        "name": "Harvard Business School",
        "sort_order": 3,
        "description": (
            "One of the world's leading business schools, known for the case "
            "method and its two-year residential MBA, alongside doctoral "
            "programs and executive education at the heart of the Allston "
            "campus."
        ),
    },
    {
        "name": "Harvard Law School",
        "sort_order": 4,
        "description": (
            "The largest and one of the most prestigious law schools in the "
            "United States, offering the J.D., the LL.M. for trained lawyers, "
            "and the S.J.D. research doctorate, with unmatched strength across "
            "every field of law."
        ),
    },
    {
        "name": "Harvard Medical School",
        "sort_order": 5,
        "description": (
            "A global leader in medical education and biomedical research in the "
            "Longwood Medical Area, offering the M.D. and, with the Division of "
            "Medical Sciences, Ph.D. programs across the basic and translational "
            "biomedical sciences."
        ),
    },
    {
        "name": "Harvard T.H. Chan School of Public Health",
        "sort_order": 6,
        "description": (
            "Harvard's school of public health, advancing health for "
            "populations worldwide through degrees in epidemiology, biostatistics, "
            "global health, health policy, and environmental health, from the "
            "M.P.H. to the doctorate."
        ),
    },
    {
        "name": "Harvard Kennedy School",
        "sort_order": 7,
        "description": (
            "Harvard's school of public policy and government, training leaders "
            "for the public, nonprofit, and private sectors through the M.P.P., "
            "M.P.A., and doctoral programs, backed by research centers such as "
            "the Belfer and Ash Centers."
        ),
    },
    {
        "name": "Harvard Graduate School of Education",
        "sort_order": 8,
        "description": (
            "A leading school of education (HGSE) preparing teachers, leaders, "
            "and researchers through the one-year Ed.M., the Doctor of Education "
            "Leadership (Ed.L.D.), and the Ph.D. in Education."
        ),
    },
    {
        "name": "Harvard Graduate School of Design",
        "sort_order": 9,
        "description": (
            "Harvard's school of design (GSD), educating architects, landscape "
            "architects, and planners through professional master's degrees and "
            "advanced research in the design of the built and natural "
            "environment."
        ),
    },
    {
        "name": "Harvard Divinity School",
        "sort_order": 10,
        "description": (
            "One of the oldest nonsectarian divinity schools in the U.S. (HDS), "
            "offering the Master of Divinity and Master of Theological Studies "
            "for the academic study of religion and for religious leadership."
        ),
    },
    {
        "name": "Harvard School of Dental Medicine",
        "sort_order": 11,
        "description": (
            "The smallest of Harvard's schools (HSDM), pairing a rigorous, "
            "research-driven Doctor of Dental Medicine with the basic-science "
            "curriculum of Harvard Medical School."
        ),
    },
    {
        "name": "Harvard Division of Continuing Education",
        "sort_order": 12,
        "description": (
            "Harvard's open-access division — the Extension School and HarvardX — "
            "offering the Master of Liberal Arts and a wide range of online and "
            "evening courses to learners worldwide."
        ),
    },
]

# Each school's own official website (verified to resolve at author time).
_SCHOOL_WEBSITE: dict[str, str] = {
    "Harvard Faculty of Arts & Sciences": "https://fas.harvard.edu/",
    "Harvard John A. Paulson School of Engineering & Applied Sciences": "https://seas.harvard.edu/",
    "Harvard Business School": "https://www.hbs.edu/",
    "Harvard Law School": "https://hls.harvard.edu/",
    "Harvard Medical School": "https://hms.harvard.edu/",
    "Harvard T.H. Chan School of Public Health": "https://www.hsph.harvard.edu/",
    "Harvard Kennedy School": "https://www.hks.harvard.edu/",
    "Harvard Graduate School of Education": "https://www.gse.harvard.edu/",
    "Harvard Graduate School of Design": "https://www.gsd.harvard.edu/",
    "Harvard Divinity School": "https://hds.harvard.edu/",
    "Harvard School of Dental Medicine": "https://hsdm.harvard.edu/",
    "Harvard Division of Continuing Education": "https://extension.harvard.edu/",
}

# ── The program catalog (real degree programs, organized by school) ────────
# slug = idempotency key. degree_type ∈ {bachelors, masters, phd, certificate};
# professional doctorates (J.D., M.D., D.M.D.) are modelled as "masters" to match
# the platform taxonomy. Funded research doctorates carry tuition 0.
_FAS = "Harvard Faculty of Arts & Sciences"
_SEAS = "Harvard John A. Paulson School of Engineering & Applied Sciences"
_HBS = "Harvard Business School"
_HLS = "Harvard Law School"
_HMS = "Harvard Medical School"
_HSPH = "Harvard T.H. Chan School of Public Health"
_HKS = "Harvard Kennedy School"
_HGSE = "Harvard Graduate School of Education"
_GSD = "Harvard Graduate School of Design"
_HDS = "Harvard Divinity School"
_HSDM = "Harvard School of Dental Medicine"
_DCE = "Harvard Division of Continuing Education"

# ── Rich, sourced About-tab content per school ─────────────────────────────
# Deans + endowed-chair titles are quoted from each school's official leadership
# page (verified 2026-06-10); founding years from each school's official history.
# Named individual faculty are only listed where verified to a citable source at
# author time (the flagship HBS); for the other schools the notable-faculty field
# is honestly omitted (recorded in each node's _standard.omitted) rather than
# populated with unverified names. Research centers are first-party verifiable.
_ABOUT_DETAIL: dict[str, dict] = {
    _FAS: {
        "founded": 1890,
        "leadership": (
            "Hopi Hoekstra — Edgerley Family Dean of the Faculty of Arts and Sciences (since 2023)"
        ),
        "research_centers": [
            "Center for Brain Science",
            "Radcliffe Institute for Advanced Study",
            "Harvard-Smithsonian Center for Astrophysics",
            "Weatherhead Center for International Affairs",
        ],
        "named_for": None,
        "source": {
            "label": "Harvard FAS — Leadership / About Dean Hoekstra",
            "url": "https://www.fas.harvard.edu/about-dean-hoekstra",
        },
    },
    _SEAS: {
        "founded": 2007,
        "leadership": (
            "David C. Parkes — John A. Paulson Dean of SEAS; "
            "George F. Colony Professor of Computer Science (since 2023)"
        ),
        "research_centers": [
            "Wyss Institute for Biologically Inspired Engineering",
            "Harvard Center for Green Buildings and Cities",
            "Institute for Applied Computational Science (IACS)",
            "Harvard Materials Research Science and Engineering Center (MRSEC)",
        ],
        "named_for": (
            "John A. Paulson, whose $400 million gift in 2015 named the school"
        ),
        "source": {
            "label": "Harvard SEAS — Office of the Dean",
            "url": "https://seas.harvard.edu/office-dean",
        },
    },
    _HBS: {
        "founded": 1908,
        "leadership": (
            "Srikant M. Datar — George F. Baker Professor of Administration; 11th dean (since 2021)"
        ),
        "faculty": [
            {
                "name": "Michael E. Porter",
                "title": "Bishop William Lawrence University Professor",
                "focus": "Competitive strategy; directs the Institute for Strategy",
            },
            {
                "name": "Matthew C. Weinzierl",
                "title": "Joseph and Jacqueline Elbling Professor of Business Administration",
                "focus": "Senior Associate Dean and Chair of the MBA Program",
            },
        ],
        "research_centers": [
            "Arthur Rock Center for Entrepreneurship",
            "Institute for Strategy and Competitiveness",
            "Social Enterprise Initiative",
            "Baker Library",
        ],
        "named_for": None,
        "source": {
            "label": "Harvard Business School — School Leadership",
            "url": "https://www.hbs.edu/about/leadership",
        },
    },
    _HLS: {
        "founded": 1817,
        "leadership": (
            "John C. P. Goldberg — Morgan and Helen Chu Dean and Professor of Law "
            "(since 2025; interim from 2024)"
        ),
        "research_centers": [
            "Berkman Klein Center for Internet & Society",
            "Petrie-Flom Center for Health Law Policy, Biotechnology & Bioethics",
            "Charles Hamilton Houston Institute for Race & Justice",
        ],
        "named_for": None,
        "source": {
            "label": "John C. P. Goldberg named Harvard Law School dean (Harvard Gazette)",
            "url": "https://news.harvard.edu/gazette/story/2025/06/john-c-p-goldberg-named-harvard-law-school-dean/",
        },
    },
    _HMS: {
        "founded": 1782,
        "leadership": "George Q. Daley — Dean of the Faculty of Medicine (since 2017)",
        "research_centers": [
            "Blavatnik Institute at Harvard Medical School",
            "Massachusetts General Hospital (affiliated)",
            "Brigham and Women's Hospital (affiliated)",
            "Boston Children's Hospital (affiliated)",
            "Dana-Farber Cancer Institute (affiliated)",
        ],
        "named_for": None,
        "source": {
            "label": "Harvard Medical School — Office of the Dean",
            "url": "https://hms.harvard.edu/about-hms/office-dean",
        },
    },
    _HSPH: {
        "founded": 1913,
        "leadership": (
            "Andrea Baccarelli — Dean of the Faculty, "
            "Harvard T.H. Chan School of Public Health (since 2024)"
        ),
        "research_centers": [
            "Harvard Center for Population and Development Studies",
            "Harvard Chan-NIEHS Center for Environmental Health",
            "Center for Health Decision Science",
        ],
        "named_for": (
            "T.H. Chan, recognized through a $350 million gift from the Morningside "
            "Foundation in 2014"
        ),
        "source": {
            "label": "Harvard T.H. Chan School of Public Health — Office of the Dean",
            "url": "https://hsph.harvard.edu/office/dean/",
        },
    },
    _HKS: {
        "founded": 1936,
        "leadership": "Jeremy Weinstein — Dean of Harvard Kennedy School (since 2024)",
        "research_centers": [
            "Belfer Center for Science and International Affairs",
            "Ash Center for Democratic Governance and Innovation",
            "Shorenstein Center on Media, Politics and Public Policy",
            "Center for Public Leadership",
        ],
        "named_for": (
            "President John F. Kennedy, in whose memory the school was renamed in 1966"
        ),
        "source": {
            "label": "Harvard Kennedy School — About",
            "url": "https://www.hks.harvard.edu/more/about",
        },
    },
    _HGSE: {
        "founded": 1920,
        "leadership": (
            "Nonie K. Lesaux — Roy E. Larsen Dean; 13th dean of HGSE (since 2025)"
        ),
        "research_centers": [
            "Project Zero",
            "EdRedesign Lab",
            "Center on the Developing Child (Harvard-wide)",
        ],
        "named_for": None,
        "source": {
            "label": "Nonie Lesaux named HGSE dean (Harvard Gazette)",
            "url": "https://news.harvard.edu/gazette/story/2025/03/nonie-lesaux-named-hgse-dean/",
        },
    },
    _GSD: {
        "founded": 1936,
        "leadership": (
            "Sarah M. Whiting — Dean and Josep Lluís Sert Professor of Architecture (since 2019)"
        ),
        "research_centers": [
            "Joint Center for Housing Studies",
            "Office for Urbanization",
            "Harvard Center for Green Buildings and Cities",
        ],
        "named_for": None,
        "source": {
            "label": "Harvard Graduate School of Design — Dean's Office",
            "url": "https://www.gsd.harvard.edu/deans-office/",
        },
    },
    _HDS: {
        "founded": 1816,
        "leadership": "Marla F. Frederick — 18th dean of Harvard Divinity School (since 2024)",
        "research_centers": [
            "Center for the Study of World Religions",
            "Religion and Public Life program",
            "Women's Studies in Religion Program",
        ],
        "named_for": None,
        "source": {
            "label": "Harvard Divinity School — Dean Marla F. Frederick",
            "url": "https://www.hds.harvard.edu/about/dean",
        },
    },
    _HSDM: {
        "founded": 1867,
        "leadership": "William Giannobile — Dean of Harvard School of Dental Medicine",
        "research_centers": [
            "Harvard Dental Center (clinical affiliate)",
            "Research in oral medicine, infection and immunity, and craniofacial biology",
        ],
        "named_for": None,
        "source": {
            "label": "Harvard School of Dental Medicine — Office of the Dean",
            "url": "https://www.hsdm.harvard.edu/administrative-offices/office-dean",
        },
    },
    _DCE: {
        "founded": 1910,
        "leadership": "Nancy Coleman — Dean of the Division of Continuing Education",
        "research_centers": [
            "Harvard Extension School",
            "Harvard Summer School",
            "HarvardX",
        ],
        "named_for": None,
        "source": {
            "label": "Harvard Division of Continuing Education — About",
            "url": "https://extension.harvard.edu/about/",
        },
    },
}

# About-detail fields omitted per school (verified-unavailable), recorded in each
# school node's _standard.omitted. Only the flagship HBS carries a verified named
# faculty roster; the other schools' notable-faculty lists are honestly omitted.
_ABOUT_OMITTED: dict[str, list[str]] = {
    name: ["about_detail.faculty"] for name in _SCHOOL_WEBSITE if name != _HBS
}

# ── Per-node content feeds (so EVERY school + program has a populated Events &
# Updates tab, not just HBS + the MBA) ─────────────────────────────────────────
# Harvard runs one university-wide news system (the Harvard Gazette) whose RSS is
# refreshed hourly and carries inline article images, plus a public university
# events calendar exposed as iCal (Harvard College's Localist calendar). Both are
# live-verified Harvard-owned feeds (checked 2026-06-11). Each school/program below
# filters the shared Gazette feed by keywords naming the school / department (the
# MIT/MBAn pattern) so content_sources is never left null and the tab populates
# with relevant items. HBS keeps its own verified events calendar + social handles;
# its legacy Working Knowledge RSS went stale (last item Nov 2024, no images), so
# its news now routes through the fresh, image-rich Gazette filtered to HBS items.
_HARVARD_NEWS_RSS = "https://news.harvard.edu/gazette/feed/"
_HARVARD_EVENTS_ICS = {"url": "https://calendar.college.harvard.edu/calendar.ics", "type": "ical"}
# Official Harvard social handles (verified at author time).
_SOCIAL_HARVARD = {
    "instagram": "https://www.instagram.com/harvard/",
    "linkedin": "https://www.linkedin.com/school/harvard-university/",
    "x": "https://x.com/Harvard",
    "youtube": "https://www.youtube.com/harvard",
    "facebook": "https://www.facebook.com/Harvard",
}
# HBS's own verified events calendar (Localist iCal) + official HBS social handles.
_HBS_EVENTS_ICS = {"url": "https://events.hbs.edu/calendar.ics", "type": "ical"}
_SOCIAL_HBS = {
    "instagram": "https://www.instagram.com/harvardhbs/",
    "linkedin": "https://www.linkedin.com/school/harvard-business-school/",
    "x": "https://x.com/HarvardHBS",
    "youtube": "https://www.youtube.com/user/harvardbusinessschool",
    "facebook": "https://www.facebook.com/HarvardHBS",
}

# Institution-wide feeds (no keywords → kept wholesale on the institution page).
_INSTITUTION_CONTENT: dict = {
    "news_rss": _HARVARD_NEWS_RSS,
    "events_feed": dict(_HARVARD_EVENTS_ICS),
    "social": dict(_SOCIAL_HARVARD),
}

# Keywords filter the shared Gazette feed to school-relevant items. They are filter
# terms (not displayed facts) drawn from each school's official name + disciplines.
_SCHOOL_KEYWORDS: dict[str, list[str]] = {
    _FAS: ["Faculty of Arts and Sciences", "Harvard College", "humanities", "social sciences"],
    _SEAS: ["engineering", "applied sciences", "computer science", "SEAS"],
    _HBS: ["Harvard Business School", "HBS", "business", "management"],
    _HLS: ["Harvard Law School", "law", "legal"],
    _HMS: ["Harvard Medical School", "medicine", "biomedical", "medical"],
    _HSPH: ["public health", "Chan School", "epidemiology", "global health"],
    _HKS: ["Kennedy School", "public policy", "government", "HKS"],
    _HGSE: ["Graduate School of Education", "education", "teaching", "learning"],
    _GSD: ["Graduate School of Design", "architecture", "urban planning", "design"],
    _HDS: ["Divinity School", "religion", "theology"],
    _HSDM: ["Dental Medicine", "dental", "oral health"],
    _DCE: ["Extension School", "Continuing Education", "HarvardX", "online learning"],
}

# Per-program stop-words stripped when deriving a keyword from a program's name, so
# the keyword that reaches the feed is the distinctive discipline term.
_KW_STOP = {"and", "of", "the", "in", "for", "with", "master", "doctor", "bachelor", "studies"}


def _school_content(name: str) -> dict:
    """A school's content_sources: the shared, verified Harvard feeds filtered to
    school-relevant items by keywords (the MIT/MBAn pattern). HBS keeps its own
    events calendar + socials; every school routes news through the Gazette."""
    base = {
        "news_rss": _HARVARD_NEWS_RSS,
        "news_curated": False,
        "events_feed": dict(_HARVARD_EVENTS_ICS),
        "keywords": list(_SCHOOL_KEYWORDS[name]),
        "social": dict(_SOCIAL_HARVARD),
    }
    if name == _HBS:
        base["events_feed"] = dict(_HBS_EVENTS_ICS)
        base["social"] = dict(_SOCIAL_HBS)
    return base


def _program_keywords(spec: dict) -> list[str]:
    """Program keywords = the program's distinctive discipline term(s) (from its
    name) layered on top of its school's keywords, so the program tab is relevant
    yet never empty."""
    school_kw = list(_SCHOOL_KEYWORDS[spec["school"]])
    name = spec["program_name"].replace("&", " ").replace("/", " ")
    terms = [w for w in name.split() if len(w) > 3 and w.lower() not in _KW_STOP]
    program_term = " ".join(terms[:3]).strip()
    return ([program_term] if program_term else []) + school_kw


def _program_content(spec: dict) -> dict:
    """A program's content_sources: its school's shared feed refined by program
    keywords (the MBA keeps its own keyword-relevant feed via _MBA_CONTENT)."""
    base = _school_content(spec["school"])
    base["keywords"] = _program_keywords(spec)
    return base


# MBA keyword-relevant feed (the flagship program): the Gazette filtered to MBA
# items + HBS's own events calendar and socials.
_MBA_CONTENT: dict = {
    "news_rss": _HARVARD_NEWS_RSS,
    "news_curated": False,
    "events_feed": dict(_HBS_EVENTS_ICS),
    "keywords": ["MBA", "Harvard MBA", "Harvard Business School", "HBS"],
    "social": dict(_SOCIAL_HBS),
}

PROGRAMS: list[dict] = [
    # ── Faculty of Arts & Sciences — Harvard College (A.B.) ───────────────────
    {
        "slug": "harvard-economics-ab",
        "school": _FAS,
        "program_name": "Economics",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Harvard's most popular concentration: empirical and theoretical economics.",
    },
    {
        "slug": "harvard-government-ab",
        "school": _FAS,
        "program_name": "Government",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Political theory, American politics, comparative politics, and IR.",
    },
    {
        "slug": "harvard-social-studies-ab",
        "school": _FAS,
        "program_name": "Social Studies",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Harvard's famed interdisciplinary social-science honors concentration.",
    },
    {
        "slug": "harvard-history-ab",
        "school": _FAS,
        "program_name": "History",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "History across periods, regions, and methods.",
    },
    {
        "slug": "harvard-english-ab",
        "school": _FAS,
        "program_name": "English",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Literature in English from the medieval period to the present.",
    },
    {
        "slug": "harvard-history-literature-ab",
        "school": _FAS,
        "program_name": "History & Literature",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "An interdisciplinary honors concentration in history and literature.",
    },
    {
        "slug": "harvard-philosophy-ab",
        "school": _FAS,
        "program_name": "Philosophy",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Logic, ethics, metaphysics, and the history of philosophy.",
    },
    {
        "slug": "harvard-art-history-ab",
        "school": _FAS,
        "program_name": "History of Art & Architecture",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "The study of art, architecture, and visual culture across history.",
    },
    {
        "slug": "harvard-psychology-ab",
        "school": _FAS,
        "program_name": "Psychology",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Cognition, behavior, and the science of the mind.",
    },
    {
        "slug": "harvard-sociology-ab",
        "school": _FAS,
        "program_name": "Sociology",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Social structure, inequality, and institutions.",
    },
    {
        "slug": "harvard-statistics-ab",
        "school": _FAS,
        "program_name": "Statistics",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Statistical theory and data science — a fast-growing concentration.",
    },
    {
        "slug": "harvard-mathematics-ab",
        "school": _FAS,
        "program_name": "Mathematics",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Harvard's renowned mathematics concentration, from analysis to topology.",
    },
    {
        "slug": "harvard-physics-ab",
        "school": _FAS,
        "program_name": "Physics",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "From quantum mechanics and particle physics to astrophysics.",
    },
    {
        "slug": "harvard-chemistry-ab",
        "school": _FAS,
        "program_name": "Chemistry",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Organic, inorganic, physical, and chemical biology.",
    },
    {
        "slug": "harvard-mcb-ab",
        "school": _FAS,
        "program_name": "Molecular & Cellular Biology",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Molecular, cellular, and developmental biology — a major pre-med path.",
    },
    {
        "slug": "harvard-neuroscience-ab",
        "school": _FAS,
        "program_name": "Neuroscience",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "From molecules and neurons to cognition, via the Center for Brain Science.",
    },
    {
        "slug": "harvard-eps-ab",
        "school": _FAS,
        "program_name": "Earth & Planetary Sciences",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Earth, climate, oceans, and the planets.",
    },
    # ── Faculty of Arts & Sciences — doctoral (Griffin GSAS) ──────────────────
    {
        "slug": "harvard-economics-phd",
        "school": _FAS,
        "program_name": "Economics",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "A leading economics doctoral program. Fully funded.",
    },
    {
        "slug": "harvard-government-phd",
        "school": _FAS,
        "program_name": "Government",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "Doctoral research across political science. Fully funded.",
    },
    {
        "slug": "harvard-history-phd",
        "school": _FAS,
        "program_name": "History",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "Doctoral research across historical fields. Fully funded.",
    },
    {
        "slug": "harvard-english-phd",
        "school": _FAS,
        "program_name": "English",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "Doctoral study of literature in English. Fully funded.",
    },
    {
        "slug": "harvard-psychology-phd",
        "school": _FAS,
        "program_name": "Psychology",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "Doctoral research across the subfields of psychology. Fully funded.",
    },
    {
        "slug": "harvard-statistics-phd",
        "school": _FAS,
        "program_name": "Statistics",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "Doctoral research in statistical theory and methods. Fully funded.",
    },
    {
        "slug": "harvard-physics-phd",
        "school": _FAS,
        "program_name": "Physics",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "Doctoral research in theoretical and experimental physics. Fully funded.",
    },
    {
        "slug": "harvard-mcb-phd",
        "school": _FAS,
        "program_name": "Biological Sciences (Molecular & Cellular Biology)",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "Doctoral research across molecular and cellular biology. Fully funded.",
    },
    # ── SEAS — undergraduate (A.B./S.B.) ──────────────────────────────────────
    {
        "slug": "harvard-cs-ab",
        "school": _SEAS,
        "program_name": "Computer Science",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Harvard's largest STEM concentration — theory, systems, and AI.",
    },
    {
        "slug": "harvard-applied-math-ab",
        "school": _SEAS,
        "program_name": "Applied Mathematics",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Mathematics applied to a chosen field, from economics to engineering.",
    },
    {
        "slug": "harvard-electrical-eng-sb",
        "school": _SEAS,
        "program_name": "Electrical Engineering",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Signals, circuits, devices, and computer engineering.",
    },
    {
        "slug": "harvard-mechanical-eng-sb",
        "school": _SEAS,
        "program_name": "Mechanical Engineering",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Mechanics, design, robotics, and energy systems.",
    },
    {
        "slug": "harvard-bioengineering-sb",
        "school": _SEAS,
        "program_name": "Bioengineering",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Engineering at the interface of biology and medicine.",
    },
    {
        "slug": "harvard-environmental-eng-sb",
        "school": _SEAS,
        "program_name": "Environmental Science & Engineering",
        "degree_type": "bachelors",
        "duration_months": 48,
        "description": "Climate, energy, and the science of the environment.",
    },
    # ── SEAS — graduate ───────────────────────────────────────────────────────
    {
        "slug": "harvard-cs-phd",
        "school": _SEAS,
        "program_name": "Computer Science",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "Doctoral research in CS — AI, systems, theory, and HCI. Fully funded.",
    },
    {
        "slug": "harvard-applied-physics-phd",
        "school": _SEAS,
        "program_name": "Applied Physics",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "Doctoral research in applied physics and materials. Fully funded.",
    },
    {
        "slug": "harvard-bioengineering-phd",
        "school": _SEAS,
        "program_name": "Bioengineering",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "Doctoral research in bioengineering, tied to the Wyss Institute. Funded.",
    },
    {
        "slug": "harvard-data-science-sm",
        "school": _SEAS,
        "program_name": "Data Science",
        "degree_type": "masters",
        "duration_months": 12,
        "description": "A one-year master's in data science (SEAS & Statistics).",
    },
    {
        "slug": "harvard-cse-sm",
        "school": _SEAS,
        "program_name": "Computational Science & Engineering",
        "degree_type": "masters",
        "duration_months": 12,
        "description": "A master's in computational science and engineering (SM/ME).",
    },
    # ── Harvard Business School ───────────────────────────────────────────────
    {
        "slug": "harvard-mba",
        "school": _HBS,
        "program_name": "MBA",
        "degree_type": "masters",
        "duration_months": 24,
        "description": "Harvard's two-year residential MBA, taught by the case method.",
    },
    {
        "slug": "harvard-business-phd",
        "school": _HBS,
        "program_name": "Business Administration",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "Doctoral research across management and business economics. Funded.",
    },
    # ── Harvard Law School ────────────────────────────────────────────────────
    {
        "slug": "harvard-jd",
        "school": _HLS,
        "program_name": "Juris Doctor (J.D.)",
        "degree_type": "masters",
        "duration_months": 36,
        "description": "The three-year professional law degree at the heart of HLS.",
    },
    {
        "slug": "harvard-llm",
        "school": _HLS,
        "program_name": "Master of Laws (LL.M.)",
        "degree_type": "masters",
        "duration_months": 12,
        "description": "A one-year degree for lawyers trained in the U.S. and abroad.",
    },
    {
        "slug": "harvard-law-sjd",
        "school": _HLS,
        "program_name": "Doctor of Juridical Science (S.J.D.)",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "HLS's most advanced law degree, for legal scholars. Funded.",
    },
    # ── Harvard Medical School ────────────────────────────────────────────────
    {
        "slug": "harvard-md",
        "school": _HMS,
        "program_name": "Doctor of Medicine (M.D.)",
        "degree_type": "masters",
        "duration_months": 48,
        "description": "Harvard's M.D. program across the Pathways and HST curricula.",
    },
    {
        "slug": "harvard-biomedical-phd",
        "school": _HMS,
        "program_name": "Biomedical Sciences",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "Doctoral research in the biomedical sciences (DMS). Fully funded.",
    },
    # ── Harvard School of Dental Medicine ─────────────────────────────────────
    {
        "slug": "harvard-dmd",
        "school": _HSDM,
        "program_name": "Doctor of Dental Medicine (D.M.D.)",
        "degree_type": "masters",
        "duration_months": 48,
        "description": "A research-driven dental degree built on the HMS basic-science core.",
    },
    # ── Harvard T.H. Chan School of Public Health ─────────────────────────────
    {
        "slug": "harvard-mph",
        "school": _HSPH,
        "program_name": "Master of Public Health (M.P.H.)",
        "degree_type": "masters",
        "duration_months": 12,
        "description": "Harvard's flagship public-health master's, with several fields.",
    },
    {
        "slug": "harvard-sm-public-health",
        "school": _HSPH,
        "program_name": "Master of Science in Public Health",
        "degree_type": "masters",
        "duration_months": 24,
        "description": "A research-oriented S.M. across epidemiology, biostatistics, and more.",
    },
    {
        "slug": "harvard-public-health-phd",
        "school": _HSPH,
        "program_name": "Population Health Sciences",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "Doctoral research across population and public-health sciences. Funded.",
    },
    # ── Harvard Kennedy School ────────────────────────────────────────────────
    {
        "slug": "harvard-mpp",
        "school": _HKS,
        "program_name": "Master in Public Policy (M.P.P.)",
        "degree_type": "masters",
        "duration_months": 24,
        "description": "HKS's two-year analytic policy degree.",
    },
    {
        "slug": "harvard-mpa",
        "school": _HKS,
        "program_name": "Master in Public Administration (M.P.A.)",
        "degree_type": "masters",
        "duration_months": 24,
        "description": "A flexible two-year degree for public-service leaders.",
    },
    {
        "slug": "harvard-mpa-id",
        "school": _HKS,
        "program_name": "M.P.A. in International Development",
        "degree_type": "masters",
        "duration_months": 24,
        "description": "A rigorous, economics-intensive degree in international development.",
    },
    {
        "slug": "harvard-public-policy-phd",
        "school": _HKS,
        "program_name": "Public Policy",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "Doctoral research in public policy and political economy. Funded.",
    },
    # ── Harvard Graduate School of Education ──────────────────────────────────
    {
        "slug": "harvard-edm",
        "school": _HGSE,
        "program_name": "Master's in Education (Ed.M.)",
        "degree_type": "masters",
        "duration_months": 12,
        "description": "A one-year master's across HGSE's education pathways.",
    },
    {
        "slug": "harvard-edld",
        "school": _HGSE,
        "program_name": "Doctor of Education Leadership (Ed.L.D.)",
        "degree_type": "phd",
        "duration_months": 36,
        "description": "A three-year practitioner doctorate in education leadership. Funded.",
    },
    {
        "slug": "harvard-education-phd",
        "school": _HGSE,
        "program_name": "Education (Ph.D.)",
        "degree_type": "phd",
        "duration_months": 60,
        "description": "Doctoral research in education, conferred with FAS. Fully funded.",
    },
    # ── Harvard Graduate School of Design ─────────────────────────────────────
    {
        "slug": "harvard-march",
        "school": _GSD,
        "program_name": "Master of Architecture (M.Arch)",
        "degree_type": "masters",
        "duration_months": 42,
        "description": "The accredited professional degree in architecture.",
    },
    {
        "slug": "harvard-mla",
        "school": _GSD,
        "program_name": "Master in Landscape Architecture (M.L.A.)",
        "degree_type": "masters",
        "duration_months": 36,
        "description": "The accredited professional degree in landscape architecture.",
    },
    {
        "slug": "harvard-mup",
        "school": _GSD,
        "program_name": "Master in Urban Planning (M.U.P.)",
        "degree_type": "masters",
        "duration_months": 24,
        "description": "A professional degree in urban planning and design.",
    },
    {
        "slug": "harvard-mdes",
        "school": _GSD,
        "program_name": "Master in Design Studies (M.Des.)",
        "degree_type": "masters",
        "duration_months": 18,
        "description": "A post-professional research master's across design domains.",
    },
    # ── Harvard Divinity School ───────────────────────────────────────────────
    {
        "slug": "harvard-mdiv",
        "school": _HDS,
        "program_name": "Master of Divinity (M.Div.)",
        "degree_type": "masters",
        "duration_months": 36,
        "description": "HDS's three-year degree for religious leadership and ministry.",
    },
    {
        "slug": "harvard-mts",
        "school": _HDS,
        "program_name": "Master of Theological Studies (M.T.S.)",
        "degree_type": "masters",
        "duration_months": 24,
        "description": "A two-year academic degree in the study of religion.",
    },
    # ── Harvard Division of Continuing Education (Extension / HarvardX) ────────
    {
        "slug": "harvard-alm",
        "school": _DCE,
        "program_name": "Master of Liberal Arts (A.L.M.)",
        "degree_type": "masters",
        "duration_months": 24,
        "delivery_format": "hybrid",
        "description": "The Extension School's part-time master's, taken on campus or online.",
    },
    {
        "slug": "harvard-cs50-cert",
        "school": _DCE,
        "program_name": "CS50: Computer Science (HarvardX Certificate)",
        "degree_type": "certificate",
        "duration_months": 6,
        "delivery_format": "online",
        "description": "Harvard's famous open online introduction to computer science.",
    },
    {
        "slug": "harvard-data-science-cert",
        "school": _DCE,
        "program_name": "Data Science (HarvardX Professional Certificate)",
        "degree_type": "certificate",
        "duration_months": 9,
        "delivery_format": "online",
        "description": "An online HarvardX professional certificate in data science.",
    },
]

_EXISTING_SLUGS = {p["slug"] for p in PROGRAMS}
_EXISTING_CIP_KEYS = {(p.get("cip"), p["degree_type"]) for p in PROGRAMS if p.get("cip")}
_EXISTING_FIELD_KEYS = {
    (p["school"], p["program_name"].lower().strip(), p["degree_type"]) for p in PROGRAMS
}

_PRO_SCHOOLS = frozenset({
    _HBS, _HLS, _HMS, _HSPH, _HKS, _HGSE, _GSD, _HDS, _HSDM, _DCE,
})


def _delivery_format(raw: str) -> str:
    """Normalize delivery labels for description clauses only."""
    if raw in ("in_person", "on_campus"):
        return "on_campus"
    return raw


# ── De-fabricate the Scorecard CIP-rollup catalog (anti-stub miss #2) ──────────
_ROLLUP_RESOLVE: dict[str, str] = {
    "Biology, General": "Human Evolutionary Biology",
    "Biomedical/Medical Engineering": "Bioengineering",
    "Cell/Cellular Biology and Anatomical Sciences": "Molecular and Cellular Biology",
    "Classics and Classical Languages, Literatures, and Linguistics": "Classics",
    "East Asian Languages, Literatures, and Linguistics": "East Asian Languages and Civilizations",
    "English Language and Literature, General": "English",
    "Psychology, General": "Psychology",
    "Geological and Earth Sciences/Geosciences": "Earth and Planetary Sciences",
    "Germanic Languages, Literatures, and Linguistics": "German",
    "Romance Languages, Literatures, and Linguistics": "Romance Languages and Literatures",
    "Middle/Near Eastern and Semitic Languages, Literatures, and Linguistics": (
        "Near Eastern Languages and Civilizations"
    ),
    "Slavic, Baltic and Albanian Languages, Literatures, and Linguistics": (
        "Slavic Languages and Literatures"
    ),
    "South Asian Languages, Literatures, and Linguistics": "South Asian Studies",
    "African Languages, Literatures, and Linguistics": "African and African American Studies",
    "Celtic Languages, Literatures, and Linguistics": "Celtic Languages and Literatures",
    "Drama/Theatre Arts and Stagecraft": "Theater, Dance, and Media",
    "Film/Video and Photographic Arts": "Film and Visual Studies",
    "City/Urban, Community, and Regional Planning": "Urban Planning and Design",
    "Urban Studies/Affairs": "Urban Studies",
    "Religion/Religious Studies": "Study of Religion",
    "Information Science/Studies": "Information Science",
    # Residual federal CIP taxonomy titles → Harvard's real published degree name
    # (REPAIR_BACKLOG #1, run 77). Verified against Harvard department / GSAS pages;
    # per-level drops for credentials Harvard does not confer live in
    # ``_ROLLUP_LEVEL_DROP`` below.
    "Linguistic, Comparative, and Related Language Studies and Services": "Linguistics",
    "Electrical, Electronics, and Communications Engineering": "Electrical Engineering",
    "Ecology, Evolution, Systematics, and Population Biology": "Integrative Biology",
    "Biomathematics, Bioinformatics, and Computational Biology": (
        "Computational Biology and Quantitative Genetics"
    ),
    "Architectural History, Criticism, and Conservation": (
        "History of Art and Architecture"
    ),
}

# (rollup title, degree_type) → DROP: credential level Harvard does not confer in
# this field (omit, never guess — REPAIR_BACKLOG #1, run 77). Verified against
# Harvard's own department / graduate-school pages:
#  • Linguistics: PhD-only graduate field (no standalone master's; AM is in-passing).
#  • Electrical Engineering bachelor's already ships as flagship ``harvard-electrical-eng-sb``.
#  • Integrative Biology (OEB): PhD-only at graduate level; no terminal master's.
#  • Computational Biology: the real master's is Harvard T.H. Chan SPH's "Master of
#    Science in Computational Biology and Quantitative Genetics" — PRESERVED and
#    reassigned to HSPH via _SLUG_SCHOOL_OVERRIDE (only the certificate is dropped).
#  • Architectural History: no standalone GSD master's; PhD work sits under GSD PhD
#    areas or FAS History of Art and Architecture (the IPEDS ms/cert rows are federal mint).
_ROLLUP_LEVEL_DROP: frozenset[tuple[str, str]] = frozenset({
    ("Linguistic, Comparative, and Related Language Studies and Services", "masters"),
    ("Linguistic, Comparative, and Related Language Studies and Services", "certificate"),
    ("Electrical, Electronics, and Communications Engineering", "bachelors"),
    ("Ecology, Evolution, Systematics, and Population Biology", "masters"),
    ("Ecology, Evolution, Systematics, and Population Biology", "certificate"),
    ("Biomathematics, Bioinformatics, and Computational Biology", "certificate"),
    ("Architectural History, Criticism, and Conservation", "masters"),
    ("Architectural History, Criticism, and Conservation", "certificate"),
})

# slug → real owning school, for an IPEDS row whose Field-of-Study completion is coded to
# F.A.S. but whose real degree is conferred by another Harvard school (REPAIR_BACKLOG #1).
# The CBQG master's is a Harvard T.H. Chan SPH degree, not F.A.S.
_SLUG_SCHOOL_OVERRIDE: dict[str, str] = {
    "harvard-biomathematics-bioinformatics-and-computational-biology-ms": _HSPH,
}

_ROLLUP_DROP: frozenset[str] = frozenset({
    "Accounting and Related Services",
    "Advanced/Graduate Dentistry and Oral Sciences",
    "Area Studies",
    "Biological and Biomedical Sciences, Other",
    "Business/Commerce, General",
    "Business/Corporate Communications",
    "Business/Managerial Economics",
    "Computer and Information Sciences, General",
    "Computer/Information Technology Administration and Management",
    "Cultural Studies/Critical Theory and Analysis",
    "Education, General",
    "Education, Other",
    "Educational/Instructional Media Design",
    "Environmental/Natural Resources Management and Policy",
    "Ethnic, Cultural Minority, Gender, and Group Studies",
    "Foods, Nutrition, and Related Services",
    "Health/Medical Preparatory Programs",
    "Intercultural/Multicultural and Diversity Studies",
    "Liberal Arts and Sciences, General Studies and Humanities",
    "Medical Clinical Sciences/Graduate Medical Studies",
    "Museology/Museum Studies",
    "Philosophy and Religious Studies, General",
    "Rhetoric and Composition/Writing Studies",
    "Social Sciences, General",
    "Southeast Asian and Australasian/Pacific Languages, Literatures, and Linguistics",
    "Theology and Religious Vocations, Other",
    "Turkic, Uralic-Altaic, Caucasian, and Central Asian Languages, Literatures, and Linguistics",
    "Visual and Performing Arts, General",
})


def _resolve_rollup(
    field_name: str, degree_type: str = "", school: str = ""
) -> str | None:
    """Real Harvard degree name for a Scorecard CIP field, or None to DROP the row."""
    if (field_name, degree_type) in _ROLLUP_LEVEL_DROP:
        return None
    if field_name in _ROLLUP_DROP:
        return None
    return _ROLLUP_RESOLVE.get(field_name, field_name)


_CRED_PREFIXES = (
    "Bachelor of Arts in ",
    "Bachelor of Science in ",
    "Bachelor of Science in Engineering in ",
    "Bachelor's in ",
    "Master of Arts in ",
    "Master of Science in ",
    "Master of Education in ",
    "Master of Business Administration in ",
    "Master's in ",
    "Doctor of Philosophy in ",
    "Graduate Certificate in ",
    "Professional program in ",
)

_POSSESSIVE_NAME_RE = re.compile(r"^(Bachelor's|Master's|Doctorate) in ")

# Schools whose graduate degrees are typically conferred as Master of Science.
_MS_SCHOOLS = frozenset({
    _SEAS,
    _HSPH,
    _HMS,
    _HSDM,
})


def _conferred_program_name(field_name: str, degree_type: str, school: str) -> str:
    """Harvard's conferred designation for a field — never the possessive IPEDS mint form."""
    if degree_type == "bachelors":
        if school == _SEAS:
            return f"Bachelor of Science in {field_name}"
        return f"Bachelor of Arts in {field_name}"
    if degree_type == "masters":
        if school == _HBS:
            if field_name in {
                "Business Administration, Management and Operations",
                "Business/Commerce, General",
            }:
                return "Master of Business Administration"
            return f"Master of Business Administration in {field_name}"
        if school == _HGSE:
            return f"Master of Education in {field_name}"
        if school in _MS_SCHOOLS or school == _SEAS:
            return f"Master of Science in {field_name}"
        return f"Master of Arts in {field_name}"
    if degree_type == "phd":
        return f"Doctor of Philosophy in {field_name}"
    if degree_type == "certificate":
        return f"Graduate Certificate in {field_name}"
    return disambiguate_program_name(field_name, degree_type)


def _real_field_of(program_name: str) -> str:
    """Extract the field-of-study part of a credential-disambiguated program name."""
    for prefix in _CRED_PREFIXES:
        if program_name.startswith(prefix):
            return program_name[len(prefix):]
    return program_name


def _field_from_program_name(program_name: str) -> str | None:
    """Extract CIP field title from a disambiguated program name."""
    field = _real_field_of(program_name)
    return field if field != program_name else None


_LEVEL_PRIORITY: dict[str, int] = {
    "bachelors": 0,
    "certificate": 1,
    "masters": 2,
    "phd": 3,
    "doctoral": 3,
    "professional": 4,
}

# Lead verbs used to slice a subarea focus from a FIELD_DESCRIPTIONS clause when no
# curated override exists (same pattern as uw_madison_profile.py).
_FOCUS_LEAD_RE = re.compile(
    r"^(.*?\b(?:covers|combines|spans|includes|integrates|offers?|examines?|trains?|"
    r"prepares?|underpins?|emphasizes?|centers? on|focuses? on|explores?|studies|study|"
    r"pairs?|blends?|joins?|teach(?:es)?|analyze[s]?|bridges?|operate[s]?|run[s]?|use[s]?|"
    r"support[s]?|choose among)\b\s*)",
    re.I,
)


def _extract_focus(clause: str) -> str:
    m = _FOCUS_LEAD_RE.match(clause)
    rest = clause[m.end():] if m else clause
    rest = re.split(
        r"\s+(?:with|through|tied to|drawing on|near|at the|across Harvard|for Harvard|for the)\s+",
        rest,
        1,
    )[0]
    rest = rest.strip().rstrip(".").strip()
    if len(rest) > 66:
        cut = rest[:66]
        cut = cut[: cut.rfind(",")] if "," in cut else cut[: cut.rfind(" ")]
        rest = cut.strip().rstrip(",").strip()
    return rest


def _focus_for(field: str) -> str:
    clause = FIELD_DESCRIPTIONS.get(field, "")
    if not clause:
        return ""
    return _extract_focus(clause)


def _sibling_body(dtype: str, field_label: str, focus: str) -> str:
    """Distinct, level-specific body for a credential sibling (not the field's anchor)."""
    if dtype == "masters":
        return (
            f"Master's study in {field_label} at Harvard builds on {focus}, with advanced "
            f"coursework, methods, and a thesis or capstone."
        )
    if dtype == "phd":
        return (
            f"Doctoral research in {field_label} at Harvard advances {focus}, supported by "
            f"a faculty-mentored dissertation and GSAS funding pathways."
        )
    if dtype == "certificate":
        return (
            f"This Harvard graduate certificate in {field_label} packages focused coursework "
            f"in {focus} for working professionals and degree-seekers."
        )
    if dtype == "professional":
        return (
            f"This professional Harvard program in {field_label} pairs classroom study with "
            f"supervised clinical or practical training in {focus}."
        )
    return (
        f"The undergraduate major in {field_label} at Harvard develops {focus} through core "
        f"sequences, hands-on labs or studio, and upper-division electives."
    )


def _adapt_clause_for_degree_type(clause: str, degree_type: str) -> str:
    if degree_type == "bachelors":
        if clause.startswith("Graduate "):
            return "Undergraduate " + clause[len("Graduate "):]
        if clause.startswith("Graduate-level "):
            return "Undergraduate-level " + clause[len("Graduate-level "):]
    return clause


def _level_appropriate_clause(clause: str, degree_type: str) -> str:
    if degree_type == "bachelors":
        return clause
    clause = re.sub(r"\bthe undergraduate major\b", "the program", clause, flags=re.I)
    clause = re.sub(
        r"\bundergraduate (major|program)\b", "program", clause, flags=re.I
    )
    return clause


def _apply_fmt_suffix(desc: str, spec: dict) -> str:
    fmt = _delivery_format(spec.get("delivery_format", "in_person"))
    if fmt == "online":
        return desc + " Delivered online."
    if fmt == "hybrid":
        return desc + " Delivered in hybrid format."
    return desc


def _resolve_fd_field(spec: dict, field_name: str | None = None) -> str:
    if spec["slug"] in SLUG_DESCRIPTIONS:
        return ""
    field_key = spec.get("_field_name") or field_name
    if field_key in FIELD_ALIASES:
        field_key = FIELD_ALIASES[field_key]
    if field_key and field_key in FIELD_DESCRIPTIONS:
        return field_key
    fallback_key = (
        field_key
        or spec.get("department")
        or _real_field_of(spec.get("program_name", ""))
    )
    if fallback_key in FIELD_ALIASES:
        fallback_key = FIELD_ALIASES[fallback_key]
    if fallback_key in FIELD_DESCRIPTIONS:
        return fallback_key
    raise ValueError(
        f"Missing FIELD_DESCRIPTIONS entry for {fallback_key!r} ({spec['slug']})"
    )


def _assign_descriptions(programs: list[dict]) -> None:
    """Assign a per-credential description to every program.

    The anchor credential (bachelors when present, else lowest level) carries the full
    verified FIELD_DESCRIPTIONS clause; siblings carry a distinct level-specific frame
    naming real subareas — no two siblings share a >=80-char contiguous body (gold MIT = 0).
    """
    from collections import defaultdict

    groups: dict[str, list[dict]] = defaultdict(list)
    for spec in programs:
        groups[_real_field_of(spec["program_name"])].append(spec)

    for label, specs in groups.items():
        fd_field = next((s.get("_fd_field") for s in specs if s.get("_fd_field")), None)
        field_clause = FIELD_DESCRIPTIONS.get(fd_field or "")

        def _slug_text(s: dict) -> str | None:
            return SLUG_DESCRIPTIONS.get(s["slug"])

        anchor = next(
            (s for s in specs if s["degree_type"] == "bachelors"),
            min(
                specs,
                key=lambda s: (_LEVEL_PRIORITY.get(s["degree_type"], 2), s["slug"]),
            ),
        )
        anchor_text = _slug_text(anchor) or field_clause
        focus = _focus_for(fd_field or "") if fd_field else _extract_focus(anchor_text or "")

        assigned: set[str] = set()
        for spec in specs:
            slug_text = _slug_text(spec)
            if spec is anchor:
                base = (
                    field_clause
                    if (field_clause and spec["slug"] not in SLUG_DESCRIPTIONS)
                    else slug_text
                )
                base = base or field_clause
                if not base:
                    raise ValueError(f"No clause for anchor {spec['slug']!r}")
                body = _level_appropriate_clause(
                    _adapt_clause_for_degree_type(base, spec["degree_type"]),
                    spec["degree_type"],
                )
            elif slug_text and slug_text not in assigned:
                body = slug_text
            else:
                if not focus:
                    raise ValueError(f"No focus for sibling {spec['slug']!r} ({label})")
                body = _sibling_body(spec["degree_type"], label, focus)
            assigned.add(body)
            spec["description"] = _apply_fmt_suffix(body, spec)
            spec.pop("_fd_field", None)


def _normalize_program(spec: dict, field_name: str | None = None) -> None:
    """Resolve FIELD_DESCRIPTIONS key; description assigned by _assign_descriptions."""
    spec["_fd_field"] = _resolve_fd_field(spec, field_name)


def _build_catalog() -> list[dict]:
    """Append breadth-first program nodes from the IPEDS Field-of-Study catalog."""
    out: list[dict] = []
    seen = set(_EXISTING_SLUGS)
    field_seen = set(_EXISTING_FIELD_KEYS)
    for slug, school, field_name, dtype, cip, dur, fmt, _legacy_desc in _IPEDS_CATALOG:
        if slug in seen:
            continue
        if (cip, dtype) in _EXISTING_CIP_KEYS:
            continue
        school = _SLUG_SCHOOL_OVERRIDE.get(slug, school)
        real_name = _resolve_rollup(field_name, dtype, school)
        if real_name is None:
            continue
        fkey = (school, real_name.lower().strip(), dtype)
        if fkey in field_seen:
            continue
        seen.add(slug)
        field_seen.add(fkey)
        pname = _conferred_program_name(real_name, dtype, school)
        spec = {
            "slug": slug,
            "school": school,
            "program_name": pname,
            "degree_type": dtype,
            "department": school,
            "cip": cip,
            "duration_months": dur,
            "delivery_format": fmt,
            "_field_name": field_name,
        }
        _normalize_program(spec, field_name)
        out.append(spec)
    return out


PROGRAMS += _build_catalog()
for _p in PROGRAMS:
    _normalize_program(_p)
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
_FLAGSHIP_SLUGS = _EXISTING_SLUGS  # explicit catalog entries (pre-IPEDS breadth)

# ── Application-requirement baselines ──────────────────────────────────────
# Official at the degree level. Harvard College is university-wide; the
# professional schools each publish their own; the GSAS baseline covers the
# arts-&-sciences and SEAS research degrees.
_REQ_UNDERGRAD = {
    "materials": [
        {"name": "Common Application, Coalition, or Common App", "required": True},
        {"name": "Harvard questions & supplemental essays", "required": True},
        {"name": "Secondary-school report + transcript", "required": True},
        {"name": "Mid-year school report", "required": True},
        {
            "name": "Alumni / admissions interview",
            "required": False,
            "note": "Offered where an interviewer is available; not held against you otherwise",
        },
        {
            "name": "Optional supplementary materials (research, art, music, maker)",
            "required": False,
            "note": "Submit if they meaningfully add to your application",
        },
    ],
    "test_policy": {
        "stance": "required",
        "note": (
            "SAT or ACT required (reinstated for fall 2025 entry); scores may be self-reported."
        ),
        "accepted_tests": ["SAT", "ACT"],
        "superscore_enabled": True,
        "typical_ranges": [
            {"test": "SAT", "low": 1500, "high": 1580},
            {"test": "ACT", "low": 34, "high": 36},
        ],
    },
    "recommendations": {
        "required_count": 3,
        "types": ["Two teacher evaluations", "School counselor report"],
    },
    "deadlines": [
        {"round": "Restrictive Early Action (non-binding)", "date": "November 1"},
        {"round": "Regular Decision", "date": "January 1"},
    ],
    "application_fee": {
        "amount_usd": 85,
        "waiver_available": True,
        "note": "Fee waivers available for students with financial need",
    },
    "evaluation": (
        "Holistic review of academic strength, intellectual curiosity, character, and "
        "contribution to the community. Harvard is need-blind for all applicants — including "
        "international students — and meets 100% of demonstrated financial need; it does not "
        "consider ability to pay."
    ),
    "source": "Harvard College Admissions",
    "source_url": "https://college.harvard.edu/admissions/apply",
}
_REQ_GRAD = {
    "materials": [
        {"name": "Statement of purpose", "required": True},
        {"name": "Academic transcripts from all institutions", "required": True},
        {"name": "Curriculum vitae / résumé", "required": True},
        {
            "name": "GRE general / subject scores",
            "required": False,
            "note": "Many programs are GRE-optional or GRE-blind — check the program",
        },
        {
            "name": "Writing sample or research statement",
            "required": False,
            "note": "Required by some humanities and social-science programs",
        },
        {
            "name": "English proficiency (TOEFL/IELTS) for international applicants",
            "required": False,
            "note": "TOEFL iBT 100 / IELTS 7.0 typical minimums",
        },
    ],
    "test_policy": {
        "stance": "varies",
        "note": "GRE requirement varies by program — many are optional or not accepted.",
    },
    "recommendations": {
        "required_count": 3,
        "types": ["Three letters of recommendation (academic or research)"],
    },
    "deadlines": [
        {"round": "Fall entry (most programs)", "date": "December 1"},
    ],
    "application_fee": {
        "amount_usd": 105,
        "waiver_available": True,
        "note": "Fee waivers available for eligible applicants",
    },
    "evaluation": (
        "Admission is by the program/department through Harvard Griffin GSAS, weighing research "
        "fit, academic preparation, letters, and the statement of purpose. PhD admits are "
        "typically offered a multi-year funding package (tuition + stipend)."
    ),
    "source": "Harvard Griffin GSAS Admissions",
    "source_url": "https://gsas.harvard.edu/apply",
}
_REQ_MBA = {
    "materials": [
        {"name": "Application essay", "required": True},
        {"name": "Résumé & transcripts", "required": True},
        {"name": "GMAT or GRE score", "required": True},
        {
            "name": "Two professional letters of recommendation",
            "required": True,
        },
        {
            "name": "TOEFL / IELTS / PTE for non-native English speakers",
            "required": False,
            "note": "Required where prior instruction was not in English",
        },
    ],
    "test_policy": {"stance": "required", "note": "GMAT or GRE required"},
    "recommendations": {
        "required_count": 2,
        "types": ["Two professional letters of recommendation"],
    },
    "deadlines": [
        {"round": "Round 1", "date": "September 2026"},
        {"round": "Round 2", "date": "January 2027"},
    ],
    "international": {
        "english": {
            "tests": ["TOEFL", "IELTS", "PTE"],
            "required": False,
            "note": "Required for applicants whose prior degree was not taught in English.",
        },
        "note": "Admitted international students receive an I-20 (F-1) or DS-2019 (J-1).",
    },
    "evaluation": (
        "HBS admits in two rounds and evaluates candidates holistically on a "
        "habit of leadership, analytical aptitude, and engaged community citizenship; "
        "exact round dates are published each cycle on the official application-dates page."
    ),
    "source": "Harvard Business School MBA Admissions",
    "source_url": "https://www.hbs.edu/mba/admissions/application-dates",
}
_REQ_LAW = {
    "materials": [
        {"name": "Personal statement", "required": True},
        {"name": "Transcripts via CAS", "required": True},
        {"name": "Résumé", "required": True},
    ],
    "test_policy": {"stance": "required", "note": "LSAT or GRE accepted"},
    "recommendations": {
        "required_count": 2,
        "types": ["Two letters of recommendation"],
    },
    "source": "Harvard Law School J.D. Admissions",
    "source_url": "https://hls.harvard.edu/dept/jdadmissions/",
}
_REQ_MED = {
    "materials": [
        {"name": "AMCAS application & Harvard secondary", "required": True},
        {"name": "Transcripts & MCAT score", "required": True},
        {"name": "Required premedical coursework", "required": True},
    ],
    "test_policy": {"stance": "required", "note": "MCAT required"},
    "recommendations": {
        "required_count": 3,
        "types": ["Letters of recommendation (committee or individual)"],
    },
    "source": "Harvard Medical School Admissions",
    "source_url": "https://meded.hms.harvard.edu/admissions",
}
_REQ_OPEN = {
    "materials": [{"name": "Open enrollment — no formal admission required", "required": False}],
    "test_policy": {"stance": "not_required"},
    "source": "Harvard Extension School / HarvardX",
    "source_url": "https://extension.harvard.edu/",
}

# Per-program application deadlines for the professional doctorates whose shared
# requirement template (_REQ_LAW / _REQ_MED) is degree-agnostic. Each date is the
# official published deadline for the current cycle (verified 2026-06-11):
#   • J.D. — regular decision Feb 15 (hls.harvard.edu J.D. Admissions)
#   • LL.M. — Dec 1 (hls.harvard.edu Graduate Program / LL.M. Admissions)
#   • M.D. — AMCAS Oct 15, HMS Supplemental Oct 22 (hms.harvard.edu MD Admissions)
_DEADLINES_BY_SLUG: dict[str, list[dict]] = {
    "harvard-jd": [{"round": "Regular decision", "date": "February 15"}],
    "harvard-llm": [{"round": "Application deadline", "date": "December 1"}],
    "harvard-md": [
        {"round": "AMCAS application", "date": "October 15"},
        {"round": "HMS Supplemental application", "date": "October 22"},
    ],
}

# ── Outcomes ───────────────────────────────────────────────────────────────
# Harvard-wide institution outcome, used (explicitly labelled) where the College
# Scorecard Field-of-Study earnings are privacy-suppressed for a program.
_OUTCOMES_INSTITUTION = {
    "median_salary": 101817,
    "employment_rate": 0.95,
    "employment_timeframe": "Harvard graduates overall",
    "top_industries": ["Finance", "Consulting", "Technology", "Law", "Healthcare"],
    "scope": "institution",
    "scope_note": "Harvard-wide figures across all graduates — not specific to this program.",
    "source": "U.S. Dept. of Education College Scorecard (institution-level)",
    "source_url": "https://collegescorecard.ed.gov/",
}

# Real per-program median earnings (+ debt where reported) from the College
# Scorecard Field-of-Study file (Most-Recent-Cohorts), Harvard UNITID 166027.
# Only non-privacy-suppressed fields appear here; every other degree program
# falls back to the labelled institution figure. Tuple = (earnings, debt|None, CIP).
_FOS_OUTCOMES: dict[str, tuple[int, int | None, str]] = {
    # Harvard College (A.B.) — bachelor's
    "harvard-cs-ab": (219550, None, "11.07"),
    "harvard-applied-math-ab": (178318, None, "27.03"),
    "harvard-statistics-ab": (229811, None, "27.05"),
    "harvard-economics-ab": (161251, 6617, "45.06"),
    "harvard-government-ab": (117484, None, "45.10"),
    "harvard-social-studies-ab": (76293, 22750, "45.01"),
    "harvard-history-ab": (94015, 12721, "54.01"),
    "harvard-english-ab": (64155, None, "23.01"),
    "harvard-psychology-ab": (102305, None, "42.27"),
    "harvard-sociology-ab": (89947, None, "45.11"),
    "harvard-mcb-ab": (87380, None, "26.04"),
    "harvard-neuroscience-ab": (75342, None, "26.15"),
    # Graduate & professional
    "harvard-mba": (283798, 41000, "52.02"),
    "harvard-jd": (250647, 93235, "22.01"),
    "harvard-md": (139818, 99160, "51.12"),
    "harvard-dmd": (172732, 184220, "51.04"),
    "harvard-mph": (204275, 49681, "51.22"),
    "harvard-mpa": (140456, 70763, "44.04"),
    "harvard-mpp": (134992, 70447, "44.05"),
    "harvard-edm": (84569, 20500, "13.01"),
    "harvard-march": (85413, None, "04.02"),
    "harvard-mla": (79176, None, "04.06"),
    "harvard-mup": (89211, 41000, "04.03"),
    "harvard-mdiv": (59192, 36777, "39.06"),
    "harvard-mts": (68181, 25632, "39.06"),
    "harvard-alm": (88617, 25780, "24.01"),
    # Doctoral (Scorecard FOS doctoral earnings; these degrees are funded)
    "harvard-education-phd": (132114, 25465, "13.01"),
    "harvard-mcb-phd": (117155, None, "26.01"),
    "harvard-public-policy-phd": (129458, None, "44.05"),
    "harvard-public-health-phd": (120143, None, "51.22"),
}

# ── Program-level employment report (the flagship), first-party + cross-checked ──
# The HBS MBA carries its own career-office employment report rather than the
# federal earnings figure. Class of 2025 numbers are from the HBS MBA Employment
# Report, cross-checked against Poets&Quants' and Fortune's reproductions of the
# same report. (The Scorecard Field-of-Study 10-year earnings figure for the MBA
# remains available but measures a different thing and is superseded here.)
_OUTCOMES_BY_SLUG: dict[str, dict] = {
    "harvard-mba": {
        "median_salary": 184500,
        "median_signing_bonus": 30000,
        "signing_bonus_rate": 0.58,
        "median_performance_bonus": 46100,
        "performance_bonus_rate": 0.67,
        "total_median_comp": 232800,
        "employment_rate": 0.90,
        "employment_timeframe": "received a job offer within three months of graduation",
        "class_size": 925,
        "scope": "program",
        "top_industries": [
            "Technology (22%)",
            "Consulting (21%)",
            "Private equity (14%)",
            "Investment management & hedge funds (7%)",
            "Venture capital (4%)",
        ],
        "conditions": [
            "Class of 2025 (925 graduates); 65% of the class sought post-MBA "
            "employment — the rest pursued ventures, sponsored returns, or further study.",
            "90% of job-seeking graduates had received an offer and 84% had accepted "
            "one within three months of graduation (about 94% had offers by the time "
            "HBS published the report).",
            "Median base salary $184,500; 58% reported a signing bonus at a median of "
            "$30,000 and 67% an expected performance bonus at a median of $46,100, for "
            "total median first-year compensation of $232,800.",
            "Compensation and employment status are self-reported by graduates; the "
            "salary figure is the median base salary and excludes bonuses.",
        ],
        "source": "Harvard Business School — MBA Class of 2025 Employment Report",
        "source_url": "https://www.hbs.edu/recruiting/employment-data/Pages/default.aspx",
    },
}

# ── Class profile, where published (the flagship) ──────────────────────────
_CLASS_PROFILE_BY_SLUG: dict[str, dict] = {
    "harvard-mba": {
        "cohort_size": "943 students (Class of 2027)",
        "applicants": 9409,
        "international_pct": 0.37,
        "countries": 62,
        "women_pct": 0.44,
        "median_gmat": 685,
        "median_gmat_note": "GMAT Focus Edition scale",
        "avg_gpa": 3.76,
        "avg_work_experience_years": 4.9,
        "source": "Harvard Business School — MBA Class Profile (Class of 2027)",
        "source_url": "https://www.hbs.edu/mba/admissions/class-profile",
    },
}

# ── Faculty (lead + directory link), where confidently sourced (the flagship) ──
_FACULTY_BY_SLUG: dict[str, dict] = {
    "harvard-mba": {
        "lead": [
            {
                "name": "Matthew C. Weinzierl",
                "title": "Senior Associate Dean and Chair of the MBA Program",
            },
            {
                "name": "Srikant M. Datar",
                "title": "George F. Baker Professor of Administration; Dean",
            },
            {
                "name": "Michael E. Porter",
                "title": "Bishop William Lawrence University Professor",
            },
        ],
        "note": "Taught by Harvard Business School faculty, almost entirely by the case method.",
        "directory_url": "https://www.hbs.edu/faculty/",
    },
}

# ── Aggregated, cited student-review themes (≥2 third-party sources) ────────
_REVIEWS_BY_SLUG: dict[str, dict] = {
    "harvard-mba": {
        "summary": (
            "Students and third-party guides consistently rank the HBS MBA among the "
            "most coveted in the world — praising the case-method classroom, the "
            "general-management breadth, and the unrivaled alumni network — while the "
            "most common cautions are the very low admit rate, the cost of a two-year "
            "residential program, and softer recent placement that pulled Harvard down "
            "some employment-weighted rankings before offers rebounded."
        ),
        "themes": [
            {
                "label": "Case method & general management",
                "sentiment": "positive",
                "detail": (
                    "Almost all teaching is by the case method, building decision-making "
                    "across every business function."
                ),
            },
            {
                "label": "Alumni network & brand",
                "sentiment": "positive",
                "detail": (
                    "One of the largest, most influential business alumni networks; HBS "
                    "topped Fortune's MBA ranking four years running and led Bloomberg's "
                    "'most desired MBA' survey."
                ),
            },
            {
                "label": "Entrepreneurship",
                "sentiment": "positive",
                "detail": (
                    "About 150 graduates of the Class of 2025 launched ventures, backed by "
                    "the Rock Center and a startup-heavy alumni base."
                ),
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": (
                    "Admission is highly competitive — a median GMAT of 685 (Focus scale) "
                    "from roughly 9,400 applications."
                ),
            },
            {
                "label": "Cost & recent placement",
                "sentiment": "caution",
                "detail": (
                    "Two-year residential tuition near $78,700/year before living costs; a "
                    "tougher 2024 job market drew a sharp Financial Times ranking drop."
                ),
            },
        ],
        "sources": [
            {
                "label": "Poets&Quants / Bloomberg — 'Because It's Harvard'",
                "url": "https://poetsandquants.com/2025/10/03/because-its-harvard-hbs-is-still-the-most-desired-mba/",
            },
            {
                "label": "Fortune — Harvard MBA graduate outcomes 2025",
                "url": "https://fortune.com/2025/12/02/harvard-business-school-mba-graduate-outcomes-2025-record-salaries-shift-to-entrepreneurship-tech-jobs/",
            },
            {
                "label": "U.S. News — Harvard University (Business)",
                "url": "https://www.usnews.com/best-graduate-schools/top-business-schools/harvard-university-01110",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "harvard-jd": {
        "summary": (
            "Students and guides describe Harvard Law School's J.D. as the most "
            "prestigious legal credential in the United States — U.S. News ranks it "
            "No. 4 among law schools (2026) — with unmatched faculty depth, the "
            "largest academic law library in the world, and extraordinary placement "
            "into clerkships, Big Law, and public service. Common cautions are the "
            "intense grading curve, the high cost of a three-year Cambridge "
            "residence, and a culture that can feel competitive despite recent "
            "reforms toward pass/fail first-year grading."
        ),
        "themes": [
            {
                "label": "National prestige & clerkships",
                "sentiment": "positive",
                "detail": (
                    "U.S. News #4 law school; historically the leading feeder to "
                    "federal clerkships and elite firms."
                ),
            },
            {
                "label": "Faculty & library resources",
                "sentiment": "positive",
                "detail": (
                    "World-renowned faculty across every legal field; the largest "
                    "academic law library globally."
                ),
            },
            {
                "label": "Career breadth",
                "sentiment": "positive",
                "detail": (
                    "Strong pipelines to private practice, government, academia, "
                    "and public-interest law."
                ),
            },
            {
                "label": "Cost & debt",
                "sentiment": "caution",
                "detail": (
                    "Three-year tuition near $78,700/year before living costs in "
                    "the Boston area."
                ),
            },
            {
                "label": "Competitive culture",
                "sentiment": "mixed",
                "detail": (
                    "Large 1L sections and a demanding workload; some students "
                    "report pressure despite pass/fail first-year reforms."
                ),
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Harvard Law School",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/harvard-university-03050",
            },
            {
                "label": "Harvard Law School — About",
                "url": "https://hls.harvard.edu/about/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "harvard-md": {
        "summary": (
            "Students and guides rank Harvard Medical School among the top medical "
            "schools in the world — U.S. News #1 for research (2026) — praising "
            "the Pathways curriculum, the Longwood research ecosystem, and "
            "affiliated hospitals such as Mass General and Brigham and Women's. "
            "Common cautions are the extreme selectivity (roughly 3% acceptance), "
            "the demanding pace of the pre-clinical years, and the high cost of "
            "living in Boston."
        ),
        "themes": [
            {
                "label": "Research leadership",
                "sentiment": "positive",
                "detail": "U.S. News #1 medical school for research (2026).",
            },
            {
                "label": "Hospital affiliations",
                "sentiment": "positive",
                "detail": (
                    "Clinical training across Harvard's affiliated teaching "
                    "hospitals in the Longwood Medical Area."
                ),
            },
            {
                "label": "Selectivity",
                "sentiment": "caution",
                "detail": (
                    "Among the most competitive M.D. programs globally; median "
                    "MCAT and GPA well above national averages."
                ),
            },
            {
                "label": "Cost of attendance",
                "sentiment": "caution",
                "detail": (
                    "Tuition near $78,700/year plus Boston-area living expenses "
                    "over four years."
                ),
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Harvard Medical School",
                "url": "https://www.usnews.com/best-graduate-schools/top-medical-schools/harvard-university-04098",
            },
            {
                "label": "Harvard Medical School — Education",
                "url": "https://hms.harvard.edu/education",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "harvard-mph": {
        "summary": (
            "Students and public-health guides describe Harvard's M.P.H. as the "
            "flagship degree at the T.H. Chan School of Public Health — U.S. News "
            "ranks Harvard #1 among public-health schools (2026) — with strengths "
            "in epidemiology, biostatistics, and global health. Common cautions are "
            "the one-year program's fast pace, the high tuition for a professional "
            "master's, and that career outcomes vary widely by concentration."
        ),
        "themes": [
            {
                "label": "Public-health ranking",
                "sentiment": "positive",
                "detail": "U.S. News #1 school of public health (2026).",
            },
            {
                "label": "Interdisciplinary breadth",
                "sentiment": "positive",
                "detail": (
                    "Multiple fields of study and cross-registration across Harvard "
                    "schools and Boston-area hospitals."
                ),
            },
            {
                "label": "Intensive timeline",
                "sentiment": "caution",
                "detail": (
                    "The standard 45-credit M.P.H. is designed to be completed in "
                    "one academic year."
                ),
            },
            {
                "label": "Tuition",
                "sentiment": "caution",
                "detail": (
                    "Professional-school tuition without the full-need aid model "
                    "of Harvard College."
                ),
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Harvard T.H. Chan School of Public Health",
                "url": (
                    "https://www.usnews.com/best-graduate-schools/top-health-"
                    "schools/harvard-university-04098"
                ),
            },
            {
                "label": "Harvard Chan — M.P.H. Program",
                "url": "https://www.hsph.harvard.edu/admissions/degree-programs/master-of-public-health/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "harvard-mpp": {
        "summary": (
            "Students and policy guides describe the Harvard Kennedy School M.P.P. "
            "as a rigorous, quantitative policy degree — U.S. News ranks HKS #3 "
            "among public-affairs schools (2026) — with unmatched access to Harvard "
            "faculty, Belfer Center research, and a global alumni network in "
            "government and NGOs. Common cautions are the math-heavy core "
            "curriculum, limited financial aid relative to Harvard College, and "
            "that the two-year residential format is costly."
        ),
        "themes": [
            {
                "label": "Policy-school standing",
                "sentiment": "positive",
                "detail": "U.S. News #3 public-affairs school (2026).",
            },
            {
                "label": "Quantitative core",
                "sentiment": "positive",
                "detail": (
                    "Microeconomics, statistics, and policy analysis training "
                    "valued by governments and multilateral organizations."
                ),
            },
            {
                "label": "Global alumni network",
                "sentiment": "positive",
                "detail": (
                    "Graduates hold leadership roles in governments, NGOs, and "
                    "international institutions worldwide."
                ),
            },
            {
                "label": "Quantitative demands",
                "sentiment": "caution",
                "detail": (
                    "The M.P.P. core requires substantial economics and statistics "
                    "coursework."
                ),
            },
            {
                "label": "Cost",
                "sentiment": "caution",
                "detail": (
                    "Two-year professional tuition without Harvard College's "
                    "need-blind aid model."
                ),
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Harvard Kennedy School",
                "url": (
                    "https://www.usnews.com/best-graduate-schools/top-public-affairs-"
                    "schools/harvard-university-21097"
                ),
            },
            {
                "label": "Harvard Kennedy School — M.P.P.",
                "url": (
                    "https://www.hks.harvard.edu/educational-programs/masters-programs/"
                    "master-public-policy"
                ),
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "harvard-cs-ab": {
        "summary": (
            "Students and guides describe Harvard's computer science concentration "
            "as a fast-growing, research-oriented program housed in SEAS — Niche "
            "ranks Harvard #12 nationally for undergraduate CS (2026) — with "
            "strengths in AI, systems, and theory and the cultural reach of CS50. "
            "Common cautions are that Harvard's CS program is smaller and newer "
            "than peer giants like MIT or Stanford, introductory courses can be "
            "large, and the concentration has become increasingly competitive to "
            "declare."
        ),
        "themes": [
            {
                "label": "Research & CS50 culture",
                "sentiment": "positive",
                "detail": (
                    "Access to SEAS faculty in AI, systems, and theory; CS50 is "
                    "among the university's largest courses."
                ),
            },
            {
                "label": "National CS standing",
                "sentiment": "positive",
                "detail": "Niche #12 Best Colleges for Computer Science (2026).",
            },
            {
                "label": "Scale vs. peer giants",
                "sentiment": "mixed",
                "detail": (
                    "Smaller CS department than MIT or Stanford; fewer dedicated "
                    "CS faculty per student."
                ),
            },
            {
                "label": "Concentration competition",
                "sentiment": "caution",
                "detail": (
                    "Rising demand has made the CS concentration increasingly "
                    "selective to enter."
                ),
            },
        ],
        "sources": [
            {
                "label": "Niche — Best Colleges for Computer Science",
                "url": "https://www.niche.com/colleges/search/best-colleges-for-computer-science/",
            },
            {
                "label": "Harvard SEAS — Computer Science",
                "url": "https://seas.harvard.edu/computer-science",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "harvard-economics-ab": {
        "summary": (
            "Students and guides describe Harvard's economics concentration as the "
            "university's most popular undergraduate field — Niche ranks it #6 "
            "nationally for economics (2026) — with rigorous training in "
            "microeconomics, econometrics, and empirical methods and strong "
            "placement into finance, consulting, and graduate school. Common "
            "cautions are large intermediate courses, a grading culture that "
            "students describe as demanding, and that the concentration's size "
            "can limit individual faculty access."
        ),
        "themes": [
            {
                "label": "National economics standing",
                "sentiment": "positive",
                "detail": "Niche #6 Best Colleges for Economics in America (2026).",
            },
            {
                "label": "Quantitative training",
                "sentiment": "positive",
                "detail": (
                    "Ec 10 and the intermediate sequence build empirical and "
                    "theoretical foundations valued by employers."
                ),
            },
            {
                "label": "Recruiting outcomes",
                "sentiment": "positive",
                "detail": (
                    "Common path into finance, consulting, tech, and top "
                    "economics Ph.D. programs."
                ),
            },
            {
                "label": "Course scale",
                "sentiment": "caution",
                "detail": (
                    "Large lecture sections in intermediate courses; concentration "
                    "size limits small-seminar access."
                ),
            },
        ],
        "sources": [
            {
                "label": "Niche — Best Colleges for Economics",
                "url": "https://www.niche.com/colleges/search/best-colleges-for-economics/",
            },
            {
                "label": "Harvard Economics — Undergraduate",
                "url": "https://economics.harvard.edu/undergraduate",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "harvard-march": {
        "summary": (
            "Students and architecture guides describe Harvard's M.Arch as one of "
            "the most prestigious professional architecture degrees — DesignIntelligence "
            "historically ranked GSD at the top tier — with a design-studio culture, "
            "the Gund Hall community, and global alumni influence. Common cautions "
            "are the intensive studio workload, high tuition for a three-year "
            "professional program, and that GSD withdrew from DesignIntelligence "
            "rankings in 2022, making cross-school comparisons harder."
        ),
        "themes": [
            {
                "label": "Design prestige",
                "sentiment": "positive",
                "detail": (
                    "GSD is among the most recognized architecture schools "
                    "worldwide with influential faculty and alumni."
                ),
            },
            {
                "label": "Studio culture",
                "sentiment": "positive",
                "detail": (
                    "Gund Hall's open studio floors foster interdisciplinary "
                    "design collaboration."
                ),
            },
            {
                "label": "Studio intensity",
                "sentiment": "caution",
                "detail": (
                    "The accredited M.Arch track demands sustained studio work "
                    "across multiple semesters."
                ),
            },
            {
                "label": "Program cost",
                "sentiment": "caution",
                "detail": (
                    "Professional tuition for a multi-year residential degree in "
                    "the Boston area."
                ),
            },
        ],
        "sources": [
            {
                "label": "Harvard GSD — Master in Architecture",
                "url": "https://www.gsd.harvard.edu/architecture/",
            },
            {
                "label": "Architectural Record — GSD and DesignIntelligence",
                "url": "https://www.architecturalrecord.com/articles/15457-gsd-pulls-out-of-designintelligence-rankings",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "harvard-data-science-sm": {
        "summary": (
            "Students and data-science guides describe Harvard's one-year Master of "
            "Science in Data Science (SEAS + Statistics) as a rigorous, quantitative "
            "program bridging statistics, computer science, and domain applications — "
            "with strengths in faculty research and Harvard's cross-school ecosystem. "
            "Common cautions are the intensive one-year timeline, limited cohort size "
            "and selectivity, and that tuition is set at the graduate SEAS rate "
            "without Harvard College's need-based aid model."
        ),
        "themes": [
            {
                "label": "Quantitative rigor",
                "sentiment": "positive",
                "detail": (
                    "Joint SEAS/Statistics curriculum covering machine learning, "
                    "inference, and scalable computing."
                ),
            },
            {
                "label": "Harvard research access",
                "sentiment": "positive",
                "detail": (
                    "Proximity to AI, biostatistics, and applied-math research "
                    "groups across Harvard."
                ),
            },
            {
                "label": "One-year intensity",
                "sentiment": "caution",
                "detail": (
                    "The SM is designed as a single-year program with a heavy "
                    "course and project load."
                ),
            },
            {
                "label": "Selectivity & cost",
                "sentiment": "caution",
                "detail": (
                    "Competitive admission; graduate tuition without the "
                    "undergraduate financial-aid guarantee."
                ),
            },
        ],
        "sources": [
            {
                "label": "Harvard SEAS — Data Science SM",
                "url": "https://seas.harvard.edu/computer-science/sm-data-science",
            },
            {
                "label": "Harvard Statistics — Data Science",
                "url": "https://statistics.fas.harvard.edu/data-science",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "harvard-cse-sm": {
        "summary": (
            "Students describe Harvard's Computational Science & Engineering SM as a "
            "technically demanding master's bridging applied math, computing, and "
            "scientific modeling — valued for SEAS faculty and research ties to the "
            "Institute for Applied Computational Science. Common cautions are the "
            "heavy prerequisites in math and programming, a smaller program relative "
            "to peer CS departments, and graduate tuition without College-level aid."
        ),
        "themes": [
            {
                "label": "Applied computing depth",
                "sentiment": "positive",
                "detail": (
                    "Coursework in numerical methods, HPC, and scientific "
                    "machine learning."
                ),
            },
            {
                "label": "IACS ecosystem",
                "sentiment": "positive",
                "detail": (
                    "Access to the Institute for Applied Computational Science "
                    "and SEAS research labs."
                ),
            },
            {
                "label": "Prerequisite bar",
                "sentiment": "caution",
                "detail": (
                    "Expects strong linear algebra, programming, and prior "
                    "STEM coursework."
                ),
            },
            {
                "label": "Program scale",
                "sentiment": "mixed",
                "detail": (
                    "Smaller than flagship CS master's programs at MIT or "
                    "Stanford, with fewer dedicated industry pipelines."
                ),
            },
        ],
        "sources": [
            {
                "label": "Harvard SEAS — Computational Science & Engineering",
                "url": "https://seas.harvard.edu/computer-science/sm-computational-science-and-engineering",
            },
            {
                "label": "Harvard IACS",
                "url": "https://iacs.seas.harvard.edu/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "harvard-llm": {
        "summary": (
            "International lawyers and guides describe Harvard Law School's LL.M. as "
            "the most prestigious one-year law master's globally — U.S. News ranks "
            "HLS No. 4 (2026) — offering unmatched faculty, library resources, and "
            "a globally networked cohort. Common cautions are the single-year "
            "timeline's intensity, tuition near the J.D. rate, and that the program "
            "is designed for lawyers already trained in their home jurisdictions."
        ),
        "themes": [
            {
                "label": "Global prestige",
                "sentiment": "positive",
                "detail": (
                    "U.S. News #4 law school; the LL.M. draws senior lawyers "
                    "and academics worldwide."
                ),
            },
            {
                "label": "Faculty & library",
                "sentiment": "positive",
                "detail": (
                    "Access to HLS's full curriculum and the largest academic "
                    "law library in the world."
                ),
            },
            {
                "label": "One-year pace",
                "sentiment": "caution",
                "detail": (
                    "A compressed schedule of coursework, activities, and "
                    "networking in Cambridge."
                ),
            },
            {
                "label": "Tuition",
                "sentiment": "caution",
                "detail": (
                    "Professional-school tuition for a one-year residential "
                    "degree in the Boston area."
                ),
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Harvard Law School",
                "url": "https://www.usnews.com/best-graduate-schools/top-law-schools/harvard-university-03050",
            },
            {
                "label": "Harvard Law School — LL.M. Program",
                "url": "https://hls.harvard.edu/dept/graduate-program/master-of-laws/",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    "harvard-edm": {
        "summary": (
            "Students and education guides describe Harvard's Ed.M. at the Graduate "
            "School of Education as a flexible, one-year professional master's — "
            "U.S. News ranks HGSE No. 1 among education schools (2026) — with "
            "strengths in leadership, learning design, and policy pathways. Common "
            "cautions are the high tuition for a one-year professional degree, "
            "variable outcomes by concentration, and that some pathways are more "
            "research-oriented than practitioner-focused."
        ),
        "themes": [
            {
                "label": "Education-school ranking",
                "sentiment": "positive",
                "detail": "U.S. News #1 graduate school of education (2026).",
            },
            {
                "label": "Pathway flexibility",
                "sentiment": "positive",
                "detail": (
                    "Multiple Ed.M. strands across leadership, teaching, and "
                    "learning design."
                ),
            },
            {
                "label": "One-year format",
                "sentiment": "caution",
                "detail": (
                    "The standard Ed.M. is designed to be completed in one "
                    "academic year."
                ),
            },
            {
                "label": "Professional tuition",
                "sentiment": "caution",
                "detail": (
                    "Graduate tuition without Harvard College's need-blind "
                    "financial-aid model."
                ),
            },
        ],
        "sources": [
            {
                "label": "U.S. News — Harvard Graduate School of Education",
                "url": (
                    "https://www.usnews.com/best-graduate-schools/top-education-"
                    "schools/harvard-university-04098"
                ),
            },
            {
                "label": "Harvard HGSE — Master's Programs",
                "url": "https://www.gse.harvard.edu/masters",
            },
        ],
        "disclaimer": (
            "Aggregated and paraphrased from public third-party sources — not "
            "individual verbatim reviews."
        ),
    },
    **DEPTH_REVIEWS,
}

# ── Per-school official tuition (2025-26 unless noted) and cost source ──────
# Real published figures from each school's financial-aid / registrar office.
# Undergraduates pay Harvard College tuition; research doctorates are fully
# funded (tuition 0); Extension / HarvardX is charged per course (left null).
_TUITION_UNDERGRAD = 57328  # Harvard College tuition, 2025-26 (FAS Registrar)
_TUITION_BY_SLUG: dict[str, int] = {
    "harvard-mba": 78700,  # HBS MBA, 2025-26
    "harvard-jd": 78692,  # HLS J.D. tuition & fees, 2025-26
    "harvard-llm": 78692,  # HLS LL.M., 2025-26
    "harvard-md": 73874,  # HMS M.D., 2025-26
    "harvard-dmd": 69300,  # HSDM D.M.D., 2025-26
    "harvard-mpp": 61926,  # HKS, 2025-26
    "harvard-mpa": 61926,
    "harvard-mpa-id": 61926,
    "harvard-march": 61510,  # GSD, 2025-26
    "harvard-mla": 61510,
    "harvard-mup": 61510,
    "harvard-mdes": 61510,
    "harvard-edm": 62244,  # HGSE Ed.M., 2025-26
    "harvard-mph": 65160,  # Harvard Chan MPH-65 (most recent published)
    "harvard-sm-public-health": 65160,
    "harvard-mdiv": 30472,  # HDS, most recent published
    "harvard-mts": 30472,
    "harvard-data-science-sm": 57328,  # Griffin GSAS full tuition, 2025-26
    "harvard-cse-sm": 57328,
}

# Published 2025-26 annual master's tuition by school — Harvard OIRA Fact Book
# (https://oira.harvard.edu/factbook/fact-book-grad-tuition/) + each school's
# financial-aid / registrar page. Griffin GSAS full tuition covers FAS and SEAS
# academic master's (FAS Registrar confirms SEAS master's follow standard GSAS).
_TUITION_MASTERS_BY_SCHOOL: dict[str, int] = {
    _FAS: 57328,
    _SEAS: 57328,
    _HBS: 78700,
    _HLS: 78692,
    _HSPH: 65160,
    _HKS: 61926,
    _HGSE: 62244,
    _GSD: 61510,
    _HDS: 30472,
    _HSDM: 69300,
}

# HMS master's and Extension credentials bill per-program / per-course — no single
# annual figure maps cleanly to the IPEDS field names in this catalog.
_MASTERS_TUITION_OMIT_SCHOOLS = frozenset({_HMS, _DCE})

_OIRA_COST_SRC = (
    "Harvard Office of Institutional Research — Graduate/Professional Tuition Fact Book",
    "https://oira.harvard.edu/factbook/fact-book-grad-tuition/",
)

_COST_SRC_BY_SCHOOL: dict[str, tuple[str, str]] = {
    _FAS: ("Harvard College / Griffin GSAS", "https://college.harvard.edu/financial-aid"),
    _SEAS: ("Harvard Griffin GSAS", "https://gsas.harvard.edu/financial-support"),
    _HBS: ("Harvard Business School", "https://www.hbs.edu/mba/financial-aid/"),
    _HLS: ("Harvard Law School", "https://hls.harvard.edu/sfs/"),
    _HMS: ("Harvard Medical School", "https://hms.harvard.edu/education-admissions"),
    _HSDM: ("Harvard School of Dental Medicine", "https://www.hsdm.harvard.edu/admissions-aid"),
    _HSPH: (
        "Harvard T.H. Chan School of Public Health",
        "https://hsph.harvard.edu/tuition-and-financial-aid/",
    ),
    _HKS: ("Harvard Kennedy School", "https://www.hks.harvard.edu/admissions-aid"),
    _HGSE: (
        "Harvard Graduate School of Education",
        "https://www.gse.harvard.edu/admissions-and-aid",
    ),
    _GSD: ("Harvard Graduate School of Design", "https://www.gsd.harvard.edu/admissions/"),
    _HDS: ("Harvard Divinity School", "https://www.hds.harvard.edu/admissions-aid"),
    _DCE: ("Harvard Extension School", "https://extension.harvard.edu/paying-for-school/"),
}

# ── Who-it's-for + highlights ──────────────────────────────────────────────
_WHO_BY_TYPE = {
    "bachelors": "Applicants seeking a rigorous liberal-arts-and-sciences education at Harvard.",
    "masters": "Students seeking advanced, professional, or specialized graduate training.",
    "phd": "Researchers pursuing an academic or research career through a funded doctorate.",
    "certificate": "Learners worldwide seeking a focused Harvard credential online.",
}
_WHO_BY_SLUG = {
    "harvard-mba": "Early-to-mid-career professionals targeting general management and leadership.",
    "harvard-jd": "Aspiring lawyers and legal scholars across every field of law.",
    "harvard-md": "Future physicians and physician-scientists.",
    "harvard-mpp": "Future policy analysts and public-sector leaders.",
    "harvard-mpa": "Experienced professionals advancing into public-service leadership.",
    "harvard-mph": "Clinicians, scientists, and leaders advancing population health.",
    "harvard-edm": "Educators and leaders driving change in schools and learning organizations.",
}
_HL_BY_TYPE = {
    "bachelors": [
        "Need-blind admission, 100% of need met with no loans",
        "Nearly 50 concentrations across the liberal arts & sciences",
        "House system & undergraduate research",
    ],
    "masters": [
        "Direct access to Harvard faculty & global networks",
        "Cross-registration across Harvard's schools",
    ],
    "phd": [
        "Fully funded — tuition + multi-year stipend",
        "World-leading research environment",
        "Mentored cohorts across Harvard's institutes",
    ],
    "certificate": [
        "Learn online, on your schedule",
        "Earn a Harvard credential",
        "Open enrollment — no application required",
    ],
}
_HL_BY_SLUG = {
    "harvard-economics-ab": [
        "Harvard's most popular concentration",
        "Among the highest reported earnings of any Harvard field",
        "Gateway to finance, consulting & policy",
    ],
    "harvard-cs-ab": [
        "Harvard's largest STEM field (SEAS)",
        "From theory to AI & systems",
        "Ties to the CS50 teaching tradition",
    ],
    "harvard-statistics-ab": [
        "One of Harvard's fastest-growing concentrations",
        "Highest reported median earnings among Harvard fields",
        "Strong path into data science & quant roles",
    ],
    "harvard-mba": [
        "Taught by the case method",
        "Two-year residential program on the Allston campus",
        "One of the world's strongest business networks",
    ],
    "harvard-jd": [
        "The largest top law school in the U.S.",
        "Unmatched breadth across every legal field",
        "LSAT or GRE accepted",
    ],
    "harvard-md": [
        "Pathways & HST curricula",
        "Clinical training across world-leading hospitals",
        "Generous need-based aid",
    ],
    "harvard-mpp": [
        "Two-year analytic policy core",
        "Belfer, Ash & Shorenstein research centers",
        "Global public-service network",
    ],
    "harvard-mph": [
        "Several fields of study (epi, global health, health policy…)",
        "Longwood Medical Area location",
        "One-year and two-year tracks",
    ],
}

# ── Concentrations / degree tracks (real), for programs that offer them ─────
_TRACKS_BY_SLUG = {
    "harvard-economics-ab": {
        "concentrations": ["Standard track", "Mathematical track", "Data-science track"],
        "note": "Economics offers tracks ranging from standard to mathematically intensive.",
    },
    "harvard-cs-ab": {
        "concentrations": [
            "Artificial Intelligence",
            "Systems",
            "Theory",
            "Mind, Brain & Behavior",
        ],
        "note": "CS concentrators choose a focus area and may pursue an honors track.",
    },
    "harvard-applied-math-ab": {
        "concentrations": [
            "Economics application field",
            "Computer-science application field",
            "Engineering & physical-science fields",
        ],
        "note": "Applied Math is built around a chosen application field.",
    },
    "harvard-mba": {
        "concentrations": [
            "Required Curriculum (year 1)",
            "Elective Curriculum (year 2)",
            "Field method",
        ],
        "note": "The MBA pairs a fixed first-year core with a fully elective second year.",
    },
    "harvard-mph": {
        "concentrations": [
            "Epidemiology",
            "Global Health",
            "Health Policy & Management",
            "Health & Social Behavior",
            "Generalist",
        ],
        "note": "The M.P.H. is offered across several fields of study.",
    },
    "harvard-mpp": {
        "concentrations": [
            "Business & Government Policy",
            "International & Global Affairs",
            "Social & Urban Policy",
            "Politics & Political Institutions",
        ],
        "note": "MPP students choose a Policy Area of Concentration.",
    },
    "harvard-edm": {
        "concentrations": [
            "Education Leadership, Organizations & Entrepreneurship",
            "Human Development & Education",
            "Learning Design, Innovation & Technology",
            "Education Policy & Analysis",
            "Teaching & Teacher Leadership",
        ],
        "note": "The Ed.M. is organized around five programs of study.",
    },
    "harvard-jd": {
        "concentrations": [
            "1L required curriculum",
            "Upper-level electives & clinics",
            "Joint degrees",
        ],
        "note": "After the first-year core, J.D. students build an individualized course of study.",
    },
}

# Richer 2-sentence descriptions for the major programs (real). Programs not
# listed keep their canonical one-line description from PROGRAMS above.
_DESC_RICH_BY_SLUG = {
    "harvard-economics-ab": (
        "Economics is Harvard College's most popular concentration, combining microeconomics, "
        "macroeconomics, and econometrics with a wide range of fields from finance to "
        "development. It reports among the highest early-career earnings of any Harvard field "
        "and is a common path into finance, consulting, and policy."
    ),
    "harvard-cs-ab": (
        "Computer Science is Harvard's largest STEM concentration, housed in the John A. Paulson "
        "School of Engineering and Applied Sciences and spanning theory, systems, and artificial "
        "intelligence. Students can pursue a basic or honors track and join Harvard's renowned "
        "CS50 teaching community."
    ),
    "harvard-statistics-ab": (
        "Statistics is one of Harvard's fastest-growing concentrations, covering probability, "
        "statistical inference, and data science. Graduates report the highest median earnings of "
        "any Harvard undergraduate field and move into data, quantitative finance, and research."
    ),
    "harvard-social-studies-ab": (
        "Social Studies is Harvard's celebrated interdisciplinary honors concentration in the "
        "social sciences, built around a sophomore tutorial in classic social theory. Students "
        "design an individual focus field spanning economics, government, sociology, history, and "
        "philosophy."
    ),
    "harvard-government-ab": (
        "Government is Harvard's political-science concentration, covering political theory, "
        "American politics, comparative politics, and international relations. It is a leading "
        "path into law, public service, journalism, and policy."
    ),
    "harvard-mcb-ab": (
        "Molecular & Cellular Biology studies how molecules and cells drive life, development, "
        "and disease, with extensive laboratory research. It is one of the most common pre-medical "
        "pathways at Harvard College."
    ),
    "harvard-neuroscience-ab": (
        "Neuroscience connects molecules and neurons to behavior and cognition, drawing on "
        "Harvard's Center for Brain Science and affiliated hospitals. Students combine rigorous "
        "biology with research across the nervous system."
    ),
    "harvard-mba": (
        "Harvard Business School's two-year residential MBA is taught almost entirely by the case "
        "method, immersing students in real decisions faced by real leaders. Its Required "
        "Curriculum is followed by a fully elective second year and one of the strongest alumni "
        "networks in business."
    ),
    "harvard-jd": (
        "The Juris Doctor is the three-year professional degree at the heart of Harvard Law "
        "School — the largest of the top U.S. law schools. After a first-year core, students "
        "choose from an unmatched breadth of upper-level courses, clinics, and joint degrees, "
        "with the LSAT or GRE accepted for admission."
    ),
    "harvard-md": (
        "Harvard Medical School's M.D. program educates physicians and physician-scientists "
        "through the Pathways and Health Sciences & Technology (HST) curricula, with clinical "
        "training across world-leading Boston hospitals. Generous need-based aid supports students "
        "throughout."
    ),
    "harvard-dmd": (
        "Harvard's Doctor of Dental Medicine is a small, research-driven program whose students "
        "complete the first-year basic-science curriculum alongside Harvard Medical School. It "
        "produces academic leaders and clinician-scientists in oral medicine."
    ),
    "harvard-mph": (
        "The Master of Public Health is Harvard Chan School's flagship degree, offered across "
        "fields such as epidemiology, global health, and health policy in one-year and two-year "
        "tracks. Students train in the Longwood Medical Area to advance the health of populations."
    ),
    "harvard-mpp": (
        "The Master in Public Policy is Harvard Kennedy School's two-year analytic degree, pairing "
        "a quantitative and economic policy core with a chosen area of concentration. Students "
        "draw on research centers such as the Belfer, Ash, and Shorenstein Centers."
    ),
    "harvard-mpa": (
        "The Master in Public Administration is a flexible two-year degree for those advancing "
        "into public-service leadership, allowing wide cross-registration across Harvard's "
        "schools."
    ),
    "harvard-edm": (
        "The one-year Ed.M. is Harvard Graduate School of Education's master's degree, organized "
        "around five programs of study from learning design to education policy. It prepares "
        "educators and leaders to drive change in schools and learning organizations."
    ),
    "harvard-march": (
        "The Master of Architecture is the Graduate School of Design's accredited professional "
        "degree — a studio-based program combining design, history and theory, and building "
        "technology at one of the world's leading design schools."
    ),
    "harvard-mdiv": (
        "The Master of Divinity is Harvard Divinity School's three-year degree preparing students "
        "for religious leadership, ministry, chaplaincy, and engaged scholarship across "
        "traditions."
    ),
    "harvard-alm": (
        "The Master of Liberal Arts is Harvard Extension School's flexible, part-time master's, "
        "taken on campus or online across fields from data science to management. Admission is "
        "earned by completing degree courses with strong grades rather than by a prior "
        "application."
    ),
}


# Full official degree names (Harvard College grants the A.B.; SEAS grants the
# S.B.; graduate schools grant named professional degrees and the PhD). Shown as
# the program-page title; programs not listed keep their short PROGRAMS label
# (already full for most professional degrees, e.g. "Juris Doctor (J.D.)").
_FULL_NAME_BY_SLUG: dict[str, str] = {
    "harvard-economics-ab": "Bachelor of Arts in Economics",
    "harvard-government-ab": "Bachelor of Arts in Government",
    "harvard-social-studies-ab": "Bachelor of Arts in Social Studies",
    "harvard-history-ab": "Bachelor of Arts in History",
    "harvard-english-ab": "Bachelor of Arts in English",
    "harvard-history-literature-ab": "Bachelor of Arts in History & Literature",
    "harvard-philosophy-ab": "Bachelor of Arts in Philosophy",
    "harvard-art-history-ab": "Bachelor of Arts in History of Art & Architecture",
    "harvard-psychology-ab": "Bachelor of Arts in Psychology",
    "harvard-sociology-ab": "Bachelor of Arts in Sociology",
    "harvard-statistics-ab": "Bachelor of Arts in Statistics",
    "harvard-mathematics-ab": "Bachelor of Arts in Mathematics",
    "harvard-physics-ab": "Bachelor of Arts in Physics",
    "harvard-chemistry-ab": "Bachelor of Arts in Chemistry",
    "harvard-mcb-ab": "Bachelor of Arts in Molecular & Cellular Biology",
    "harvard-neuroscience-ab": "Bachelor of Arts in Neuroscience",
    "harvard-eps-ab": "Bachelor of Arts in Earth & Planetary Sciences",
    "harvard-cs-ab": "Bachelor of Arts in Computer Science",
    "harvard-applied-math-ab": "Bachelor of Arts in Applied Mathematics",
    "harvard-electrical-eng-sb": "Bachelor of Science in Electrical Engineering",
    "harvard-mechanical-eng-sb": "Bachelor of Science in Mechanical Engineering",
    "harvard-bioengineering-sb": "Bachelor of Science in Bioengineering",
    "harvard-environmental-eng-sb": "Bachelor of Science in Environmental Science & Engineering",
    "harvard-economics-phd": "Doctor of Philosophy in Economics",
    "harvard-government-phd": "Doctor of Philosophy in Government",
    "harvard-history-phd": "Doctor of Philosophy in History",
    "harvard-english-phd": "Doctor of Philosophy in English",
    "harvard-psychology-phd": "Doctor of Philosophy in Psychology",
    "harvard-statistics-phd": "Doctor of Philosophy in Statistics",
    "harvard-physics-phd": "Doctor of Philosophy in Physics",
    "harvard-mcb-phd": "Doctor of Philosophy in Biological Sciences (Molecular & Cellular Biology)",
    "harvard-cs-phd": "Doctor of Philosophy in Computer Science",
    "harvard-applied-physics-phd": "Doctor of Philosophy in Applied Physics",
    "harvard-bioengineering-phd": "Doctor of Philosophy in Bioengineering",
    "harvard-business-phd": "Doctor of Philosophy in Business Administration",
    "harvard-biomedical-phd": "Doctor of Philosophy in Biomedical Sciences",
    "harvard-public-health-phd": "Doctor of Philosophy in Population Health Sciences",
    "harvard-public-policy-phd": "Doctor of Philosophy in Public Policy",
    "harvard-education-phd": "Doctor of Philosophy in Education",
    "harvard-data-science-sm": "Master of Science in Data Science",
    "harvard-cse-sm": "Master of Science in Computational Science & Engineering",
    "harvard-mba": "Master of Business Administration",
    "harvard-mpa-id": "Master in Public Administration in International Development",
    "harvard-edm": "Master of Education (Ed.M.)",
}


def _finalize_catalog(programs: list[dict]) -> None:
    """In-place repair for explicit flagship entries: full names, departments, descriptions."""
    for p in programs:
        slug = p["slug"]
        if slug not in _FLAGSHIP_SLUGS:
            continue
        school = p["school"]
        dtype = p["degree_type"]
        raw_field = p["program_name"]
        if slug in _FULL_NAME_BY_SLUG:
            p["program_name"] = _FULL_NAME_BY_SLUG[slug]
        else:
            field = _field_from_program_name(raw_field) or raw_field
            resolved = _resolve_rollup(field, dtype, school)
            if resolved is not None:
                p["program_name"] = _conferred_program_name(resolved, dtype, school)
        p["department"] = school


def _normalize_all_program_names() -> None:
    """Ensure every catalog row carries a conferred designation (0% possessive mint)."""
    for p in PROGRAMS:
        slug = p["slug"]
        if slug in _FULL_NAME_BY_SLUG:
            p["program_name"] = _FULL_NAME_BY_SLUG[slug]
            continue
        field = (
            p.get("_field_name")
            or _field_from_program_name(p.get("program_name", ""))
            or p.get("program_name", "")
        )
        resolved = _resolve_rollup(field, p["degree_type"], p["school"])
        if resolved is None:
            continue
        p["program_name"] = _conferred_program_name(
            resolved, p["degree_type"], p["school"]
        )


def _dedupe_conferred_name_collisions() -> None:
    """Drop breadth IPEDS rows that collide with an explicit flagship's conferred name."""
    flagship_names = {
        (_FULL_NAME_BY_SLUG.get(p["slug"]) or p["program_name"])
        for p in PROGRAMS
        if p["slug"] in _FLAGSHIP_SLUGS
    }
    keep: list[dict] = []
    for p in PROGRAMS:
        if p["slug"] in _FLAGSHIP_SLUGS or p["program_name"] not in flagship_names:
            keep.append(p)
    PROGRAMS.clear()
    PROGRAMS.extend(keep)


_finalize_catalog(PROGRAMS)
_normalize_all_program_names()
_dedupe_conferred_name_collisions()
PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]
counts = Counter(p["program_name"] for p in PROGRAMS)
for p in PROGRAMS:
    if counts[p["program_name"]] > 1:
        suffix = (
            " (Online)" if p.get("delivery_format") == "online"
            else f" ({p['school']})"
        )
        p["program_name"] += suffix
for _p in PROGRAMS:
    _normalize_program(
        _p,
        _p.get("_field_name")
        or _field_from_program_name(_p.get("program_name", "")),
    )
_assign_descriptions(PROGRAMS)

# ── Catalog quality gate (anti-stub miss #2/#8/#9, gold MIT = 0 on each) ───────
_ROLLUP_NAME_RE = re.compile(
    r", General\b|, Other\b|, and Linguistics\b|, Pharmaceutical Sciences, and "
    r"Administration\b|, and Group Studies\b|, and Technicians\b|/"
)
_CIP_CODE_RE = re.compile(r"\(CIP\s*\d|\b\d\d\.\d\d\b")
_catalog_errors = validate_catalog(PROGRAMS)
_name_prefix_desc = sum(
    1
    for p in PROGRAMS
    if (p.get("description") or "").startswith(p.get("program_name", ""))
)
if _name_prefix_desc:
    _catalog_errors.append(f"name-prefixed descriptions on {_name_prefix_desc} programs")
_rollup_names = [
    p["program_name"]
    for p in PROGRAMS
    if _ROLLUP_NAME_RE.search(_real_field_of(p.get("program_name", "")))
]
if _rollup_names:
    _catalog_errors.append(f"CIP-rollup program names: {_rollup_names[:5]}")
_cip_in_name = [
    p["program_name"]
    for p in PROGRAMS
    if _CIP_CODE_RE.search(p.get("program_name", ""))
    or _CIP_CODE_RE.search(p.get("department") or "")
]
if _cip_in_name:
    _catalog_errors.append(f"literal CIP code in name/department: {_cip_in_name[:5]}")
_field_echo_dept = [
    p["program_name"]
    for p in PROGRAMS
    if (p.get("department") or "") == _real_field_of(p.get("program_name", ""))
]
if _field_echo_dept:
    _catalog_errors.append(f"field-echo departments: {_field_echo_dept[:5]}")
_possessive_names = [
    p["program_name"]
    for p in PROGRAMS
    if _POSSESSIVE_NAME_RE.match(p.get("program_name", ""))
]
if _possessive_names:
    _catalog_errors.append(
        f"possessive-mint program names ({len(_possessive_names)}): "
        f"{_possessive_names[:5]}"
    )
try:
    from unipaith.profile_standard import anti_stub as _anti_stub

    _astub = _anti_stub.analyze(
        [
            {"program_name": p["program_name"], "description": p.get("description")}
            for p in PROGRAMS
        ]
    )
    if not _astub.is_clean:
        _catalog_errors.append(f"anti-stub: {_astub.summary()}")
    _artifacts = _anti_stub.machine_artifacts(
        [
            {"program_name": p["program_name"], "description": p.get("description")}
            for p in PROGRAMS
        ]
    )
    if _artifacts:
        _catalog_errors.append(f"machine artifacts on {len(_artifacts)} programs")
except ImportError:
    pass
if _catalog_errors:
    raise RuntimeError(f"Harvard catalog quality gate failed: {_catalog_errors}")
for _p in PROGRAMS:
    _p.setdefault("delivery_format", "in_person")


# Official program-page URLs (every URL verified to resolve at author time;
# uncertain deep links fall back to the verified school home page).
_WEBSITE_BY_SLUG: dict[str, str] = {
    "harvard-economics-ab": "https://economics.harvard.edu/",
    "harvard-economics-phd": "https://economics.harvard.edu/",
    "harvard-government-ab": "https://gov.harvard.edu/",
    "harvard-government-phd": "https://gov.harvard.edu/",
    "harvard-social-studies-ab": "https://socialstudies.fas.harvard.edu/",
    "harvard-history-ab": "https://history.fas.harvard.edu/",
    "harvard-history-phd": "https://history.fas.harvard.edu/",
    "harvard-english-ab": "https://english.fas.harvard.edu/",
    "harvard-english-phd": "https://english.fas.harvard.edu/",
    "harvard-history-literature-ab": "https://histlit.fas.harvard.edu/",
    "harvard-philosophy-ab": "https://philosophy.fas.harvard.edu/",
    "harvard-art-history-ab": "https://haa.fas.harvard.edu/",
    "harvard-psychology-ab": "https://psychology.fas.harvard.edu/",
    "harvard-psychology-phd": "https://psychology.fas.harvard.edu/",
    "harvard-sociology-ab": "https://sociology.fas.harvard.edu/",
    "harvard-statistics-ab": "https://statistics.fas.harvard.edu/",
    "harvard-statistics-phd": "https://statistics.fas.harvard.edu/",
    "harvard-mathematics-ab": "https://www.math.harvard.edu/",
    "harvard-physics-ab": "https://www.physics.harvard.edu/",
    "harvard-physics-phd": "https://www.physics.harvard.edu/",
    "harvard-chemistry-ab": "https://www.chemistry.harvard.edu/",
    "harvard-mcb-ab": "https://www.mcb.harvard.edu/",
    "harvard-mcb-phd": "https://www.mcb.harvard.edu/",
    "harvard-neuroscience-ab": "https://www.mcb.harvard.edu/",
    "harvard-eps-ab": "https://eps.harvard.edu/",
    "harvard-cs-ab": "https://seas.harvard.edu/computer-science",
    "harvard-cs-phd": "https://seas.harvard.edu/computer-science",
    "harvard-applied-math-ab": "https://seas.harvard.edu/applied-mathematics",
    "harvard-electrical-eng-sb": "https://seas.harvard.edu/electrical-engineering",
    "harvard-mechanical-eng-sb": "https://seas.harvard.edu/materials-science-mechanical-engineering",
    "harvard-bioengineering-sb": "https://seas.harvard.edu/bioengineering",
    "harvard-bioengineering-phd": "https://seas.harvard.edu/bioengineering",
    "harvard-environmental-eng-sb": "https://seas.harvard.edu/environmental-science-engineering",
    "harvard-applied-physics-phd": "https://seas.harvard.edu/applied-physics",
    "harvard-cse-sm": "https://seas.harvard.edu/",
    "harvard-data-science-sm": "https://www.hsph.harvard.edu/biostatistics/data-science/",
    "harvard-mba": "https://www.hbs.edu/mba/",
    "harvard-business-phd": "https://www.hbs.edu/doctoral/",
    "harvard-jd": "https://hls.harvard.edu/",
    "harvard-llm": "https://hls.harvard.edu/dept/graduate-program/",
    "harvard-law-sjd": "https://hls.harvard.edu/dept/graduate-program/",
    "harvard-md": "https://hms.harvard.edu/",
    "harvard-biomedical-phd": "https://gsas.harvard.edu/",
    "harvard-dmd": "https://hsdm.harvard.edu/",
    "harvard-mph": "https://www.hsph.harvard.edu/",
    "harvard-sm-public-health": "https://www.hsph.harvard.edu/",
    "harvard-public-health-phd": "https://www.hsph.harvard.edu/",
    "harvard-mpp": (
        "https://www.hks.harvard.edu/educational-programs/masters-programs/master-public-policy"
    ),
    "harvard-mpa": "https://www.hks.harvard.edu/",
    "harvard-mpa-id": "https://www.hks.harvard.edu/",
    "harvard-public-policy-phd": (
        "https://www.hks.harvard.edu/educational-programs/doctoral-programs"
    ),
    "harvard-edm": "https://www.gse.harvard.edu/masters",
    "harvard-edld": "https://www.gse.harvard.edu/doctorate/doctor-education-leadership",
    "harvard-education-phd": "https://www.gse.harvard.edu/",
    "harvard-march": "https://www.gsd.harvard.edu/architecture/",
    "harvard-mla": "https://www.gsd.harvard.edu/landscape-architecture/",
    "harvard-mup": "https://www.gsd.harvard.edu/urban-planning-design/",
    "harvard-mdes": "https://www.gsd.harvard.edu/design-studies/",
    "harvard-mdiv": "https://hds.harvard.edu/",
    "harvard-mts": "https://hds.harvard.edu/",
    "harvard-alm": "https://extension.harvard.edu/",
    "harvard-cs50-cert": "https://pll.harvard.edu/course/cs50-introduction-computer-science",
    "harvard-data-science-cert": "https://pll.harvard.edu/",
}


# Real Harvard campus photo (Harvard Yard) — Wikimedia Commons, hotlinkable,
# landscape JPG. Leads the hero on the institution detail page.
_CAMPUS_PHOTO = SCHOOL_OUTCOMES["campus_photos"][0]["url"]


# ── Idempotent, FK-safe upsert ─────────────────────────────────────────────
def apply(session: Session) -> bool:
    """Enrich Harvard to the canonical profile. Flushes; caller commits.

    Returns False (no-op) when Harvard is absent — safe on fresh/CI databases.
    """
    inst = session.scalar(select(Institution).where(Institution.name == INSTITUTION_NAME))
    if inst is None:
        return False
    # Shallow-merge JSONB: every sub-object we provide is complete.
    inst.ranking_data = {**(inst.ranking_data or {}), **RANKING_DATA}
    school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
    # Drop any stale value for a path we explicitly declare omitted, so the merge
    # can't keep serving a figure the enrichment run refused to assert.
    for _path in _OMITTED_INSTITUTION:
        if _path.startswith("school_outcomes."):
            school_outcomes.pop(_path.split(".", 1)[1], None)
    school_outcomes["_standard"] = _standard(_OMITTED_INSTITUTION)
    inst.school_outcomes = school_outcomes
    inst.description_text = DESCRIPTION
    inst.student_body_size = UNDERGRAD_COUNT
    inst.founded_year = FOUNDED_YEAR
    inst.campus_setting = CAMPUS_SETTING
    # Lead the gallery with a real campus photo (the detail-page hero shows the
    # first raster image; the gallery otherwise holds only the logo SVG).
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
        # Every school carries a populated Events & Updates feed: the Gazette news
        # feed filtered by school keywords + the university (or, for HBS, the
        # school's own) events calendar. Always assign so a stale value on a
        # pre-existing row is cleared. None is never left here (the prior bug).
        sc.content_sources = _school_content(spec["name"])
        by_name[spec["name"]] = sc
    # Drop legacy schools — programs.school_id is ON DELETE SET NULL, so this is
    # FK-safe (any orphaned programs are handled by the program reconcile).
    for name, sc in existing.items():
        if name not in canonical_names:
            session.delete(sc)
    session.flush()
    return by_name


def _program_has_dependents(session: Session, program_id) -> bool:
    """True if any FK in the schema references this programs row (delete unsafe).

    Introspects FKs pointing at programs.id rather than hard-coding table names,
    so it stays correct as the schema grows.
    """
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


def _requirements_for(spec: dict) -> dict:
    slug, dtype = spec["slug"], spec["degree_type"]
    if slug == "harvard-mba":
        return dict(_REQ_MBA)
    if slug in ("harvard-jd", "harvard-llm"):
        return dict(_REQ_LAW)
    if slug == "harvard-md":
        return dict(_REQ_MED)
    if dtype == "certificate" or spec.get("delivery_format") == "online":
        return dict(_REQ_OPEN)
    if dtype == "bachelors":
        return dict(_REQ_UNDERGRAD)
    return dict(_REQ_GRAD)


def _deadline_for(spec: dict) -> date | None:
    slug, dtype = spec["slug"], spec["degree_type"]
    if dtype == "certificate" or spec.get("delivery_format") == "online":
        return None
    if slug == "harvard-mba":
        return date(2027, 1, 6)  # HBS Round 2
    if slug == "harvard-jd":
        return date(2027, 2, 15)  # HLS J.D.
    if slug == "harvard-md":
        return date(2026, 10, 15)  # AMCAS cycle
    if dtype == "bachelors":
        return date(2027, 1, 1)  # Harvard College Regular Decision
    return date(2026, 12, 15)  # graduate baseline (varies by program)


def _cost_data_for(tuition: int | None, spec: dict) -> dict | None:
    """Build persisted cost_data from a resolved tuition figure."""
    dt = spec["degree_type"]
    school = spec["school"]
    if dt == "phd":
        src_name, src_url = _COST_SRC_BY_SCHOOL.get(
            school, ("Harvard Griffin GSAS", "https://gsas.harvard.edu/financial-support")
        )
        return {
            "tuition_usd": 0,
            "funded": True,
            "source": src_name,
            "source_url": src_url,
            "year": "2025-26",
            "note": "Harvard PhD students typically receive a funding package covering tuition.",
        }
    if tuition is None:
        return None
    src_name, src_url = _COST_SRC_BY_SCHOOL.get(school, _OIRA_COST_SRC)
    return {
        "tuition_usd": tuition,
        "funded": False,
        "source": src_name,
        "source_url": src_url,
        "year": "2025-26",
    }


def _program_tuition(spec: dict) -> tuple[int | None, dict | None]:
    """Return ``(tuition, cost_data)`` from Harvard's published per-school rates.

    ``tuition`` is ``None`` only when Harvard bills per-course / per-program with
    no flat annual figure for this catalog row (Extension A.L.M., certificates,
    HMS master's with program-specific COA) — recorded omitted-with-reason, never
    guessed and never the undergraduate sticker copied onto graduate rows.
    """
    slug, dt, school = spec["slug"], spec["degree_type"], spec["school"]
    if slug in _TUITION_BY_SLUG:
        t = _TUITION_BY_SLUG[slug]
        return t, _cost_data_for(t, spec)
    if dt == "phd":
        return 0, _cost_data_for(0, spec)
    if dt == "bachelors":
        return _TUITION_UNDERGRAD, _cost_data_for(_TUITION_UNDERGRAD, spec)
    if (
        slug == "harvard-alm"
        or spec.get("delivery_format") == "online"
        or dt == "certificate"
    ):
        return None, None
    if dt == "masters":
        if school in _MASTERS_TUITION_OMIT_SCHOOLS:
            return None, None
        school_rate = _TUITION_MASTERS_BY_SCHOOL.get(school)
        if school_rate is not None:
            return school_rate, _cost_data_for(school_rate, spec)
        return None, None
    return None, None


def _resolved_tuition_present(spec: dict) -> bool:
    """True when the program ends up with a real cost_data.tuition_usd (mirrors
    ``_program_tuition``). Funded PhDs carry tuition_usd = 0 (present); Extension,
    online, certificate, and HMS master's (program-specific COA) → null."""
    tuition, _ = _program_tuition(spec)
    return tuition is not None


def _uses_open_admissions(spec: dict) -> bool:
    """True for open-enrollment / online credentials (the _REQ_OPEN path), which
    publish no fixed application deadline (rolling) → deadlines honestly omitted."""
    return spec["degree_type"] == "certificate" or spec.get("delivery_format") == "online"


def _outcomes_kind(spec: dict) -> str:
    """Which outcomes source a program resolves to (mirrors _apply_programs)."""
    if spec["slug"] in _OUTCOMES_BY_SLUG:
        return "full"  # program-level employment report (e.g. the MBA)
    if spec["slug"] in _FOS_OUTCOMES:
        return "fos"  # College Scorecard Field of Study: median_salary + source only
    if spec["degree_type"] in ("bachelors", "masters", "phd"):
        return "institution"  # Harvard-wide proxy: salary + employment_rate + industries
    return "none"  # non-degree credential: no outcomes published


def _program_standard(spec: dict) -> dict:
    """Per-program omitted-field list (verified-unavailable), for _standard. Derives,
    purely from the spec, exactly what _apply_programs persists so the stamp matches
    the row. content_sources is now always set (Gazette/school feed filtered by
    program keywords) → never omitted."""
    slug = spec["slug"]
    omitted: list[str] = []
    if slug not in _TRACKS_BY_SLUG:
        omitted.append("tracks")
    if slug not in _CLASS_PROFILE_BY_SLUG:
        omitted.append("class_profile.cohort_size")
    if slug not in _FACULTY_BY_SLUG:
        omitted.append("faculty_contacts.lead")
    if slug not in _REVIEWS_BY_SLUG:
        omitted.append("external_reviews.summary")
    if not _resolved_tuition_present(spec):
        omitted += ["cost_data.tuition_usd", "cost_data.source"]
    if _uses_open_admissions(spec):
        omitted.append("application_requirements.deadlines")
    elif (
        slug not in _DEADLINES_BY_SLUG
        and slug != "harvard-mba"
        and spec["degree_type"] != "bachelors"
    ):
        omitted.append("application_requirements.deadlines")
    kind = _outcomes_kind(spec)
    if kind == "fos":
        omitted += [
            "outcomes_data.employment_rate",
            "outcomes_data.top_industries",
            "outcomes_data.conditions",
        ]
    elif kind == "institution":
        omitted.append("outcomes_data.conditions")
    elif kind == "none":
        omitted += [
            "outcomes_data.median_salary",
            "outcomes_data.employment_rate",
            "outcomes_data.top_industries",
            "outcomes_data.conditions",
            "outcomes_data.source",
        ]
    return _standard(omitted)


def _apply_programs(session: Session, inst: Institution, school_by_name: dict[str, School]) -> None:
    existing = {
        p.slug: p
        for p in session.scalars(select(Program).where(Program.institution_id == inst.id))
        if p.slug
    }
    canonical = set(PROGRAM_SLUGS)
    for spec in PROGRAMS:
        p = existing.get(spec["slug"])
        if p is None:
            p = Program(
                institution_id=inst.id,
                program_name=spec["program_name"],
                degree_type=spec["degree_type"],
                slug=spec["slug"],
            )
            session.add(p)
        # Full official degree name as the title (falls back to the short label).
        p.program_name = _FULL_NAME_BY_SLUG.get(spec["slug"]) or spec["program_name"]
        p.degree_type = spec["degree_type"]
        p.duration_months = spec.get("duration_months")
        p.description_text = _DESC_RICH_BY_SLUG.get(spec["slug"]) or spec["description"]
        # Official program-page URL (read-more link on the program page).
        p.website_url = _WEBSITE_BY_SLUG.get(spec["slug"]) or _SCHOOL_WEBSITE.get(spec["school"])
        p.school_id = school_by_name[spec["school"]].id
        p.department = spec.get("department")
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec.get("delivery_format", "in_person")
        tuition, cost = _program_tuition(spec)
        p.tuition = tuition
        p.cost_data = cost
        p.application_requirements = _requirements_for(spec)
        # Inject per-program deadlines for the professional doctorates whose shared
        # requirement template is degree-agnostic (J.D. / LL.M. / M.D.).
        deadlines = _DEADLINES_BY_SLUG.get(spec["slug"])
        if deadlines is not None:
            p.application_requirements["deadlines"] = deadlines
        # Real per-program outcomes from College Scorecard Field-of-Study where
        # Harvard reports non-suppressed figures; otherwise Harvard-wide
        # institution outcomes, explicitly labelled (degree programs only);
        # non-degree credentials: none.
        # Outcomes precedence: program employment report (flagship) → Scorecard FOS
        # → institution median; non-degree credentials get none.
        out_override = _OUTCOMES_BY_SLUG.get(spec["slug"])
        fos = _FOS_OUTCOMES.get(spec["slug"])
        if out_override is not None:
            outcomes = dict(out_override)
        elif fos is not None:
            salary, debt, cip = fos
            outcomes = {
                "median_salary": salary,
                "scope": "program",
                "cip": cip,
                "source": "U.S. Dept. of Education College Scorecard — Field of Study",
                "source_url": "https://collegescorecard.ed.gov/",
            }
            if debt is not None:
                outcomes["median_debt_completers"] = debt
        elif spec["degree_type"] in ("bachelors", "masters", "phd"):
            outcomes = dict(_OUTCOMES_INSTITUTION)
        else:
            outcomes = None
        # Stamp every program with its _standard (version + honest omitted list).
        # outcomes_data is the carrier; non-degree credentials get a bare holder so
        # they are never left un-stamped (the prior bug for the certificates).
        if outcomes is None:
            outcomes = {"_standard": _program_standard(spec)}
        else:
            outcomes["_standard"] = _program_standard(spec)
        p.outcomes_data = outcomes
        # Audience + highlights: per-program for flagship, else by degree type.
        p.who_its_for = _WHO_BY_SLUG.get(spec["slug"]) or _WHO_BY_TYPE.get(spec["degree_type"])
        p.highlights = _HL_BY_SLUG.get(spec["slug"]) or _HL_BY_TYPE.get(spec["degree_type"])
        # Always assign so a stale value on a pre-existing row is cleared.
        p.tracks = _TRACKS_BY_SLUG.get(spec["slug"])
        # Insights (class profile, faculty, reviews) + per-program feed: flagship only.
        p.class_profile = _CLASS_PROFILE_BY_SLUG.get(spec["slug"])
        p.faculty_contacts = _FACULTY_BY_SLUG.get(spec["slug"])
        p.external_reviews = _REVIEWS_BY_SLUG.get(spec["slug"])
        # Every program carries a populated Events & Updates feed: the MBA keeps
        # its own keyword-relevant feed; the rest filter their school's feed by
        # program keywords (the MBAn pattern) so none is ever empty (the prior bug).
        if spec["slug"] == "harvard-mba":
            p.content_sources = _MBA_CONTENT
        else:
            p.content_sources = _program_content(spec)
        p.application_deadline = _deadline_for(spec)
    session.flush()
    # Reconcile legacy Harvard programs (slug not in the canonical set): delete
    # when unreferenced, otherwise unpublish so the catalog is clean without
    # breaking any application/match rows that point at them.
    for p in session.scalars(select(Program).where(Program.institution_id == inst.id)):
        if (p.slug or "") in canonical:
            continue
        if _program_has_dependents(session, p.id):
            p.is_published = False
        else:
            session.delete(p)
    session.flush()
