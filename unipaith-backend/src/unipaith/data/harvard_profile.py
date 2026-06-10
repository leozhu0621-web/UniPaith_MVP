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
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from unipaith.models.institution import Institution, Program, School
from unipaith.profile_standard import STANDARD_VERSION

INSTITUTION_NAME = "Harvard University"

# Date this run certified Harvard's institution + school nodes against the
# profile standard (used in the per-node _standard stamps below).
_ENRICHED_AT = "2026-06-10"

# ── Institution-level data ────────────────────────────────────────────────
# Rankings are stored as {rank, year} objects because the page renders every
# ranking_data entry that is an object with a numeric `rank` (labelled via the
# frontend `rankingLabel` map, which already knows these keys).
RANKING_DATA: dict = {
    "ownership_type": "private_nonprofit",
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
        # Total instructional faculty (full-time 1,846 + part-time 316) per the
        # Harvard Common Data Set 2024-2025, Section I-1 — the same CDS/IPEDS
        # "instructional faculty" definition MIT's count uses.
        "faculty_count": 2162,
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
    },
    "campus_life": {
        "varsity_sports": 42,
        "athletics_division": "NCAA Division I (Ivy League)",
        "residence_halls": 12,
    },
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
            "label": "Instructional faculty count (CDS-I)",
            "source": "Harvard Common Data Set 2024-2025",
            "year": 2024,
            "url": "https://oira.harvard.edu/factbook/",
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
    "Founded in 1636, Harvard University is the oldest institution of higher "
    "education in the United States and one of the most influential research "
    "universities in the world. Its campus centers on Harvard Yard in Cambridge, "
    "Massachusetts, and extends across the Charles River into the Allston "
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

