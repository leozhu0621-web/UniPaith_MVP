"""Institution-level enrichment for 4 universities the routine left shallow
(Boston, Cornell, Duke, Northwestern) — all values LIVE-VERIFIED by research
agents: ownership/Carnegie/accreditor + cited QS/THE/U.S.News rankings, official
news+events feeds, research labs WITH links, campus-life resources WITH links,
scale, founded/setting/location, and a character-leading description.

Merges into existing school_outcomes (preserves federal report-card stats), sets
content_sources only where NULL, stamps _standard. Idempotent; no-ops when an
institution is absent (fresh/CI DBs).

Revision ID: instenrich1
Revises: mergeofmerges1
"""
# ruff: noqa: E501

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from alembic import op
from unipaith.models.institution import Institution

revision = "instenrich1"
down_revision = "mergeofmerges1"
branch_labels = None
depends_on = None

_STAMP = {"version": 2, "enriched_at": "2026-06-10"}

_DATA = {
    "Boston University": {
        "ranking_data": {
            "ownership_type": "private",
            "carnegie_classification": "Research 1: Very High Research Spending "
            "and Doctorate Production (2025 Carnegie "
            "Classification)",
            "accreditor": "New England Commission of Higher Education (NECHE)",
            "qs_world_university_rankings": {
                "rank": 88,
                "year": 2026,
                "source_url": "https://www.topuniversities.com/universities/boston-university",
            },
            "times_higher_education": {
                "rank": 76,
                "year": 2026,
                "source_url": "https://www.timeshighereducation.com/world-university-rankings/boston-university",
            },
            "us_news_national": {
                "rank": 42,
                "year": 2026,
                "source_url": "https://www.usnews.com/best-colleges/boston-university-2130",
            },
        },
        "school_outcomes_add": {
            "research": {
                "areas": [
                    "Photonics and optical science",
                    "Emerging infectious diseases",
                    "Computing, data sciences, and artificial intelligence",
                    "Neuroscience and neurodegenerative disease (including CTE)",
                    "Climate and global sustainability",
                    "Biomedical engineering and life sciences",
                ],
                "labs": [
                    "Boston University Photonics Center",
                    "National Emerging Infectious Diseases Laboratories (NEIDL)",
                    "Rafik B. Hariri Institute for "
                    "Computing and Computational "
                    "Science & Engineering",
                    "Boston University CTE Center",
                    "Institute for Global Sustainability",
                    "Center for Systems Neuroscience",
                    "Frederick S. Pardee Center for the Study of the Longer-Range Future",
                ],
                "lab_links": {
                    "Boston University Photonics Center": "https://www.bu.edu/photonics/",
                    "National Emerging Infectious Diseases Laboratories (NEIDL)": "https://www.bu.edu/neidl/",
                    "Rafik B. Hariri Institute for Computing and Computational Science & Engineering": "https://www.bu.edu/hic/",
                    "Boston University CTE Center": "https://www.bu.edu/cte/",
                    "Institute for Global Sustainability": "https://www.bu.edu/igs/",
                    "Center for Systems Neuroscience": "https://www.bu.edu/csn/",
                    "Frederick S. Pardee Center for the Study of the Longer-Range Future": "https://www.bu.edu/pardee/",
                },
            },
            "campus_life": {
                "student_orgs": 450,
                "varsity_sports": 24,
                "athletics_division": "NCAA Division I "
                "(Patriot League; "
                "Hockey East for ice "
                "hockey)",
                "resources": [
                    {
                        "label": "Boston University Athletics (GoTerriers)",
                        "url": "https://goterriers.com/",
                    },
                    {
                        "label": "Student Leadership & Impact Center (student organizations)",
                        "url": "https://www.bu.edu/studentactivities/",
                    },
                    {"label": "Boston University Housing", "url": "https://www.bu.edu/housing/"},
                    {"label": "BU Office for the Arts", "url": "https://www.bu.edu/arts/"},
                ],
            },
            "scale": {
                "faculty_count": 4309,
                "student_faculty_ratio": "11:1",
                "endowment_usd": 4000000000,
                "campus_acres": 140,
            },
            "location": {"lat": 42.3505, "lng": -71.1054},
        },
        "content_sources": {
            "events_feed": {"url": "https://www.bu.edu/phpbin/calendar/ical.php", "type": "ical"},
            "social": {
                "instagram": "https://www.instagram.com/bostonu/",
                "linkedin": "https://www.linkedin.com/school/boston-university/",
                "x": "https://twitter.com/BU_Tweets",
                "youtube": "https://www.youtube.com/channel/UCuNjAAXrEmQyxLAanISnZUw",
                "facebook": "https://www.facebook.com/BostonUniversity/",
                "tiktok": "https://www.tiktok.com/@bostonu",
            },
        },
        "campus_setting": "urban",
        "founded_year": 1839,
        "description_text": "Boston University is a private research university in Boston, MA, "
        "founded in 1839 and chartered in the city in 1869. One of the "
        "largest private universities in the United States, BU enrolls more "
        "than 37,000 students from over 140 countries across 17 schools and "
        "colleges and is a member of the Association of American "
        "Universities. Its research footprint runs from the Photonics Center "
        "to the National Emerging Infectious Diseases Laboratories, threaded "
        "along the dense urban spine of its 140-acre Charles River Campus.",
    },
    "Cornell University": {
        "ranking_data": {
            "ownership_type": "private",
            "carnegie_classification": "Research 1: Very High Research Spending "
            "and Doctorate Production (2025 Carnegie "
            "Classification)",
            "accreditor": "Middle States Commission on Higher Education (MSCHE)",
            "qs_world_university_rankings": {
                "rank": 16,
                "year": 2026,
                "source_url": "https://www.topuniversities.com/universities/cornell-university",
            },
            "times_higher_education": {
                "rank": 18,
                "year": 2026,
                "source_url": "https://www.timeshighereducation.com/world-university-rankings/cornell-university",
            },
            "us_news_national": {
                "rank": 12,
                "year": 2026,
                "source_url": "https://www.usnews.com/best-colleges/cornell-university-2711",
            },
        },
        "school_outcomes_add": {
            "research": {
                "areas": [
                    "Artificial intelligence",
                    "Sustainability",
                    "Genome biology",
                    "Digital agriculture",
                    "Infection biology",
                    "Nanoscale science and microsystems engineering",
                ],
                "labs": [
                    "Cornell Lab of Ornithology",
                    "Cornell High Energy Synchrotron Source (CHESS)",
                    "Cornell Atkinson Center for Sustainability",
                    "Cornell NanoScale Science and Technology Facility (CNF)",
                    "Cornell Center for Materials Research (CCMR)",
                    "Laboratory of Atomic and Solid State Physics (LASSP)",
                ],
                "lab_links": {
                    "Cornell Lab of Ornithology": "https://www.birds.cornell.edu/home/",
                    "Cornell High Energy Synchrotron Source (CHESS)": "https://www.chess.cornell.edu/",
                    "Cornell Atkinson Center for Sustainability": "https://atkinson.cornell.edu/",
                    "Cornell NanoScale Science and Technology Facility (CNF)": "https://www.cnf.cornell.edu/",
                    "Cornell Center for Materials Research (CCMR)": "https://www.ccmr.cornell.edu/",
                    "Laboratory of Atomic and Solid State Physics (LASSP)": "https://www.lassp.cornell.edu/",
                },
            },
            "campus_life": {
                "student_orgs": 1000,
                "varsity_sports": 37,
                "athletics_division": "NCAA Division I (Ivy League)",
                "resources": [
                    {"label": "Cornell Athletics (Big Red)", "url": "https://cornellbigred.com/"},
                    {"label": "Student & Campus Life", "url": "https://scl.cornell.edu/"},
                    {
                        "label": "Housing & Residential Life",
                        "url": "https://scl.cornell.edu/residential-life/housing",
                    },
                    {
                        "label": "CampusGroups — student organizations portal",
                        "url": "https://cornell.campusgroups.com/",
                    },
                    {
                        "label": "Herbert F. Johnson Museum of Art",
                        "url": "https://museum.cornell.edu/",
                    },
                ],
            },
            "scale": {
                "faculty_count": 3025,
                "student_faculty_ratio": "9:1",
                "endowment_usd": 11800000000,
                "campus_acres": 2300,
            },
            "location": {"lat": 42.4492, "lng": -76.4839},
        },
        "content_sources": {
            "news_rss": "https://news.cornell.edu/taxonomy/term/81/feed",
            "events_feed": {"url": "https://events.cornell.edu/calendar.ics", "type": "ical"},
            "social": {
                "instagram": "https://instagram.com/cornelluniversity",
                "linkedin": "https://www.linkedin.com/school/cornell-university/",
                "x": "https://twitter.com/Cornell",
                "youtube": "https://www.youtube.com/c/Cornell",
                "facebook": "https://www.facebook.com/Cornell",
            },
        },
        "campus_setting": "urban",
        "founded_year": 1865,
        "description_text": "Cornell University is a private research university in Ithaca, NY. "
        "Founded in 1865, it is both an Ivy League member and New York "
        "State's federal land-grant institution — a \"private university, "
        'public mission" hybrid that pairs privately endowed colleges with '
        "state-supported statutory schools. Its community counts 52 Nobel "
        "laureates, and its 2,300-acre campus above Cayuga Lake is home to "
        "landmarks such as the Cornell Lab of Ornithology and the Cornell "
        "High Energy Synchrotron Source.",
    },
    "Duke University": {
        "ranking_data": {
            "ownership_type": "private",
            "carnegie_classification": "R1: Doctoral Universities – Very High Research Activity",
            "accreditor": "Southern Association of Colleges and Schools Commission "
            "on Colleges (SACSCOC)",
            "qs_world_university_rankings": {
                "rank": 62,
                "year": 2026,
                "source_url": "https://www.topuniversities.com/universities/duke-university",
            },
            "times_higher_education": {
                "rank": 28,
                "year": 2026,
                "source_url": "https://www.timeshighereducation.com/world-university-rankings/duke-university",
            },
            "us_news_national": {
                "rank": 7,
                "year": 2026,
                "source_url": "https://www.usnews.com/best-colleges/duke-university-2920",
            },
        },
        "school_outcomes_add": {
            "research": {
                "areas": [
                    "Global health",
                    "Brain sciences & neuroscience",
                    "Energy, environment & climate sustainability",
                    "Health policy",
                    "Ethics & humanities",
                    "Quantum science & engineering",
                ],
                "labs": [
                    "Duke Global Health Institute",
                    "Duke Institute for Brain Sciences",
                    "Nicholas Institute for Energy, Environment & Sustainability",
                    "Duke Margolis Institute for Health Policy",
                    "Kenan Institute for Ethics",
                    "John Hope Franklin Humanities Institute",
                    "Duke Human Vaccine Institute",
                    "Duke Quantum Center",
                ],
                "lab_links": {
                    "Duke Global Health Institute": "https://globalhealth.duke.edu/",
                    "Duke Institute for Brain Sciences": "https://dibs.duke.edu/",
                    "Nicholas Institute for Energy, Environment & Sustainability": "https://nicholasinstitute.duke.edu/",
                    "Duke Margolis Institute for Health Policy": "https://healthpolicy.duke.edu/",
                    "Kenan Institute for Ethics": "https://kenan.ethics.duke.edu/",
                    "John Hope Franklin Humanities Institute": "https://fhi.duke.edu/",
                    "Duke Human Vaccine Institute": "https://dhvi.duke.edu/",
                    "Duke Quantum Center": "https://quantum.duke.edu/",
                },
            },
            "campus_life": {
                "varsity_sports": 27,
                "athletics_division": "NCAA Division I (Atlantic Coast Conference)",
                "resources": [
                    {"label": "Duke Athletics", "url": "https://goduke.com/"},
                    {
                        "label": "DukeGroups — Student Organizations Portal",
                        "url": "https://dukegroups.com/",
                    },
                    {
                        "label": "Living at Duke — Housing & Residence Life",
                        "url": "https://students.duke.edu/living/",
                    },
                    {"label": "Duke Arts", "url": "https://arts.duke.edu/"},
                    {"label": "Duke Student Affairs", "url": "https://students.duke.edu/"},
                ],
            },
            "scale": {
                "faculty_count": 4236,
                "student_faculty_ratio": "5:1",
                "endowment_usd": 11900000000,
                "campus_acres": 8693,
            },
            "location": {"lat": 36.0016, "lng": -78.9382},
        },
        "content_sources": {
            "news_rss": "https://today.duke.edu/topics/campus-%26-community/rss",
            "events_feed": {"url": "https://calendar.duke.edu/events/index.ics", "type": "ical"},
            "social": {
                "instagram": "https://www.instagram.com/dukeuniversity/",
                "x": "https://x.com/DukeU",
                "facebook": "https://www.facebook.com/DukeUniv",
                "youtube": "https://www.youtube.com/@dukeuniversity",
                "linkedin": "https://www.linkedin.com/school/duke-university/",
                "tiktok": "https://www.tiktok.com/@dukeu",
            },
        },
        "campus_setting": "urban",
        "founded_year": 1838,
        "description_text": "Duke University is a private research university in Durham, NC. "
        "Founded in 1838 as Union Institute by local Methodist and Quaker "
        "communities and renamed Duke University in 1924 through James B. "
        "Duke's endowment, it now enrolls roughly 17,300 students on an "
        "8,693-acre footprint that includes Duke Forest. A Carnegie R1 "
        "institution with a 5:1 student-faculty ratio and an $11.9 billion "
        "endowment, Duke pairs flagship institutes in global health, brain "
        "sciences, and health policy with 27 NCAA Division I varsity teams in "
        "the Atlantic Coast Conference.",
    },
    "Northwestern University": {
        "ranking_data": {
            "ownership_type": "private",
            "carnegie_classification": "Research 1: Very High Research "
            "Spending and Doctorate Production",
            "accreditor": "Higher Learning Commission (HLC)",
            "qs_world_university_rankings": {
                "rank": 42,
                "year": 2026,
                "source_url": "https://www.topuniversities.com/universities/northwestern-university",
            },
            "times_higher_education": {
                "rank": 30,
                "year": 2026,
                "source_url": "https://www.timeshighereducation.com/world-university-rankings/northwestern-university",
            },
            "us_news_national": {
                "rank": 7,
                "year": 2026,
                "source_url": "https://www.usnews.com/best-colleges/northwestern-university-1739",
            },
        },
        "school_outcomes_add": {
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
                    "Northwestern University "
                    "Clinical and Translational "
                    "Sciences (NUCATS) Institute",
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
                "student_orgs": 500,
                "varsity_sports": 19,
                "athletics_division": "NCAA Division I (Big Ten)",
                "resources": [
                    {"label": "Northwestern Athletics", "url": "https://nusports.com/"},
                    {
                        "label": "Student Organizations & Activities",
                        "url": "https://www.northwestern.edu/studentorgs/",
                    },
                    {
                        "label": "Norris University Center",
                        "url": "https://www.northwestern.edu/norris/",
                    },
                    {"label": "Residential Services", "url": "https://www.northwestern.edu/living/"},
                    {
                        "label": "Campus Experience",
                        "url": "https://www.northwestern.edu/campus-experience/",
                    },
                ],
            },
            "scale": {
                "faculty_count": 3300,
                "student_faculty_ratio": "6:1",
                "endowment_usd": 15300000000,
                "campus_acres": 240,
            },
            "location": {"lat": 42.0565, "lng": -87.6753},
        },
        "content_sources": {
            "news_rss": "https://news.northwestern.edu/feeds/allStories",
            "events_feed": {
                "url": "https://planitpurple.northwestern.edu/feed/ical/124",
                "type": "ical",
            },
            "social": {
                "instagram": "https://instagram.com/northwesternu",
                "facebook": "https://www.facebook.com/NorthwesternU",
                "x": "https://x.com/northwesternu",
                "youtube": "https://www.youtube.com/user/NorthwesternU",
                "linkedin": "https://www.linkedin.com/school/northwestern-university/",
            },
        },
        "campus_setting": "suburban",
        "founded_year": 1851,
        "description_text": "Northwestern University is a private research university in "
        "Evanston, IL, founded in 1851 on the shore of Lake Michigan "
        "just north of Chicago. A founding member of the Big Ten "
        "Conference, it pairs a 240-acre lakefront campus and a 6:1 "
        "student-faculty ratio with a research enterprise topping $1 "
        "billion in annual funding. Its International Institute for "
        "Nanotechnology, established in 2000, was the first institute "
        "of its kind in the United States.",
    },
}


def upgrade() -> None:
    s = Session(bind=op.get_bind())
    for name, d in _DATA.items():
        inst = s.scalar(select(Institution).where(Institution.name == name))
        if inst is None:
            continue
        inst.ranking_data = {**(inst.ranking_data or {}), **d["ranking_data"]}
        so = {**(inst.school_outcomes or {}), **d["school_outcomes_add"]}
        so["_standard"] = dict(_STAMP)
        inst.school_outcomes = so
        if d["content_sources"] and not inst.content_sources:
            inst.content_sources = d["content_sources"]
        if d.get("campus_setting") and not inst.campus_setting:
            inst.campus_setting = d["campus_setting"]
        if d.get("founded_year") and not inst.founded_year:
            inst.founded_year = d["founded_year"]
        if d.get("description_text"):
            inst.description_text = d["description_text"]
        flag_modified(inst, "ranking_data")
        flag_modified(inst, "school_outcomes")
    s.flush()


def downgrade() -> None:
    pass
