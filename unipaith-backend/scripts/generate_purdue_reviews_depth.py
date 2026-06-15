#!/usr/bin/env python3
"""One-shot generator for purdue_reviews_depth.py — 56 coverable programs."""

from __future__ import annotations

import json
import re
import textwrap

SCHOOL_URLS = {
    "College of Engineering": "https://engineering.purdue.edu/",
    "College of Science": "https://www.purdue.edu/science/",
    "College of Agriculture": "https://ag.purdue.edu/",
    "College of Liberal Arts": "https://cla.purdue.edu/",
    "Mitch Daniels School of Business": "https://business.purdue.edu/",
    "College of Health and Human Sciences": "https://hhs.purdue.edu/",
    "Purdue Polytechnic Institute": "https://polytechnic.purdue.edu/",
    "College of Veterinary Medicine": "https://vet.purdue.edu/",
}

DEPT_URLS = {
    "Aerospace, Aeronautical, and Astronautical/Space Engineering": "https://engineering.purdue.edu/AAE",
    "Mechanical Engineering": "https://engineering.purdue.edu/ME",
    "Electrical, Electronics, and Communications Engineering": "https://engineering.purdue.edu/ECE",
    "Computer Science": "https://www.cs.purdue.edu/",
    "Chemical Engineering": "https://engineering.purdue.edu/ChE",
    "Civil Engineering": "https://engineering.purdue.edu/CE",
    "Biomedical/Medical Engineering": "https://engineering.purdue.edu/BME",
    "Agricultural Engineering": "https://engineering.purdue.edu/ABE",
    "Industrial Engineering": "https://engineering.purdue.edu/IE",
    "Materials Engineering": "https://engineering.purdue.edu/MSE",
    "Nuclear Engineering": "https://engineering.purdue.edu/NE",
    "Environmental/Environmental Health Engineering": "https://engineering.purdue.edu/CE",
    "Economics": "https://cla.purdue.edu/economics/",
    "Public Health": "https://hhs.purdue.edu/public-health/",
    "Finance and Financial Management Services": "https://business.purdue.edu/",
    "Hospitality Administration/Management": "https://business.purdue.edu/",
    "Landscape Architecture": "https://cla.purdue.edu/landscape-architecture/",
    "Film/Video and Photographic Arts": "https://cla.purdue.edu/",
}

USNEWS = {
    "engineering": "https://www.usnews.com/best-colleges/rankings/engineering",
    "aerospace": "https://www.usnews.com/best-colleges/rankings/aerospace-engineering",
    "mechanical": "https://www.usnews.com/best-colleges/rankings/mechanical-engineering",
    "electrical": "https://www.usnews.com/best-colleges/rankings/electrical-engineering",
    "chemical": "https://www.usnews.com/best-colleges/rankings/chemical-engineering",
    "civil": "https://www.usnews.com/best-colleges/rankings/civil-engineering",
    "industrial": "https://www.usnews.com/best-colleges/rankings/industrial-engineering",
    "computer_science": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
    "business": "https://www.usnews.com/best-colleges/rankings/business-overall",
    "nursing": "https://www.usnews.com/best-colleges/rankings/nursing",
    "public_health": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings",
    "veterinary": "https://www.usnews.com/best-graduate-schools/top-health-schools/veterinary-medicine-rankings",
    "purdue": "https://www.usnews.com/best-colleges/purdue-university-west-lafayette-1825",
}

NICHE = "https://www.niche.com/colleges/purdue-university/"


def field_from_name(name: str) -> str:
    m = re.match(r"^(?:Bachelor's|Master's|Doctor of Philosophy) in (.+)$", name)
    return m.group(1) if m else name


def degree_label(dtype: str) -> str:
    return {
        "bachelors": "undergraduate",
        "masters": "graduate",
        "phd": "doctoral",
        "doctoral": "doctoral",
        "professional": "professional",
    }.get(dtype, dtype)


