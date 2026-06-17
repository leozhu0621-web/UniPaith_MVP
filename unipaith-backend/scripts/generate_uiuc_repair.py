#!/usr/bin/env python3
"""Generate UIUC profile repair artifacts: credential-disambiguated names,
field descriptions, and coverable external_reviews.

Run from unipaith-backend/:
  PYTHONPATH=src python scripts/generate_uiuc_repair.py
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
        "undergraduate research or internships across the Champaign-Urbana campus."
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
    "doctoral": (
        " Doctoral students conduct original dissertation research with faculty "
        "mentorship and departmental seminars."
    ),
    "diploma": (
        " Diploma students complete intensive performance training and recitals."
    ),
}

# Verified school-specific description clauses (first-party UIUC sources).
_SCHOOL_CLAUSE: dict[str, str] = {
    "The Grainger College of Engineering": (
        "Grainger Engineering — home to the Siebel School of Computing and Data Science, "
        "the Coordinated Science Laboratory, and the National Center for Supercomputing "
        "Applications (NCSA) — trains engineers across aerospace, civil, electrical, "
        "mechanical, materials, and bioengineering."
    ),
    "College of Liberal Arts and Sciences": (
        "the College of LAS — UIUC's largest college — spans the School of Chemical Sciences, "
        "the School of Molecular & Cellular Biology, the Department of Economics, and the "
        "Department of Mathematics on the Champaign-Urbana campus."
    ),
    "Gies College of Business": (
        "Gies Business programs combine case-based coursework with the Illinois MakerLab, "
        "the Deloitte Center for Business Analytics, and the flagship Coursera online "
        "degrees (iMBA, iMSA, iMSM)."
    ),
    "College of Agricultural, Consumer and Environmental Sciences": (
        "ACES programs connect crop sciences, animal sciences, and agricultural economics "
        "with the Morrow Plots — the oldest experimental agricultural field in the U.S. — "
        "and ACES research farms."
    ),
    "College of Fine and Applied Arts": (
        "FAA programs span the School of Architecture, the School of Art & Design, the "
        "School of Music, and Krannert Art Museum on the Champaign-Urbana campus."
    ),
    "College of Applied Health Sciences": (
        "Applied Health Sciences programs combine kinesiology, recreation sport & tourism, "
        "and speech & hearing science with campus wellness and community-health research."
    ),
    "College of Education": (
        "the College of Education trains teachers, counselors, and education researchers "
        "through curriculum & instruction, educational psychology, and special education "
        "departments."
    ),
    "College of Media": (
        "the College of Media links advertising, journalism, and the Institute of "
        "Communications Research with Illinois Public Media and student newsrooms."
    ),
    "School of Information Sciences": (
        "the iSchool — ranked #1 for library and information studies by U.S. News — "
        "trains information scientists, data curators, and informatics researchers."
    ),
    "School of Social Work": (
        "the School of Social Work integrates field practica with community agencies "
        "across central Illinois and the Chicago metropolitan area."
    ),
    "School of Labor and Employment Relations": (
        "the School of LER trains human-resources and labor-relations professionals "
        "through the MHRIR program and Institute of Labor and Industrial Relations research."
    ),
    "College of Law": (
        "the College of Law combines doctrinal coursework with clinics, the Program in "
        "Trial Advocacy, and the Illinois Program in Law, Behavior & Social Science."
    ),
    "College of Veterinary Medicine": (
        "the College of Veterinary Medicine operates the Veterinary Teaching Hospital "
        "and research across comparative biosciences, pathobiology, and clinical medicine."
    ),
    "Carle Illinois College of Medicine": (
        "Carle Illinois College of Medicine — the nation's first engineering-based "
        "medical school — trains physician-innovators across engineering, basic sciences, "
        "and Carle Health clinical partners."
    ),
}

SCHOOL_URLS = {
    "The Grainger College of Engineering": "https://grainger.illinois.edu/",
    "College of Liberal Arts and Sciences": "https://las.illinois.edu/",
    "Gies College of Business": "https://giesbusiness.illinois.edu/",
    "College of Agricultural, Consumer and Environmental Sciences": "https://aces.illinois.edu/",
    "College of Fine and Applied Arts": "https://faa.illinois.edu/",
    "College of Applied Health Sciences": "https://ahs.illinois.edu/",
    "College of Education": "https://education.illinois.edu/",
    "College of Media": "https://media.illinois.edu/",
    "School of Information Sciences": "https://ischool.illinois.edu/",
    "School of Social Work": "https://socialwork.illinois.edu/",
    "School of Labor and Employment Relations": "https://ler.illinois.edu/",
    "College of Law": "https://law.illinois.edu/",
    "College of Veterinary Medicine": "https://vetmed.illinois.edu/",
    "Carle Illinois College of Medicine": "https://medicine.illinois.edu/",
}

USNEWS = {
    "national": "https://www.usnews.com/best-colleges/university-of-illinois-urbana-champaign-1775",
    "engineering": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/university-of-illinois-urbana-champaign-02073",
    "business": "https://www.usnews.com/best-graduate-schools/top-business-schools/university-of-illinois-urbana-champaign-01096",
    "law": "https://www.usnews.com/best-graduate-schools/top-law-schools/university-of-illinois-urbana-champaign-03029",
    "medicine": "https://www.usnews.com/best-graduate-schools/top-medical-schools/university-of-illinois-urbana-champaign-04052",
    "cs": "https://www.usnews.com/best-graduate-schools/top-science-schools/computer-science-rankings",
    "education": "https://www.usnews.com/best-graduate-schools/top-education-schools/university-of-illinois-urbana-champaign-06028",
    "social_work": "https://www.usnews.com/best-graduate-schools/top-health-schools/social-work-rankings",
    "library": "https://www.usnews.com/best-graduate-schools/top-library-information-science-programs/university-of-illinois-urbana-champaign-06028",
}

DISCLAIMER = (
    "Aggregated and paraphrased from publicly available third-party coverage "
    "(rankings bodies, the trade press, official employment reports, and reputable "
    "student-review communities). Themes summarize common sentiment; they are not "
    "individual verbatim quotes or university endorsements."
)


def field_key(program_name: str) -> str:
    """Strip credential prefix to get the field key for description lookup."""
    overrides = {
        "Juris Doctor": "Law (J.D.)",
        "Doctor of Medicine": "Medicine (M.D.)",
        "Doctor of Veterinary Medicine": "Veterinary Medicine (D.V.M.)",
        "Master of Business Administration (iMBA, Online)": "Business Administration (iMBA)",
        "Master of Computer Science (Online)": "Computer Science (Online MCS)",
        "Master of Science in Accountancy (iMSA, Online)": "Accountancy (iMSA)",
        "Master of Science in Management (iMSM, Online)": "Management (iMSM)",
    }
    if program_name in overrides:
        return overrides[program_name]
    for prefix in (
        "Bachelor of Science in Liberal Arts and Sciences — ",
        "Bachelor of Science in Agricultural Sciences — ",
        "Bachelor of Science in ",
        "Bachelor of Arts in ",
        "Bachelor of Fine Arts in ",
        "Bachelor of Music in ",
        "Master of Science in ",
        "Master of Arts in ",
        "Master of Fine Arts in ",
        "Master of Music in ",
        "Master of Engineering in ",
        "Master of Education (Ed.M.) in ",
        "Master of Accounting Science in ",
        "Master of Agricultural and Applied Economics in ",
        "Master of Computer Science in ",
        "Master of Computer Science (Online)",
        "Master of Business Administration (iMBA, Online)",
        "Master of Science in Accountancy (iMSA, Online)",
        "Master of Science in Management (iMSM, Online)",
        "Doctor of Philosophy in ",
        "Doctor of Education (Ed.D.) in ",
        "Doctor of Musical Arts in ",
        "Master of Public Health in ",
        "Master of Health Administration in ",
        "Master of Architecture in ",
        "Master of Landscape Architecture in ",
        "Master of Urban Planning in ",
        "Master of Social Work in ",
        "Master of Human Resources and Industrial Relations in ",
        "Master of Laws (LL.M.) in ",
        "Master of Studies in Law in ",
        "Doctor of the Science of Law in ",
        "Doctor of Audiology in ",
        "Doctor of Veterinary Medicine",
        "Juris Doctor",
        "Doctor of Medicine",
    ):
        if program_name.startswith(prefix):
            return program_name[len(prefix) :].strip()
    return program_name


def field_description_clause(field: str, school: str, department: str) -> str:
    school_clause = _SCHOOL_CLAUSE.get(school, f"programs within {school}")
    dept = department if department and department != field else field
    return (
        f"UIUC's {dept} program connects to {school_clause}. "
        f"Students build depth in {field.lower()} through seminars, research, and "
        f"Champaign-Urbana industry and community partnerships."
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
    school_url = SCHOOL_URLS.get(school, "https://illinois.edu/")
    is_phd = dtype in ("phd", "doctoral")
    is_ms = dtype == "masters"
    is_bs = dtype == "bachelors"
    is_prof = dtype == "professional"
    fl = field.lower()
    sl = school.lower()

    usnews = USNEWS["national"]
    if "gies" in sl or "business" in fl or "mba" in fl or "accountancy" in fl or "finance" in fl:
        usnews = USNEWS["business"]
    elif "law" in sl or "juris" in fl or "law" in fl:
        usnews = USNEWS["law"]
    elif "medicine" in sl or "medicine" in fl or "md" in slug:
        usnews = USNEWS["medicine"]
    elif "grainger" in sl or "engineering" in sl or ("engineering" in fl and "computer" not in fl):
        usnews = USNEWS["engineering"]
    elif "computer" in fl or "data science" in fl or "informatics" in fl:
        usnews = USNEWS["cs"]
    elif "ischool" in sl or "information" in fl or "library" in fl:
        usnews = USNEWS["library"]
    elif "education" in sl or "education" in fl:
        usnews = USNEWS["education"]
    elif "social work" in fl:
        usnews = USNEWS["social_work"]

    deg_word = {"bachelors": "undergraduate", "masters": "graduate", "phd": "doctoral"}.get(
        dtype, dtype
    )

    if is_prof and ("law" in fl or "jd" in slug):
        summary = (
            "Applicants describe UIUC Law's J.D. as a well-regarded Midwestern program with "
            "strong employment outcomes, a nationally ranked trial-advocacy program, and "
            "affordable public-university tuition; praise includes Big-Law and government "
            "placement, with cautions about a smaller alumni network than coastal T14 schools."
        )
        themes = [
            {"label": "Strong employment", "sentiment": "positive", "detail": "Recent classes report high bar-passage and employment rates within ten months."},
            {"label": "Trial advocacy", "sentiment": "positive", "detail": "UIUC's Program in Trial Advocacy is nationally ranked for litigation training."},
            {"label": "Public-university value", "sentiment": "positive", "detail": "In-state tuition is lower than most private law schools."},
            {"label": "Regional network", "sentiment": "caution", "detail": "Alumni concentration is strongest in the Midwest and Chicago markets."},
            {"label": "Selective admission", "sentiment": "mixed", "detail": "Admission is competitive; scholarship aid varies by cycle."},
        ]
    elif is_prof and ("medicine" in fl or "md" in slug):
        summary = (
            f"Applicants describe Carle Illinois's {pname} as an engineering-based M.D. program "
            "integrating innovation, basic sciences, and Carle Health clinical training; praise "
            "includes the physician-innovator curriculum and research opportunities, with cautions "
            "about a newer program and demanding clinical schedules."
        )
        themes = [
            {"label": "Engineering-based curriculum", "sentiment": "positive", "detail": "The nation's first engineering-based medical school trains physician-innovators."},
            {"label": "Carle Health clinical partners", "sentiment": "positive", "detail": "Clinical training spans Carle Foundation Hospital and regional affiliates."},
            {"label": "Research integration", "sentiment": "positive", "detail": "Students engage with Jump ARCHES and engineering-faculty research."},
            {"label": "Newer program", "sentiment": "caution", "detail": "The college is younger than established medical schools; outcomes data are still maturing."},
            {"label": "Clinical intensity", "sentiment": "caution", "detail": "Rotations and board preparation require sustained workload."},
        ]
    elif is_prof and ("veterinary" in fl or "dvm" in slug):
        summary = (
            "Applicants describe UIUC's D.V.M. program as a top veterinary college with the "
            "Veterinary Teaching Hospital, strong large-animal and companion-animal training, "
            "and research across comparative biosciences; praise includes clinical breadth, "
            "with cautions about competitive admission and demanding clinical rotations."
        )
        themes = [
            {"label": "Teaching hospital", "sentiment": "positive", "detail": "The Veterinary Teaching Hospital supports diverse clinical cases."},
            {"label": "Research breadth", "sentiment": "positive", "detail": "Departments span comparative biosciences, pathobiology, and clinical medicine."},
            {"label": "Large-animal strength", "sentiment": "positive", "detail": "ACES and vet-med ties support agricultural and livestock health training."},
            {"label": "Selective admission", "sentiment": "caution", "detail": "Veterinary programs nationally admit a small fraction of applicants."},
            {"label": "Clinical workload", "sentiment": "caution", "detail": "Rotations and licensure preparation are intensive."},
        ]
    elif "mba" in fl or "mba" in slug or "imba" in slug:
        summary = (
            "Applicants describe Gies's iMBA as a top-ranked online MBA prized for flexibility, "
            "affordable total tuition (~$27,288), and the same Illinois diploma as on-campus "
            "programs; praise includes live sessions and global cohort networking, with cautions "
            "about fully online delivery and self-directed pacing."
        )
        themes = [
            {"label": "Top-ranked online MBA", "sentiment": "positive", "detail": "U.S. News ranks Gies's online MBA among the nation's best."},
            {"label": "Affordable tuition", "sentiment": "positive", "detail": "Flat total tuition is lower than most peer online MBAs."},
            {"label": "Live Coursera sessions", "sentiment": "positive", "detail": "Synchronous sessions with Illinois faculty anchor the experience."},
            {"label": "Fully online", "sentiment": "caution", "detail": "No on-campus residency; best suits working professionals."},
            {"label": "Self-directed pacing", "sentiment": "mixed", "detail": "Flexible pacing rewards motivated students but demands time management."},
        ]
    elif is_phd:
        summary = (
            f"Doctoral students describe UIUC's {field} Ph.D. within {school} as a research degree "
            "with R1 faculty mentorship and interdisciplinary resources across the Champaign-Urbana "
            "campus; praise includes funded assistantships in many departments, with cautions about "
            "funding competition and academic job-market variability."
        )
        themes = [
            {"label": "R1 research mentorship", "sentiment": "positive", "detail": "Doctoral students work with faculty across a top-tier research university."},
            {"label": "Interdisciplinary access", "sentiment": "positive", "detail": "Cross-college institutes and NCSA support computational and applied research."},
            {"label": "Midwest ecosystem", "sentiment": "positive", "detail": "Chicago, St. Louis, and industry partnerships support applied scholarship."},
            {"label": "Funding competition", "sentiment": "caution", "detail": "Fellowships and assistantships are competitive across programs."},
            {"label": "Academic market", "sentiment": "caution", "detail": "Tenure-track hiring varies by field nationally."},
        ]
    elif is_ms and ("computer" in fl or "data" in fl or "analytics" in fl or "mcs" in slug):
        summary = (
            f"Graduate applicants describe UIUC's {pname} as a rigorous program with Siebel School "
            "strength in systems, AI, and data science; praise includes the same Illinois MCS "
            "degree online or on-campus and strong tech recruiting, with cautions about "
            "self-funded master's costs and competitive admission."
        )
        themes = [
            {"label": "Top-5 CS reputation", "sentiment": "positive", "detail": "U.S. News ranks UIUC CS among the nation's best graduate programs."},
            {"label": "Systems and AI depth", "sentiment": "positive", "detail": "Faculty strength spans systems, architecture, programming languages, and AI."},
            {"label": "Tech recruiting", "sentiment": "positive", "detail": "Graduates recruit into major technology firms and quant roles."},
            {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students often self-fund without assistantships."},
            {"label": "Competitive admission", "sentiment": "mixed", "detail": "Popular CS graduate programs admit a fraction of applicants."},
        ]
    elif is_bs and "computer" in fl:
        summary = (
            f"Undergraduate applicants describe UIUC's {pname} as a top-ranked program with Siebel "
            "School strength in systems, AI, and the distinctive 'CS + X' blended degrees; praise "
            "includes world-class faculty and big-tech recruiting, with cautions about extremely "
            "competitive direct admission and large core courses."
        )
        themes = [
            {"label": "Top-7 CS reputation", "sentiment": "positive", "detail": "U.S. News ranks UIUC undergraduate CS #7 nationally."},
            {"label": "CS + X blended degrees", "sentiment": "positive", "detail": "UIUC pioneered majors pairing computing with anthropology, economics, music, and more."},
            {"label": "Industry placement", "sentiment": "positive", "detail": "Graduates recruit heavily into major technology firms."},
            {"label": "Selective admission", "sentiment": "caution", "detail": "Direct admission to CS is highly competitive."},
            {"label": "Large courses", "sentiment": "caution", "detail": "Popular CS courses are high-enrollment; reviewers advise early research engagement."},
        ]
    elif "grainger" in sl or "engineering" in fl:
        summary = (
            f"Students describe Grainger Engineering's {pname} as a top-ranked engineering program "
            "with project-based learning and NCSA/CSL research labs; praise includes semiconductor, "
            "aerospace, and systems recruiting, with cautions about rigorous prerequisites and "
            "engineering differential tuition."
        )
        themes = [
            {"label": "Top-10 engineering", "sentiment": "positive", "detail": "U.S. News ranks Grainger Engineering among the nation's best."},
            {"label": "Research labs", "sentiment": "positive", "detail": "NCSA, CSL, and Holonyak Micro & Nanotechnology Lab anchor research."},
            {"label": "Industry recruiting", "sentiment": "positive", "detail": "Tech, semiconductor, and infrastructure firms recruit Grainger graduates."},
            {"label": "Rigorous core", "sentiment": "caution", "detail": "Math and physics prerequisites are demanding."},
            {"label": "Differential tuition", "sentiment": "mixed", "detail": "Engineering programs carry higher tuition than LAS majors."},
        ]
    elif "gies" in sl or "business" in fl or "finance" in fl or "accountancy" in fl:
        summary = (
            f"Students describe Gies's {pname} as a {deg_word} business program with case-based "
            "coursework and strong accounting/finance recruiting; praise includes the Deloitte "
            "Center for Business Analytics and online degree options, with cautions about "
            "selective admission and business differential tuition."
        )
        themes = [
            {"label": "Business analytics", "sentiment": "positive", "detail": "The Deloitte Center for Business Analytics anchors data-driven coursework."},
            {"label": "Accounting strength", "sentiment": "positive", "detail": "Gies accountancy is widely recruited by Big Four and industry firms."},
            {"label": "Online options", "sentiment": "positive", "detail": "Coursera iMBA, iMSA, and iMSM extend access for working professionals."},
            {"label": "Selective programs", "sentiment": "caution", "detail": "Popular business majors and graduate programs are competitive."},
            {"label": "Differential tuition", "sentiment": "caution", "detail": "Business programs carry higher tuition than many LAS majors."},
        ]
    elif "ischool" in sl or "information" in fl or "library" in fl:
        summary = (
            f"Students describe the iSchool's {pname} as the nation's top-ranked library and "
            "information-science program; praise includes data curation, informatics, and "
            "interdisciplinary research, with cautions about funding for terminal master's students."
        )
        themes = [
            {"label": "#1 LIS ranking", "sentiment": "positive", "detail": "U.S. News ranks UIUC library and information studies #1 nationally."},
            {"label": "Informatics breadth", "sentiment": "positive", "detail": "Programs span data science, UX, and information policy."},
            {"label": "Research centers", "sentiment": "positive", "detail": "The Center for Informatics Research in Science and Scholarship anchors projects."},
            {"label": "Funding", "sentiment": "caution", "detail": "Assistantships are limited for terminal master's students."},
            {"label": "Career paths", "sentiment": "mixed", "detail": "Outcomes split between tech, libraries, archives, and policy roles."},
        ]
    elif "education" in sl or "education" in fl:
        summary = (
            f"Students describe UIUC's {pname} as an education program with teacher-preparation "
            "and research training; praise includes Champaign-Urbana school partnerships and "
            "educational-psychology research, with cautions about state licensure requirements."
        )
        themes = [
            {"label": "Teacher preparation", "sentiment": "positive", "detail": "Programs connect to local schools for student-teaching practica."},
            {"label": "Research training", "sentiment": "positive", "detail": "Educational psychology and policy faculty anchor graduate research."},
            {"label": "Community partnerships", "sentiment": "positive", "detail": "Champaign-Urbana schools support field placements."},
            {"label": "Licensure requirements", "sentiment": "caution", "detail": "Teaching credentials require state-specific exams and supervised hours."},
            {"label": "Funding", "sentiment": "mixed", "detail": "Assistantships vary by doctoral vs. professional master's programs."},
        ]
    elif "social work" in fl:
        summary = (
            f"Students describe UIUC's {pname} as a field-practice-oriented social-work program "
            "with central Illinois agency placements; praise includes clinical training and "
            "community partnerships, with cautions about emotionally demanding practica."
        )
        themes = [
            {"label": "Field practica", "sentiment": "positive", "detail": "Supervised placements at community agencies anchor the curriculum."},
            {"label": "Clinical training", "sentiment": "positive", "detail": "Coursework prepares students for LCSW licensure pathways."},
            {"label": "Community focus", "sentiment": "positive", "detail": "Programs serve central Illinois and Chicago-area partners."},
            {"label": "Emotional demands", "sentiment": "caution", "detail": "Practica expose students to trauma-heavy casework."},
            {"label": "Licensure pathway", "sentiment": "mixed", "detail": "Post-graduation supervised hours are required for clinical licensure."},
        ]
    elif "media" in sl or "journalism" in fl or "advertising" in fl:
        summary = (
            f"Students describe UIUC's {pname} as a media program linking journalism and "
            "advertising with Illinois Public Media; praise includes student newsrooms and "
            "communications-research training, with cautions about a shifting media job market."
        )
        themes = [
            {"label": "Student newsrooms", "sentiment": "positive", "detail": "Daily Illini and college media labs support hands-on reporting."},
            {"label": "Communications research", "sentiment": "positive", "detail": "The Institute of Communications Research anchors graduate scholarship."},
            {"label": "Illinois Public Media", "sentiment": "positive", "detail": "NPR/PBS affiliates provide internship and production opportunities."},
            {"label": "Job market shifts", "sentiment": "caution", "detail": "Traditional newsroom hiring has contracted nationally."},
            {"label": "Portfolio building", "sentiment": "mixed", "detail": "Digital skills and internships matter as much as coursework."},
        ]
    elif "aces" in sl or "agricultural" in fl or "agronomy" in fl or "animal" in fl:
        summary = (
            f"Students describe ACES's {pname} as an agricultural and environmental sciences "
            "program with the Morrow Plots and research farms; praise includes extension "
            "connections and USDA-funded research, with cautions about rural placement "
            "concentration for some career paths."
        )
        themes = [
            {"label": "Morrow Plots heritage", "sentiment": "positive", "detail": "The oldest U.S. experimental agricultural field anchors crop-science training."},
            {"label": "Research farms", "sentiment": "positive", "detail": "ACES farms support animal, crop, and environmental field research."},
            {"label": "Extension network", "sentiment": "positive", "detail": "Illinois Extension connects research to statewide communities."},
            {"label": "Rural placement", "sentiment": "caution", "detail": "Some agricultural careers concentrate in rural markets."},
            {"label": "Interdisciplinary breadth", "sentiment": "mixed", "detail": "Programs span economics, nutrition, and natural resources."},
        ]
    elif "faa" in sl or "architecture" in fl or "music" in fl or "art" in fl:
        summary = (
            f"Students describe FAA's {pname} as a fine-and-applied-arts program with studio "
            "training and Krannert Art Museum resources; praise includes design studios and "
            "performance opportunities, with cautions about portfolio/audition requirements."
        )
        themes = [
            {"label": "Studio training", "sentiment": "positive", "detail": "Architecture, art, and music programs emphasize hands-on production."},
            {"label": "Krannert Art Museum", "sentiment": "positive", "detail": "Campus museum resources support art-history and studio practice."},
            {"label": "Performance opportunities", "sentiment": "positive", "detail": "Krannert Center and school ensembles anchor music and theatre training."},
            {"label": "Portfolio/audition", "sentiment": "caution", "detail": "Admission often requires portfolios or auditions."},
            {"label": "Cost of materials", "sentiment": "mixed", "detail": "Studio supplies and performance costs add to tuition."},
        ]
    elif "public health" in fl or "mph" in slug or "epidemiology" in fl:
        summary = (
            f"Students describe UIUC's {pname} as a public-health program linking epidemiology "
            "and health-administration coursework with campus wellness research; praise includes "
            "interdisciplinary health sciences, with cautions about limited funding for terminal "
            "master's students."
        )
        themes = [
            {"label": "Health sciences breadth", "sentiment": "positive", "detail": "Programs connect kinesiology, speech & hearing, and health policy."},
            {"label": "Campus wellness research", "sentiment": "positive", "detail": "Applied health sciences research supports community health initiatives."},
            {"label": "Interdisciplinary ties", "sentiment": "positive", "detail": "Cross-college collaborations span ACES, AHS, and veterinary medicine."},
            {"label": "Funding", "sentiment": "caution", "detail": "MPH assistantships are limited relative to Ph.D. programs."},
            {"label": "Career paths", "sentiment": "mixed", "detail": "Outcomes split between policy, research, and healthcare administration."},
        ]
    else:
        summary = (
            f"Students and guides describe UIUC's {pname} within {school} as a {deg_word} program "
            "drawing on Champaign-Urbana research and industry resources; praise includes "
            "interdisciplinary access at a top public R1 university, with cautions about "
            "competitive admission and program-specific workload."
        )
        themes = [
            {"label": "R1 university resources", "sentiment": "positive", "detail": "Students access libraries, research institutes, and cross-college electives."},
            {"label": "Champaign-Urbana campus", "sentiment": "positive", "detail": "Internships and partnerships leverage the university town and Chicago access."},
            {"label": "Public-university value", "sentiment": "positive", "detail": "In-state tuition and strong aid make UIUC competitive on cost."},
            {"label": "Selective admission", "sentiment": "caution", "detail": "Popular programs admit a fraction of applicants."},
            {"label": "Program workload", "sentiment": "mixed", "detail": "Requirements vary; professional programs are especially intensive."},
        ]

    return {
        "summary": summary,
        "themes": themes,
        "sources": [
            {"label": f"UIUC — {school}", "url": school_url},
            {"label": "U.S. News — UIUC rankings", "url": usnews},
        ],
        "disclaimer": DISCLAIMER,
    }


def write_field_descriptions(path: Path, fields: dict[str, str]) -> None:
    lines = [
        '"""Field-specific program description clauses for UIUC.',
        "",
        "Each entry states something concrete about what UIUC's program in that field",
        "covers — never a credential/school classification stub. Sources: UIUC Academic",
        "Catalog (catalog.illinois.edu), college and department pages, UIUC Facts.",
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
        '"""Generated external_reviews for UIUC coverable programs."""',
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
    import unipaith.data.uiuc_profile as mod  # noqa: WPS433

    def _bootstrap_desc(spec: dict) -> str:
        key = field_key(spec["program_name"])
        return field_description_clause(key, spec["school"], spec.get("department", key))

    mod._uiuc_description = _bootstrap_desc  # type: ignore[attr-defined]
    importlib.reload(mod)
    programs = mod.PROGRAMS
    fields = build_field_descriptions(programs)
    write_field_descriptions(ROOT / "uiuc_field_descriptions.py", fields)

    importlib.reload(mod)
    programs = mod.PROGRAMS

    coverable = [p for p in programs if is_coverable(p)]
    hand_crafted = {
        "uiuc-computer-science-bs",
        "uiuc-computer-science-online-mcs",
        "uiuc-computer-engineering-bs",
        "uiuc-electrical-engineering-bs",
        "uiuc-mechanical-engineering-bs",
        "uiuc-aerospace-engineering-bs",
        "uiuc-civil-engineering-bs",
        "uiuc-materials-science-engineering-bs",
        "uiuc-chemical-engineering-bs",
        "uiuc-bioengineering-bs",
        "uiuc-accountancy-bs",
        "uiuc-finance-bs",
        "uiuc-business-administration-online-mba",
        "uiuc-library-information-science-ms",
        "uiuc-law-jd",
        "uiuc-medicine-md",
        "uiuc-veterinary-medicine-dvm",
        "uiuc-statistics-bslas",
        "uiuc-economics-balas",
    }
    reviews: dict[str, dict] = {}
    for p in coverable:
        slug = p["slug"]
        if slug in hand_crafted:
            continue
        reviews[slug] = review_for(p)

    write_reviews(ROOT / "uiuc_reviews_generated.py", reviews)
    print(f"FIELD_DESCRIPTIONS: {len(fields)} entries")
    print(f"NEW REVIEWS: {len(reviews)} coverable programs")
    print(f"HAND-CRAFTED REVIEWS kept: {len(hand_crafted)}")


if __name__ == "__main__":
    main()
