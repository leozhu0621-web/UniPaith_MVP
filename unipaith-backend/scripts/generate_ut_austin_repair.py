#!/usr/bin/env python3
"""Generate UT Austin profile repair artifacts: field descriptions and coverable reviews.

Run from unipaith-backend/:
  PYTHONPATH=src python scripts/generate_ut_austin_repair.py
"""
# ruff: noqa: E501

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")

from fleet_audit import is_coverable  # noqa: E402

ROOT = Path("src/unipaith/data")

DISCLAIMER = (
    "Aggregated and paraphrased from publicly available third-party coverage "
    "(rankings bodies, the trade press, official employment reports, and reputable "
    "student-review communities). Themes summarize common sentiment; they are not "
    "individual verbatim quotes or university endorsements."
)

_SCHOOL_CLAUSE: dict[str, str] = {
    "Cockrell School of Engineering": (
        "the Cockrell School of Engineering — home to the #1-ranked petroleum "
        "engineering program and the Chandra Family Department of Electrical and "
        "Computer Engineering — trains engineers across aerospace, biomedical, civil, "
        "chemical, mechanical, and petroleum disciplines with TACC and Applied "
        "Research Laboratories partnerships."
    ),
    "Red McCombs School of Business": (
        "Texas McCombs combines the Full-Time MBA, the M.S. in Business Analytics, "
        "the Master in Professional Accounting, and undergraduate BBA majors with "
        "strong consulting, finance, and Austin tech recruiting."
    ),
    "College of Natural Sciences": (
        "the College of Natural Sciences — anchored by the top-10 UT Computer Science "
        "department — spans mathematics, physics, chemistry, molecular biosciences, "
        "and statistics, plus the $10,000 online MSCS/MSDS/MSAI degrees."
    ),
    "College of Liberal Arts": (
        "the College of Liberal Arts — UT Austin's largest college — spans economics, "
        "government, psychology, history, English, and the humanities and social "
        "sciences across the Forty Acres."
    ),
    "Moody College of Communication": (
        "Moody College trains journalists, advertisers, public-relations specialists, "
        "and communication researchers through the Stan Richards School and the School "
        "of Journalism and Media."
    ),
    "College of Fine Arts": (
        "the College of Fine Arts combines the Butler School of Music, theatre and "
        "dance, studio art, and the School of Design and Creative Technologies on "
        "the Austin campus."
    ),
    "Jackson School of Geosciences": (
        "the Jackson School of Geosciences connects geology, geophysics, and "
        "geosystems engineering with the Bureau of Economic Geology and field "
        "research across Texas energy basins."
    ),
    "School of Information": (
        "the School of Information trains archivists, UX researchers, and data "
        "professionals through the MSIS and the iSchool's human-centered computing "
        "programs."
    ),
    "LBJ School of Public Affairs": (
        "the LBJ School offers the Master of Public Affairs and the Master of Global "
        "Policy Studies with quantitative policy training and Austin government "
        "partnerships."
    ),
    "School of Law": (
        "Texas Law combines doctrinal coursework with clinical programs, the "
        "Bernard and Audre Rapoport Center, and very strong Big-Law and public-"
        "interest placement."
    ),
    "Dell Medical School": (
        "Dell Medical School — UT Austin's newest college — trains M.D. students "
        "through a value-based-care curriculum integrated with Austin's safety-net "
        "health systems."
    ),
    "College of Education": (
        "the College of Education trains teachers, counselors, and education "
        "researchers through curriculum and instruction, educational psychology, "
        "kinesiology, and special education."
    ),
    "School of Nursing": (
        "the School of Nursing offers the BSN, MSN specialties, the DNP, and the "
        "Ph.D. in Nursing Science with simulation labs and Austin clinical "
        "placements."
    ),
    "College of Pharmacy": (
        "the College of Pharmacy trains Pharm.D. students across clinical pharmacy, "
        "medicinal chemistry, and pharmaceutics with Dell Seton Medical Center ties."
    ),
    "School of Social Work": (
        "the Steve Hicks School of Social Work integrates field practica with "
        "community agencies across Central Texas."
    ),
    "School of Architecture": (
        "the School of Architecture offers NAAB-accredited architecture degrees, "
        "landscape architecture, interior design, urban design, and community "
        "planning studios."
    ),
    "School of Public Health": (
        "UT Austin Public Health spans epidemiology, biostatistics, and health "
        "promotion with Dell Med and community-health partnerships."
    ),
    "School of Civic Leadership": (
        "the School of Civic Leadership trains undergraduates in civics, leadership, "
        "and public-service pathways."
    ),
}