# ── School "About" tabs — founded · leadership · notable faculty · research
# centers · named-for · source. Every value verified against the school's own
# official harvard.edu page (cross-checked against Harvard Gazette / official
# announcements for the current 2025-26 deans). Faculty rosters list only
# currently-active professors confirmed on official profile pages (deceased and
# emeritus names were deliberately excluded). The Division of Continuing
# Education legitimately omits faculty/research_centers (a teaching division
# with no citable notable-faculty roster or named research centers) — recorded
# in _SCHOOL_STANDARD[...].omitted.
_SCHOOL_ABOUT_DETAIL: dict[str, dict] = {
    "Harvard Faculty of Arts & Sciences": {
        "founded": 1890,
        "leadership": "Hopi E. Hoekstra, Edgerley Family Dean of the Faculty of Arts and Sciences",
        "faculty": [
            {
                "name": "Claudia Goldin",
                "title": "Henry Lee Professor of Economics",
                "focus": "Labor economics and economic history of gender — 2023 Nobel laureate",
            },
            {
                "name": "Henry Louis Gates Jr.",
                "title": "Alphonse Fletcher University Professor",
                "focus": "African & African American studies; directs the Hutchins Center",
            },
            {
                "name": "Steven Pinker",
                "title": "Johnstone Family Professor of Psychology",
                "focus": "Cognitive psychology, psycholinguistics, and human rationality",
            },
        ],
        "research_centers": [
            "Weatherhead Center for International Affairs",
            "Davis Center for Russian & Eurasian Studies",
            "Hutchins Center for African & African American Research",
            "Fairbank Center for Chinese Studies",
            "David Rockefeller Center for Latin American Studies",
        ],
        "source": {
            "label": "Harvard Faculty of Arts & Sciences",
            "url": "https://www.fas.harvard.edu/",
        },
    },
    "Harvard John A. Paulson School of Engineering & Applied Sciences": {
        "founded": 2007,
        "named_for": (
            "Named in June 2015 for hedge-fund manager and alumnus John A. Paulson "
            "(M.B.A. 1980) following his $400 million gift — the largest in "
            "Harvard's history at the time."
        ),
        "leadership": (
            "David C. Parkes, Dean; George F. Colony Professor of Computer Science"
        ),
        "faculty": [
            {
                "name": "Joanna Aizenberg",
                "title": "Amy Smith Berylson Professor of Materials Science",
                "focus": "Bio-inspired materials, surfaces, and self-assembly",
            },
            {
                "name": "Michael P. Brenner",
                "title": "Catalyst Professor of Applied Mathematics and Applied Physics",
                "focus": "Applied mathematics, computational physics, and ML for science",
            },
            {
                "name": "Katia Bertoldi",
                "title": "William and Ami Kuan Danoff Professor of Applied Mechanics",
                "focus": "Mechanical metamaterials and the mechanics of soft structures",
            },
            {
                "name": "Michael J. Aziz",
                "title": "Gene and Tracy Sykes Professor of Materials and Energy Technologies",
                "focus": "Grid-scale energy storage and flow batteries",
            },
        ],
        "research_centers": [
            "Center for Integrated Quantum Materials",
            "Kempner Institute for the Study of Natural & Artificial Intelligence",
            "Max Planck–Harvard Research Center for Quantum Optics",
            "Materials Research Science and Engineering Center (MRSEC)",
            "Harvard–China Project on Energy, Economy and Environment",
        ],
        "source": {
            "label": "Harvard SEAS — School overview",
            "url": "https://seas.harvard.edu/about-us/school-overview",
        },
    },
    "Harvard Business School": {
        "founded": 1908,
        "leadership": "Srikant M. Datar, Dean",
        "faculty": [
            {
                "name": "Amy C. Edmondson",
                "title": "Novartis Professor of Leadership and Management",
                "focus": "Teaming, organizational learning, and psychological safety",
            },
            {
                "name": "Michael E. Porter",
                "title": "Bishop William Lawrence University Professor",
                "focus": "Competitive strategy and the competitiveness of nations",
            },
            {
                "name": "Rebecca M. Henderson",
                "title": "John and Natty McArthur University Professor",
                "focus": "Capitalism, climate change, and reimagining the firm",
            },
        ],
        "research_centers": [
            "Institute for Strategy and Competitiveness",
            "Arthur Rock Center for Entrepreneurship",
            "Laboratory for Innovation Science at Harvard",
            "Institute for Business in Global Society (BiGS)",
            "Health Care Initiative",
        ],
        "source": {
            "label": "Harvard Business School — History",
            "url": "https://www.hbs.edu/about/history",
        },
    },
    "Harvard Law School": {
        "founded": 1817,
        "leadership": "John C.P. Goldberg, Morgan and Helen Chu Dean and Professor of Law",
        "faculty": [
            {
                "name": "Cass R. Sunstein",
                "title": "Robert Walmsley University Professor",
                "focus": "Behavioral economics, administrative and constitutional law",
            },
            {
                "name": "Noah Feldman",
                "title": "Felix Frankfurter Professor of Law",
                "focus": "Constitutional studies, international law, and legal history",
            },
            {
                "name": "Jeannie Suk Gersen",
                "title": "John H. Watson, Jr. Professor of Law",
                "focus": "Constitutional, criminal, and family law",
            },
        ],
        "research_centers": [
            "Program on Negotiation",
            "Harvard Negotiation and Mediation Clinical Program",
            "Center on the Legal Profession",
            "Program on International Legal Studies",
            "Program on Behavioral Economics and Public Policy",
        ],
        "source": {
            "label": "Harvard Law School — Founding history",
            "url": "https://hls.harvard.edu/today/looking-back-founding-harvard-law-school/",
        },
    },
    "Harvard Medical School": {
        "founded": 1782,
        "leadership": (
            "George Q. Daley, Dean of the Faculty of Medicine; "
            "Caroline Shields Walker Professor of Medicine"
        ),
        "faculty": [
            {
                "name": "George M. Church",
                "title": "Robert Winthrop Professor of Genetics",
                "focus": "Genomics, synthetic biology, and gene editing",
            },
            {
                "name": "David A. Sinclair",
                "title": "Professor of Genetics",
                "focus": "Biology of aging, cellular reprogramming, and longevity",
            },
            {
                "name": "Clifford J. Tabin",
                "title": "George Jacob and Jacqueline Hazel Leder Professor of Genetics",
                "focus": "Developmental and evolutionary genetics",
            },
        ],
        "research_centers": [
            "Blavatnik Institute at Harvard Medical School",
            "Wyss Institute for Biologically Inspired Engineering",
            "Harvard Stem Cell Institute",
            "Broad Institute of MIT and Harvard",
            "Harvard Catalyst (Clinical and Translational Science Center)",
        ],
        "source": {
            "label": "Harvard Medical School — History of HMS",
            "url": "https://hms.harvard.edu/about-hms/history-hms",
        },
    },
    "Harvard T.H. Chan School of Public Health": {
        "founded": 1913,
        "named_for": (
            "Renamed in 2014 in recognition of a $350 million gift from alumnus "
            "Gerald L. Chan, his family, and the Morningside Foundation, given in "
            "memory of his father, T.H. Chan — the largest gift in Harvard's "
            "history at the time."
        ),
        "leadership": "Andrea A. Baccarelli, Dean of the Faculty",
        "faculty": [
            {
                "name": "Walter C. Willett",
                "title": "Professor of Epidemiology and Nutrition",
                "focus": "Nutritional epidemiology and diet's effect on chronic disease",
            },
            {
                "name": "Marc Lipsitch",
                "title": "Professor of Epidemiology",
                "focus": "Infectious-disease dynamics; directs the CCDD",
            },
        ],
        "research_centers": [
            "Center for Communicable Disease Dynamics",
            "Harvard Center for Climate, Health, and the Global Environment (C-CHANGE)",
            "Harvard Center for Population and Development Studies",
            "Center for Health Communication",
            "India Research Center",
        ],
        "source": {
            "label": "Harvard T.H. Chan School of Public Health — History",
            "url": "https://hsph.harvard.edu/history/",
        },
    },
    "Harvard Kennedy School": {
        "founded": 1936,
        "named_for": (
            "Founded in 1936 as the Graduate School of Public Administration with a "
            "gift from Lucius Littauer; renamed the John F. Kennedy School of "
            "Government in 1966 in honor of President John F. Kennedy."
        ),
        "leadership": (
            "Jeremy M. Weinstein, Dean of the Faculty; "
            "Don K. Price Professor of Public Policy"
        ),
        "faculty": [
            {
                "name": "Dani Rodrik",
                "title": "Ford Foundation Professor of International Political Economy",
                "focus": "Economic development, globalization, and political economy",
            },
            {
                "name": "Pippa Norris",
                "title": "Paul F. McGuire Lecturer in Comparative Politics",
                "focus": "Comparative democracy, elections, and political communication",
            },
        ],
        "research_centers": [
            "Belfer Center for Science and International Affairs",
            "Ash Center for Democratic Governance and Innovation",
            "Carr-Ryan Center for Human Rights",
            "Bloomberg Center for Cities",
            "Center for International Development",
        ],
        "source": {
            "label": "Harvard Kennedy School — History timeline",
            "url": "https://www.hks.harvard.edu/more/about/timeline-harvard-kennedy-schools-history",
        },
    },
    "Harvard Graduate School of Education": {
        "founded": 1920,
        "leadership": (
            "Nonie K. Lesaux, Dean; "
            "Roy E. Larsen Professor of Education and Human Development"
        ),
        "faculty": [
            {
                "name": "Howard Gardner",
                "title": (
                    "John H. and Elisabeth A. Hobbs Research Professor "
                    "of Cognition and Education"
                ),
                "focus": "Theory of multiple intelligences; cognition and education",
            },
            {
                "name": "Fernando M. Reimers",
                "title": "Ford Foundation Professor of Practice in International Education",
                "focus": "Global and comparative education and educational innovation",
            },
            {
                "name": "Karen L. Mapp",
                "title": "Professor of Practice in Adult Learning and Professional Development",
                "focus": "Family–school–community partnerships and school improvement",
            },
        ],
        "research_centers": [
            "Project Zero",
            "Center for Education Policy Research",
            "Center on the Developing Child",
            "Center for Digital Thriving",
            "Making Caring Common",
        ],
        "source": {
            "label": "Harvard Graduate School of Education — About",
            "url": "https://www.gse.harvard.edu/about",
        },
    },
    "Harvard Graduate School of Design": {
        "founded": 1936,
        "leadership": "Sarah M. Whiting, Dean; Josep Lluís Sert Professor of Architecture",
        "faculty": [
            {
                "name": "Charles Waldheim",
                "title": "John E. Irving Professor of Landscape Architecture",
                "focus": "Landscape urbanism; directs the Office for Urbanization",
            },
            {
                "name": "Anita Berrizbeitia",
                "title": "Professor of Landscape Architecture",
                "focus": "Landscape architecture theory, design, and history",
            },
            {
                "name": "Ann Forsyth",
                "title": "Ruth and Frank Stanton Professor of Urban Planning",
                "focus": "Urban planning, health, and the built environment",
            },
        ],
        "research_centers": [
            "Joint Center for Housing Studies",
            "Harvard Center for Green Buildings and Cities",
            "Office for Urbanization",
        ],
        "source": {
            "label": "Harvard Graduate School of Design — About",
            "url": "https://www.gsd.harvard.edu/about/",
        },
    },
    "Harvard Divinity School": {
        "founded": 1816,
        "leadership": "Marla F. Frederick, Dean of Harvard Divinity School",
        "faculty": [
            {
                "name": "Catherine A. Brekus",
                "title": "Charles Warren Professor of the History of Religion in America",
                "focus": "Religion and American culture; gender and Christianity",
            },
            {
                "name": "Benjamin H. Dunning",
                "title": "Florence Corliss Lamont Professor of Divinity",
                "focus": "New Testament and early Christianity",
            },
            {
                "name": "Matthew Ichihashi Potts",
                "title": "Plummer Professor of Christian Morals; Pusey Minister",
                "focus": "Christian ethics and theology",
            },
        ],
        "research_centers": [
            "Center for the Study of World Religions",
            "Religion and Public Life",
            "Women's Studies in Religion Program",
            "Religious Literacy Project",
        ],
        "source": {
            "label": "Harvard Divinity School — History and mission",
            "url": "https://www.hds.harvard.edu/about/history-and-mission",
        },
    },
    "Harvard School of Dental Medicine": {
        "founded": 1867,
        "named_for": (
            "Its shield's tower (a heraldic 'keep') honors founding dean Nathan "
            "Cooley Keep; the school itself carries no personal eponym."
        ),
        "leadership": (
            "William V. Giannobile, Dean; "
            "A. Lee Loomis, Jr. Professor of Oral Medicine, Infection, and Immunity"
        ),
        "faculty": [
            {
                "name": "Vicki Rosen",
                "title": "Doctors Samuel and Ida Gelfand Professor; Chair of Developmental Biology",
                "focus": "Bone biology and skeletal development",
            },
            {
                "name": "Yingzi Yang",
                "title": "Professor of Developmental Biology; Associate Dean for Research",
                "focus": "Signaling in skeletal and craniofacial development",
            },
            {
                "name": "Magda Feres",
                "title": "Chair, Department of Oral Medicine, Infection, and Immunity",
                "focus": "Periodontology and periodontal microbiology",
            },
        ],
        "research_centers": [
            "Initiative to Integrate Oral Health and Medicine",
            "HSDM Office of Research",
        ],
        "source": {
            "label": "Harvard School of Dental Medicine — History",
            "url": "https://www.hsdm.harvard.edu/history",
        },
    },
    "Harvard Division of Continuing Education": {
        # DCE is a teaching division (Harvard Extension School, est. 1910;
        # Harvard Summer School, est. 1871) formally organized as the Division
        # of Continuing Education in 1975. faculty + research_centers are
        # legitimately omitted (no citable DCE-specific roster or named centers;
        # courses are taught by Harvard and visiting faculty across schools) —
        # see _SCHOOL_STANDARD[...].omitted.
        "founded": 1975,
        "leadership": "Nancy J. Coleman, Dean of Continuing Education and University Extension",
        "source": {
            "label": "Harvard Division of Continuing Education — About",
            "url": "https://www.dce.harvard.edu/about",
        },
    },
}