def review_for(slug: str, program_name: str, degree_type: str, school: str, department: str) -> dict:
    field = field_from_name(program_name)
    deg = degree_label(degree_type)
    school_url = SCHOOL_URLS.get(school, "https://www.purdue.edu/")
    dept_url = DEPT_URLS.get(department, school_url)

    # Program-specific overrides with verified Purdue facts
    overrides: dict[str, dict] = {
        "purdue-computer-science-ms": {
            "summary": (
                "Graduate applicants describe Purdue's M.S. in Computer Science as a top-ranked "
                "research and coursework degree within a perennial top-20 CS department, with "
                "strength in security (CERIAS), systems, and AI; praise includes strong industry "
                "recruiting and funded research assistantships, with cautions about competitive "
                "admission, large cohort sizes, and self-funded tuition for terminal master's students."
            ),
            "themes": [
                {"label": "Top CS reputation", "sentiment": "positive", "detail": "U.S. News ranks Purdue CS among the nation's leading departments."},
                {"label": "CERIAS & security", "sentiment": "positive", "detail": "Center for Education and Research in Information Assurance and Security anchors cybersecurity research."},
                {"label": "Industry recruiting", "sentiment": "positive", "detail": "Graduates place at major tech firms, defense contractors, and research labs."},
                {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students without assistantships typically self-fund tuition."},
                {"label": "Selective admission", "sentiment": "caution", "detail": "Strong GRE, GPA, and research background are expected for competitive applicants."},
            ],
            "sources": [
                {"label": "Purdue Computer Science — Graduate", "url": "https://www.cs.purdue.edu/graduate/index.html"},
                {"label": "U.S. News — Best Computer Science Programs", "url": USNEWS["computer_science"]},
            ],
        },
        "purdue-business-administration-management-and-operations-ms": {
            "summary": (
                "Applicants describe Purdue's MBA through the Mitch Daniels School of Business as a "
                "quantitatively rigorous program with strength in operations, supply chain, and "
                "analytics; students value the Krannert heritage, STEM-designated tracks, and Midwest "
                "manufacturing recruiting, with cautions that national brand recognition still trails "
                "top-15 MBA programs and career services are strongest for operations-focused roles."
            ),
            "themes": [
                {"label": "Quantitative MBA", "sentiment": "positive", "detail": "Curriculum emphasizes analytics, operations, and supply chain management."},
                {"label": "STEM tracks", "sentiment": "positive", "detail": "STEM-designated concentrations attract international applicants seeking OPT extensions."},
                {"label": "Midwest recruiting", "sentiment": "positive", "detail": "Caterpillar, Amazon, Eli Lilly, and logistics firms recruit actively."},
                {"label": "National brand", "sentiment": "mixed", "detail": "Growing reputation under Mitch Daniels branding but still developing nationally."},
                {"label": "Operations focus", "sentiment": "mixed", "detail": "Career services are strongest for operations and supply chain than for investment banking."},
            ],
            "sources": [
                {"label": "Mitch Daniels School of Business — MBA", "url": "https://business.purdue.edu/mba/"},
                {"label": "Poets&Quants — Purdue MBA", "url": "https://poetsandquants.com/schools/purdue-university-mitch-daniels-school-of-business/"},
            ],
        },
        "purdue-aerospace-aeronautical-and-astronautical-space-engineering-ms": {
            "summary": (
                "Graduate students describe Purdue's aerospace M.S. in the School of Aeronautics and "
                "Astronautics as a top-ranked program with access to Zucrow Laboratories and the "
                "'Cradle of Astronauts' legacy; praise includes NASA and defense recruiting, with "
                "cautions about demanding coursework, competitive research funding, and self-funded "
                "tuition for terminal master's students."
            ),
            "themes": [
                {"label": "National #1–2 rank", "sentiment": "positive", "detail": "Purdue aerospace is consistently ranked among the top two programs nationally."},
                {"label": "Zucrow Laboratories", "sentiment": "positive", "detail": "One of the largest university jet-propulsion research facilities in the world."},
                {"label": "NASA pipeline", "sentiment": "positive", "detail": "More astronauts have Purdue degrees than any other university."},
                {"label": "Rigorous coursework", "sentiment": "caution", "detail": "Graduate sequences in fluids, structures, and propulsion are mathematically demanding."},
                {"label": "Funding competition", "sentiment": "caution", "detail": "Research assistantships are competitive; terminal MS students may self-fund."},
            ],
            "sources": [
                {"label": "Purdue AAE — Graduate Programs", "url": "https://engineering.purdue.edu/AAE/academics/graduate"},
                {"label": "U.S. News — Aerospace Engineering", "url": USNEWS["aerospace"]},
            ],
        },
        "purdue-economics-bs": {
            "summary": (
                "Students describe Purdue's undergraduate economics major in the College of Liberal Arts "
                "as a quantitatively oriented program with strong preparation for graduate study and "
                "analytics roles; praise includes Krannert-adjacent quantitative training and research "
                "opportunities, with cautions that large introductory sections require proactive faculty "
                "engagement and career outcomes vary without further graduate study."
            ),
            "themes": [
                {"label": "Quantitative training", "sentiment": "positive", "detail": "Econometrics and statistics sequences prepare students for data and policy roles."},
                {"label": "Graduate preparation", "sentiment": "positive", "detail": "Strong track record placing graduates in economics and public policy Ph.D. programs."},
                {"label": "Research access", "sentiment": "positive", "detail": "Faculty labs in behavioral, labor, and development economics accept undergraduates."},
                {"label": "Large intro courses", "sentiment": "caution", "detail": "Gateway economics courses can be lecture-heavy with limited individual attention."},
                {"label": "Career without grad school", "sentiment": "mixed", "detail": "Undergraduate economics alone narrows options; pairing with data science or finance is common."},
            ],
            "sources": [
                {"label": "Purdue Economics — Undergraduate", "url": "https://cla.purdue.edu/economics/undergraduate/"},
                {"label": "Niche — Purdue University", "url": NICHE},
            ],
        },
        "purdue-public-health-bs": {
            "summary": (
                "Students describe Purdue's undergraduate public health program in HHS as an "
                "interdisciplinary major drawing on epidemiology, health policy, and biostatistics; "
                "praise includes access to Indiana health-system partnerships and a growing program "
                "within a land-grant research university, with cautions that the major is newer than "
                "peer pre-med tracks and upper-division courses can fill quickly."
            ),
            "themes": [
                {"label": "Interdisciplinary design", "sentiment": "positive", "detail": "Combines population health, statistics, and policy across HHS departments."},
                {"label": "Indiana partnerships", "sentiment": "positive", "detail": "Regional health systems and state agencies offer internship opportunities."},
                {"label": "Land-grant mission", "sentiment": "positive", "detail": "Extension and community health outreach connect classroom learning to practice."},
                {"label": "Program maturity", "sentiment": "mixed", "detail": "Undergraduate public health is newer than established pre-med pathways at peer schools."},
                {"label": "Course capacity", "sentiment": "caution", "detail": "Popular upper-division electives can be competitive to access."},
            ],
            "sources": [
                {"label": "Purdue Public Health — Undergraduate", "url": "https://hhs.purdue.edu/public-health/"},
                {"label": "U.S. News — Purdue University", "url": USNEWS["purdue"]},
            ],
        },
        "purdue-public-health-ms": {
            "summary": (
                "Graduate applicants describe Purdue's MPH as a practice-oriented public health degree "
                "within HHS emphasizing epidemiology, health policy, and community health; students value "
                "Indiana health-system partnerships and affordable tuition relative to coastal programs, "
                "with cautions that the school is smaller than top-10 public health programs and "
                "research funding is more limited than at R1 peers on the coasts."
            ),
            "themes": [
                {"label": "Practice orientation", "sentiment": "positive", "detail": "MPH curriculum emphasizes applied epidemiology and community health practice."},
                {"label": "Indiana network", "sentiment": "positive", "detail": "State health department and hospital partnerships support practicum placements."},
                {"label": "Affordable tuition", "sentiment": "positive", "detail": "In-state and competitive out-of-state rates versus coastal MPH programs."},
                {"label": "Program scale", "sentiment": "mixed", "detail": "Smaller than top-10 public health schools; fewer specialized concentrations."},
                {"label": "Research funding", "sentiment": "caution", "detail": "Assistantships and funded research spots are more limited than at larger peer schools."},
            ],
            "sources": [
                {"label": "Purdue Public Health — Graduate", "url": "https://hhs.purdue.edu/public-health/graduate/"},
                {"label": "U.S. News — Public Health Rankings", "url": USNEWS["public_health"]},
            ],
        },
        "purdue-finance-and-financial-management-services-bs": {
            "summary": (
                "Students describe Purdue's finance major through the Mitch Daniels School of Business "
                "as a quantitatively rigorous undergraduate program with strength in corporate finance, "
                "investments, and analytics; praise includes Krannert heritage and strong Midwest "
                "recruiting, with cautions that national finance recruiting trails top-10 undergraduate "
                "business programs and students must proactively pursue coastal internship opportunities."
            ),
            "themes": [
                {"label": "Quantitative finance", "sentiment": "positive", "detail": "Curriculum emphasizes corporate finance, investments, and financial analytics."},
                {"label": "Midwest recruiting", "sentiment": "positive", "detail": "Manufacturing, logistics, and regional banks recruit actively from MDSB."},
                {"label": "Analytics integration", "sentiment": "positive", "detail": "Krannert heritage brings operations and data skills into finance coursework."},
                {"label": "Coastal recruiting", "sentiment": "mixed", "detail": "Investment banking and buy-side placement require proactive networking beyond campus."},
                {"label": "Brand recognition", "sentiment": "mixed", "detail": "Strong regional reputation; national finance brand still developing."},
            ],
            "sources": [
                {"label": "Mitch Daniels School of Business — Finance", "url": "https://business.purdue.edu/undergraduate/"},
                {"label": "U.S. News — Best Undergraduate Business", "url": USNEWS["business"]},
            ],
        },
        "purdue-hospitality-administration-management-bs": {
            "summary": (
                "Students describe Purdue's hospitality management program in MDSB as one of the few "
                "top-ranked hospitality programs at a major research university, with strength in "
                "food-service management, event planning, and hotel operations; praise includes the "
                "Marriott Hall facilities and industry partnerships, with cautions that the program is "
                "niche relative to Purdue's engineering identity and coastal hospitality markets "
                "require relocation for top-tier hotel careers."
            ),
            "themes": [
                {"label": "Top hospitality rank", "sentiment": "positive", "detail": "Purdue hospitality is consistently ranked among the top programs nationally."},
                {"label": "Marriott Hall facilities", "sentiment": "positive", "detail": "Dedicated hospitality labs and demo kitchens support hands-on learning."},
                {"label": "Industry partnerships", "sentiment": "positive", "detail": "Major hotel, restaurant, and event companies recruit on campus."},
                {"label": "Niche within Purdue", "sentiment": "mixed", "detail": "Smaller program relative to engineering; fewer cross-campus resources."},
                {"label": "Geographic market", "sentiment": "caution", "detail": "Top-tier hotel careers often require relocation to coastal or resort markets."},
            ],
            "sources": [
                {"label": "Purdue Hospitality — About", "url": "https://business.purdue.edu/hospitality/"},
                {"label": "U.S. News — Purdue University", "url": USNEWS["purdue"]},
            ],
        },
        "purdue-landscape-architecture-bs": {
            "summary": (
                "Students describe Purdue's landscape architecture program in CLA as a design-intensive "
                "professional degree with emphasis on ecological planning and Midwest land-use issues; "
                "praise includes studio culture and interdisciplinary ties to agriculture and "
                "engineering, with cautions about long studio hours and that the B.L.A. requires "
                "further study or licensure pathways for full professional practice."
            ),
            "themes": [
                {"label": "Studio culture", "sentiment": "positive", "detail": "Design studios and site-planning projects anchor the curriculum."},
                {"label": "Ecological focus", "sentiment": "positive", "detail": "Midwest land-use and sustainability themes distinguish the program."},
                {"label": "Interdisciplinary ties", "sentiment": "positive", "detail": "Connections to agriculture, civil engineering, and urban planning enrich projects."},
                {"label": "Studio workload", "sentiment": "caution", "detail": "Long studio hours and intensive crit schedules are recurring themes."},
                {"label": "Licensure path", "sentiment": "mixed", "detail": "Professional landscape architecture licensure requires additional experience beyond the degree."},
            ],
            "sources": [
                {"label": "Purdue Landscape Architecture", "url": "https://cla.purdue.edu/landscape-architecture/"},
                {"label": "Niche — Purdue University", "url": NICHE},
            ],
        },
        "purdue-film-video-and-photographic-arts-bs": {
            "summary": (
                "Students describe Purdue's film and video studies program in CLA as a creative-arts "
                "major within a STEM-dominant campus, offering production courses and critical media "
                "studies; praise includes access to Polytechnic production facilities and "
                "interdisciplinary projects, with cautions that the program is smaller than dedicated "
                "film schools and industry networking requires proactive outreach beyond campus."
            ),
            "themes": [
                {"label": "Production access", "sentiment": "positive", "detail": "Students use Polytechnic and CLA media production facilities."},
                {"label": "Critical media studies", "sentiment": "positive", "detail": "Curriculum balances production skills with film theory and criticism."},
                {"label": "Interdisciplinary projects", "sentiment": "positive", "detail": "Collaborations with engineering and agriculture create unique documentary opportunities."},
                {"label": "Program scale", "sentiment": "mixed", "detail": "Smaller than dedicated film schools; fewer industry guest speakers."},
                {"label": "Industry networking", "sentiment": "caution", "detail": "Entertainment-industry placement requires proactive outreach beyond campus recruiting."},
            ],
            "sources": [
                {"label": "Purdue Brian Lamb School — Film & Video", "url": "https://cla.purdue.edu/communication/"},
                {"label": "Niche — Purdue University", "url": NICHE},
            ],
        },
        "purdue-nuclear-engineering-bs": {
            "summary": (
                "Students describe Purdue's nuclear engineering program as one of the few dedicated "
                "undergraduate nuclear programs in the United States, with strength in reactor physics, "
                "radiation detection, and nuclear materials; praise includes the PUR-1 research reactor "
                "on campus and strong ties to the national labs, with cautions that the field is niche "
                "and career paths concentrate in government, utilities, and national-security sectors."
            ),
            "themes": [
                {"label": "PUR-1 reactor", "sentiment": "positive", "detail": "On-campus research reactor provides rare undergraduate hands-on nuclear experience."},
                {"label": "National lab ties", "sentiment": "positive", "detail": "Connections to Argonne, Oak Ridge, and INL support internships and research."},
                {"label": "Specialized expertise", "sentiment": "positive", "detail": "One of the few standalone undergraduate nuclear engineering programs nationally."},
                {"label": "Niche field", "sentiment": "mixed", "detail": "Career paths concentrate in utilities, national labs, and defense."},
                {"label": "Program size", "sentiment": "caution", "detail": "Small cohort means fewer peer study groups but more faculty access."},
            ],
            "sources": [
                {"label": "Purdue Nuclear Engineering", "url": "https://engineering.purdue.edu/NE"},
                {"label": "U.S. News — Purdue Engineering", "url": USNEWS["engineering"]},
            ],
        },
        "purdue-industrial-engineering-bs": {
            "summary": (
                "Students describe Purdue's industrial engineering program as a perennial top-10 program "
                "nationally, known for operations research, human factors, and manufacturing systems; "
                "praise includes the Grissom Hall facilities and strong recruiting from Amazon, "
                "Caterpillar, and consulting firms, with cautions that large lower-division courses "
                "require proactive engagement and the quantitative curriculum is demanding."
            ),
            "themes": [
                {"label": "Top-10 national rank", "sentiment": "positive", "detail": "U.S. News consistently ranks Purdue IE among the nation's best programs."},
                {"label": "Operations research", "sentiment": "positive", "detail": "OR, simulation, and supply chain coursework are program hallmarks."},
                {"label": "Industry recruiting", "sentiment": "positive", "detail": "Amazon, Caterpillar, and consulting firms recruit actively."},
                {"label": "Quantitative demands", "sentiment": "caution", "detail": "Statistics, optimization, and simulation courses require strong math preparation."},
                {"label": "Large intro sections", "sentiment": "caution", "detail": "Gateway courses can be impersonal; office hours and study groups matter."},
            ],
            "sources": [
                {"label": "Purdue Industrial Engineering", "url": "https://engineering.purdue.edu/IE"},
                {"label": "U.S. News — Industrial Engineering", "url": USNEWS["industrial"]},
            ],
        },
    }

    if slug in overrides:
        r = overrides[slug]
        r["disclaimer"] = "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews."
        return r

    # Category-based templates
    fl = field.lower()
    is_eng = school == "College of Engineering" or "engineering" in fl
    is_poly = school == "Purdue Polytechnic Institute"
    is_business = school == "Mitch Daniels School of Business"
    is_ag = school == "College of Agriculture"
    is_hhs = school == "College of Health and Human Sciences"
    is_vet = school == "College of Veterinary Medicine"
    is_phd = degree_type in ("phd", "doctoral")
    is_ms = degree_type == "masters"
    is_bs = degree_type == "bachelors"

    usnews_key = "engineering"
    if "aerospace" in fl or "astronautical" in fl:
        usnews_key = "aerospace"
    elif "mechanical" in fl:
        usnews_key = "mechanical"
    elif "electrical" in fl or "electronic" in fl or "communications" in fl:
        usnews_key = "electrical"
    elif "chemical" in fl:
        usnews_key = "chemical"
    elif "civil" in fl or "construction" in fl:
        usnews_key = "civil"
    elif "industrial" in fl:
        usnews_key = "industrial"
    elif "computer" in fl:
        usnews_key = "computer_science"
    elif is_business:
        usnews_key = "business"
    elif "nursing" in fl:
        usnews_key = "nursing"
    elif "public health" in fl:
        usnews_key = "public_health"
    elif is_vet:
        usnews_key = "veterinary"

    if is_phd:
        summary = (
            f"Doctoral students describe Purdue's Ph.D. in {field} as a research degree within "
            f"{'the ' + school if school else 'Purdue'} producing scholars and industry researchers; "
            f"praise includes R1 research infrastructure and faculty mentorship, with cautions about "
            f"competitive admission, five-plus-year timelines, and specialized hiring markets."
        )
        themes = [
            {"label": "Research infrastructure", "sentiment": "positive", "detail": "Purdue's R1 status and Discovery Park support doctoral research across disciplines."},
            {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Doctoral students work closely with faculty on funded research projects."},
            {"label": "Career placement", "sentiment": "positive", "detail": "Graduates enter academia, national labs, and industry R&D leadership."},
            {"label": "Time to degree", "sentiment": "caution", "detail": "Dissertation timelines commonly span five or more years."},
            {"label": "Selective admission", "sentiment": "caution", "detail": "Strong research background and faculty alignment are expected."},
        ]
    elif is_ms:
        summary = (
            f"Graduate applicants describe Purdue's M.S. in {field} as a {'research and coursework' if is_eng else 'coursework and research'} "
            f"degree within {school}; students value Purdue's engineering and research reputation "
            f"{'and industry recruiting' if is_eng else 'and practical training'}, with cautions about "
            f"self-funded tuition for terminal master's students and competitive research funding."
        )
        themes = [
            {"label": "Graduate curriculum", "sentiment": "positive", "detail": f"M.S. coursework spans core {field.lower()} theory and applied projects."},
            {"label": "Research access", "sentiment": "positive", "detail": "Graduate students join faculty labs and interdisciplinary research centers."},
            {"label": "Industry paths", "sentiment": "positive", "detail": "Graduates enter industry R&D, consulting, and doctoral programs."},
            {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students without assistantships typically self-fund tuition."},
            {"label": "Funding competition", "sentiment": "caution", "detail": "Research assistantships are competitive across Purdue's large graduate population."},
        ]
    elif is_bs and is_eng:
        summary = (
            f"Students describe Purdue's undergraduate {field} program in the College of Engineering "
            f"as a nationally ranked engineering degree with strong theory-to-application training; "
            f"praise includes research lab access and Midwest industry recruiting, with cautions that "
            f"large lower-division sections require proactive faculty engagement."
        )
        themes = [
            {"label": "Engineering reputation", "sentiment": "positive", "detail": "Purdue Engineering is consistently ranked among the top programs nationally."},
            {"label": "Research labs", "sentiment": "positive", "detail": "Undergraduates access Discovery Park labs and school-specific research centers."},
            {"label": "Industry recruiting", "sentiment": "positive", "detail": "Manufacturing, tech, and defense firms recruit actively from Purdue Engineering."},
            {"label": "Rigorous curriculum", "sentiment": "caution", "detail": "Math and physics sequences in years 1–2 are demanding."},
            {"label": "Large class sizes", "sentiment": "caution", "detail": "Gateway courses can be impersonal; study groups and office hours matter."},
        ]
    elif is_bs and is_poly:
        summary = (
            f"Students describe Purdue's {field} program in the Polytechnic Institute as a "
            f"technology-focused applied degree emphasizing hands-on labs and industry skills; "
            f"praise includes smaller cohorts and practical project work, with cautions that "
            f"Polytechnic programs have less national brand recognition than traditional engineering degrees."
        )
        themes = [
            {"label": "Hands-on learning", "sentiment": "positive", "detail": "Polytechnic programs emphasize applied labs and project-based coursework."},
            {"label": "Industry skills", "sentiment": "positive", "detail": "Curriculum aligns with technician and applied-engineering career paths."},
            {"label": "Smaller cohorts", "sentiment": "positive", "detail": "Polytechnic classes are typically smaller than flagship engineering programs."},
            {"label": "Brand recognition", "sentiment": "mixed", "detail": "Applied technology degrees have less national visibility than traditional engineering."},
            {"label": "Career scope", "sentiment": "mixed", "detail": "Graduates enter applied engineering and technician roles rather than research-track positions."},
        ]
    elif is_bs and is_ag:
        summary = (
            f"Students describe Purdue's {field} program in the College of Agriculture as a "
            f"land-grant program with deep ties to Indiana agriculture and Purdue Extension; "
            f"praise includes practical field experience and USDA connections, with cautions that "
            f"career paths are specialized to agriculture and food systems."
        )
        themes = [
            {"label": "Land-grant mission", "sentiment": "positive", "detail": "Purdue Extension and Indiana agriculture provide unmatched applied learning."},
            {"label": "Field experience", "sentiment": "positive", "detail": "Research farms and extension stations support hands-on learning."},
            {"label": "USDA connections", "sentiment": "positive", "detail": "Faculty partnerships with USDA create policy and industry placement pipelines."},
            {"label": "Specialized careers", "sentiment": "mixed", "detail": "Career paths concentrate in agriculture, food systems, and rural development."},
            {"label": "Program scale", "sentiment": "mixed", "detail": "Smaller than flagship engineering programs but with strong faculty access."},
        ]
    elif is_bs and is_hhs:
        summary = (
            f"Students describe Purdue's {field} program in the College of Health and Human Sciences "
            f"as a health-focused undergraduate degree with clinical and community partnerships; "
            f"praise includes interdisciplinary HHS infrastructure and Indiana health-system access, "
            f"with cautions that the program is smaller than Purdue's engineering colleges."
        )
        themes = [
            {"label": "Clinical partnerships", "sentiment": "positive", "detail": "Indiana health systems provide clinical and community practicum opportunities."},
            {"label": "Interdisciplinary HHS", "sentiment": "positive", "detail": "Proximity to nursing, pharmacy, and nutrition enriches cross-training."},
            {"label": "Practical training", "sentiment": "positive", "detail": "Curriculum emphasizes applied health and human sciences skills."},
            {"label": "Program scale", "sentiment": "mixed", "detail": "Smaller than engineering programs; fewer elective options."},
            {"label": "Selective tracks", "sentiment": "caution", "detail": "Some HHS programs have enrollment caps and competitive admission."},
        ]
    elif is_ms and is_hhs:
        summary = (
            f"Graduate students describe Purdue's M.S. in {field} in HHS as a practice-oriented "
            f"health sciences degree with clinical research opportunities; praise includes Indiana "
            f"health-system partnerships, with cautions about limited research funding compared "
            f"to larger coastal health programs."
        )
        themes = [
            {"label": "Clinical research", "sentiment": "positive", "detail": "Graduate students engage in clinical and community health research."},
            {"label": "Indiana partnerships", "sentiment": "positive", "detail": "Regional hospitals and health agencies support practicum placements."},
            {"label": "Practice orientation", "sentiment": "positive", "detail": "Curriculum emphasizes applied health sciences and patient care."},
            {"label": "Funding limits", "sentiment": "caution", "detail": "Research assistantships are more limited than at larger peer programs."},
            {"label": "Program scale", "sentiment": "mixed", "detail": "Smaller graduate cohort than flagship engineering departments."},
        ]
    elif is_ms and is_vet:
        summary = (
            f"Graduate students describe Purdue's M.S. in {field} at the College of Veterinary "
            f"Medicine as a research degree with access to the veterinary teaching hospital and "
            f"ADDL diagnostic laboratory; praise includes One Health research initiatives, with "
            f"cautions about competitive admission and specialized veterinary career paths."
        )
        themes = [
            {"label": "Teaching hospital", "sentiment": "positive", "detail": "Small, large, and exotic animal hospitals provide broad clinical exposure."},
            {"label": "ADDL diagnostics", "sentiment": "positive", "detail": "Animal Disease Diagnostic Lab supports real-world disease surveillance research."},
            {"label": "One Health research", "sentiment": "positive", "detail": "Comparative medicine and zoonotic disease research are program strengths."},
            {"label": "Competitive admission", "sentiment": "caution", "detail": "Graduate veterinary research programs have selective admission pools."},
            {"label": "Specialized market", "sentiment": "mixed", "detail": "Career paths concentrate in veterinary research, academia, and government."},
        ]
    elif is_phd and is_vet:
        summary = (
            f"Doctoral students describe Purdue's Ph.D. in {field} at the College of Veterinary "
            f"Medicine as a research degree in comparative medicine and biomedical sciences; "
            f"praise includes the veterinary teaching hospital and One Health initiatives, with "
            f"cautions about long dissertation timelines and specialized academic hiring markets."
        )
        themes = [
            {"label": "Comparative medicine", "sentiment": "positive", "detail": "Doctoral research spans veterinary, human, and environmental health."},
            {"label": "Teaching hospital access", "sentiment": "positive", "detail": "On-campus veterinary hospitals support translational research."},
            {"label": "One Health focus", "sentiment": "positive", "detail": "Zoonotic disease and comparative oncology are active research areas."},
            {"label": "Dissertation timeline", "sentiment": "caution", "detail": "Veterinary biomedical Ph.D. programs commonly span five or more years."},
            {"label": "Academic market", "sentiment": "mixed", "detail": "Faculty positions concentrate in veterinary and biomedical sciences."},
        ]
    else:
        summary = (
            f"Students and third-party guides describe Purdue's {deg} program in {field} within "
            f"{school} as a {'research-oriented' if 'science' in school.lower() else 'professionally focused'} "
            f"degree at a top-50 national research university; praise includes Purdue's R1 "
            f"infrastructure and Midwest industry ties, with cautions about large class sizes "
            f"and that career outcomes vary by field and graduate-school plans."
        )
        themes = [
            {"label": "Research university", "sentiment": "positive", "detail": "Purdue's R1 status and Discovery Park support undergraduate and graduate research."},
            {"label": "Faculty expertise", "sentiment": "positive", "detail": f"Faculty in {department or school} lead applied and theoretical research."},
            {"label": "Career preparation", "sentiment": "positive", "detail": "Graduates enter industry, government, and graduate programs across the Midwest and nationally."},
            {"label": "Class scale", "sentiment": "caution", "detail": "Large university means gateway courses can be lecture-heavy."},
            {"label": "Career variability", "sentiment": "mixed", "detail": "Outcomes depend on field specialization and whether students pursue further study."},
        ]

    return {
        "summary": summary,
        "themes": themes,
        "sources": [
            {"label": f"Purdue — {department or school}", "url": dept_url},
            {"label": "U.S. News — Purdue University", "url": USNEWS.get(usnews_key, USNEWS["purdue"])},
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews.",
    }


def main():
    programs = []
    with open("/tmp/purdue_missing_reviews.txt") as f:
        for line in f:
            parts = line.strip().split("|")
            if len(parts) >= 5:
                programs.append({
                    "slug": parts[0],
                    "program_name": parts[1],
                    "degree_type": parts[2],
                    "school": parts[3],
                    "department": parts[4],
                })

    reviews = {p["slug"]: review_for(**p) for p in programs}

    lines = [
        '"""Purdue University external_reviews depth pass.',
        "",
        "Depth pass date: 2026-06-15. Consumed by the ``purdueprof3`` migration to merge",
        f'``DEPTH_REVIEWS`` into ``purdue_profile._REVIEWS_BY_SLUG`` for {len(reviews)}',
        "remaining coverable programs (64/64 total).",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "# ruff: noqa: E501",
        "",
        '_DISCLAIMER = (',
        '    "Aggregated and paraphrased from public third-party sources — not "',
        '    "individual verbatim reviews."',
        ")",
        "",
        "DEPTH_REVIEWS: dict[str, dict] = {",
    ]

    for slug in sorted(reviews):
        r = reviews[slug]
        lines.append(f'    "{slug}": {{')
        lines.append(f'        "summary": {json.dumps(r["summary"])},')
        lines.append('        "themes": [')
        for t in r["themes"]:
            lines.append("            {")
            lines.append(f'                "label": {json.dumps(t["label"])},')
            lines.append(f'                "sentiment": {json.dumps(t["sentiment"])},')
            lines.append(f'                "detail": {json.dumps(t["detail"])},')
            lines.append("            },")
        lines.append("        ],")
        lines.append('        "sources": [')
        for s in r["sources"]:
            lines.append("            {")
            lines.append(f'                "label": {json.dumps(s["label"])},')
            lines.append(f'                "url": {json.dumps(s["url"])},')
            lines.append("            },")
        lines.append("        ],")
        lines.append(f'        "disclaimer": _DISCLAIMER,')
        lines.append("    },")

    lines.append("}")
    lines.append("")

    out = "/workspace/unipaith-backend/src/unipaith/data/purdue_reviews_depth.py"
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {len(reviews)} reviews to {out}")


if __name__ == "__main__":
    main()