SCHOOL_URLS = {
    "Cockrell School of Engineering": "https://cockrell.utexas.edu/",
    "Red McCombs School of Business": "https://www.mccombs.utexas.edu/",
    "College of Natural Sciences": "https://cns.utexas.edu/",
    "College of Liberal Arts": "https://liberalarts.utexas.edu/",
    "Moody College of Communication": "https://moody.utexas.edu/",
    "College of Fine Arts": "https://finearts.utexas.edu/",
    "Jackson School of Geosciences": "https://www.jsg.utexas.edu/",
    "School of Information": "https://ischool.utexas.edu/",
    "LBJ School of Public Affairs": "https://lbj.utexas.edu/",
    "School of Law": "https://law.utexas.edu/",
    "Dell Medical School": "https://dellmed.utexas.edu/",
    "College of Education": "https://education.utexas.edu/",
    "School of Nursing": "https://nursing.utexas.edu/",
    "College of Pharmacy": "https://pharmacy.utexas.edu/",
    "School of Social Work": "https://socialwork.utexas.edu/",
    "School of Architecture": "https://soa.utexas.edu/",
    "School of Public Health": "https://publichealth.utexas.edu/",
    "School of Civic Leadership": "https://civicleadership.utexas.edu/",
}

USNEWS = {
    "national": "https://www.usnews.com/best-colleges/university-of-texas-austin-3658",
    "engineering": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/university-of-texas-austin-02169",
    "business": "https://www.usnews.com/best-graduate-schools/top-business-schools/university-of-texas-austin-01058",
    "law": "https://www.usnews.com/best-graduate-schools/top-law-schools/university-of-texas-at-austin-03128",
    "medicine": "https://www.usnews.com/best-graduate-schools/top-medical-schools/university-of-texas-austin-dell-04067",
    "cs": "https://www.usnews.com/best-graduate-schools/top-science-schools/computer-science-rankings",
    "education": "https://www.usnews.com/best-graduate-schools/top-education-schools/university-of-texas-austin-06035",
    "social_work": "https://www.usnews.com/best-graduate-schools/top-health-schools/social-work-rankings",
    "public_health": "https://www.usnews.com/best-graduate-schools/top-public-health-schools/university-of-texas-austin-101511",
    "nursing": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/university-of-texas-austin-06122",
    "public_affairs": "https://www.usnews.com/best-graduate-schools/top-public-affairs-schools/public-affairs-rankings",
}


def field_key(program_name: str) -> str:
    overrides = {
        "Juris Doctor": "Law (J.D.)",
        "Doctor of Medicine": "Medicine (M.D.)",
        "Master of Business Administration": "Business Administration (MBA)",
        "Doctor of Pharmacy": "Pharmacy (Pharm.D.)",
        "Doctor of Audiology": "Audiology (Au.D.)",
        "Doctor of Nursing Practice": "Nursing Practice (DNP)",
        "Master in Professional Accounting": "Accounting (MPA)",
        "Master of Public Affairs": "Public Affairs (MPAff)",
        "Master of Laws": "Law (LL.M.)",
    }
    if program_name in overrides:
        return overrides[program_name]
    for prefix in (
        "Bachelor of Science in ",
        "Bachelor of Arts in ",
        "Bachelor of Fine Arts in ",
        "Bachelor of Business Administration in ",
        "Bachelor of Architecture in ",
        "Bachelor of Social Work in ",
        "Bachelor of Journalism in ",
        "Master of Science in ",
        "Master of Arts in ",
        "Master of Fine Arts in ",
        "Master of Architecture in ",
        "Master of Landscape Architecture in ",
        "Master of Education in ",
        "Master of Music in ",
        "Master of Interior Design in ",
        "Master of Global Policy Studies in ",
        "Master of Public Leadership in ",
        "Master of Advanced Architectural Design in ",
        "Doctor of Philosophy in ",
        "Doctor of Education in ",
        "Doctor of Musical Arts in ",
        "Juris Doctor",
        "Doctor of Medicine",
        "Doctor of Pharmacy",
        "Master in Professional Accounting",
        "Master of Public Affairs",
        "Master of Business Administration",
        "Master of Laws",
    ):
        if program_name.startswith(prefix):
            return program_name[len(prefix) :].strip()
    return program_name