# ── Profile-standard stamps (provenance for the gold-standard routine) ──────
# version = the STANDARD_VERSION the node was certified against; enriched_at =
# the run date; omitted = required fields legitimately unavailable for that node
# (verified-absent, recorded so conformance treats the node as gold). Programs
# are not yet certified to v2 — they are enriched in a subsequent run.
INSTITUTION_STANDARD: dict = {
    "version": STANDARD_VERSION,
    "enriched_at": _ENRICHED_AT,
    "omitted": [],
}

_SCHOOL_STANDARD: dict[str, dict] = {
    name: {"version": STANDARD_VERSION, "enriched_at": _ENRICHED_AT, "omitted": []}
    for name in _SCHOOL_ABOUT_DETAIL
}
# The Division of Continuing Education is a teaching division: it has no citable
# school-specific notable-faculty roster and operates no named research centers
# (courses are taught by Harvard and visiting faculty across the schools), so
# those two required about_detail fields are omitted rather than fabricated.
_SCHOOL_STANDARD["Harvard Division of Continuing Education"]["omitted"] = [
    "about_detail.faculty",
    "about_detail.research_centers",
]

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

PROGRAM_SLUGS = [p["slug"] for p in PROGRAMS]

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
    ],
    "test_policy": {"stance": "required", "note": "GMAT or GRE required"},
    "recommendations": {
        "required_count": 2,
        "types": ["Two professional letters of recommendation"],
    },
    "source": "Harvard Business School MBA Admissions",
    "source_url": "https://www.hbs.edu/mba/admissions",
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
_CAMPUS_PHOTO = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/"
    "2014-04-03-Harvard-Yard-Cambridge-Massachusetts.jpg/"
    "1920px-2014-04-03-Harvard-Yard-Cambridge-Massachusetts.jpg"
)


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
    inst.school_outcomes = {**(inst.school_outcomes or {}), **SCHOOL_OUTCOMES}
    inst.description_text = DESCRIPTION
    inst.student_body_size = UNDERGRAD_COUNT
    inst.founded_year = FOUNDED_YEAR
    inst.campus_setting = CAMPUS_SETTING
    # Lead the gallery with a real campus photo (the detail-page hero shows the
    # first raster image; the gallery otherwise holds only the logo SVG).
    _gallery = [u for u in (inst.media_gallery or []) if u != _CAMPUS_PHOTO]
    inst.media_gallery = [_CAMPUS_PHOTO, *_gallery]
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
        about = _SCHOOL_ABOUT_DETAIL.get(spec["name"])
        if about is not None:
            sc.about_detail = about
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
        p.website_url = _WEBSITE_BY_SLUG.get(spec["slug"])
        p.school_id = school_by_name[spec["school"]].id
        p.is_published = True
        p.catalog_source = "curated"
        p.delivery_format = spec.get("delivery_format", "in_person")
        # Tuition: explicit per-school published rate → undergrad rate → funded
        # PhD (0) → Extension/HarvardX per-course (null). Every figure is real.
        if spec["slug"] in _TUITION_BY_SLUG:
            p.tuition = _TUITION_BY_SLUG[spec["slug"]]
        elif spec["degree_type"] == "phd":
            p.tuition = 0
        elif (
            spec["slug"] == "harvard-alm"
            or p.delivery_format == "online"
            or (spec["degree_type"] == "certificate")
        ):
            p.tuition = None
        elif spec["degree_type"] == "bachelors":
            p.tuition = _TUITION_UNDERGRAD
        else:
            p.tuition = None
        src_name, src_url = _COST_SRC_BY_SCHOOL.get(
            spec["school"], ("Harvard University", "https://www.harvard.edu/")
        )
        p.cost_data = (
            {
                "tuition_usd": p.tuition,
                "funded": spec["degree_type"] == "phd",
                "source": src_name,
                "source_url": src_url,
                "year": "2025-26",
            }
            if (p.tuition is not None or spec["degree_type"] == "phd")
            else None
        )
        p.application_requirements = _requirements_for(spec)
        # Real per-program outcomes from College Scorecard Field-of-Study where
        # Harvard reports non-suppressed figures; otherwise Harvard-wide
        # institution outcomes, explicitly labelled (degree programs only);
        # non-degree credentials: none.
        fos = _FOS_OUTCOMES.get(spec["slug"])
        if fos is not None:
            salary, debt, cip = fos
            p.outcomes_data = {
                "median_salary": salary,
                "scope": "program",
                "cip": cip,
                "source": "U.S. Dept. of Education College Scorecard — Field of Study",
                "source_url": "https://collegescorecard.ed.gov/",
            }
            if debt is not None:
                p.outcomes_data["median_debt_completers"] = debt
        elif spec["degree_type"] in ("bachelors", "masters", "phd"):
            p.outcomes_data = dict(_OUTCOMES_INSTITUTION)
        else:
            p.outcomes_data = None
        # Audience + highlights: per-program for flagship, else by degree type.
        p.who_its_for = _WHO_BY_SLUG.get(spec["slug"]) or _WHO_BY_TYPE.get(spec["degree_type"])
        p.highlights = _HL_BY_SLUG.get(spec["slug"]) or _HL_BY_TYPE.get(spec["degree_type"])
        if spec["slug"] in _TRACKS_BY_SLUG:
            p.tracks = _TRACKS_BY_SLUG[spec["slug"]]
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
