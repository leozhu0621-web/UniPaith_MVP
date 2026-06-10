"""Institution-level enrichment for the remaining 14 shallow universities
(Carnegie Mellon, Georgia Tech, Johns Hopkins, NYU, Purdue, Rice, UT Austin,
UCLA, UCSD, UIUC, Michigan, USC, UW-Seattle, Wisconsin) — all values
LIVE-VERIFIED by research agents: ownership/Carnegie/accreditor + cited
QS/THE/U.S.News rankings, official news+events feeds, research labs WITH links,
campus-life resources WITH links, scale, founded/setting/location, and a
character-leading description. Completes the institution level for all 18.

Merges into existing school_outcomes (federal stats preserved); content_sources
only where NULL; stamps _standard v2. Idempotent; no-ops when absent.

Revision ID: instenrich2
Revises: instenrich1
"""
# ruff: noqa: E501

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from alembic import op
from unipaith.models.institution import Institution

revision = "instenrich2"
down_revision = "instenrich1"
branch_labels = None
depends_on = None

_STAMP = {"version": 2, "enriched_at": "2026-06-10"}

_DATA = {
    "Carnegie Mellon University": {
        "ranking_data": {
            "ownership_type": "private",
            "carnegie_classification": "R1: Doctoral Universities – Very "
            "High Research Spending and "
            "Doctorate Production",
            "accreditor": "MSCHE (Middle States Commission on Higher Education)",
            "qs_world_university_rankings": {
                "rank": 52,
                "year": 2026,
                "source_url": "https://www.topuniversities.com/universities/carnegie-mellon-university",
            },
            "times_higher_education": {
                "rank": 24,
                "year": 2026,
                "source_url": "https://www.timeshighereducation.com/world-university-rankings/carnegie-mellon-university",
            },
            "us_news_national": {
                "rank": 20,
                "year": 2026,
                "source_url": "https://www.usnews.com/best-colleges/carnegie-mellon-university-3242",
            },
        },
        "school_outcomes_add": {
            "research": {
                "areas": [
                    "Artificial intelligence and machine learning",
                    "Robotics and autonomous systems",
                    "Human-computer interaction",
                    "Language technologies and natural language processing",
                    "Cybersecurity and privacy",
                    "Software engineering",
                ],
                "labs": [
                    "Robotics Institute",
                    "Software Engineering Institute (SEI)",
                    "Human-Computer Interaction Institute (HCII)",
                    "Language Technologies Institute (LTI)",
                    "Machine Learning Department",
                    "CyLab Security and Privacy Institute",
                ],
                "lab_links": {
                    "Robotics Institute": "https://www.ri.cmu.edu/",
                    "Software Engineering Institute (SEI)": "https://www.sei.cmu.edu/",
                    "Human-Computer Interaction Institute (HCII)": "https://hcii.cmu.edu/",
                    "Language Technologies Institute (LTI)": "https://www.lti.cs.cmu.edu/",
                    "Machine Learning Department": "https://www.ml.cmu.edu/",
                    "CyLab Security and Privacy Institute": "https://www.cylab.cmu.edu/",
                },
            },
            "campus_life": {
                "student_orgs": 400,
                "varsity_sports": 19,
                "athletics_division": "NCAA Division III (University Athletic Association)",
                "resources": [
                    {
                        "name": "Get Involved - Student Affairs",
                        "url": "https://www.cmu.edu/student-affairs/get-involved/index.html",
                    },
                    {
                        "name": "Student Involvement & Traditions",
                        "url": "https://www.cmu.edu/student-affairs/sit/involvement/index.html",
                    },
                    {
                        "name": "Carnegie Mellon Athletics (Tartans)",
                        "url": "https://athletics.cmu.edu/",
                    },
                    {"name": "CMU Events Calendar", "url": "https://events.cmu.edu/"},
                    {
                        "name": "Center for Student Diversity and Inclusion",
                        "url": "https://www.cmu.edu/student-diversity/",
                    },
                ],
            },
            "scale": {
                "faculty_count": 1615,
                "student_faculty_ratio": "6:1",
                "endowment_usd": 3484600000,
                "campus_acres": 157,
            },
            "location": {"lat": 40.4433, "lng": -79.9436},
        },
        "content_sources": {
            "news_rss": "https://www.cmu.edu/news/feeds/news.rss",
            "events_feed": {"url": "https://events.cmu.edu/live/ical/events", "type": "ical"},
            "social": {
                "instagram": "https://www.instagram.com/carnegiemellon/",
                "linkedin": "https://www.linkedin.com/company/carnegie-mellon-university/",
                "x": "https://x.com/carnegiemellon",
                "youtube": "https://www.youtube.com/carnegiemellonu",
                "facebook": "https://www.facebook.com/carnegiemellonu",
            },
        },
        "campus_setting": "urban",
        "founded_year": 1900,
        "description_text": "Carnegie Mellon University is a private research university "
        "in Pittsburgh, Pennsylvania, formed in 1967 by the merger "
        "of the Carnegie Institute of Technology (founded by Andrew "
        "Carnegie in 1900) and the Mellon Institute of Industrial "
        "Research. It is an R1 doctoral university accredited by the "
        "Middle States Commission on Higher Education, home to the "
        "world's first Robotics Institute (1979) and the first "
        "academic Machine Learning Department (2006). CMU is "
        "consistently ranked first in the United States for its "
        "computer science and artificial intelligence programs and "
        "operates the federally funded Software Engineering "
        "Institute on behalf of the U.S. Department of Defense.",
    },
    "Georgia Institute of Technology-Main Campus": {
        "ranking_data": {
            "ownership_type": "public",
            "carnegie_classification": "R1: Doctoral "
            "Universities – "
            "Very High "
            "Research "
            "Spending and "
            "Doctorate "
            "Production",
            "accreditor": "SACSCOC",
            "qs_world_university_rankings": {
                "rank": 123,
                "year": 2026,
                "source_url": "https://www.topuniversities.com/universities/georgia-institute-technology",
            },
            "times_higher_education": {
                "rank": 41,
                "year": 2026,
                "source_url": "https://www.timeshighereducation.com/world-university-rankings/georgia-institute-technology",
            },
            "us_news_national": {
                "rank": 32,
                "year": 2026,
                "source_url": "https://news.gatech.edu/news/2025/09/23/georgia-tech-secures-multiple-no-1-rankings",
            },
        },
        "school_outcomes_add": {
            "research": {
                "areas": [
                    "Robotics and intelligent machines",
                    "Advanced manufacturing",
                    "Energy and sustainability",
                    "Bioengineering and bioscience",
                    "Materials and nanotechnology",
                    "Data engineering and science",
                ],
                "labs": [
                    "Georgia Tech Research Institute (GTRI)",
                    "Institute for Robotics and Intelligent Machines (IRIM)",
                    "Parker H. Petit Institute for Bioengineering and Bioscience (IBB)",
                    "Institute for Matter and Systems (IMS)",
                    "Strategic Energy Institute (SEI)",
                    "Georgia Tech Manufacturing Institute (GTMI)",
                    "Renewable Bioproducts Institute (RBI)",
                    "Institute for People and Technology (IPaT)",
                ],
                "lab_links": {
                    "Georgia Tech Research Institute (GTRI)": "https://gtri.gatech.edu/",
                    "Institute for Robotics and Intelligent Machines (IRIM)": "https://research.gatech.edu/robotics",
                    "Parker H. Petit Institute for Bioengineering and Bioscience (IBB)": "https://bioresearch.gatech.edu/",
                    "Institute for Matter and Systems (IMS)": "https://matter-systems.gatech.edu/",
                    "Strategic Energy Institute (SEI)": "https://energy.gatech.edu/",
                    "Georgia Tech Manufacturing Institute (GTMI)": "https://manufacturing.gatech.edu/",
                    "Renewable Bioproducts Institute (RBI)": "https://renewablebioproducts.gatech.edu/",
                    "Institute for People and Technology (IPaT)": "https://research.gatech.edu/ipat",
                },
            },
            "campus_life": {
                "student_orgs": 500,
                "varsity_sports": 17,
                "athletics_division": "NCAA Division I (Atlantic Coast Conference)",
                "resources": [
                    {"name": "Division of Student Life", "url": "https://studentlife.gatech.edu/"},
                    {
                        "name": "Center for Student Engagement",
                        "url": "https://studentengagement.gatech.edu/",
                    },
                    {
                        "name": "Engage (student organizations hub)",
                        "url": "https://gatech.campuslabs.com/engage/organizations",
                    },
                    {
                        "name": "Georgia Tech Yellow Jackets Athletics",
                        "url": "https://ramblinwreck.com/",
                    },
                ],
            },
            "scale": {
                "student_faculty_ratio": "21:1",
                "endowment_usd": 2751221000,
                "campus_acres": 426,
            },
            "location": {"lat": 33.7756, "lng": -84.3963},
        },
        "content_sources": {
            "news_rss": "https://news.gatech.edu/rss.xml",
            "events_feed": {
                "url": "https://calendar.gatech.edu/event-calendar-day.xml",
                "type": "rss",
            },
            "social": {
                "instagram": "https://www.instagram.com/georgiatech",
                "linkedin": "https://www.linkedin.com/school/georgia-institute-of-technology",
                "x": "https://x.com/georgiatech",
                "youtube": "https://www.youtube.com/georgiatech",
                "facebook": "https://www.facebook.com/georgiatech",
            },
        },
        "campus_setting": "urban",
        "founded_year": 1885,
        "description_text": "Georgia Institute of Technology is a "
        "public research university in Atlanta, GA, "
        "founded in 1885 and classified as an R1 "
        "(very high research activity) institution. "
        "It is one of the nation's leading "
        "technological universities, with all of "
        "its undergraduate and graduate engineering "
        "disciplines ranked among the best in the "
        "country and more than $1.3 billion in "
        "annual research awards. Its urban Midtown "
        "campus spans roughly 426 acres and enrolls "
        "more than 53,000 students drawn from all "
        "50 states and over 140 countries.",
    },
    "Johns Hopkins University": {
        "ranking_data": {
            "ownership_type": "private",
            "carnegie_classification": "R1: Doctoral Universities – Very "
            "High Research Activity (2025 "
            'Carnegie: "Research 1: Very High '
            "Spending and Doctorate "
            'Production")',
            "accreditor": "Middle States Commission on Higher Education (MSCHE)",
            "qs_world_university_rankings": {
                "rank": 24,
                "year": 2026,
                "source_url": "https://www.topuniversities.com/universities/johns-hopkins-university",
            },
            "times_higher_education": {
                "rank": 16,
                "year": 2026,
                "source_url": "https://www.timeshighereducation.com/world-university-rankings/johns-hopkins-university",
            },
            "us_news_national": {
                "rank": 7,
                "year": 2026,
                "source_url": "https://hub.jhu.edu/2025/09/23/us-news-best-colleges-rankings-2025/",
            },
        },
        "school_outcomes_add": {
            "research": {
                "areas": [
                    "Public health and global health",
                    "Biomedical engineering and medicine",
                    "Space science and astrophysics",
                    "Neuroscience",
                    "Artificial intelligence and data science",
                    "National security science and engineering",
                ],
                "labs": [
                    "Johns Hopkins University Applied Physics Laboratory (APL)",
                    "Kavli Neuroscience Discovery Institute",
                    "Space Telescope Science Institute (STScI)",
                    "Johns Hopkins Bloomberg School of Public Health",
                    "Johns Hopkins Data Science and AI Institute",
                    "Malone Center for Engineering in Healthcare",
                ],
                "lab_links": {
                    "Johns Hopkins University Applied Physics Laboratory (APL)": "https://www.jhuapl.edu/",
                    "Kavli Neuroscience Discovery Institute": "https://www.kavlijhu.org/",
                    "Space Telescope Science Institute (STScI)": "https://www.stsci.edu/",
                    "Johns Hopkins Bloomberg School of Public Health": "https://publichealth.jhu.edu/",
                    "Johns Hopkins Data Science and AI Institute": "https://ai.jhu.edu/",
                    "Malone Center for Engineering in Healthcare": "https://malonecenter.jhu.edu/",
                },
            },
            "campus_life": {
                "student_orgs": 430,
                "varsity_sports": 24,
                "athletics_division": "NCAA Division "
                "III "
                "(Centennial "
                "Conference); "
                "men's and "
                "women's "
                "lacrosse "
                "compete in "
                "NCAA Division "
                "I (men's "
                "lacrosse in "
                "the Big Ten "
                "Conference)",
                "resources": [
                    {"name": "Campus Life", "url": "https://www.jhu.edu/life/"},
                    {
                        "name": "Athletics (Johns Hopkins Blue Jays)",
                        "url": "https://www.jhu.edu/life/athletics/",
                    },
                    {
                        "name": "Registered Student Organizations (Homewood)",
                        "url": "https://studentaffairs.jhu.edu/leed/student-organizations/",
                    },
                    {
                        "name": "Clubs & Activities",
                        "url": "https://apply.jhu.edu/life-at-hopkins/clubs-activities/",
                    },
                    {
                        "name": "Homewood Campus",
                        "url": "https://www.jhu.edu/life/campuses/homewood/",
                    },
                ],
            },
            "scale": {
                "student_faculty_ratio": "6:1",
                "endowment_usd": 13060000000,
                "campus_acres": 140,
            },
            "location": {"lat": 39.3286, "lng": -76.6207},
        },
        "content_sources": {
            "news_rss": "https://hub.jhu.edu/feed/",
            "events_feed": {"url": "https://events.jhu.edu/rss.xml", "type": "rss"},
            "social": {
                "instagram": "https://www.instagram.com/johnshopkinsu/",
                "linkedin": "https://www.linkedin.com/school/johns-hopkins-university/",
                "x": "https://x.com/JohnsHopkins",
                "youtube": "https://www.youtube.com/@JohnsHopkins",
                "facebook": "https://www.facebook.com/johnshopkinsuniversity/",
            },
        },
        "campus_setting": "urban",
        "founded_year": 1876,
        "description_text": "Johns Hopkins University is a private research university in "
        "Baltimore, Maryland, founded in 1876 on the European "
        "research-institution model and widely regarded as the first "
        "research university in the United States. It has led all U.S. "
        "universities in annual research and development spending for "
        "more than four decades and is home to the Bloomberg School of "
        "Public Health, founded in 1916 and the oldest and largest "
        "independent school of public health in the world. Its main "
        "undergraduate campus, Homewood, sits on roughly 140 acres in "
        "north Baltimore.",
    },
    "New York University": {
        "ranking_data": {
            "ownership_type": "private",
            "carnegie_classification": "R1: Doctoral Universities – Very High "
            "Research Activity (Carnegie 2025: "
            '"Research 1: Very High Research '
            'Spending and Doctorate Production")',
            "accreditor": "Middle States Commission on Higher Education (MSCHE)",
            "qs_world_university_rankings": {
                "rank": 55,
                "year": 2026,
                "source_url": "https://www.topuniversities.com/universities/new-york-university-nyu",
            },
            "times_higher_education": {
                "rank": 31,
                "year": 2026,
                "source_url": "https://www.timeshighereducation.com/world-university-rankings/new-york-university",
            },
            "us_news_national": {
                "rank": 32,
                "year": 2026,
                "source_url": "https://www.usnews.com/best-colleges/nyu-2785",
            },
        },
        "school_outcomes_add": {
            "research": {
                "areas": [
                    "Mathematics and computer science",
                    "Data science and artificial intelligence",
                    "Neural science and brain sciences",
                    "Cosmology and particle physics",
                    "Urban science and policy",
                    "Law, justice, and democracy",
                ],
                "labs": [
                    "Courant Institute of Mathematical Sciences",
                    "Center for Data Science",
                    "Center for Neural Science",
                    "Marron Institute of Urban Management",
                    "Brennan Center for Justice",
                ],
                "lab_links": {
                    "Courant Institute of Mathematical Sciences": "https://cims.nyu.edu/",
                    "Center for Data Science": "https://cds.nyu.edu/",
                    "Center for Neural Science": "https://as.nyu.edu/departments/cns.html",
                    "Marron Institute of Urban Management": "https://marroninstitute.nyu.edu/",
                    "Brennan Center for Justice": "https://www.brennancenter.org/",
                },
            },
            "campus_life": {
                "student_orgs": 300,
                "varsity_sports": 23,
                "athletics_division": "NCAA Division III (University Athletic Association)",
                "resources": [
                    {"name": "NYU Students Hub", "url": "https://www.nyu.edu/students.html"},
                    {
                        "name": "Clubs and Organizations",
                        "url": "https://www.nyu.edu/students/getting-involved/clubs-and-organizations.html",
                    },
                    {"name": "NYU Athletics (Violets)", "url": "https://gonyuathletics.com/"},
                    {"name": "Meet NYU — Student Life", "url": "https://meet.nyu.edu/life/"},
                ],
            },
            "scale": {
                "faculty_count": 4633,
                "student_faculty_ratio": "8:1",
                "endowment_usd": 6650000000,
            },
            "location": {"lat": 40.7295, "lng": -73.9965},
        },
        "content_sources": {
            "news_rss": "https://events.nyu.edu/live/rss/events",
            "events_feed": {"url": "https://events.nyu.edu/live/ical/events", "type": "ical"},
            "social": {
                "instagram": "https://www.instagram.com/nyuniversity/",
                "linkedin": "https://www.linkedin.com/school/new-york-university/",
                "x": "https://twitter.com/nyuniversity",
                "youtube": "https://www.youtube.com/user/nyu",
                "facebook": "https://www.facebook.com/NYU",
            },
        },
        "campus_setting": "urban",
        "founded_year": 1831,
        "description_text": "New York University is a private research university in New York, "
        "NY, founded in 1831 and built around Washington Square Park in "
        "Greenwich Village rather than a traditional gated campus. "
        'Classified as an R1 "very high research activity" institution and '
        "accredited by the Middle States Commission on Higher Education, "
        "NYU spans 18 schools and colleges and operates degree-granting "
        "campuses in New York, Abu Dhabi, and Shanghai plus academic "
        "centers in more than 25 countries. Its Courant Institute of "
        "Mathematical Sciences and Center for Data Science anchor "
        "longstanding strengths in mathematics, computing, and the "
        "sciences.",
    },
    "Purdue University-Main Campus": {
        "ranking_data": {
            "ownership_type": "public",
            "carnegie_classification": "R1: Doctoral Universities – Very High Research Activity",
            "accreditor": "Higher Learning Commission (HLC)",
            "qs_world_university_rankings": {
                "rank": 88,
                "year": 2026,
                "source_url": "https://www.topuniversities.com/universities/purdue-university",
            },
            "times_higher_education": {
                "rank": 85,
                "year": 2026,
                "source_url": "https://www.timeshighereducation.com/world-university-rankings/purdue-university-west-lafayette",
            },
            "us_news_national": {
                "rank": 46,
                "year": 2026,
                "source_url": "https://www.usnews.com/best-colleges/purdue-university-west-lafayette-1825",
            },
        },
        "school_outcomes_add": {
            "research": {
                "areas": [
                    "Engineering and nanotechnology",
                    "Agriculture and life sciences",
                    "Aerospace and aviation",
                    "Computing and semiconductors",
                    "Pharmacy and health sciences",
                    "Bioscience and biomedical research",
                ],
                "labs": [
                    "Birck Nanotechnology Center",
                    "Bindley Bioscience Center",
                    "Ray W. Herrick Laboratories",
                    "Discovery Park District",
                    "Office of Research Institutes and Centers",
                ],
                "lab_links": {
                    "Birck Nanotechnology Center": "https://www.purdue.edu/research/oevprp/institutes-and-centers/facilities/birck.php",
                    "Bindley Bioscience Center": "https://www.purdue.edu/research/oevprp/institutes-and-centers/facilities/bindley.php",
                    "Ray W. Herrick Laboratories": "https://engineering.purdue.edu/Herrick",
                    "Discovery Park District": "https://www.purdue.edu/discoverypark/",
                    "Office of Research Institutes and Centers": "https://www.purdue.edu/research/oevprp/institutes-and-centers/",
                },
            },
            "campus_life": {
                "student_orgs": 1000,
                "varsity_sports": 18,
                "athletics_division": "NCAA Division I FBS (Big Ten Conference)",
                "resources": [
                    {
                        "name": "Office of the Vice Provost for Student Life",
                        "url": "https://www.purdue.edu/vpsl/",
                    },
                    {
                        "name": "BoilerLink Student Organizations",
                        "url": "https://boilerlink.purdue.edu/",
                    },
                    {"name": "Recreation & Wellness", "url": "https://www.purdue.edu/recwell/"},
                    {
                        "name": "University Residences (Housing)",
                        "url": "https://www.purdue.edu/housing/",
                    },
                    {"name": "Purdue Athletics", "url": "https://purduesports.com/"},
                ],
            },
            "scale": {
                "faculty_count": 3193,
                "student_faculty_ratio": "15:1",
                "endowment_usd": 4440000000,
                "campus_acres": 2660,
            },
            "location": {"lat": 40.425, "lng": -86.9231},
        },
        "content_sources": {
            "events_feed": {"url": "https://events.purdue.edu/calendar.ics", "type": "ical"},
            "social": {
                "instagram": "https://www.instagram.com/lifeatpurdue/",
                "linkedin": "https://www.linkedin.com/edu/purdue-university-18357",
                "x": "https://twitter.com/LifeAtPurdue",
                "youtube": "https://www.youtube.com/purdueuniversity",
                "facebook": "https://www.facebook.com/PurdueUniversity/",
            },
        },
        "campus_setting": "suburban",
        "founded_year": 1869,
        "description_text": "Purdue University is a public land-grant research "
        "university in West Lafayette, Indiana, founded in 1869 "
        "after businessman John Purdue's gift toward establishing "
        "a college of science, technology, and agriculture. "
        "Classified R1 for very high research activity and "
        "continuously accredited by the Higher Learning "
        "Commission since 1913, it is best known for its "
        "engineering, agriculture, and aviation programs and for "
        "a record of producing astronauts that has earned it the "
        'nickname "Cradle of Astronauts." Its main campus spans '
        "roughly 2,660 acres along the Wabash River and anchors "
        "the Discovery Park research district.",
    },
    "Rice University": {
        "ranking_data": {
            "ownership_type": "private",
            "carnegie_classification": "R1: Doctoral Universities – Very High "
            'Research Activity (Carnegie 2025: "Research '
            "1: Very High Research Spending and "
            'Doctorate Production")',
            "accreditor": "SACSCOC (Southern Association of Colleges and Schools "
            "Commission on Colleges)",
            "qs_world_university_rankings": {
                "rank": 119,
                "year": 2026,
                "source_url": "https://news.rice.edu/news/2025/rice-moves-more-20-spots-qs-world-university-rankings",
            },
            "times_higher_education": {
                "rank": 103,
                "year": 2026,
                "source_url": "https://news.rice.edu/news/2025/rice-climbs-9-spots-times-higher-education-global-rankings-places-among-worlds-top",
            },
            "us_news_national": {
                "rank": 17,
                "year": 2026,
                "source_url": "https://news.rice.edu/news/2025/rice-rises-us-news-rankings-recognized-value-teaching-and-innovation",
            },
        },
        "school_outcomes_add": {
            "research": {
                "areas": [
                    "Nanoscale science and nanotechnology",
                    "Quantum materials and quantum information science",
                    "Computing, data science and information technology",
                    "Public policy",
                    "Bioengineering and global health",
                    "Urban research and sustainability",
                ],
                "labs": [
                    "Smalley-Curl Institute",
                    "Ken Kennedy Institute",
                    "Baker Institute for Public Policy",
                    "Kinder Institute for Urban Research",
                    "Rice 360 Institute for Global Health",
                    "Rice Space Institute",
                    "Rice Advanced Materials Institute",
                    "Rice Sustainability Institute",
                ],
                "lab_links": {
                    "Smalley-Curl Institute": "https://sci.rice.edu/",
                    "Ken Kennedy Institute": "https://kenkennedy.rice.edu/",
                    "Baker Institute for Public Policy": "https://www.bakerinstitute.org/",
                    "Kinder Institute for Urban Research": "https://kinder.rice.edu/",
                    "Rice 360 Institute for Global Health": "https://www.rice360.rice.edu/",
                    "Rice Space Institute": "https://rsi.rice.edu/",
                    "Rice Advanced Materials Institute": "https://rami.rice.edu/",
                    "Rice Sustainability Institute": "https://si.rice.edu/",
                },
            },
            "campus_life": {
                "student_orgs": 300,
                "varsity_sports": 14,
                "athletics_division": "NCAA Division I (American Conference)",
                "resources": [
                    {"name": "Rice Student Center", "url": "https://studentcenter.rice.edu/"},
                    {"name": "Rice Owls Athletics", "url": "https://riceowls.com/"},
                    {"name": "Housing & Residential Colleges", "url": "https://housing.rice.edu/"},
                    {"name": "Campus Life", "url": "https://www.rice.edu/campus-life"},
                ],
            },
            "scale": {
                "faculty_count": 896,
                "student_faculty_ratio": "6:1",
                "endowment_usd": 7900000000,
                "campus_acres": 300,
            },
            "location": {"lat": 29.7174, "lng": -95.4018},
        },
        "content_sources": {
            "news_rss": "https://news2.rice.edu/feed/",
            "events_feed": {"url": "https://events.rice.edu/live/ical/events", "type": "ical"},
            "social": {
                "instagram": "https://www.instagram.com/riceuniversity/",
                "linkedin": "https://www.linkedin.com/school/rice-university/",
                "x": "https://twitter.com/riceuniversity",
                "youtube": "https://www.youtube.com/riceuniversity",
                "facebook": "https://www.facebook.com/RiceUniversity",
            },
        },
        "campus_setting": "urban",
        "founded_year": 1912,
        "description_text": "Rice University is a private research university in Houston, TX, "
        "chartered in 1891 by cotton merchant William Marsh Rice and opened to "
        "students in 1912. Set on a 300-acre tree-lined campus near the Texas "
        "Medical Center and Houston's Museum District, it enrolls roughly 4,500 "
        "undergraduates under a residential-college system and a "
        'student-to-faculty ratio of about 6-to-1. Classified as an R1 "very '
        'high research activity" institution, Rice is known for its '
        "nanotechnology and quantum-science roots — the Nobel-winning discovery "
        'of the buckminsterfullerene ("buckyball") was made here — alongside '
        "the Baker Institute for Public Policy and a wide engineering, "
        "sciences, and music portfolio.",
    },
    "The University of Texas at Austin": {
        "ranking_data": {
            "ownership_type": "public",
            "carnegie_classification": "Research 1: Very High "
            "Research Spending and "
            "Doctorate Production (R1)",
            "accreditor": "SACSCOC",
            "qs_world_university_rankings": {
                "rank": 68,
                "year": 2026,
                "source_url": "https://global.utexas.edu/about/rankings",
            },
            "times_higher_education": {
                "rank": 50,
                "year": 2026,
                "source_url": "https://www.timeshighereducation.com/world-university-rankings/university-texas-austin",
            },
            "us_news_national": {
                "rank": 30,
                "year": 2026,
                "source_url": "https://news.utexas.edu/2025/09/23/ut-ranks-as-no-1-public-university-in-texas-no-7-nationally-in-u-s-news-world-report-rankings/",
            },
        },
        "school_outcomes_add": {
            "research": {
                "areas": [
                    "Computational engineering and scientific computing",
                    "Advanced computing and supercomputing",
                    "Astronomy and astrophysics",
                    "Geosciences and energy geology",
                    "Geophysics and earth/planetary science",
                    "Marine science",
                ],
                "labs": [
                    "Oden Institute for Computational Engineering and Sciences",
                    "Texas Advanced Computing Center (TACC)",
                    "McDonald Observatory",
                    "Bureau of Economic Geology",
                    "University of Texas Institute for Geophysics",
                    "Applied Research Laboratories",
                    "Marine Science Institute",
                    "Lady Bird Johnson Wildflower Center",
                ],
                "lab_links": {
                    "Oden Institute for Computational Engineering and Sciences": "https://oden.utexas.edu/",
                    "Texas Advanced Computing Center (TACC)": "https://www.tacc.utexas.edu/",
                    "McDonald Observatory": "https://mcdonaldobservatory.org/",
                    "Bureau of Economic Geology": "https://www.beg.utexas.edu/",
                    "University of Texas Institute for Geophysics": "https://ig.utexas.edu/",
                    "Applied Research Laboratories": "https://www.arlut.utexas.edu/",
                    "Marine Science Institute": "https://utmsi.utexas.edu/",
                    "Lady Bird Johnson Wildflower Center": "https://www.wildflower.org/",
                },
            },
            "campus_life": {
                "student_orgs": 1300,
                "varsity_sports": 21,
                "athletics_division": "NCAA Division I (Southeastern Conference)",
                "resources": [
                    {
                        "name": "Student Involvement",
                        "url": "https://www.utexas.edu/campus-life/student-involvement",
                    },
                    {
                        "name": "Office of the Dean of Students",
                        "url": "https://deanofstudents.utexas.edu/",
                    },
                    {
                        "name": "UT RecSports (Recreational Sports)",
                        "url": "https://www.utrecsports.org/",
                    },
                    {"name": "Texas Today Events Calendar", "url": "https://calendar.utexas.edu/"},
                ],
            },
            "scale": {"faculty_count": 4693, "student_faculty_ratio": "18:1", "campus_acres": 431},
            "location": {"lat": 30.285, "lng": -97.735},
        },
        "content_sources": {
            "news_rss": "https://news.utexas.edu/feed/",
            "events_feed": {"url": "https://calendar.utexas.edu/calendar/1.ics", "type": "ical"},
            "social": {
                "instagram": "https://www.instagram.com/utaustintx/",
                "facebook": "https://www.facebook.com/UTAustinTX",
                "x": "https://twitter.com/UTAustin",
                "youtube": "https://www.youtube.com/@UTAustin",
                "linkedin": "https://www.linkedin.com/school/theuniversityoftexasataustin-",
            },
        },
        "campus_setting": "urban",
        "founded_year": 1883,
        "description_text": "The University of Texas at Austin is a public "
        "research university in Austin, Texas, established in "
        "1883 as the flagship institution of the University "
        "of Texas System. With more than 55,000 students and "
        "over 4,600 faculty, it is one of the largest "
        "universities in the United States and carries the "
        "Carnegie R1 (very high research activity) "
        "designation. UT Austin is home to nationally "
        "significant research units including the Texas "
        "Advanced Computing Center, the Oden Institute for "
        "Computational Engineering and Sciences, and the "
        "McDonald Observatory in West Texas.",
    },
    "University of California-Los Angeles": {
        "ranking_data": {
            "ownership_type": "public",
            "carnegie_classification": "R1: Doctoral Universities – Very High Research Activity",
            "accreditor": "WSCUC (WASC Senior College and University Commission)",
            "qs_world_university_rankings": {
                "rank": 46,
                "year": 2026,
                "source_url": "https://www.topuniversities.com/universities/university-california-los-angeles-ucla",
            },
            "times_higher_education": {
                "rank": 18,
                "year": 2026,
                "source_url": "https://www.timeshighereducation.com/world-university-rankings/university-california-los-angeles",
            },
            "us_news_national": {
                "rank": 17,
                "year": 2026,
                "source_url": "https://www.usnews.com/best-colleges/ucla-1315",
            },
        },
        "school_outcomes_add": {
            "research": {
                "areas": [
                    "Nanoscience and nanotechnology",
                    "Cancer research and oncology",
                    "Neuroscience and brain research",
                    "Regenerative medicine and stem cell research",
                    "Environment and sustainability",
                    "Mental health and human behavior",
                ],
                "labs": [
                    "California NanoSystems Institute (CNSI)",
                    "UCLA Health Jonsson Comprehensive Cancer Center",
                    "UCLA Brain Research Institute",
                    "Eli and Edythe Broad Center of Regenerative Medicine and Stem Cell Research",
                    "Jane and Terry Semel Institute for Neuroscience and Human Behavior",
                    "UCLA Institute of the Environment and Sustainability",
                ],
                "lab_links": {
                    "California NanoSystems Institute (CNSI)": "https://cnsi.ucla.edu/",
                    "UCLA Health Jonsson Comprehensive Cancer Center": "https://www.uclahealth.org/cancer",
                    "UCLA Brain Research Institute": "https://www.bri.ucla.edu/",
                    "Eli and Edythe Broad Center of Regenerative Medicine and Stem Cell Research": "https://stemcell.ucla.edu/",
                    "Jane and Terry Semel Institute for Neuroscience and Human Behavior": "https://www.semel.ucla.edu/",
                    "UCLA Institute of the Environment and Sustainability": "https://www.ioes.ucla.edu/",
                },
            },
            "campus_life": {
                "student_orgs": 1300,
                "varsity_sports": 25,
                "athletics_division": "NCAA Division I (Big Ten Conference)",
                "resources": [
                    {"name": "UCLA Student Affairs", "url": "https://www.studentaffairs.ucla.edu/"},
                    {"name": "UCLA Bruins Athletics", "url": "https://uclabruins.com/"},
                    {"name": "UCLA Recreation", "url": "https://recreation.ucla.edu/"},
                    {
                        "name": "UCLA Undergraduate Admission — Clubs & Organizations",
                        "url": "https://admission.ucla.edu/explore/clubs-organizations",
                    },
                ],
            },
            "scale": {"faculty_count": 5700, "student_faculty_ratio": "18:1", "campus_acres": 419},
            "location": {"lat": 34.0689, "lng": -118.4452},
        },
        "content_sources": {
            "news_rss": "https://newsroom.ucla.edu/rss.xml",
            "social": {
                "instagram": "https://www.instagram.com/ucla/",
                "linkedin": "https://www.linkedin.com/school/ucla/",
                "x": "https://twitter.com/ucla",
                "youtube": "https://www.youtube.com/user/UCLA",
                "facebook": "https://www.facebook.com/UCLA",
            },
        },
        "campus_setting": "urban",
        "founded_year": 1919,
        "description_text": "University of California-Los Angeles is a public "
        "research university in Los Angeles, CA, founded "
        "in 1919 as the Southern Branch of the University "
        "of California. The flagship of the UC system's "
        "Westwood campus, it is classified R1 for very "
        "high research activity, draws roughly $1.6 "
        "billion in annual research funding, and has won "
        "127 NCAA team championships — the second most of "
        "any U.S. university. UCLA joined the Big Ten "
        "Conference in 2024 and was the U.S. News No. 1 "
        "public university for eight of the prior nine "
        "years.",
    },
    "University of California-San Diego": {
        "ranking_data": {
            "ownership_type": "public",
            "carnegie_classification": "R1: Doctoral Universities – Very High Research Activity",
            "accreditor": "WSCUC (WASC Senior College and University Commission)",
            "qs_world_university_rankings": {
                "rank": 66,
                "year": 2026,
                "source_url": "https://www.topuniversities.com/universities/university-california-san-diego-ucsd",
            },
            "times_higher_education": {
                "rank": 47,
                "year": 2026,
                "source_url": "https://www.timeshighereducation.com/world-university-rankings/university-california-san-diego",
            },
            "us_news_national": {
                "rank": 29,
                "year": 2026,
                "source_url": "https://www.usnews.com/best-colleges/university-of-california-san-diego-1317",
            },
        },
        "school_outcomes_add": {
            "research": {
                "areas": [
                    "Oceanography and Earth Science",
                    "Biological Sciences and Neuroscience",
                    "Engineering and Computing",
                    "Data Science and High-Performance Computing",
                    "Health and Medicine",
                    "Physical Sciences",
                ],
                "labs": [
                    "Scripps Institution of Oceanography",
                    "San Diego Supercomputer Center",
                    "Qualcomm Institute",
                    "Halıcıoğlu Data Science Institute",
                    "Jacobs School of Engineering",
                ],
                "lab_links": {
                    "Scripps Institution of Oceanography": "https://scripps.ucsd.edu/",
                    "San Diego Supercomputer Center": "https://www.sdsc.edu/",
                    "Qualcomm Institute": "https://qi.ucsd.edu/",
                    "Halıcıoğlu Data Science Institute": "https://datascience.ucsd.edu/",
                    "Jacobs School of Engineering": "https://jacobsschool.ucsd.edu/",
                },
            },
            "campus_life": {
                "student_orgs": 650,
                "varsity_sports": 22,
                "athletics_division": "NCAA Division I (Big West Conference)",
                "resources": [
                    {"name": "Current Students Hub", "url": "https://students.ucsd.edu/"},
                    {
                        "name": "Center for Student Involvement",
                        "url": "https://getinvolved.ucsd.edu/",
                    },
                    {"name": "UC San Diego Recreation", "url": "https://recreation.ucsd.edu/"},
                    {"name": "UC San Diego Athletics (Tritons)", "url": "https://ucsdtritons.com/"},
                    {"name": "UC San Diego Events Calendar", "url": "https://calendar.ucsd.edu/"},
                ],
            },
            "scale": {
                "student_faculty_ratio": "26:1",
                "endowment_usd": 1590000000,
                "campus_acres": 1200,
            },
            "location": {"lat": 32.8801, "lng": -117.234},
        },
        "content_sources": {
            "events_feed": {"url": "https://calendar.ucsd.edu/calendar.ics", "type": "ical"},
            "social": {
                "instagram": "https://instagram.com/ucsandiego",
                "facebook": "https://facebook.com/ucsandiego",
                "x": "https://x.com/UCSanDiego",
                "youtube": "https://youtube.com/ucsandiego",
                "linkedin": "https://www.linkedin.com/company/university-of-california-at-san-diego/",
            },
        },
        "campus_setting": "suburban",
        "founded_year": 1960,
        "description_text": "University of California-San Diego is a public "
        "research university in La Jolla, San Diego, "
        "California. Founded in 1960 around the established "
        "Scripps Institution of Oceanography, it is "
        "organized into a distinctive system of "
        "undergraduate residential colleges and ranks among "
        "the nation's top public research universities, with "
        "annual research expenditures exceeding $1.7 "
        "billion. Its faculty and affiliates include "
        "numerous Nobel laureates, and the university "
        "operates the San Diego Supercomputer Center and the "
        "Qualcomm Institute.",
    },
    "University of Illinois Urbana-Champaign": {
        "ranking_data": {
            "ownership_type": "public",
            "carnegie_classification": "Research 1: Very "
            "High Research "
            "Spending and "
            "Doctorate "
            "Production (R1)",
            "accreditor": "Higher Learning Commission (HLC)",
            "qs_world_university_rankings": {
                "rank": 70,
                "year": 2026,
                "source_url": "https://www.topuniversities.com/universities/university-illinois-urbana-champaign",
            },
            "times_higher_education": {
                "rank": 41,
                "year": 2026,
                "source_url": "https://www.timeshighereducation.com/world-university-rankings/university-illinois-urbana-champaign",
            },
            "us_news_national": {
                "rank": 36,
                "year": 2026,
                "source_url": "https://www.usnews.com/best-colleges/university-of-illinois-urbanachampaign-1775",
            },
        },
        "school_outcomes_add": {
            "research": {
                "areas": [
                    "Engineering and computing",
                    "Supercomputing and data science",
                    "Genomic and life sciences",
                    "Materials science and nanotechnology",
                    "Sustainability, energy and environment",
                    "Neuroscience and bioimaging",
                ],
                "labs": [
                    "Beckman Institute for Advanced Science and Technology",
                    "National Center for Supercomputing Applications (NCSA)",
                    "Carl R. Woese Institute for Genomic Biology",
                    "Prairie Research Institute",
                    "Institute for Sustainability, Energy, and Environment (iSEE)",
                    "Cancer Center at Illinois",
                ],
                "lab_links": {
                    "Beckman Institute for Advanced Science and Technology": "https://beckman.illinois.edu/",
                    "National Center for Supercomputing Applications (NCSA)": "https://www.ncsa.illinois.edu/",
                    "Carl R. Woese Institute for Genomic Biology": "https://www.igb.illinois.edu/",
                    "Prairie Research Institute": "https://prairie.illinois.edu/",
                    "Institute for Sustainability, Energy, and Environment (iSEE)": "https://isee.illinois.edu/",
                    "Cancer Center at Illinois": "https://cancer.illinois.edu/",
                },
            },
            "campus_life": {
                "student_orgs": 1000,
                "varsity_sports": 21,
                "athletics_division": "NCAA Division I (Big Ten Conference)",
                "resources": [
                    {"name": "Illini Union", "url": "https://union.illinois.edu/"},
                    {"name": "Office of the Dean of Students", "url": "https://odos.illinois.edu/"},
                    {
                        "name": "Student Engagement (Registered Student Organizations)",
                        "url": "https://studentengagement.illinois.edu/",
                    },
                    {"name": "Campus Recreation", "url": "https://campusrec.illinois.edu/"},
                    {"name": "Fighting Illini Athletics", "url": "https://fightingillini.com/"},
                ],
            },
            "scale": {"faculty_count": 2548, "student_faculty_ratio": "18:1", "campus_acres": 6370},
            "location": {"lat": 40.102, "lng": -88.2272},
        },
        "content_sources": {
            "news_rss": "https://news.illinois.edu/feed/",
            "events_feed": {
                "url": "https://calendars.illinois.edu/icalGmail/7.ics?hourOffset=0&timeZone=America%2FChicago",
                "type": "ical",
            },
            "social": {
                "instagram": "https://www.instagram.com/illinois1867/",
                "facebook": "https://www.facebook.com/illinois.edu",
                "x": "https://twitter.com/UofIllinois",
                "youtube": "https://www.youtube.com/user/Illinois1867",
                "linkedin": "https://www.linkedin.com/school/university-of-illinois-urbana-champaign/",
            },
        },
        "campus_setting": "suburban",
        "founded_year": 1867,
        "description_text": "University of Illinois Urbana-Champaign is a "
        "public land-grant research university in "
        "Urbana and Champaign, Illinois, founded in "
        "1867 as the flagship campus of the University "
        "of Illinois System. Classified as an R1 "
        "institution with very high research activity, "
        "it is renowned for engineering and computing — "
        "the campus built the first graphical web "
        "browser (Mosaic / later Netscape) and hosts "
        "the National Center for Supercomputing "
        "Applications. Its 6,370-acre campus enrolls "
        "more than 60,000 students across 11 colleges "
        "and schools.",
    },
    "University of Michigan-Ann Arbor": {
        "ranking_data": {
            "ownership_type": "public",
            "carnegie_classification": "R1: Doctoral Universities "
            "– Very High Research "
            "Activity (2025 Carnegie "
            'label: "Research 1: Very '
            "High Research Spending and "
            'Doctorate Production")',
            "accreditor": "Higher Learning Commission (HLC)",
            "qs_world_university_rankings": {
                "rank": 45,
                "year": 2026,
                "source_url": "https://www.topuniversities.com/world-university-rankings",
            },
            "times_higher_education": {
                "rank": 23,
                "year": 2026,
                "source_url": "https://www.timeshighereducation.com/world-university-rankings/university-michigan",
            },
            "us_news_national": {
                "rank": 20,
                "year": 2026,
                "source_url": "https://www.usnews.com/best-colleges/university-of-michigan-ann-arbor-9092",
            },
        },
        "school_outcomes_add": {
            "research": {
                "areas": [
                    "Social science and survey research",
                    "Life sciences and biomedical research",
                    "Engineering and robotics",
                    "Artificial intelligence and data science",
                    "Sustainability, climate and environment",
                    "Medicine and public health",
                ],
                "labs": [
                    "Institute for Social Research (ISR)",
                    "Life Sciences Institute (LSI)",
                    "Graham Sustainability Institute",
                    "Robotics Department",
                ],
                "lab_links": {
                    "Institute for Social Research (ISR)": "https://isr.umich.edu/",
                    "Life Sciences Institute (LSI)": "https://www.lsi.umich.edu/",
                    "Graham Sustainability Institute": "https://graham.umich.edu/",
                    "Robotics Department": "https://robotics.umich.edu/",
                },
            },
            "campus_life": {
                "student_orgs": 1600,
                "varsity_sports": 27,
                "athletics_division": "NCAA Division I (Big Ten Conference)",
                "resources": [
                    {
                        "name": "Maize Pages (Student Organizations directory)",
                        "url": "https://maizepages.umich.edu/",
                    },
                    {"name": "Michigan Athletics (MGoBlue)", "url": "https://mgoblue.com/"},
                    {
                        "name": "Counseling and Psychological Services (CAPS)",
                        "url": "https://caps.umich.edu/",
                    },
                    {"name": "Student Life", "url": "https://studentlife.umich.edu/"},
                    {
                        "name": "Center for Campus Involvement",
                        "url": "https://campusinvolvement.umich.edu/",
                    },
                ],
            },
            "scale": {
                "faculty_count": 8526,
                "student_faculty_ratio": "15:1",
                "endowment_usd": 21200000000,
                "campus_acres": 3177,
            },
            "location": {"lat": 42.27694, "lng": -83.73806},
        },
        "content_sources": {
            "news_rss": "https://record.umich.edu/feed/",
            "social": {
                "instagram": "https://www.instagram.com/uofmichigan/",
                "linkedin": "https://www.linkedin.com/school/university-of-michigan/",
                "x": "https://x.com/UMich",
                "youtube": "https://www.youtube.com/channel/UC9JPJoeQo9ohpzZUzEsU6Og",
                "facebook": "https://www.facebook.com/UniversityOfMichigan/",
            },
        },
        "campus_setting": "suburban",
        "founded_year": 1817,
        "description_text": "University of Michigan-Ann Arbor is a public research "
        "university in Ann Arbor, Michigan, chartered in 1817 "
        "and one of the oldest and most prominent public "
        "universities in the United States. It enrolls more "
        "than 50,000 students across 19 schools and colleges "
        "and ranks consistently among the top three U.S. "
        "public universities for undergraduate education. Home "
        "to the Institute for Social Research — the world's "
        "largest academic survey and social-science research "
        "organization — and Michigan Stadium, the largest "
        "stadium in the United States, the university sustains "
        "over $1.8 billion in annual research activity.",
    },
    "University of Southern California": {
        "ranking_data": {
            "ownership_type": "private",
            "carnegie_classification": "R1: Doctoral Universities – Very High Research Activity",
            "accreditor": "WSCUC (WASC Senior College and University Commission)",
            "qs_world_university_rankings": {
                "rank": 146,
                "year": 2026,
                "source_url": "https://www.topuniversities.com/universities/university-southern-california-usc",
            },
            "times_higher_education": {
                "rank": 73,
                "year": 2026,
                "source_url": "https://www.timeshighereducation.com/world-university-rankings/university-southern-california",
            },
            "us_news_national": {
                "rank": 28,
                "year": 2026,
                "source_url": "https://www.usnews.com/best-colleges/university-of-southern-california-1328",
            },
        },
        "school_outcomes_add": {
            "research": {
                "areas": [
                    "Artificial intelligence and information sciences",
                    "Neuroimaging and brain mapping",
                    "Convergent bioscience and biomedical engineering",
                    "Computer graphics, virtual humans and mixed reality",
                    "Geospatial / spatial sciences",
                    "Holocaust and genocide testimony preservation",
                ],
                "labs": [
                    "USC Information Sciences Institute (ISI)",
                    "USC Mark and Mary Stevens Neuroimaging and Informatics Institute",
                    "USC Shoah Foundation",
                    "USC Institute for Creative Technologies (ICT)",
                    "USC Michelson Center for Convergent Bioscience",
                    "USC Spatial Sciences Institute",
                ],
                "lab_links": {
                    "USC Information Sciences Institute (ISI)": "https://www.isi.edu/",
                    "USC Mark and Mary Stevens Neuroimaging and Informatics Institute": "https://ini.usc.edu/",
                    "USC Shoah Foundation": "https://sfi.usc.edu/",
                    "USC Institute for Creative Technologies (ICT)": "https://ict.usc.edu/",
                    "USC Michelson Center for Convergent Bioscience": "https://michelson.usc.edu/",
                    "USC Spatial Sciences Institute": "https://dornsife.usc.edu/spatial/",
                },
            },
            "campus_life": {
                "student_orgs": 800,
                "varsity_sports": 23,
                "athletics_division": "NCAA Division I FBS (Big Ten Conference)",
                "resources": [
                    {"name": "USC Student Life", "url": "https://studentlife.usc.edu/"},
                    {
                        "name": "USC Campus Activities — Recognized Student Organizations",
                        "url": "https://campusactivities.usc.edu/programs/recognized-student-organizations/",
                    },
                    {"name": "USC Recreational Sports", "url": "https://recsports.usc.edu/"},
                    {
                        "name": "EngageSC (student organizations directory)",
                        "url": "https://engage.usc.edu/",
                    },
                ],
            },
            "scale": {
                "faculty_count": 4626,
                "student_faculty_ratio": "8:1",
                "endowment_usd": 8800000000,
                "campus_acres": 226,
            },
            "location": {"lat": 34.0206, "lng": -118.2848},
        },
        "content_sources": {
            "news_rss": "https://today.usc.edu/feed/",
            "events_feed": {"url": "https://calendar.usc.edu/calendar.ics", "type": "ical"},
            "social": {
                "instagram": "https://www.instagram.com/uscedu/",
                "linkedin": "https://www.linkedin.com/school/university-of-southern-california/",
                "x": "https://x.com/USC",
                "youtube": "https://www.youtube.com/usc",
                "facebook": "https://www.facebook.com/usc",
            },
        },
        "campus_setting": "urban",
        "founded_year": 1880,
        "description_text": "University of Southern California is a private "
        "research university in Los Angeles, California, "
        "founded in 1880 as the oldest private research "
        "university in the state. Anchored by its 226-acre "
        "University Park campus near downtown Los Angeles, "
        "USC enrolls roughly 46,000 students across 23 "
        "schools and academic divisions and carries a "
        'Carnegie R1 "very high research activity" '
        "designation. Its research enterprise spans the "
        "Information Sciences Institute, the Institute for "
        "Creative Technologies, and the Shoah Foundation, and "
        "in 2024 its Trojan athletic teams joined the Big Ten "
        "Conference.",
    },
    "University of Washington-Seattle Campus": {
        "ranking_data": {
            "ownership_type": "public",
            "carnegie_classification": "R1: Doctoral "
            "Universities – Very "
            "High Research "
            "Spending and "
            "Doctorate "
            "Production",
            "accreditor": "NWCCU",
            "qs_world_university_rankings": {
                "rank": 81,
                "year": 2026,
                "source_url": "https://www.topuniversities.com/world-university-rankings",
            },
            "times_higher_education": {
                "rank": 25,
                "year": 2026,
                "source_url": "https://www.timeshighereducation.com/world-university-rankings/university-washington",
            },
            "us_news_national": {
                "rank": 42,
                "year": 2026,
                "source_url": "https://www.usnews.com/best-colleges/university-of-washington-3798",
            },
        },
        "school_outcomes_add": {
            "research": {
                "areas": [
                    "Computer science and artificial intelligence",
                    "Protein design and biotechnology",
                    "Oceanography and polar science",
                    "Data science",
                    "Health and medicine",
                    "Climate and environmental science",
                ],
                "labs": [
                    "Paul G. Allen School of Computer Science & Engineering",
                    "Applied Physics Laboratory (APL-UW)",
                    "Institute for Protein Design",
                    "eScience Institute",
                ],
                "lab_links": {
                    "Paul G. Allen School of Computer Science & Engineering": "https://www.cs.washington.edu/",
                    "Applied Physics Laboratory (APL-UW)": "https://www.apl.washington.edu/",
                    "Institute for Protein Design": "https://www.ipd.uw.edu/",
                    "eScience Institute": "https://escience.washington.edu/",
                },
            },
            "campus_life": {
                "student_orgs": 1000,
                "varsity_sports": 22,
                "athletics_division": "NCAA Division I FBS (Big Ten Conference)",
                "resources": [
                    {
                        "name": "HUB (Husky Union Building) — Student Life",
                        "url": "https://hub.washington.edu/",
                    },
                    {
                        "name": "HuskyLink — Registered Student Organizations",
                        "url": "https://huskylink.washington.edu/",
                    },
                    {"name": "UW Recreation", "url": "https://recreation.uw.edu/"},
                    {"name": "Student Life", "url": "https://www.washington.edu/studentlife/"},
                    {
                        "name": "UW Social Media Directory",
                        "url": "https://www.washington.edu/social/",
                    },
                ],
            },
            "scale": {
                "student_faculty_ratio": "20:1",
                "endowment_usd": 6000000000,
                "campus_acres": 700,
            },
            "location": {"lat": 47.6553, "lng": -122.3035},
        },
        "content_sources": {
            "news_rss": "https://www.washington.edu/news/feed/",
            "events_feed": {
                "url": "https://www.trumba.com/calendars/sea_campus.ics",
                "type": "ical",
            },
            "social": {
                "instagram": "https://www.instagram.com/uofwa/",
                "facebook": "https://www.facebook.com/UofWA",
                "x": "https://x.com/UW",
                "youtube": "https://www.youtube.com/user/uwhuskies",
                "linkedin": "https://www.linkedin.com/school/university-of-washington",
            },
        },
        "campus_setting": "urban",
        "founded_year": 1861,
        "description_text": "University of Washington-Seattle Campus is a "
        "public research university in Seattle, WA, "
        "founded in 1861 and one of the oldest "
        "universities on the West Coast. Its 700-acre "
        "main campus on Montlake serves the flagship of "
        "a tri-campus system and is a top recipient of "
        "federal research funding among U.S. public "
        "universities. The university is home to the "
        "Paul G. Allen School of Computer Science & "
        "Engineering and the Institute for Protein "
        "Design, whose director David Baker received "
        "the 2024 Nobel Prize in Chemistry.",
    },
    "University of Wisconsin-Madison": {
        "ranking_data": {
            "ownership_type": "public",
            "carnegie_classification": "Research 1: Very High "
            "Spending and Doctorate "
            "Production (R1)",
            "accreditor": "Higher Learning Commission (HLC)",
            "qs_world_university_rankings": {
                "rank": 110,
                "year": 2026,
                "source_url": "https://www.topuniversities.com/universities/university-wisconsin-madison",
            },
            "times_higher_education": {
                "rank": 53,
                "year": 2026,
                "source_url": "https://www.timeshighereducation.com/world-university-rankings/university-wisconsin-madison",
            },
            "us_news_national": {
                "rank": 36,
                "year": 2026,
                "source_url": "https://www.usnews.com/best-colleges/university-of-wisconsin-3895",
            },
        },
        "school_outcomes_add": {
            "research": {
                "areas": [
                    "Biomedical and health sciences",
                    "Atmospheric, space, and earth sciences",
                    "Stem cell and regenerative biology",
                    "Human development and developmental disabilities",
                    "Data science, AI, and computational biology",
                    "Agriculture and life sciences",
                ],
                "labs": [
                    "Wisconsin Institute for Discovery",
                    "Morgridge Institute for Research",
                    "Space Science and Engineering Center",
                    "Waisman Center",
                    "Wisconsin Alumni Research Foundation",
                ],
                "lab_links": {
                    "Wisconsin Institute for Discovery": "https://wid.wisc.edu/",
                    "Morgridge Institute for Research": "https://morgridge.org/",
                    "Space Science and Engineering Center": "https://www.ssec.wisc.edu/",
                    "Waisman Center": "https://www.waisman.wisc.edu/",
                    "Wisconsin Alumni Research Foundation": "https://www.warf.org/",
                },
            },
            "campus_life": {
                "student_orgs": 1062,
                "varsity_sports": 23,
                "athletics_division": "NCAA Division I (Big Ten)",
                "resources": [
                    {"name": "Student Affairs hub", "url": "https://students.wisc.edu/"},
                    {
                        "name": "Recreation & Wellbeing (RecWell)",
                        "url": "https://recwell.wisc.edu/",
                    },
                    {"name": "University Housing", "url": "https://www.housing.wisc.edu/"},
                    {"name": "University Health Services", "url": "https://www.uhs.wisc.edu/"},
                    {
                        "name": "Student Organizations, Leadership & Involvement",
                        "url": "https://soli.wisc.edu/",
                    },
                ],
            },
            "scale": {
                "student_faculty_ratio": "17:1",
                "endowment_usd": 4900000000,
                "campus_acres": 939,
            },
            "location": {"lat": 43.0766, "lng": -89.4125},
        },
        "content_sources": {
            "news_rss": "https://news.wisc.edu/feed/",
            "events_feed": {"url": "https://today.wisc.edu/events.ics", "type": "ical"},
            "social": {
                "instagram": "https://instagram.com/uwmadison",
                "linkedin": "https://www.linkedin.com/school/uwmadison/",
                "x": "https://x.com/UWMadison",
                "youtube": "https://www.youtube.com/user/uwmadison",
                "facebook": "https://facebook.com/uwmadison",
            },
        },
        "campus_setting": "urban",
        "founded_year": 1848,
        "description_text": "University of Wisconsin-Madison is a public research "
        "university in Madison, WI, founded in 1848 as the "
        "state's flagship land-grant institution. "
        "Carnegie-classified R1 with very high research "
        "activity, it ranks fifth nationally in research "
        "expenditures and is home to the Wisconsin Alumni "
        "Research Foundation, whose patenting and licensing of "
        "campus discoveries (including the isolation of vitamin "
        "D and the first human embryonic stem cells) has "
        "returned billions to the university. Its guiding "
        '"Wisconsin Idea" holds that the university\'s work '
        "should extend beyond the classroom to benefit the "
        "entire state.",
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