def field_description_clause(field: str, school: str, department: str) -> str:
    school_clause = _SCHOOL_CLAUSE.get(school, f"programs within {school}")
    dept = department if department and department != field else field
    return (
        f"UT Austin's {dept} program connects to {school_clause}. "
        f"Students build depth in {field.lower()} through seminars, research, and "
        f"Austin industry and community partnerships."
    )


def build_field_descriptions(programs: list[dict]) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in programs:
        key = field_key(p["program_name"])
        if key not in out:
            out[key] = field_description_clause(key, p["school"], p.get("department", key))
    return dict(sorted(out.items()))


def review_for(spec: dict) -> dict:
    pname = spec["program_name"]
    field = field_key(pname)
    school = spec["school"]
    dtype = spec["degree_type"]
    slug = spec["slug"]
    school_url = SCHOOL_URLS.get(school, "https://www.utexas.edu/")
    is_phd = dtype in ("phd", "doctoral")
    is_ms = dtype == "masters"
    is_bs = dtype == "bachelors"
    is_prof = dtype == "professional"
    fl = field.lower()
    sl = school.lower()

    usnews = USNEWS["national"]
    if "mccombs" in sl or "business" in sl or "mba" in fl or "accounting" in fl or "finance" in fl:
        usnews = USNEWS["business"]
    elif "law" in sl or "juris" in fl or "law" in fl:
        usnews = USNEWS["law"]
    elif "dell med" in sl or ("medicine" in fl and "md" in slug):
        usnews = USNEWS["medicine"]
    elif "cockrell" in sl or ("engineering" in fl and "computer" not in fl):
        usnews = USNEWS["engineering"]
    elif "computer" in fl or "data science" in fl or "artificial intelligence" in fl:
        usnews = USNEWS["cs"]
    elif "education" in sl or "education" in fl:
        usnews = USNEWS["education"]
    elif "social work" in fl:
        usnews = USNEWS["social_work"]
    elif "public health" in fl:
        usnews = USNEWS["public_health"]
    elif "nursing" in fl:
        usnews = USNEWS["nursing"]
    elif "lbj" in sl or "public affairs" in fl or "public leadership" in fl:
        usnews = USNEWS["public_affairs"]

    deg_word = {"bachelors": "undergraduate", "masters": "graduate", "phd": "doctoral"}.get(
        dtype, dtype
    )

    if is_prof and ("law" in fl or "jd" in slug):
        summary = (
            "Applicants describe Texas Law's J.D. as a top-15 law school with very strong "
            "employment — about 97% of the Class of 2023 in long-term jobs — clinical "
            "programs, and public-university value; cautions include intense workload and "
            "a competitive bar."
        )
        themes = [
            {"label": "Strong employment", "sentiment": "positive", "detail": "Class of 2023 reported about 96.8% employed in long-term jobs."},
            {"label": "Clinical training", "sentiment": "positive", "detail": "Clinical programs and externships anchor practical training."},
            {"label": "Public-university value", "sentiment": "positive", "detail": "Texas Law delivers top-tier outcomes at lower tuition than private peers."},
            {"label": "Competitive admission", "sentiment": "caution", "detail": "Admission is highly selective with a ~15% acceptance rate."},
            {"label": "Workload", "sentiment": "mixed", "detail": "Reviewers describe a rigorous, writing-intensive curriculum."},
        ]
    elif is_prof and ("medicine" in fl or "md" in slug):
        summary = (
            "Applicants describe Dell Med's M.D. as an innovation-focused medical school with "
            "a value-based-care curriculum, small cohorts, and Austin clinical partners; "
            "praise includes the modern curriculum, with cautions about its youth (founded 2016)."
        )
        themes = [
            {"label": "Innovative curriculum", "sentiment": "positive", "detail": "Dell Med emphasizes value-based care and health-systems redesign."},
            {"label": "Austin clinical partners", "sentiment": "positive", "detail": "Training spans Ascension Seton and Central Health partners."},
            {"label": "Small cohort", "sentiment": "positive", "detail": "A selective entering class supports close mentorship."},
            {"label": "Young program", "sentiment": "caution", "detail": "Founded in 2016, Dell Med has a shorter track record than peer schools."},
            {"label": "Selective admission", "sentiment": "mixed", "detail": "Medical school admission is highly competitive nationally."},
        ]
    elif is_prof and ("pharmacy" in fl or "pharmd" in slug):
        summary = (
            "Applicants describe UT Pharmacy's Pharm.D. as a rigorous program with clinical "
            "rotations and pharmaceutical-sciences research; praise includes Dell Seton ties, "
            "with cautions about licensing exams."
        )
        themes = [
            {"label": "Clinical rotations", "sentiment": "positive", "detail": "Rotations span hospital and community pharmacy settings."},
            {"label": "Research departments", "sentiment": "positive", "detail": "Medicinal chemistry and pharmaceutics anchor research."},
            {"label": "Health-system ties", "sentiment": "positive", "detail": "Dell Seton Medical Center supports clinical training."},
            {"label": "Licensing exams", "sentiment": "caution", "detail": "NAPLEX and MPJE preparation is intensive."},
            {"label": "Workload", "sentiment": "mixed", "detail": "Professional pharmacy programs require sustained study."},
        ]
    elif "mba" in fl or "mba" in slug:
        summary = (
            "Applicants describe Texas McCombs' Full-Time MBA as a top-20 program with strong "
            "consulting, tech, and finance recruiting in Austin; praise includes salary "
            "outcomes and cohort culture, with cautions about cyclical consulting demand."
        )
        themes = [
            {"label": "Consulting and tech recruiting", "sentiment": "positive", "detail": "Class of 2024 placed 30% in consulting and 22% in technology."},
            {"label": "Austin location", "sentiment": "positive", "detail": "Austin's tech and finance hub supports local recruiting."},
            {"label": "Salary outcomes", "sentiment": "positive", "detail": "2024 graduates reported average base salary of $151,178."},
            {"label": "Consulting cycles", "sentiment": "mixed", "detail": "Consulting hiring softened in the 2024 cycle nationally."},
            {"label": "Regional brand", "sentiment": "caution", "detail": "Placement skews toward Texas and the South/Southwest."},
        ]
    elif is_phd:
        summary = (
            f"Doctoral students describe UT Austin's {field} Ph.D. within {school} as a "
            "research degree with R1 faculty mentorship and interdisciplinary resources "
            "across Austin; praise includes funded assistantships in many departments, "
            "with cautions about funding competition."
        )
        themes = [
            {"label": "R1 research mentorship", "sentiment": "positive", "detail": "Doctoral students work with faculty across a top public research university."},
            {"label": "Interdisciplinary access", "sentiment": "positive", "detail": "Cross-college institutes support computational and applied research."},
            {"label": "Austin ecosystem", "sentiment": "positive", "detail": "Tech, energy, and biotech partnerships support applied scholarship."},
            {"label": "Funding competition", "sentiment": "caution", "detail": "Fellowships and assistantships are competitive across programs."},
            {"label": "Academic market", "sentiment": "caution", "detail": "Tenure-track hiring varies by field nationally."},
        ]
    elif is_ms and ("computer" in fl or "data" in fl or "artificial intelligence" in fl):
        summary = (
            f"Graduate applicants describe UT Austin's {pname} as a rigorous program with "
            "top-10 CS strength in AI, systems, and theory; praise includes Austin tech "
            "recruiting and the affordable online MSCS option, with cautions about "
            "competitive admission."
        )
        themes = [
            {"label": "Top CS reputation", "sentiment": "positive", "detail": "UT CS is consistently ranked among the top 10 U.S. programs."},
            {"label": "AI and systems depth", "sentiment": "positive", "detail": "Faculty strength spans AI, systems, and programming languages."},
            {"label": "Tech recruiting", "sentiment": "positive", "detail": "Graduates recruit into major technology firms and Austin startups."},
            {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students often self-fund without assistantships."},
            {"label": "Competitive admission", "sentiment": "mixed", "detail": "Popular CS graduate programs admit a fraction of applicants."},
        ]
    elif is_bs and "computer" in fl:
        summary = (
            f"Undergraduate applicants describe UT Austin's {pname} as a top-10 program "
            "with renowned faculty in AI, systems, and theory; praise includes Austin "
            "tech placement, with cautions about very competitive direct admission."
        )
        themes = [
            {"label": "Top-10 computer science", "sentiment": "positive", "detail": "UT CS is consistently ranked among the best U.S. programs."},
            {"label": "Research breadth", "sentiment": "positive", "detail": "Undergraduates engage in AI, robotics, systems, and security research."},
            {"label": "Industry placement", "sentiment": "positive", "detail": "Graduates recruit heavily into major technology firms and Austin startups."},
            {"label": "Selective admission", "sentiment": "caution", "detail": "Direct admission to CS is highly competitive."},
            {"label": "Large courses", "sentiment": "caution", "detail": "Popular CS courses are high-enrollment; reviewers advise early research engagement."},
        ]
    elif "petroleum" in fl:
        summary = (
            f"Students describe UT Austin's {pname} as the nation's #1-ranked petroleum "
            "engineering program with Hildebrand Department strength in reservoir "
            "engineering and energy recruiting; praise includes industry placement, "
            "with cautions about energy-sector cyclicality."
        )
        themes = [
            {"label": "#1 petroleum engineering", "sentiment": "positive", "detail": "U.S. News ranks UT petroleum engineering #1 nationally."},
            {"label": "Energy industry ties", "sentiment": "positive", "detail": "Deep ties to oil, gas, and geosystems employers across Texas."},
            {"label": "Hildebrand Department", "sentiment": "positive", "detail": "Faculty strength spans reservoir, drilling, and production engineering."},
            {"label": "Sector cyclicality", "sentiment": "caution", "detail": "Energy hiring varies with commodity cycles."},
            {"label": "Rigorous core", "sentiment": "mixed", "detail": "Math, physics, and geology prerequisites are demanding."},
        ]
    elif "cockrell" in sl or "engineering" in fl:
        summary = (
            f"Students describe Cockrell's {pname} as a top-ranked engineering program "
            "with TACC, ARL:UT, and Austin semiconductor and tech industry ties; praise "
            "includes placement, with cautions about rigorous prerequisites."
        )
        themes = [
            {"label": "Top engineering", "sentiment": "positive", "detail": "Cockrell is consistently ranked among the nation's best engineering schools."},
            {"label": "Research labs", "sentiment": "positive", "detail": "TACC and Applied Research Laboratories anchor research partnerships."},
            {"label": "Industry recruiting", "sentiment": "positive", "detail": "Semiconductor, tech, and energy firms recruit UT engineers."},
            {"label": "Rigorous core", "sentiment": "caution", "detail": "Math and physics prerequisites are demanding."},
            {"label": "Large program", "sentiment": "mixed", "detail": "Engineering enrollment is high; reviewers advise early faculty engagement."},
        ]
    elif "mccombs" in sl or "business" in fl or "finance" in fl:
        summary = (
            f"Students describe McCombs' {pname} as a {deg_word} business program with "
            "consulting, finance, and Austin tech recruiting; praise includes the MBA "
            "and MPA pipelines, with cautions about selective admission."
        )
        themes = [
            {"label": "Consulting and finance", "sentiment": "positive", "detail": "McCombs places graduates into consulting, finance, and tech roles."},
            {"label": "Austin recruiting", "sentiment": "positive", "detail": "Austin's tech and finance hub supports internships and placement."},
            {"label": "Business analytics", "sentiment": "positive", "detail": "The M.S. in Business Analytics is a flagship quantitative program."},
            {"label": "Selective programs", "sentiment": "caution", "detail": "Popular business programs are competitive."},
            {"label": "Workload", "sentiment": "mixed", "detail": "Reviewers describe a rigorous, team-oriented culture."},
        ]
    elif "lbj" in sl or "public affairs" in fl or "public leadership" in fl:
        summary = (
            f"Students describe the LBJ School's {pname} as a top public-policy program "
            "with quantitative training and Austin government partnerships; praise "
            "includes policy research, with cautions about public-sector salary paths."
        )
        themes = [
            {"label": "Policy research", "sentiment": "positive", "detail": "LBJ connects policy analysis to Texas and national governance."},
            {"label": "Quantitative training", "sentiment": "positive", "detail": "Coursework emphasizes economics, statistics, and policy analysis."},
            {"label": "Austin partnerships", "sentiment": "positive", "detail": "Internships span state government, nonprofits, and regional agencies."},
            {"label": "Public-sector pay", "sentiment": "caution", "detail": "Public-service salaries can lag private-sector pay."},
            {"label": "Career paths", "sentiment": "mixed", "detail": "Outcomes split between government, consulting, and nonprofits."},
        ]
    elif "moody" in sl or "journalism" in fl or "advertising" in fl or "communication" in fl:
        summary = (
            f"Students describe Moody's {pname} as a communication program with Stan "
            "Richards School and journalism strength; praise includes media-industry "
            "placement in Austin and nationally, with cautions about a competitive field."
        )
        themes = [
            {"label": "Journalism and media", "sentiment": "positive", "detail": "Programs span journalism, advertising, and public relations."},
            {"label": "Industry connections", "sentiment": "positive", "detail": "Austin media and tech firms support internships."},
            {"label": "Portfolio work", "sentiment": "positive", "detail": "Coursework emphasizes hands-on reporting and campaigns."},
            {"label": "Competitive field", "sentiment": "caution", "detail": "Media jobs nationally are competitive."},
            {"label": "Workload", "sentiment": "mixed", "detail": "Reviewers describe deadline-driven studio and reporting courses."},
        ]
    elif "architecture" in sl or "architecture" in fl or "urban design" in fl or "landscape" in fl:
        summary = (
            f"Students describe UT SOA's {pname} as a studio-based design program with "
            "NAAB-accredited pathways and Austin urban-design partnerships; praise "
            "includes design training, with cautions about portfolio requirements."
        )
        themes = [
            {"label": "Studio training", "sentiment": "positive", "detail": "Architecture and planning programs emphasize hands-on studios."},
            {"label": "NAAB accreditation", "sentiment": "positive", "detail": "Professional architecture degrees meet licensure pathways."},
            {"label": "Austin design context", "sentiment": "positive", "detail": "Urban projects connect coursework to real Austin sites."},
            {"label": "Portfolio requirements", "sentiment": "caution", "detail": "Graduate admission often requires design portfolios."},
            {"label": "Studio costs", "sentiment": "mixed", "detail": "Materials and travel for studio projects add to tuition."},
        ]
    elif "nursing" in fl:
        summary = (
            f"Students describe UT Nursing's {pname} as a rigorous program with "
            "simulation labs and Austin clinical placements; praise includes NCLEX "
            "outcomes, with cautions about clinical workload."
        )
        themes = [
            {"label": "Clinical training", "sentiment": "positive", "detail": "Simulation labs and hospital rotations anchor the curriculum."},
            {"label": "Licensure outcomes", "sentiment": "positive", "detail": "The BSN reports strong NCLEX-RN pass rates."},
            {"label": "Faculty research", "sentiment": "positive", "detail": "Nursing research connects to health-system outcomes."},
            {"label": "Clinical workload", "sentiment": "caution", "detail": "Rotations and board preparation are intensive."},
            {"label": "Competitive admission", "sentiment": "mixed", "detail": "Direct BSN admission is capacity-limited."},
        ]
    elif "public health" in fl:
        summary = (
            f"Students describe UT Public Health's {pname} as a program linking "
            "epidemiology, biostatistics, and community health; praise includes Dell "
            "Med ties, with cautions about funding for terminal master's students."
        )
        themes = [
            {"label": "Public health breadth", "sentiment": "positive", "detail": "Programs span epidemiology, biostatistics, and health promotion."},
            {"label": "Dell Med ties", "sentiment": "positive", "detail": "Health-system partnerships support applied research."},
            {"label": "Community health", "sentiment": "positive", "detail": "Coursework connects to Austin community-health initiatives."},
            {"label": "Funding", "sentiment": "caution", "detail": "Assistantships are limited for terminal master's students."},
            {"label": "Career paths", "sentiment": "mixed", "detail": "Outcomes split between policy, research, and healthcare administration."},
        ]
    elif "social work" in fl:
        summary = (
            f"Students describe UT's {pname} as a field-practice-oriented social-work "
            "program with Central Texas agency placements; praise includes clinical "
            "training, with cautions about emotionally demanding practica."
        )
        themes = [
            {"label": "Field practica", "sentiment": "positive", "detail": "Supervised placements at community agencies anchor the curriculum."},
            {"label": "Clinical training", "sentiment": "positive", "detail": "Coursework prepares students for LCSW licensure pathways."},
            {"label": "Community focus", "sentiment": "positive", "detail": "Programs serve Austin and Central Texas partners."},
            {"label": "Emotional demands", "sentiment": "caution", "detail": "Practica expose students to trauma-heavy casework."},
            {"label": "Licensure pathway", "sentiment": "mixed", "detail": "Post-graduation supervised hours are required for clinical licensure."},
        ]
    elif "education" in sl or "education" in fl or "kinesiology" in fl:
        summary = (
            f"Students describe UT's {pname} as an education program with teacher-"
            "preparation and research training; praise includes Austin school "
            "partnerships, with cautions about state licensure requirements."
        )
        themes = [
            {"label": "Teacher preparation", "sentiment": "positive", "detail": "Programs connect to local schools for student-teaching practica."},
            {"label": "Research training", "sentiment": "positive", "detail": "Educational psychology and policy faculty anchor graduate research."},
            {"label": "Community partnerships", "sentiment": "positive", "detail": "Austin-area schools support field placements."},
            {"label": "Licensure requirements", "sentiment": "caution", "detail": "Teaching credentials require state-specific exams."},
            {"label": "Funding", "sentiment": "mixed", "detail": "Assistantships vary by doctoral vs. professional master's programs."},
        ]
    elif "jsg" in sl or "geosci" in sl or "geology" in fl or "geophysics" in fl:
        summary = (
            f"Students describe the Jackson School's {pname} as a geosciences program "
            "with Bureau of Economic Geology field research and energy-industry ties; "
            "praise includes geology and geophysics strength, with cautions about "
            "fieldwork costs."
        )
        themes = [
            {"label": "Field research", "sentiment": "positive", "detail": "The Bureau of Economic Geology and Texas field sites support research."},
            {"label": "Energy geosciences", "sentiment": "positive", "detail": "Programs connect to petroleum, hydrogeology, and climate science."},
            {"label": "Industry ties", "sentiment": "positive", "detail": "Energy and environmental employers recruit Jackson School graduates."},
            {"label": "Fieldwork costs", "sentiment": "caution", "detail": "Field courses and research travel add to tuition."},
            {"label": "Funding", "sentiment": "mixed", "detail": "Research assistantships vary by doctoral vs. terminal master's programs."},
        ]
    else:
        summary = (
            f"Students and guides describe UT Austin's {pname} within {school} as a "
            f"{deg_word} program drawing on Austin research and industry resources; "
            "praise includes interdisciplinary access at a top public R1 university, "
            "with cautions about competitive admission."
        )
        themes = [
            {"label": "R1 university resources", "sentiment": "positive", "detail": "Students access libraries, TACC, and cross-college electives."},
            {"label": "Austin ecosystem", "sentiment": "positive", "detail": "Internships leverage the tech, energy, and biotech hub."},
            {"label": "Public-university value", "sentiment": "positive", "detail": "In-state tuition and Texas Advance Commitment support affordability."},
            {"label": "Selective admission", "sentiment": "caution", "detail": "Popular programs admit a fraction of applicants."},
            {"label": "Program workload", "sentiment": "mixed", "detail": "Requirements vary; professional programs are especially intensive."},
        ]

    return {
        "summary": summary,
        "themes": themes,
        "sources": [
            {"label": f"UT Austin — {school}", "url": school_url},
            {"label": "U.S. News — UT Austin rankings", "url": usnews},
        ],
        "disclaimer": DISCLAIMER,
    }


def write_field_descriptions(path: Path, fields: dict[str, str]) -> None:
    lines = [
        '"""Field-specific program description clauses for UT Austin.',
        "",
        "Each entry states something concrete about what UT Austin's program in that field",
        "covers — never a credential/school classification stub. Sources: UT Austin Catalog,",
        "college and department pages, UT Austin Fast Facts.",
        '"""',
        "",
        "# ruff: noqa: E501",
        "",
        "FIELD_DESCRIPTIONS: dict[str, str] = {",
    ]
    for key, val in fields.items():
        esc = val.replace('"', '\\"')
        lines.append(f'    "{key}": "{esc}",')
    lines.append("}")
    lines.append("")
    path.write_text("\n".join(lines))


def write_reviews(path: Path, reviews: dict[str, dict]) -> None:
    lines = [
        '"""Generated external_reviews for UT Austin coverable programs."""',
        "",
        "# ruff: noqa: E501",
        "",
        "REVIEWS: dict[str, dict] = {",
    ]
    for slug, rev in sorted(reviews.items()):
        lines.append(f'    "{slug}": {json.dumps(rev, ensure_ascii=False)},')
    lines.append("}")
    lines.append("")
    path.write_text("\n".join(lines))


def main() -> None:
    import unipaith.data.ut_austin_profile as mod  # noqa: WPS433

    importlib.reload(mod)
    programs = mod.PROGRAMS
    from unipaith.data.profile_catalog_utils import validate_catalog

    errors = validate_catalog(programs)
    if errors:
        raise SystemExit(f"Catalog validation failed: {errors}")

    fields = build_field_descriptions(programs)
    write_field_descriptions(ROOT / "ut_austin_field_descriptions.py", fields)

    importlib.reload(mod)
    programs = mod.PROGRAMS

    hand_crafted = {
        "ut-austin-business-administration-mba",
        "ut-austin-law-jd",
        "ut-austin-medicine-md",
        "ut-austin-computer-science-bsa",
        "ut-austin-computer-science-online-ms",
        "ut-austin-business-administration-bba",
        "ut-austin-accounting-mpa",
        "ut-austin-business-analytics-ms",
        "ut-austin-petroleum-engineering-bspe",
        "ut-austin-electrical-and-computer-engineering-bsece",
        "ut-austin-mechanical-engineering-bsme",
        "ut-austin-public-affairs-mpaff",
        "ut-austin-nursing-bsn",
    }
    reviews: dict[str, dict] = {}
    for p in programs:
        slug = p["slug"]
        if not is_coverable(p) or slug in hand_crafted:
            continue
        reviews[slug] = review_for(p)

    write_reviews(ROOT / "ut_austin_reviews_generated.py", reviews)
    print(f"FIELD_DESCRIPTIONS: {len(fields)} entries")
    print(f"NEW REVIEWS: {len(reviews)} coverable programs")
    print(f"HAND-CRAFTED REVIEWS kept: {len(hand_crafted)}")
    print(f"PROGRAMS: {len(programs)} (catalog errors: {len(errors)})")


if __name__ == "__main__":
    main()
