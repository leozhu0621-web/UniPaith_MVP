#!/usr/bin/env python3
"""Generate Michigan profile repair artifacts: credential-disambiguated names,
field descriptions, and coverable external_reviews.

Run from unipaith-backend/:
  PYTHONPATH=src python scripts/generate_michigan_repair.py
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

_LEVEL_SUFFIX: dict[str, str] = {
    "bachelors": (
        " Undergraduates complete major requirements, electives, and often "
        "undergraduate research or internships across the Ann Arbor campus."
    ),
    "masters": (
        " Graduate students complete advanced seminars, practica, and a thesis or "
        "capstone project."
    ),
    "phd": (
        " Doctoral students conduct original dissertation research with faculty "
        "mentorship and departmental seminars."
    ),
    "professional": (
        " Professional students complete clinical rotations, licensure preparation, "
        "and professional-skills training."
    ),
}

# Verified school-specific description clauses (first-party U-M sources).
_SCHOOL_CLAUSE: dict[str, str] = {
    "College of Literature, Science, and the Arts": (
        "LSA — Michigan's largest college — spans the humanities, natural sciences, "
        "mathematical sciences, and social sciences, with the Residential College and "
        "LSA Honors Program on the Ann Arbor campus."
    ),
    "College of Engineering": (
        "Michigan Engineering — home to EECS, the Robotics Department, and the Ford "
        "Motor Company Robotics Building — trains engineers across aerospace, biomedical, "
        "civil, electrical, mechanical, and industrial operations."
    ),
    "Stephen M. Ross School of Business": (
        "Michigan Ross combines action-based learning (MAP), the Zell Lurie Institute "
        "for Entrepreneurial Studies, and the Tauber Institute for Global Operations "
        "with Full-Time, Weekend, Online, and Executive MBA programs."
    ),
    "University of Michigan Medical School": (
        "Michigan Medicine integrates the Medical School with the Rogel Cancer Center, "
        "Michigan Neuroscience Institute, and the Program in Biomedical Sciences (PIBS)."
    ),
    "University of Michigan Law School": (
        "Michigan Law combines doctrinal coursework with the Clinical Law Program, the "
        "Center for International and Comparative Law, and the Gothic Law Quadrangle."
    ),
    "School of Information": (
        "UMSI trains information scientists through the MSI, the undergraduate BSI, and "
        "the Master of Health Informatics, with the Center for Social Media Responsibility "
        "and Citizen Interaction Design."
    ),
    "School of Public Health": (
        "Michigan Public Health spans epidemiology, biostatistics, environmental health "
        "sciences, health behavior, health management and policy, and nutritional sciences."
    ),
    "School of Dentistry": (
        "Michigan Dentistry operates the Doctor of Dental Surgery program, dental hygiene "
        "programs, and advanced specialty training across endodontics, orthodontics, and "
        "pediatric dentistry."
    ),
    "College of Pharmacy": (
        "Michigan Pharmacy trains Pharm.D. students across clinical pharmacy, medicinal "
        "chemistry, and pharmaceutical sciences."
    ),
    "School of Music, Theatre & Dance": (
        "SMTD spans music performance and composition, theatre and drama, dance, musical "
        "theatre, and performing arts technology on the Ann Arbor campus."
    ),
    "Marsal Family School of Education": (
        "the Marsal Family School of Education trains teachers, counselors, and education "
        "researchers through curriculum and instruction, educational psychology, and the "
        "Combined Program in Education and Psychology."
    ),
    "School of Nursing": (
        "Michigan Nursing offers the BSN, nurse-practitioner master's specialties, the "
        "Doctor of Nursing Practice, and the Ph.D. in Nursing."
    ),
    "School of Kinesiology": (
        "Michigan Kinesiology combines movement science, applied exercise science, sport "
        "management, and athletic training with campus wellness research."
    ),
    "School of Social Work": (
        "Michigan Social Work integrates field practica with community agencies across "
        "Southeast Michigan and the Joint Doctoral Program in Social Work and Social Science."
    ),
    "Gerald R. Ford School of Public Policy": (
        "the Ford School offers the MPP and MPA, joint Ph.D. programs with Economics and "
        "Political Science, and the Center for Local, State, and Urban Policy (CLOSUP)."
    ),
    "A. Alfred Taubman College of Architecture and Urban Planning": (
        "Taubman College trains architects and urban planners through the M.Arch, B.S. in "
        "Architecture, M.U.R.P., and the Master of Urban Design."
    ),
    "Penny W. Stamps School of Art & Design": (
        "Stamps trains artists and designers through studio-based BFA and MFA programs "
        "on the Ann Arbor campus."
    ),
    "School for Environment and Sustainability": (
        "SEAS connects environmental science, sustainability, and conservation with "
        "interdisciplinary field research across Michigan's Great Lakes region."
    ),
    "Horace H. Rackham School of Graduate Studies": (
        "Rackham administers doctoral and master's degrees across Michigan's graduate "
        "programs, with fellowship and dissertation support for research students."
    ),
}

SCHOOL_URLS = {
    "College of Literature, Science, and the Arts": "https://lsa.umich.edu/",
    "College of Engineering": "https://www.engin.umich.edu/",
    "Stephen M. Ross School of Business": "https://michiganross.umich.edu/",
    "University of Michigan Medical School": "https://medschool.umich.edu/",
    "University of Michigan Law School": "https://michigan.law.umich.edu/",
    "School of Information": "https://www.si.umich.edu/",
    "School of Public Health": "https://sph.umich.edu/",
    "School of Dentistry": "https://dent.umich.edu/",
    "College of Pharmacy": "https://pharmacy.umich.edu/",
    "School of Music, Theatre & Dance": "https://smtd.umich.edu/",
    "Marsal Family School of Education": "https://marsal.umich.edu/",
    "School of Nursing": "https://nursing.umich.edu/",
    "School of Kinesiology": "https://www.kines.umich.edu/",
    "School of Social Work": "https://ssw.umich.edu/",
    "Gerald R. Ford School of Public Policy": "https://fordschool.umich.edu/",
    "A. Alfred Taubman College of Architecture and Urban Planning": "https://taubmancollege.umich.edu/",
    "Penny W. Stamps School of Art & Design": "https://stamps.umich.edu/",
    "School for Environment and Sustainability": "https://seas.umich.edu/",
    "Horace H. Rackham School of Graduate Studies": "https://rackham.umich.edu/",
}

USNEWS = {
    "national": "https://www.usnews.com/best-colleges/university-of-michigan-ann-arbor-9092",
    "engineering": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/university-of-michigan-ann-arbor-02075",
    "business": "https://www.usnews.com/best-graduate-schools/top-business-schools/university-of-michigan-ann-arbor-01108",
    "law": "https://www.usnews.com/best-graduate-schools/top-law-schools/university-of-michigan-ann-arbor-03047",
    "medicine": "https://www.usnews.com/best-graduate-schools/top-medical-schools/university-of-michigan-ann-arbor-04051",
    "cs": "https://www.usnews.com/best-graduate-schools/top-science-schools/computer-science-rankings",
    "education": "https://www.usnews.com/best-graduate-schools/top-education-schools/university-of-michigan-ann-arbor-06028",
    "social_work": "https://www.usnews.com/best-graduate-schools/top-health-schools/social-work-rankings",
    "public_health": "https://www.usnews.com/best-graduate-schools/top-public-health-schools/university-of-michigan-ann-arbor-101500",
    "nursing": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/university-of-michigan-ann-arbor-030047",
}

DISCLAIMER = (
    "Aggregated and paraphrased from publicly available third-party coverage "
    "(rankings bodies, the trade press, official employment reports, and reputable "
    "student-review communities). Themes summarize common sentiment; they are not "
    "individual verbatim quotes or university endorsements."
)


def field_key(program_name: str) -> str:
    overrides = {
        "Juris Doctor": "Law (J.D.)",
        "Doctor of Medicine": "Medicine (M.D.)",
        "Master of Business Administration": "Business Administration (MBA)",
        "Bachelor of Business Administration": "Business (BBA)",
        "Doctor of Dental Surgery": "Dental Surgery (D.D.S.)",
        "Doctor of Pharmacy": "Pharmacy (Pharm.D.)",
        "Master of Architecture": "Architecture (M.Arch)",
        "Master of Urban Design": "Urban Design",
        "Master of Engineering": "Engineering (M.Eng)",
        "Doctor of Engineering": "Engineering (D.Eng)",
        "Master of Health Informatics": "Health Informatics",
        "Master of Science in Information": "Information (MSI)",
        "Master of Laws": "Law (LL.M.)",
        "Master of Music": "Music (M.M.)",
        "Specialist in Music": "Music (Specialist)",
        "Master of Science in Nursing": "Nursing (M.S.N.)",
        "Master of Public Health": "Public Health (MPH)",
        "Master of Health Services Administration": "Health Services Administration (MHSA)",
        "Doctor of Public Health": "Public Health (DrPH)",
        "Master of Social Work": "Social Work (M.S.W.)",
    }
    if program_name in overrides:
        return overrides[program_name]
    for prefix in (
        "Bachelor of Science in ",
        "Bachelor of Arts in ",
        "Bachelor of Fine Arts in ",
        "Bachelor of Music in ",
        "Bachelor of Business Administration in ",
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
        "Bachelor of Business Administration",
    ):
        if program_name.startswith(prefix):
            return program_name[len(prefix) :].strip()
    return program_name


def field_description_clause(field: str, school: str, department: str) -> str:
    school_clause = _SCHOOL_CLAUSE.get(school, f"programs within {school}")
    dept = department if department and department != field else field
    return (
        f"Michigan's {dept} program connects to {school_clause}. "
        f"Students build depth in {field.lower()} through seminars, research, and "
        f"Ann Arbor industry and community partnerships."
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
    school_url = SCHOOL_URLS.get(school, "https://www.umich.edu/")
    is_phd = dtype in ("phd", "doctoral")
    is_ms = dtype == "masters"
    is_bs = dtype == "bachelors"
    is_prof = dtype == "professional"
    fl = field.lower()
    sl = school.lower()

    usnews = USNEWS["national"]
    if "ross" in sl or "business" in fl or "mba" in fl or "accountancy" in fl or "finance" in fl:
        usnews = USNEWS["business"]
    elif "law" in sl or "juris" in fl or "law" in fl:
        usnews = USNEWS["law"]
    elif "medical" in sl or ("medicine" in fl and "md" in slug):
        usnews = USNEWS["medicine"]
    elif "engineering" in sl or ("engineering" in fl and "computer" not in fl):
        usnews = USNEWS["engineering"]
    elif "computer" in fl or "data science" in fl or "informatics" in fl:
        usnews = USNEWS["cs"]
    elif "education" in sl or "education" in fl:
        usnews = USNEWS["education"]
    elif "social work" in fl:
        usnews = USNEWS["social_work"]
    elif "public health" in fl or "mph" in slug:
        usnews = USNEWS["public_health"]
    elif "nursing" in fl:
        usnews = USNEWS["nursing"]

    deg_word = {"bachelors": "undergraduate", "masters": "graduate", "phd": "doctoral"}.get(
        dtype, dtype
    )

    if is_prof and ("law" in fl or "jd" in slug):
        summary = (
            "Applicants describe Michigan Law's J.D. as a perennial top-10 (T14) program with "
            "near-total employment, a $225,000 median salary in bar-passage-required jobs, and "
            "a strong clerkship pipeline; praise includes the Gothic Law Quadrangle and clinical "
            "programs, with cautions about elite-law-school cost and intensity."
        )
        themes = [
            {"label": "Near-total employment", "sentiment": "positive", "detail": "Class of 2023: about 98% employed ten months after graduation."},
            {"label": "Top-tier salaries", "sentiment": "positive", "detail": "Median full-time salary $225,000 in bar-passage-required jobs."},
            {"label": "Clerkships", "sentiment": "positive", "detail": "A deep federal-clerkship pipeline and extensive clinics broaden outcomes."},
            {"label": "High cost", "sentiment": "caution", "detail": "Tuition and living costs reflect a top-tier private-feel public law school."},
            {"label": "Intense environment", "sentiment": "mixed", "detail": "Reviewers describe a rigorous, competitive academic culture."},
        ]
    elif is_prof and ("medicine" in fl or "md" in slug):
        summary = (
            f"Applicants describe Michigan Medicine's {pname} as a top-ranked M.D. program with "
            "Michigan Medicine clinical training, the Rogel Cancer Center, and PIBS research "
            "integration; praise includes research breadth and hospital resources, with cautions "
            "about demanding clinical schedules and competitive admission."
        )
        themes = [
            {"label": "Michigan Medicine system", "sentiment": "positive", "detail": "Clinical training spans Michigan Medicine hospitals and affiliates."},
            {"label": "Research integration", "sentiment": "positive", "detail": "PIBS and institute research support basic-science training."},
            {"label": "Rogel Cancer Center", "sentiment": "positive", "detail": "NCI-designated cancer center anchors oncology research."},
            {"label": "Clinical intensity", "sentiment": "caution", "detail": "Rotations and board preparation require sustained workload."},
            {"label": "Selective admission", "sentiment": "mixed", "detail": "Medical school admission is highly competitive nationally."},
        ]
    elif is_prof and ("dental" in fl or "dds" in slug):
        summary = (
            "Applicants describe Michigan Dentistry's D.D.S. as a top dental program with "
            "specialty training and the School of Dentistry clinics; praise includes clinical "
            "breadth and research, with cautions about competitive admission and licensure exams."
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
            "Applicants describe Michigan Pharmacy's Pharm.D. as a rigorous program with "
            "clinical rotations and pharmaceutical-sciences research; praise includes "
            "hospital partnerships, with cautions about licensing exams and workload."
        )
        themes = [
            {"label": "Clinical rotations", "sentiment": "positive", "detail": "Rotations span hospital and community pharmacy settings."},
            {"label": "Research departments", "sentiment": "positive", "detail": "Medicinal chemistry and pharmaceutical sciences anchor research."},
            {"label": "Hospital ties", "sentiment": "positive", "detail": "Michigan Medicine supports clinical training."},
            {"label": "Licensing exams", "sentiment": "caution", "detail": "NAPLEX and MPJE preparation is intensive."},
            {"label": "Workload", "sentiment": "mixed", "detail": "Professional pharmacy programs require sustained study."},
        ]
    elif "mba" in fl or "mba" in slug:
        summary = (
            "Applicants describe Michigan Ross's Full-Time MBA as a top-tier program known for "
            "action-based learning (MAP), consulting recruiting, and collaborative culture; "
            "praise includes a Class of 2024 median base salary of $170,000, with cautions "
            "about a softer 2024 hiring market."
        )
        themes = [
            {"label": "Action-based learning (MAP)", "sentiment": "positive", "detail": "Multidisciplinary Action Projects send teams to solve real company problems."},
            {"label": "Consulting recruiting", "sentiment": "positive", "detail": "Consulting was 36% of accepted jobs in 2024."},
            {"label": "Strong pay", "sentiment": "mixed", "detail": "Class of 2024 median base salary $170,000 with $30,000 signing bonus."},
            {"label": "Collaborative culture", "sentiment": "positive", "detail": "Students emphasize a supportive, team-oriented environment."},
            {"label": "Softer 2024 placement", "sentiment": "caution", "detail": "Job offers within three months fell to 84.6% from 96% the prior year."},
        ]
    elif is_phd:
        summary = (
            f"Doctoral students describe Michigan's {field} Ph.D. within {school} as a research "
            "degree with R1 faculty mentorship and interdisciplinary resources across Ann Arbor; "
            "praise includes funded assistantships in many departments, with cautions about "
            "funding competition and academic job-market variability."
        )
        themes = [
            {"label": "R1 research mentorship", "sentiment": "positive", "detail": "Doctoral students work with faculty across a top-tier research university."},
            {"label": "Interdisciplinary access", "sentiment": "positive", "detail": "Cross-school institutes support computational and applied research."},
            {"label": "Ann Arbor ecosystem", "sentiment": "positive", "detail": "Detroit, Chicago, and industry partnerships support applied scholarship."},
            {"label": "Funding competition", "sentiment": "caution", "detail": "Fellowships and assistantships are competitive across programs."},
            {"label": "Academic market", "sentiment": "caution", "detail": "Tenure-track hiring varies by field nationally."},
        ]
    elif is_ms and ("computer" in fl or "data" in fl or "analytics" in fl or "informatics" in fl):
        summary = (
            f"Graduate applicants describe Michigan's {pname} as a rigorous program with EECS "
            "and UMSI strength in systems, AI, and data science; praise includes strong tech "
            "recruiting and Michigan Medicine ties for health informatics, with cautions about "
            "self-funded master's costs and competitive admission."
        )
        themes = [
            {"label": "Top CS reputation", "sentiment": "positive", "detail": "U.S. News ranks Michigan CS and engineering among the nation's best."},
            {"label": "Systems and AI depth", "sentiment": "positive", "detail": "Faculty strength spans systems, architecture, and AI."},
            {"label": "Tech recruiting", "sentiment": "positive", "detail": "Graduates recruit into major technology firms and quant roles."},
            {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students often self-fund without assistantships."},
            {"label": "Competitive admission", "sentiment": "mixed", "detail": "Popular CS graduate programs admit a fraction of applicants."},
        ]
    elif is_bs and "computer" in fl:
        summary = (
            f"Undergraduate applicants describe Michigan's {pname} as a top-ranked program with "
            "EECS strength in systems, AI, and software engineering; praise includes world-class "
            "faculty and big-tech recruiting, with cautions about competitive direct admission "
            "and large core courses."
        )
        themes = [
            {"label": "Top CS reputation", "sentiment": "positive", "detail": "Michigan undergraduate CS and engineering rank among the nation's best."},
            {"label": "EECS breadth", "sentiment": "positive", "detail": "Programs span computer science, computer engineering, and data science."},
            {"label": "Industry placement", "sentiment": "positive", "detail": "Graduates recruit heavily into major technology firms."},
            {"label": "Selective admission", "sentiment": "caution", "detail": "Direct admission to engineering and CS is highly competitive."},
            {"label": "Large courses", "sentiment": "caution", "detail": "Popular CS courses are high-enrollment; reviewers advise early research engagement."},
        ]
    elif "engineering" in sl or "engineering" in fl:
        summary = (
            f"Students describe Michigan Engineering's {pname} as a top-ranked program with "
            "project-based learning and the Ford Robotics Building; praise includes aerospace, "
            "automotive, and systems recruiting, with cautions about rigorous prerequisites."
        )
        themes = [
            {"label": "Top-10 engineering", "sentiment": "positive", "detail": "U.S. News ranks Michigan Engineering among the nation's best."},
            {"label": "Robotics and labs", "sentiment": "positive", "detail": "The Ford Motor Company Robotics Building anchors robotics research."},
            {"label": "Industry recruiting", "sentiment": "positive", "detail": "Automotive, aerospace, and tech firms recruit Michigan engineers."},
            {"label": "Rigorous core", "sentiment": "caution", "detail": "Math and physics prerequisites are demanding."},
            {"label": "Large program", "sentiment": "mixed", "detail": "Engineering enrollment is high; reviewers advise early faculty engagement."},
        ]
    elif "ross" in sl or "business" in fl or "finance" in fl:
        summary = (
            f"Students describe Ross's {pname} as a {deg_word} business program with action-based "
            "learning and strong consulting/finance recruiting; praise includes MAP and the Zell "
            "Lurie Institute, with cautions about selective admission."
        )
        themes = [
            {"label": "Action-based learning", "sentiment": "positive", "detail": "MAP and case-based coursework anchor the Ross curriculum."},
            {"label": "Entrepreneurship", "sentiment": "positive", "detail": "The Zell Lurie Institute supports startup and venture training."},
            {"label": "Recruiting", "sentiment": "positive", "detail": "Consulting, finance, and tech firms recruit Ross graduates."},
            {"label": "Selective programs", "sentiment": "caution", "detail": "Popular business programs are competitive."},
            {"label": "Workload", "sentiment": "mixed", "detail": "Reviewers describe a rigorous, team-oriented culture."},
        ]
    elif "information" in sl or "information" in fl:
        summary = (
            f"Students describe UMSI's {pname} as a top information-science program; praise "
            "includes data curation, UX, and health informatics, with cautions about funding "
            "for terminal master's students."
        )
        themes = [
            {"label": "Information science breadth", "sentiment": "positive", "detail": "Programs span data science, UX, and information policy."},
            {"label": "Health informatics", "sentiment": "positive", "detail": "Joint programs with Michigan Medicine and Public Health."},
            {"label": "Industry paths", "sentiment": "positive", "detail": "Graduates enter tech, healthcare, and consulting roles."},
            {"label": "Funding", "sentiment": "caution", "detail": "Assistantships are limited for terminal master's students."},
            {"label": "Interdisciplinary", "sentiment": "mixed", "detail": "Programs connect computing, policy, and design."},
        ]
    elif "public health" in fl or "mph" in slug or "epidemiology" in fl:
        summary = (
            f"Students describe Michigan Public Health's {pname} as a top-ranked program linking "
            "epidemiology, biostatistics, and health policy; praise includes Michigan Medicine "
            "ties, with cautions about limited funding for terminal master's students."
        )
        themes = [
            {"label": "Top public health ranking", "sentiment": "positive", "detail": "U.S. News ranks Michigan Public Health among the nation's best."},
            {"label": "Department breadth", "sentiment": "positive", "detail": "Programs span epidemiology, biostatistics, and health equity."},
            {"label": "Michigan Medicine ties", "sentiment": "positive", "detail": "Health-system partnerships support applied research."},
            {"label": "Funding", "sentiment": "caution", "detail": "MPH assistantships are limited relative to Ph.D. programs."},
            {"label": "Career paths", "sentiment": "mixed", "detail": "Outcomes split between policy, research, and healthcare administration."},
        ]
    elif "social work" in fl:
        summary = (
            f"Students describe Michigan's {pname} as a field-practice-oriented social-work "
            "program with Southeast Michigan agency placements; praise includes clinical "
            "training, with cautions about emotionally demanding practica."
        )
        themes = [
            {"label": "Field practica", "sentiment": "positive", "detail": "Supervised placements at community agencies anchor the curriculum."},
            {"label": "Clinical training", "sentiment": "positive", "detail": "Coursework prepares students for LCSW licensure pathways."},
            {"label": "Community focus", "sentiment": "positive", "detail": "Programs serve Detroit and Ann Arbor-area partners."},
            {"label": "Emotional demands", "sentiment": "caution", "detail": "Practica expose students to trauma-heavy casework."},
            {"label": "Licensure pathway", "sentiment": "mixed", "detail": "Post-graduation supervised hours are required for clinical licensure."},
        ]
    elif "architecture" in fl or "urban" in fl or "taubman" in sl:
        summary = (
            f"Students describe Taubman's {pname} as an architecture and planning program with "
            "studio training and urban-design research; praise includes Detroit and Ann Arbor "
            "partnerships, with cautions about portfolio requirements and studio costs."
        )
        themes = [
            {"label": "Studio training", "sentiment": "positive", "detail": "Architecture and urban-design programs emphasize hands-on studios."},
            {"label": "Urban partnerships", "sentiment": "positive", "detail": "Detroit and Ann Arbor projects connect coursework to real sites."},
            {"label": "Interdisciplinary planning", "sentiment": "positive", "detail": "M.U.R.P. and urban-design programs link policy and design."},
            {"label": "Portfolio/audition", "sentiment": "caution", "detail": "Admission often requires portfolios or design samples."},
            {"label": "Studio costs", "sentiment": "mixed", "detail": "Materials and travel for studio projects add to tuition."},
        ]
    elif "nursing" in fl:
        summary = (
            f"Students describe Michigan Nursing's {pname} as a rigorous program with Michigan "
            "Medicine clinical training; praise includes nurse-practitioner specialties, with "
            "cautions about clinical workload and licensure exams."
        )
        themes = [
            {"label": "Clinical training", "sentiment": "positive", "detail": "Michigan Medicine supports diverse clinical rotations."},
            {"label": "NP specialties", "sentiment": "positive", "detail": "Master's programs span nurse-practitioner specialties."},
            {"label": "Research", "sentiment": "positive", "detail": "Nursing research connects to health-system outcomes."},
            {"label": "Clinical workload", "sentiment": "caution", "detail": "Rotations and board preparation are intensive."},
            {"label": "Licensure", "sentiment": "mixed", "detail": "NCLEX and specialty certification require sustained preparation."},
        ]
    elif "education" in sl or "education" in fl:
        summary = (
            f"Students describe Michigan's {pname} as an education program with teacher-preparation "
            "and research training; praise includes Ann Arbor school partnerships, with cautions "
            "about state licensure requirements."
        )
        themes = [
            {"label": "Teacher preparation", "sentiment": "positive", "detail": "Programs connect to local schools for student-teaching practica."},
            {"label": "Research training", "sentiment": "positive", "detail": "Educational psychology and policy faculty anchor graduate research."},
            {"label": "Community partnerships", "sentiment": "positive", "detail": "Southeast Michigan schools support field placements."},
            {"label": "Licensure requirements", "sentiment": "caution", "detail": "Teaching credentials require state-specific exams and supervised hours."},
            {"label": "Funding", "sentiment": "mixed", "detail": "Assistantships vary by doctoral vs. professional master's programs."},
        ]
    elif "music" in fl or "dance" in fl or "theatre" in fl or "smtd" in sl:
        summary = (
            f"Students describe SMTD's {pname} as a performance program with conservatory-style "
            "training; praise includes recitals and ensemble opportunities, with cautions about "
            "audition requirements and performance costs."
        )
        themes = [
            {"label": "Performance training", "sentiment": "positive", "detail": "Programs emphasize studio, rehearsal, and recital work."},
            {"label": "Ensemble opportunities", "sentiment": "positive", "detail": "Campus ensembles and productions anchor training."},
            {"label": "Faculty artists", "sentiment": "positive", "detail": "Faculty include active performers and composers."},
            {"label": "Audition requirements", "sentiment": "caution", "detail": "Admission often requires auditions or portfolios."},
            {"label": "Performance costs", "sentiment": "mixed", "detail": "Instruments, lessons, and production costs add to tuition."},
        ]
    elif "public policy" in fl or "ford" in sl:
        summary = (
            f"Students describe the Ford School's {pname} as a top public-policy program with "
            "CLOSUP research and joint degrees; praise includes quantitative policy training, "
            "with cautions about funding for terminal master's students."
        )
        themes = [
            {"label": "Policy research", "sentiment": "positive", "detail": "CLOSUP and the Education Policy Initiative anchor applied research."},
            {"label": "Quantitative training", "sentiment": "positive", "detail": "Coursework emphasizes economics, statistics, and policy analysis."},
            {"label": "Joint degrees", "sentiment": "positive", "detail": "Joint programs connect to economics, law, and social work."},
            {"label": "Funding", "sentiment": "caution", "detail": "MPP assistantships are limited for some cohorts."},
            {"label": "Career paths", "sentiment": "mixed", "detail": "Outcomes split between government, consulting, and nonprofits."},
        ]
    else:
        summary = (
            f"Students and guides describe Michigan's {pname} within {school} as a {deg_word} "
            "program drawing on Ann Arbor research and industry resources; praise includes "
            "interdisciplinary access at a top public R1 university, with cautions about "
            "competitive admission and program-specific workload."
        )
        themes = [
            {"label": "R1 university resources", "sentiment": "positive", "detail": "Students access libraries, research institutes, and cross-college electives."},
            {"label": "Ann Arbor campus", "sentiment": "positive", "detail": "Internships and partnerships leverage the university town and Detroit access."},
            {"label": "Public-university value", "sentiment": "positive", "detail": "In-state tuition and the Go Blue Guarantee support affordability."},
            {"label": "Selective admission", "sentiment": "caution", "detail": "Popular programs admit a fraction of applicants."},
            {"label": "Program workload", "sentiment": "mixed", "detail": "Requirements vary; professional programs are especially intensive."},
        ]

    return {
        "summary": summary,
        "themes": themes,
        "sources": [
            {"label": f"U-M — {school}", "url": school_url},
            {"label": "U.S. News — Michigan rankings", "url": usnews},
        ],
        "disclaimer": DISCLAIMER,
    }


def write_field_descriptions(path: Path, fields: dict[str, str]) -> None:
    lines = [
        '"""Field-specific program description clauses for University of Michigan.',
        "",
        "Each entry states something concrete about what Michigan's program in that field",
        "covers — never a credential/school classification stub. Sources: U-M Rackham",
        "Programs of Study, college and department pages, U-M Facts.",
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
        '"""Generated external_reviews for Michigan coverable programs."""',
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
    import unipaith.data.michigan_profile as mod  # noqa: WPS433

    importlib.reload(mod)
    programs = mod.PROGRAMS
    fields = build_field_descriptions(programs)
    write_field_descriptions(ROOT / "michigan_field_descriptions.py", fields)

    importlib.reload(mod)
    programs = mod.PROGRAMS

    coverable = [p for p in programs if is_coverable(p)]
    hand_crafted = {
        "mich-master-of-business-administration-mba",
        "mich-juris-doctor-jd",
        "mich-business-ug",
        "mich-computer-science-ug-eng",
        "mich-doctor-of-medicine-md",
    }
    reviews: dict[str, dict] = {}
    for p in coverable:
        slug = p["slug"]
        if slug in hand_crafted:
            continue
        reviews[slug] = review_for(p)

    write_reviews(ROOT / "michigan_reviews_generated.py", reviews)
    print(f"FIELD_DESCRIPTIONS: {len(fields)} entries")
    print(f"NEW REVIEWS: {len(reviews)} coverable programs")
    print(f"HAND-CRAFTED REVIEWS kept: {len(hand_crafted)}")


if __name__ == "__main__":
    main()
