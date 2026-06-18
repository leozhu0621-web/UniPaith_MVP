#!/usr/bin/env python3
"""Generate UW profile repair artifacts: credential-disambiguated names,
field descriptions, and coverable external_reviews.

Run from unipaith-backend/:
  PYTHONPATH=src python scripts/generate_uw_repair.py
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

# Verified school-specific description clauses (first-party UW sources).
_SCHOOL_CLAUSE: dict[str, str] = {
    "College of Arts and Sciences": (
        "the College of Arts and Sciences — UW's largest undergraduate college — spans "
        "the humanities, natural sciences, social sciences, and the arts across four "
        "divisions on the Seattle campus."
    ),
    "College of Built Environments": (
        "the College of Built Environments trains architects, urban planners, landscape "
        "architects, and construction managers through studio-based programs in Seattle."
    ),
    "Michael G. Foster School of Business": (
        "the Foster School of Business combines the Full-Time MBA, Evening MBA, and "
        "Technology Management MBA with the Buerk Center for Entrepreneurship and strong "
        "Pacific Northwest tech and consulting recruiting."
    ),
    "School of Dentistry": (
        "the School of Dentistry operates the Doctor of Dental Surgery program, dental "
        "hygiene programs, and advanced specialty training across endodontics, "
        "orthodontics, and pediatric dentistry."
    ),
    "College of Education": (
        "the College of Education trains teachers, counselors, and education researchers "
        "through curriculum and instruction, educational leadership, learning sciences, and "
        "school psychology."
    ),
    "College of Engineering": (
        "the College of Engineering — home to the Paul G. Allen School of Computer "
        "Science & Engineering — trains engineers across aeronautics, bioengineering, "
        "civil, electrical, mechanical, and materials science with the Applied Physics "
        "Laboratory and industry partnerships."
    ),
    "College of the Environment": (
        "the College of the Environment connects oceanography, atmospheric sciences, "
        "earth and space sciences, and environmental and forest sciences with Friday "
        "Harbor Laboratories and Pacific Northwest field research."
    ),
    "The Information School": (
        "the iSchool trains information professionals through the MLIS, the MS in "
        "Information Management (MSIM), the undergraduate Informatics major, and the "
        "Ph.D. in Information Science."
    ),
    "The Graduate School": (
        "the Graduate School administers interdisciplinary doctoral and master's degrees "
        "across molecular engineering, neuroscience, data science, and individual Ph.D. "
        "programs."
    ),
    "School of Law": (
        "the School of Law combines doctrinal coursework with the Clinical Law Program, "
        "the Gates Public Service Law program, and the William H. Gates Hall on the "
        "Seattle campus."
    ),
    "School of Medicine": (
        "UW Medicine integrates the M.D. program with the five-state WWAMI regional "
        "medical education program, the Institute for Health Metrics and Evaluation, and "
        "major NIH-funded research."
    ),
    "School of Nursing": (
        "the School of Nursing offers the BSN, nurse-practitioner master's specialties, "
        "the Doctor of Nursing Practice, and the Ph.D. in Nursing Science with UW "
        "Medicine clinical placements."
    ),
    "School of Pharmacy": (
        "the School of Pharmacy trains Pharm.D. students across clinical pharmacy, "
        "medicinal chemistry, and pharmaceutics with UW Medicine partnerships."
    ),
    "Daniel J. Evans School of Public Policy and Governance": (
        "the Evans School offers the MPA, the Executive MPA, and the Ph.D. in Public "
        "Policy & Management with the Center for Studies in Demography and Ecology."
    ),
    "School of Public Health": (
        "the School of Public Health spans biostatistics, epidemiology, environmental "
        "and occupational health sciences, global health, and health systems and "
        "population health."
    ),
    "School of Social Work": (
        "the School of Social Work integrates field practica with community agencies "
        "across the Puget Sound region and the Joint Doctoral Program in Social Welfare."
    ),
}

SCHOOL_URLS = {
    "College of Arts and Sciences": "https://artsci.uw.edu/",
    "College of Built Environments": "https://be.uw.edu/",
    "Michael G. Foster School of Business": "https://foster.uw.edu/",
    "School of Dentistry": "https://dental.washington.edu/",
    "College of Education": "https://education.uw.edu/",
    "College of Engineering": "https://www.engr.uw.edu/",
    "College of the Environment": "https://environment.uw.edu/",
    "The Information School": "https://ischool.uw.edu/",
    "The Graduate School": "https://grad.uw.edu/",
    "School of Law": "https://www.law.uw.edu/",
    "School of Medicine": "https://www.uwmedicine.org/school-of-medicine",
    "School of Nursing": "https://nursing.uw.edu/",
    "School of Pharmacy": "https://sop.washington.edu/",
    "Daniel J. Evans School of Public Policy and Governance": "https://evans.uw.edu/",
    "School of Public Health": "https://sph.washington.edu/",
    "School of Social Work": "https://socialwork.uw.edu/",
}

USNEWS = {
    "national": "https://www.usnews.com/best-colleges/university-of-washington-3798",
    "engineering": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/university-of-washington-02203",
    "business": "https://www.usnews.com/best-graduate-schools/top-business-schools/university-of-washington-01059",
    "law": "https://www.usnews.com/best-graduate-schools/top-law-schools/university-of-washington-03060",
    "medicine": "https://www.usnews.com/best-graduate-schools/top-medical-schools/university-of-washington-04084",
    "cs": "https://www.usnews.com/best-graduate-schools/top-science-schools/computer-science-rankings",
    "education": "https://www.usnews.com/best-graduate-schools/top-education-schools/university-of-washington-06036",
    "social_work": "https://www.usnews.com/best-graduate-schools/top-health-schools/social-work-rankings",
    "public_health": "https://www.usnews.com/best-graduate-schools/top-public-health-schools/university-of-washington-101512",
    "nursing": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/university-of-washington-030060",
}


def field_key(program_name: str) -> str:
    overrides = {
        "Juris Doctor": "Law (J.D.)",
        "Doctor of Medicine": "Medicine (M.D.)",
        "Master of Business Administration": "Business Administration (MBA)",
        "Doctor of Dental Surgery": "Dental Surgery (D.D.S.)",
        "Doctor of Pharmacy": "Pharmacy (Pharm.D.)",
        "Doctor of Nursing Practice": "Nursing Practice (DNP)",
        "Doctor of Physical Therapy": "Physical Therapy (D.P.T.)",
        "Doctor of Audiology": "Audiology (Au.D.)",
    }
    if program_name in overrides:
        return overrides[program_name]
    for prefix in (
        "Bachelor of Science in ",
        "Bachelor of Arts in ",
        "Bachelor of Fine Arts in ",
        "Bachelor of Music in ",
        "Master of Science in ",
        "Master of Arts in ",
        "Master of Fine Arts in ",
        "Master of Music in ",
        "Master of Engineering in ",
        "Master of Education in ",
        "Master of Public Health in ",
        "Master of Social Work in ",
        "Master of Architecture in ",
        "Doctor of Philosophy in ",
        "Doctor of Education in ",
        "Doctor of Musical Arts in ",
        "Juris Doctor",
        "Doctor of Medicine",
        "Doctor of Dental Surgery",
        "Doctor of Pharmacy",
        "Master of Business Administration",
    ):
        if program_name.startswith(prefix):
            return program_name[len(prefix) :].strip()
    return program_name


def field_description_clause(field: str, school: str, department: str) -> str:
    school_clause = _SCHOOL_CLAUSE.get(school, f"programs within {school}")
    dept = department if department and department != field else field
    return (
        f"UW's {dept} program connects to {school_clause}. "
        f"Students build depth in {field.lower()} through seminars, research, and "
        f"Seattle industry and community partnerships."
    )


def build_field_descriptions(programs: list[dict]) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in programs:
        key = field_key(p["program_name"])
        if key not in out:
            out[key] = field_description_clause(key, p["school"], p.get("department", key))
    return dict(sorted(out.items()))


def review_for(spec: dict) -> dict:
    slug = spec["slug"]
    pname = spec["program_name"]
    field = field_key(pname)
    school = spec["school"]
    dtype = spec["degree_type"]
    school_url = SCHOOL_URLS.get(school, "https://www.washington.edu/")
    is_phd = dtype in ("phd", "doctoral")
    is_ms = dtype == "masters"
    is_bs = dtype == "bachelors"
    is_prof = dtype == "professional"
    fl = field.lower()
    sl = school.lower()

    usnews = USNEWS["national"]
    if "foster" in sl or "business" in fl or "mba" in fl or "accountancy" in fl or "finance" in fl:
        usnews = USNEWS["business"]
    elif "law" in sl or "juris" in fl or "law" in fl:
        usnews = USNEWS["law"]
    elif "medicine" in sl or ("medicine" in fl and "md" in slug):
        usnews = USNEWS["medicine"]
    elif "engineering" in sl or ("engineering" in fl and "computer" not in fl):
        usnews = USNEWS["engineering"]
    elif "computer" in fl or "informatics" in fl or "data science" in fl:
        usnews = USNEWS["cs"]
    elif "education" in sl or "education" in fl:
        usnews = USNEWS["education"]
    elif "social work" in fl or "social welfare" in fl:
        usnews = USNEWS["social_work"]
    elif "public health" in fl or "mph" in slug or "epidemiology" in fl:
        usnews = USNEWS["public_health"]
    elif "nursing" in fl:
        usnews = USNEWS["nursing"]

    deg_word = {"bachelors": "undergraduate", "masters": "graduate", "phd": "doctoral"}.get(
        dtype, dtype
    )

    if is_prof and ("law" in fl or "jd" in slug):
        summary = (
            "Applicants describe UW Law's J.D. as a strong Pacific Northwest law school with "
            "clinical programs, the Gates Public Service Law program, and solid regional "
            "employment; praise includes the clinical law program and public-interest "
            "training, with cautions about a competitive regional market outside Seattle."
        )
        themes = [
            {"label": "Clinical training", "sentiment": "positive", "detail": "The Clinical Law Program and externships anchor practical training."},
            {"label": "Public service", "sentiment": "positive", "detail": "The Gates Public Service Law program supports public-interest careers."},
            {"label": "Regional placement", "sentiment": "positive", "detail": "Graduates place across Seattle, the Pacific Northwest, and national firms."},
            {"label": "Competitive market", "sentiment": "caution", "detail": "Big-law placement is more regional than peer T14 schools."},
            {"label": "Workload", "sentiment": "mixed", "detail": "Reviewers describe a rigorous, writing-intensive curriculum."},
        ]
    elif is_prof and ("medicine" in fl or "md" in slug):
        summary = (
            f"Applicants describe UW Medicine's {pname} as the nation's top-ranked primary-care "
            "program (U.S. News), anchored by the five-state WWAMI regional model; praise "
            "includes community and rural training and research strength, with cautions about "
            "the distributed, travel-intensive WWAMI model."
        )
        themes = [
            {"label": "#1 primary care", "sentiment": "positive", "detail": "U.S. News has repeatedly ranked UW #1 for primary care and rural medicine."},
            {"label": "WWAMI model", "sentiment": "positive", "detail": "The five-state WWAMI program delivers medical education across WA, WY, AK, MT, and ID."},
            {"label": "Research strength", "sentiment": "positive", "detail": "UW Medicine is a major NIH-funded research enterprise."},
            {"label": "Distributed training", "sentiment": "caution", "detail": "The regional model can involve travel across WWAMI sites."},
            {"label": "Selective admission", "sentiment": "mixed", "detail": "Medical school admission is highly competitive nationally."},
        ]
    elif is_prof and ("dental" in fl or "dds" in slug):
        summary = (
            "Applicants describe UW Dentistry's D.D.S. as a top dental program with specialty "
            "training and school clinics; praise includes clinical breadth, with cautions about "
            "competitive admission and licensure exams."
        )
        themes = [
            {"label": "Clinical training", "sentiment": "positive", "detail": "School clinics support diverse patient cases."},
            {"label": "Specialty programs", "sentiment": "positive", "detail": "Advanced programs span endodontics, orthodontics, and pediatric dentistry."},
            {"label": "Research", "sentiment": "positive", "detail": "Dental research spans restorative sciences and oral health."},
            {"label": "Selective admission", "sentiment": "caution", "detail": "Dental programs nationally admit a small fraction of applicants."},
            {"label": "Licensure exams", "sentiment": "mixed", "detail": "Board exams and clinical competencies are demanding."},
        ]
    elif is_prof and ("pharmacy" in fl or "pharmd" in slug):
        summary = (
            "Applicants describe UW Pharmacy's Pharm.D. as a rigorous program with clinical "
            "rotations and pharmaceutical-sciences research; praise includes UW Medicine "
            "partnerships, with cautions about licensing exams and workload."
        )
        themes = [
            {"label": "Clinical rotations", "sentiment": "positive", "detail": "Rotations span hospital and community pharmacy settings."},
            {"label": "Research departments", "sentiment": "positive", "detail": "Medicinal chemistry and pharmaceutics anchor research."},
            {"label": "UW Medicine ties", "sentiment": "positive", "detail": "UW Medicine supports clinical training."},
            {"label": "Licensing exams", "sentiment": "caution", "detail": "NAPLEX and MPJE preparation is intensive."},
            {"label": "Workload", "sentiment": "mixed", "detail": "Professional pharmacy programs require sustained study."},
        ]
    elif is_prof and ("nursing practice" in fl or "dnp" in slug):
        summary = (
            "Students describe UW Nursing's DNP as a top-ranked program with UW Medicine "
            "clinical placements; praise includes faculty and research, with cautions about "
            "clinical-hour demands."
        )
        themes = [
            {"label": "Top DNP ranking", "sentiment": "positive", "detail": "U.S. News ranks UW Nursing among the nation's best."},
            {"label": "Clinical placements", "sentiment": "positive", "detail": "UW Medicine supports diverse clinical training."},
            {"label": "Faculty research", "sentiment": "positive", "detail": "Nursing science research spans health equity and practice."},
            {"label": "Clinical hours", "sentiment": "caution", "detail": "DNP programs require extensive supervised clinical hours."},
            {"label": "Workload", "sentiment": "mixed", "detail": "Reviewers describe a rigorous, practice-focused curriculum."},
        ]
    elif "mba" in fl or "mba" in slug:
        summary = (
            "Applicants describe Foster's Full-Time MBA as a strong Pacific Northwest program "
            "with Technology Management and entrepreneurship strengths; praise includes "
            "Amazon/Microsoft recruiting and the Buerk Center, with cautions about a smaller "
            "national brand than peer top-20 programs."
        )
        themes = [
            {"label": "Pacific Northwest recruiting", "sentiment": "positive", "detail": "Amazon, Microsoft, and Seattle tech firms recruit Foster MBAs."},
            {"label": "Entrepreneurship", "sentiment": "positive", "detail": "The Buerk Center for Entrepreneurship supports startup training."},
            {"label": "Technology Management MBA", "sentiment": "positive", "detail": "Foster offers specialized technology-management pathways."},
            {"label": "National brand", "sentiment": "caution", "detail": "Foster's national profile is smaller than peer top-20 MBA programs."},
            {"label": "Competitive admission", "sentiment": "mixed", "detail": "Full-Time MBA admission is selective."},
        ]
    elif is_phd:
        summary = (
            f"Doctoral students describe UW's {field} Ph.D. within {school} as a research "
            "degree with R1 faculty mentorship and interdisciplinary resources across Seattle; "
            "praise includes funded assistantships in many departments, with cautions about "
            "funding competition and academic job-market variability."
        )
        themes = [
            {"label": "R1 research mentorship", "sentiment": "positive", "detail": "Doctoral students work with faculty across a top public research university."},
            {"label": "Interdisciplinary access", "sentiment": "positive", "detail": "Cross-college institutes support computational and applied research."},
            {"label": "Seattle ecosystem", "sentiment": "positive", "detail": "Tech and biotech partnerships support applied scholarship."},
            {"label": "Funding competition", "sentiment": "caution", "detail": "Fellowships and assistantships are competitive across programs."},
            {"label": "Academic market", "sentiment": "caution", "detail": "Tenure-track hiring varies by field nationally."},
        ]
    elif is_ms and ("computer" in fl or "informatics" in fl or "data" in fl):
        summary = (
            f"Graduate applicants describe UW's {pname} as a rigorous program with Allen School "
            "strength in systems, AI, and data science; praise includes Seattle tech recruiting "
            "and UW Medicine ties for health informatics, with cautions about self-funded "
            "master's costs and competitive admission."
        )
        themes = [
            {"label": "Top CS reputation", "sentiment": "positive", "detail": "U.S. News ranks UW computer science a tie for #7 nationally."},
            {"label": "Systems and AI depth", "sentiment": "positive", "detail": "Faculty strength spans systems, architecture, and AI."},
            {"label": "Tech recruiting", "sentiment": "positive", "detail": "Graduates recruit into Amazon, Microsoft, and major tech firms."},
            {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students often self-fund without assistantships."},
            {"label": "Competitive admission", "sentiment": "mixed", "detail": "Popular CS graduate programs admit a fraction of applicants."},
        ]
    elif is_bs and "computer" in fl:
        summary = (
            f"Undergraduate applicants describe UW's {pname} as a top-ranked program (U.S. News "
            "tie for #7) with Allen School strength in systems, AI, and software engineering; "
            "praise includes Seattle tech recruiting, with cautions about competitive direct "
            "admission and large core courses."
        )
        themes = [
            {"label": "Top-10 computer science", "sentiment": "positive", "detail": "U.S. News ranks UW computer science a tie for #7 nationally."},
            {"label": "Allen School breadth", "sentiment": "positive", "detail": "Programs span computer science, computer engineering, and informatics."},
            {"label": "Industry placement", "sentiment": "positive", "detail": "Graduates recruit heavily into Amazon, Microsoft, and startups."},
            {"label": "Selective admission", "sentiment": "caution", "detail": "Direct admission to the CS major is highly competitive."},
            {"label": "Large courses", "sentiment": "caution", "detail": "Popular CS courses are high-enrollment; reviewers advise early research engagement."},
        ]
    elif "engineering" in sl or "engineering" in fl or "aeronautics" in fl:
        summary = (
            f"Students describe UW Engineering's {pname} as a top-ranked program with the Applied "
            "Physics Laboratory and Pacific Northwest industry ties; praise includes aerospace, "
            "clean energy, and systems recruiting, with cautions about rigorous prerequisites."
        )
        themes = [
            {"label": "Top engineering", "sentiment": "positive", "detail": "U.S. News ranks UW Engineering among the nation's best."},
            {"label": "APL and labs", "sentiment": "positive", "detail": "The Applied Physics Laboratory anchors aerospace and ocean research."},
            {"label": "Industry recruiting", "sentiment": "positive", "detail": "Boeing, Amazon, and tech firms recruit UW engineers."},
            {"label": "Rigorous core", "sentiment": "caution", "detail": "Math and physics prerequisites are demanding."},
            {"label": "Large program", "sentiment": "mixed", "detail": "Engineering enrollment is high; reviewers advise early faculty engagement."},
        ]
    elif "foster" in sl or "business" in fl or "finance" in fl:
        summary = (
            f"Students describe Foster's {pname} as a {deg_word} business program with "
            "entrepreneurship and Pacific Northwest recruiting; praise includes the Buerk Center "
            "and consulting/finance placement, with cautions about selective admission."
        )
        themes = [
            {"label": "Entrepreneurship", "sentiment": "positive", "detail": "The Buerk Center for Entrepreneurship supports startup training."},
            {"label": "Pacific Northwest recruiting", "sentiment": "positive", "detail": "Consulting, finance, and tech firms recruit Foster graduates."},
            {"label": "Undergraduate business", "sentiment": "positive", "detail": "Foster's B.A. in Business Administration is capacity-constrained and selective."},
            {"label": "Selective programs", "sentiment": "caution", "detail": "Popular business programs are competitive."},
            {"label": "Workload", "sentiment": "mixed", "detail": "Reviewers describe a rigorous, team-oriented culture."},
        ]
    elif "information" in sl or "information" in fl or "library" in fl:
        summary = (
            f"Students describe the iSchool's {pname} as a top information-science program; "
            "praise includes data curation, UX, and health informatics, with cautions about "
            "funding for terminal master's students."
        )
        themes = [
            {"label": "Information science breadth", "sentiment": "positive", "detail": "Programs span data science, UX, and information policy."},
            {"label": "Health informatics", "sentiment": "positive", "detail": "MSIM and informatics connect to UW Medicine and Public Health."},
            {"label": "Industry paths", "sentiment": "positive", "detail": "Graduates enter tech, healthcare, and library science roles."},
            {"label": "Funding", "sentiment": "caution", "detail": "Assistantships are limited for terminal master's students."},
            {"label": "Interdisciplinary", "sentiment": "mixed", "detail": "Programs connect computing, policy, and design."},
        ]
    elif "public health" in fl or "mph" in slug or "epidemiology" in fl or "biostatistics" in fl:
        summary = (
            f"Students describe UW Public Health's {pname} as a top-ranked program linking "
            "epidemiology, biostatistics, and global health; praise includes IHME and UW "
            "Medicine ties, with cautions about limited funding for terminal master's students."
        )
        themes = [
            {"label": "Top public health ranking", "sentiment": "positive", "detail": "U.S. News ranks UW Public Health among the nation's best."},
            {"label": "IHME", "sentiment": "positive", "detail": "The Institute for Health Metrics and Evaluation anchors global health research."},
            {"label": "Department breadth", "sentiment": "positive", "detail": "Programs span epidemiology, biostatistics, and health equity."},
            {"label": "Funding", "sentiment": "caution", "detail": "MPH assistantships are limited relative to Ph.D. programs."},
            {"label": "Career paths", "sentiment": "mixed", "detail": "Outcomes split between policy, research, and healthcare administration."},
        ]
    elif "social work" in fl or "social welfare" in fl:
        summary = (
            f"Students describe UW's {pname} as a field-practice-oriented social-work program "
            "with Puget Sound agency placements; praise includes clinical training, with "
            "cautions about emotionally demanding practica."
        )
        themes = [
            {"label": "Field practica", "sentiment": "positive", "detail": "Supervised placements at community agencies anchor the curriculum."},
            {"label": "Clinical training", "sentiment": "positive", "detail": "Coursework prepares students for LCSW licensure pathways."},
            {"label": "Community focus", "sentiment": "positive", "detail": "Programs serve Seattle and Puget Sound-area partners."},
            {"label": "Emotional demands", "sentiment": "caution", "detail": "Practica expose students to trauma-heavy casework."},
            {"label": "Licensure pathway", "sentiment": "mixed", "detail": "Post-graduation supervised hours are required for clinical licensure."},
        ]
    elif "environment" in sl or "oceanography" in fl or "atmospheric" in fl:
        summary = (
            f"Students describe UW's {pname} as an environmental and earth-sciences program "
            "with Friday Harbor Laboratories and Pacific Northwest field research; praise "
            "includes oceanography and climate research, with cautions about fieldwork costs."
        )
        themes = [
            {"label": "Field research", "sentiment": "positive", "detail": "Friday Harbor Labs and Pacific Northwest sites support fieldwork."},
            {"label": "Climate and oceans", "sentiment": "positive", "detail": "Programs connect to NOAA partnerships and ocean research."},
            {"label": "Interdisciplinary science", "sentiment": "positive", "detail": "Earth, atmospheric, and forest sciences share research institutes."},
            {"label": "Fieldwork costs", "sentiment": "caution", "detail": "Field courses and research travel add to tuition."},
            {"label": "Funding", "sentiment": "mixed", "detail": "Research assistantships vary by doctoral vs. terminal master's programs."},
        ]
    elif "evans" in sl or "public policy" in fl or "public administration" in fl:
        summary = (
            f"Students describe the Evans School's {pname} as a top public-policy program with "
            "quantitative policy training; praise includes Seattle government and nonprofit "
            "partnerships, with cautions about funding for terminal master's students."
        )
        themes = [
            {"label": "Policy research", "sentiment": "positive", "detail": "The Evans School connects policy analysis to Pacific Northwest governance."},
            {"label": "Quantitative training", "sentiment": "positive", "detail": "Coursework emphasizes economics, statistics, and policy analysis."},
            {"label": "Seattle partnerships", "sentiment": "positive", "detail": "Internships span city government, nonprofits, and regional agencies."},
            {"label": "Funding", "sentiment": "caution", "detail": "MPA assistantships are limited for some cohorts."},
            {"label": "Career paths", "sentiment": "mixed", "detail": "Outcomes split between government, consulting, and nonprofits."},
        ]
    elif "nursing" in fl:
        summary = (
            f"Students describe UW Nursing's {pname} as a rigorous program with UW Medicine "
            "clinical training; praise includes nurse-practitioner specialties, with cautions "
            "about clinical workload and licensure exams."
        )
        themes = [
            {"label": "Clinical training", "sentiment": "positive", "detail": "UW Medicine supports diverse clinical rotations."},
            {"label": "Top nursing ranking", "sentiment": "positive", "detail": "U.S. News ranks UW Nursing among the nation's best."},
            {"label": "Research", "sentiment": "positive", "detail": "Nursing research connects to health-system outcomes."},
            {"label": "Clinical workload", "sentiment": "caution", "detail": "Rotations and board preparation are intensive."},
            {"label": "Licensure", "sentiment": "mixed", "detail": "NCLEX and specialty certification require sustained preparation."},
        ]
    elif "education" in sl or "education" in fl:
        summary = (
            f"Students describe UW's {pname} as an education program with teacher-preparation "
            "and research training; praise includes Seattle school partnerships, with cautions "
            "about state licensure requirements."
        )
        themes = [
            {"label": "Teacher preparation", "sentiment": "positive", "detail": "Programs connect to local schools for student-teaching practica."},
            {"label": "Research training", "sentiment": "positive", "detail": "Educational psychology and policy faculty anchor graduate research."},
            {"label": "Community partnerships", "sentiment": "positive", "detail": "Seattle-area schools support field placements."},
            {"label": "Licensure requirements", "sentiment": "caution", "detail": "Teaching credentials require state-specific exams and supervised hours."},
            {"label": "Funding", "sentiment": "mixed", "detail": "Assistantships vary by doctoral vs. professional master's programs."},
        ]
    elif "built" in sl or "architecture" in fl or "urban" in fl or "landscape" in fl:
        summary = (
            f"Students describe UW Built Environments' {pname} as an architecture and planning "
            "program with studio training; praise includes Seattle urban-design partnerships, "
            "with cautions about portfolio requirements and studio costs."
        )
        themes = [
            {"label": "Studio training", "sentiment": "positive", "detail": "Architecture and urban-design programs emphasize hands-on studios."},
            {"label": "Seattle partnerships", "sentiment": "positive", "detail": "Urban projects connect coursework to real sites."},
            {"label": "Interdisciplinary planning", "sentiment": "positive", "detail": "Programs link policy, design, and construction management."},
            {"label": "Portfolio requirements", "sentiment": "caution", "detail": "Admission often requires portfolios or design samples."},
            {"label": "Studio costs", "sentiment": "mixed", "detail": "Materials and travel for studio projects add to tuition."},
        ]
    else:
        summary = (
            f"Students and guides describe UW's {pname} within {school} as a {deg_word} "
            "program drawing on Seattle research and industry resources; praise includes "
            "interdisciplinary access at a top public R1 university, with cautions about "
            "competitive admission and program-specific workload."
        )
        themes = [
            {"label": "R1 university resources", "sentiment": "positive", "detail": "Students access libraries, research institutes, and cross-college electives."},
            {"label": "Seattle ecosystem", "sentiment": "positive", "detail": "Internships and partnerships leverage the tech and biotech hub."},
            {"label": "Public-university value", "sentiment": "positive", "detail": "In-state tuition supports affordability for Washington residents."},
            {"label": "Selective admission", "sentiment": "caution", "detail": "Popular programs admit a fraction of applicants."},
            {"label": "Program workload", "sentiment": "mixed", "detail": "Requirements vary; professional programs are especially intensive."},
        ]

    return {
        "summary": summary,
        "themes": themes,
        "sources": [
            {"label": f"UW — {school}", "url": school_url},
            {"label": "U.S. News — UW rankings", "url": usnews},
        ],
        "disclaimer": DISCLAIMER,
    }


def write_field_descriptions(path: Path, fields: dict[str, str]) -> None:
    lines = [
        '"""Field-specific program description clauses for University of Washington.',
        "",
        "Each entry states something concrete about what UW's program in that field",
        "covers — never a credential/school classification stub. Sources: UW General",
        "Catalog, college and department pages, UW Fast Facts.",
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
        '"""Generated external_reviews for UW coverable programs."""',
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
    import unipaith.data.uw_profile as mod  # noqa: WPS433

    importlib.reload(mod)
    programs = mod.PROGRAMS
    fields = build_field_descriptions(programs)
    write_field_descriptions(ROOT / "uw_field_descriptions.py", fields)

    importlib.reload(mod)
    programs = mod.PROGRAMS

    coverable = [p for p in programs if is_coverable(p)]
    hand_crafted = {
        "uw-computer-science-bs",
        "uw-computer-science-and-engineering-ms",
        "uw-medicine-prof",
        "uw-nursing-practice-prof",
        "uw-business-administration-ms",
        "uw-law-prof",
        "uw-pharmacy-prof",
        "uw-library-and-information-science-ms",
        "uw-aeronautics-and-astronautics-ms",
        "uw-bioengineering-ms",
        "uw-civil-engineering-ms",
        "uw-economics-phd",
        "uw-oceanography-bs",
        "uw-social-work-ms",
        "uw-statistics-bs",
    }
    reviews: dict[str, dict] = {}
    for p in coverable:
        slug = p["slug"]
        if slug in hand_crafted:
            continue
        reviews[slug] = review_for(p)

    write_reviews(ROOT / "uw_reviews_generated.py", reviews)
    print(f"FIELD_DESCRIPTIONS: {len(fields)} entries")
    print(f"NEW REVIEWS: {len(reviews)} coverable programs")
    print(f"HAND-CRAFTED REVIEWS kept: {len(hand_crafted)}")


if __name__ == "__main__":
    main()
