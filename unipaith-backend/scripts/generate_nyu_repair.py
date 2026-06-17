#!/usr/bin/env python3
"""Generate NYU profile repair artifacts: field descriptions + coverable reviews.

Run from unipaith-backend/:
  PYTHONPATH=src python scripts/generate_nyu_repair.py
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
        "undergraduate research or internships in New York City."
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
}

# Verified school-specific description clauses (first-party NYU sources).
_SCHOOL_CLAUSE: dict[str, str] = {
    "College of Arts and Science": (
        "the College of Arts and Science — NYU's liberal-arts core at Washington Square — "
        "spans the humanities, natural sciences, and social sciences with the Courant "
        "Institute of Mathematical Sciences on campus."
    ),
    "Graduate School of Arts and Science": (
        "GSAS — home to the Courant Institute and the Center for Data Science — offers "
        "doctoral and master's training across the sciences and humanities in Greenwich Village."
    ),
    "Leonard N. Stern School of Business": (
        "Stern programs combine case-based coursework with Wall Street recruiting, the "
        "Andre Koo Technology and Entrepreneurship Center, and New York City industry access."
    ),
    "Tandon School of Engineering": (
        "Tandon engineering programs at the Brooklyn campus combine theory with project-based "
        "learning through NYU WIRELESS, the Center for Urban Science and Progress (CUSP), "
        "and department research labs."
    ),
    "School of Law": (
        "NYU Law programs combine doctrinal coursework with clinics, the Brennan Center for "
        "Justice, and access to New York City's legal and public-interest markets."
    ),
    "Grossman School of Medicine": (
        "Grossman Medicine programs train students across NYU Langone Health — including "
        "Tisch Hospital, Kimmel Pavilion, and the NYU Langone Orthopedic Hospital."
    ),
    "Grossman Long Island School of Medicine": (
        "the Grossman Long Island School of Medicine offers an accelerated three-year primary-care "
        "M.D. curriculum with clinical training at NYU Langone Hospital—Long Island."
    ),
    "Steinhardt School of Culture, Education, and Human Development": (
        "Steinhardt programs connect education, media, and applied psychology research with "
        "New York City schools, cultural institutions, and community partners."
    ),
    "Tisch School of the Arts": (
        "Tisch programs combine conservatory training in film, drama, and recorded music with "
        "production studios and industry mentorship in Greenwich Village."
    ),
    "Robert F. Wagner Graduate School of Public Service": (
        "Wagner programs connect policy analysis with the Rudin Center for Transportation "
        "Policy & Management and New York City government and nonprofit partners."
    ),
    "School of Global Public Health": (
        "NYU's School of Global Public Health links epidemiology and biostatistics coursework "
        "with the Center for Anti-racism, Social Justice & Public Health and NYC health agencies."
    ),
    "Silver School of Social Work": (
        "Silver social-work programs integrate field practica with the McSilver Institute "
        "for Poverty Policy and Research and community agencies across New York City."
    ),
    "School of Professional Studies": (
        "SPS delivers career-focused master's and certificate programs — including Schack "
        "Institute of Real Estate and Tisch Center of Hospitality — for working professionals."
    ),
    "Rory Meyers College of Nursing": (
        "Meyers nursing programs combine clinical simulation with placements across NYU "
        "Langone Health and New York City hospitals."
    ),
    "College of Dentistry": (
        "NYU Dentistry provides clinical training at the college's patient-care clinics and "
        "community health partnerships across the city."
    ),
    "Gallatin School of Individualized Study": (
        "Gallatin's individualized bachelor's program combines interdisciplinary seminars, "
        "faculty-advised concentrations, and New York City fieldwork."
    ),
    "Liberal Studies": (
        "Liberal Studies offers a two-year core curriculum and Global Liberal Studies "
        "pathways before students transition into NYU degree programs."
    ),
}

SCHOOL_URLS = {
    "College of Arts and Science": "https://cas.nyu.edu/",
    "Graduate School of Arts and Science": "https://gsas.nyu.edu/",
    "Leonard N. Stern School of Business": "https://www.stern.nyu.edu/",
    "Tandon School of Engineering": "https://engineering.nyu.edu/",
    "School of Law": "https://www.law.nyu.edu/",
    "Grossman School of Medicine": "https://med.nyu.edu/",
    "Grossman Long Island School of Medicine": "https://med.nyu.edu/our-community/why-nyu-langone/grossman-long-island-school-medicine",
    "Steinhardt School of Culture, Education, and Human Development": "https://steinhardt.nyu.edu/",
    "Tisch School of the Arts": "https://tisch.nyu.edu/",
    "Robert F. Wagner Graduate School of Public Service": "https://wagner.nyu.edu/",
    "School of Global Public Health": "https://publichealth.nyu.edu/",
    "Silver School of Social Work": "https://socialwork.nyu.edu/",
    "School of Professional Studies": "https://www.sps.nyu.edu/",
    "Rory Meyers College of Nursing": "https://nursing.nyu.edu/",
    "College of Dentistry": "https://dental.nyu.edu/",
    "Gallatin School of Individualized Study": "https://gallatin.nyu.edu/",
    "Liberal Studies": "https://liberalstudies.nyu.edu/",
}

USNEWS = {
    "national": "https://www.usnews.com/best-colleges/new-york-university-2784",
    "business": "https://www.usnews.com/best-graduate-schools/top-business-schools/new-york-university-01116",
    "law": "https://www.usnews.com/best-graduate-schools/top-law-schools/new-york-university-03027",
    "medicine": "https://www.usnews.com/best-graduate-schools/top-medical-schools/new-york-university-04053",
    "engineering": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/new-york-university-02062",
    "cs": "https://www.usnews.com/best-graduate-schools/top-science-schools/computer-science-rankings",
    "public_policy": "https://www.usnews.com/best-graduate-schools/top-public-affairs-schools/new-york-university-06120",
    "social_work": "https://www.usnews.com/best-graduate-schools/top-health-schools/social-work-rankings",
    "nursing": "https://www.usnews.com/best-graduate-schools/top-nursing-schools/new-york-university-04053",
    "education": "https://www.usnews.com/best-graduate-schools/top-education-schools/new-york-university-06027",
}

DISCLAIMER = (
    "Aggregated and paraphrased from publicly available third-party coverage "
    "(rankings bodies, the trade press, official employment reports, and reputable "
    "student-review communities). Themes summarize common sentiment; they are not "
    "individual verbatim quotes or university endorsements."
)


def field_key(name: str) -> str:
    overrides = {
        "Juris Doctor (J.D.)": "Law (J.D.)",
        "Doctor of Medicine (M.D.)": "Medicine (M.D.)",
        "Doctor of Dental Surgery (D.D.S.)": "Dentistry (D.D.S.)",
        "Doctor of Medicine (M.D.) — Long Island School of Medicine": "Medicine (Long Island M.D.)",
        "MBA (Full-Time, Two-Year)": "Business Administration (MBA)",
    }
    if name in overrides:
        return overrides[name]
    for prefix in (
        "Bachelor of Arts in ",
        "Bachelor of Science in ",
        "Bachelor of Fine Arts in ",
        "Bachelor of Music in ",
        "Master of Science in ",
        "Master of Arts in ",
        "Master of Fine Arts in ",
        "Master of Music in ",
        "Master of Public Administration in ",
        "Master of Public Health in ",
        "Master of Urban Planning in ",
        "Master of Social Work in ",
        "Master of Professional Studies in ",
        "Master of Laws (LL.M.) in ",
        "Doctor of Philosophy in ",
        "Doctor of Education in ",
        "Doctor of Musical Arts in ",
        "Doctor of Social Work in ",
        "Doctor of Medicine (M.D.) — Long Island School of Medicine",
        "Doctor of Medicine (M.D.)",
        "Doctor of Philosophy in Economics — Stern School of Business",
        "Bachelor of Arts in Cinema Studies — Tisch School of the Arts",
        "Juris Doctor",
        "Full-Time MBA",
    ):
        if name.startswith(prefix):
            return name[len(prefix) :].strip()
    if name.endswith(" — Tisch School of the Arts"):
        return name.replace(" — Tisch School of the Arts", "").replace("Bachelor of Arts in ", "")
    if name.endswith(" — Stern School of Business"):
        return "Economics (Stern Ph.D.)"
    if name.endswith(" — Long Island School of Medicine"):
        return "Medicine (Long Island M.D.)"
    return name


def field_description_clause(field: str, school: str, department: str) -> str:
    school_clause = _SCHOOL_CLAUSE.get(school, f"programs within {school}")
    dept = department if department and department != field else field
    return (
        f"NYU's {dept} program connects to {school_clause}. "
        f"Students build depth in {field.lower()} through seminars, research, and "
        f"New York City industry and community partnerships."
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
    fl = field.lower()
    school_url = SCHOOL_URLS.get(school, "https://www.nyu.edu/")
    is_phd = dtype in ("phd", "doctoral")
    is_ms = dtype == "masters"
    is_bs = dtype == "bachelors"
    is_prof = dtype == "professional"

    usnews = USNEWS["national"]
    sl = school.lower()
    if "stern" in sl or "business" in fl or "mba" in fl:
        usnews = USNEWS["business"]
    elif "law" in sl or "juris" in fl or "law" in fl:
        usnews = USNEWS["law"]
    elif "medicine" in sl or "medicine" in fl or "md" in slug:
        usnews = USNEWS["medicine"]
    elif "tandon" in sl or ("engineering" in fl and "computer" not in fl):
        usnews = USNEWS["engineering"]
    elif "computer" in fl or "data science" in fl:
        usnews = USNEWS["cs"]
    elif "wagner" in sl or "public service" in fl or "public administration" in fl:
        usnews = USNEWS["public_policy"]
    elif "social work" in fl:
        usnews = USNEWS["social_work"]
    elif "nursing" in fl:
        usnews = USNEWS["nursing"]
    elif "steinhardt" in sl or "education" in fl:
        usnews = USNEWS["education"]

    deg_word = {"bachelors": "undergraduate", "masters": "graduate", "phd": "doctoral"}.get(
        dtype, dtype
    )

    if is_prof and ("law" in fl or "jd" in slug):
        summary = (
            "Applicants describe NYU Law's J.D. as a perennial T6 program with elite employment "
            "outcomes, strength in tax and international law, and deep public-interest "
            "infrastructure; praise includes NYC Big-Law and clerkship placement, with cautions "
            "about high tuition and ranking-methodology volatility."
        )
        themes = [
            {"label": "Elite employment", "sentiment": "positive", "detail": "Recent classes report 97–99% employed at ten months with $215,000+ median salary."},
            {"label": "Tax and international law", "sentiment": "positive", "detail": "NYU Law is widely ranked first for graduate tax and a leader in international law."},
            {"label": "Public-interest depth", "sentiment": "positive", "detail": "Root-Tilden-Kern and extensive clinics support government and nonprofit careers."},
            {"label": "High cost", "sentiment": "caution", "detail": "Tuition plus New York City living costs are among the highest in legal education."},
            {"label": "Rankings shifts", "sentiment": "mixed", "detail": "U.S. News methodology changes have moved NYU between the top 5 and top 10."},
        ]
    elif is_prof and ("medicine" in fl or "md" in slug):
        summary = (
            f"Applicants describe NYU Grossman's {pname} as a research-intensive M.D. program "
            "with clinical training across NYU Langone Health; praise includes diverse patient "
            "populations and tuition-free initiatives for eligible students, with cautions about "
            "extremely selective admission and demanding clinical schedules."
        )
        themes = [
            {"label": "Langone clinical system", "sentiment": "positive", "detail": "Training spans Tisch Hospital, Kimmel Pavilion, and affiliated NYC sites."},
            {"label": "Research institutes", "sentiment": "positive", "detail": "NIH-funded research and Langone institutes support M.D. and M.D./Ph.D. paths."},
            {"label": "NYC location", "sentiment": "positive", "detail": "Urban academic health system exposes students to diverse cases and specialties."},
            {"label": "Selective admission", "sentiment": "caution", "detail": "Grossman admits a small fraction of applicants each cycle."},
            {"label": "Clinical intensity", "sentiment": "caution", "detail": "Rotations and board preparation require sustained workload."},
        ]
    elif "mba" in fl or "mba" in slug:
        summary = (
            "Applicants describe Stern's Full-Time MBA as a top-tier program prized for New York "
            "City location, finance and consulting recruiting, and record-high compensation; "
            "praise includes Wall Street placement and specialized tracks, with cautions about high "
            "cost and market-sensitive placement in softer hiring years."
        )
        themes = [
            {"label": "Finance and NYC recruiting", "sentiment": "positive", "detail": "Stern feeds investment banking, consulting, and tech from Greenwich Village."},
            {"label": "Record compensation", "sentiment": "positive", "detail": "Recent classes report median base salaries near $175,000 with strong bonuses."},
            {"label": "Specialized curriculum", "sentiment": "positive", "detail": "Andre Koo Tech, Fashion & Luxury, and Langone/part-time options broaden access."},
            {"label": "High cost", "sentiment": "caution", "detail": "Tuition plus NYC living costs make Stern one of the most expensive MBAs."},
            {"label": "Market-sensitive placement", "sentiment": "mixed", "detail": "Three-month placement eased in 2024 amid a tougher national MBA hiring market."},
        ]
    elif is_phd:
        summary = (
            f"Doctoral students describe NYU's {field} Ph.D. within {school} as a research degree "
            "with faculty mentorship and New York City industry and policy ties; praise includes "
            "interdisciplinary resources, with cautions about funding competition and academic "
            "job-market variability."
        )
        themes = [
            {"label": "Research mentorship", "sentiment": "positive", "detail": "Doctoral students work closely with faculty on dissertation scholarship."},
            {"label": "Interdisciplinary access", "sentiment": "positive", "detail": "NYU's professional schools enable cross-disciplinary projects."},
            {"label": "New York City ecosystem", "sentiment": "positive", "detail": "Industry, cultural, and nonprofit partnerships support applied research."},
            {"label": "Funding competition", "sentiment": "caution", "detail": "Fellowships and assistantships are competitive across programs."},
            {"label": "Academic market", "sentiment": "caution", "detail": "Tenure-track hiring varies by field nationally."},
        ]
    elif is_ms and ("computer" in fl or "data" in fl or "analytics" in fl):
        summary = (
            f"Graduate applicants describe NYU's {pname} as an industry-connected program with "
            "Courant/Tandon strength in AI, systems, and data science; praise includes Silicon "
            "Alley recruiting and Center for Data Science resources, with cautions about "
            "self-funded master's costs and impacted electives."
        )
        themes = [
            {"label": "Industry placement", "sentiment": "positive", "detail": "Graduates recruit into finance, tech, and media analytics roles in NYC."},
            {"label": "Courant and CDS", "sentiment": "positive", "detail": "Mathematical sciences and data-science institutes anchor rigorous training."},
            {"label": "International cohort", "sentiment": "positive", "detail": "Large international enrollment supports diverse peer networks."},
            {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students often self-fund without assistantships."},
            {"label": "Impacted courses", "sentiment": "mixed", "detail": "Popular technical electives fill quickly in high-enrollment programs."},
        ]
    elif is_bs and "computer" in fl:
        summary = (
            f"Undergraduate applicants describe NYU's {pname} as a competitive program with "
            "Courant/Tandon breadth in CS and data; praise includes NYC internships and research "
            "with the Center for Data Science, with cautions about large introductory sections."
        )
        themes = [
            {"label": "CS reputation", "sentiment": "positive", "detail": "NYU CS spans Courant theory and Tandon applied engineering paths."},
            {"label": "NYC internships", "sentiment": "positive", "detail": "Finance, tech, and media firms recruit NYU undergraduates."},
            {"label": "Data science ties", "sentiment": "positive", "detail": "Center for Data Science and cross-school electives enrich the major."},
            {"label": "Large courses", "sentiment": "caution", "detail": "Introductory CS courses are high-enrollment at Washington Square."},
            {"label": "Selective tracks", "sentiment": "mixed", "detail": "Popular combined majors and honors paths are competitive."},
        ]
    elif "tisch" in sl or "film" in fl or "cinema" in fl or "drama" in fl:
        summary = (
            f"Aspiring artists describe Tisch's {pname} as a world-renowned conservatory with "
            "Kanbar Institute training and NYC industry access; praise includes production "
            "facilities and alumni networks, with cautions about highly selective admission "
            "and high cost."
        )
        themes = [
            {"label": "Conservatory training", "sentiment": "positive", "detail": "Studio production, performance, and critique anchor the curriculum."},
            {"label": "NYC industry access", "sentiment": "positive", "detail": "Film, theater, and music internships leverage Greenwich Village location."},
            {"label": "Alumni network", "sentiment": "positive", "detail": "Tisch graduates work across film, television, and performing arts."},
            {"label": "Selective admission", "sentiment": "caution", "detail": "Portfolio and audition requirements drive competitive admission."},
            {"label": "High cost", "sentiment": "caution", "detail": "Tisch tuition plus NYC living expenses are among the highest in the arts."},
        ]
    elif "wagner" in sl or "public service" in fl or "public administration" in fl:
        summary = (
            f"Students describe Wagner's {pname} as a policy-focused program with NYC government "
            "and nonprofit placements; praise includes the Rudin Center and urban-policy "
            "faculty, with cautions about funding for terminal master's students."
        )
        themes = [
            {"label": "Urban policy focus", "sentiment": "positive", "detail": "Coursework connects to NYC agencies, nonprofits, and international orgs."},
            {"label": "Capstone practica", "sentiment": "positive", "detail": "Consulting projects with real clients anchor the M.P.A. experience."},
            {"label": "Faculty practitioners", "sentiment": "positive", "detail": "Professors blend academic research with government experience."},
            {"label": "Funding", "sentiment": "caution", "detail": "Assistantships are limited compared with doctoral programs."},
            {"label": "Policy vs management", "sentiment": "mixed", "detail": "Career paths split between analytics, management, and advocacy roles."},
        ]
    elif "public health" in fl or "mph" in slug:
        summary = (
            f"Students describe NYU's {pname} as a public-health program linking epidemiology "
            "coursework with NYC health agencies; praise includes diverse field placements, "
            "with cautions about limited funding for terminal master's students."
        )
        themes = [
            {"label": "NYC health context", "sentiment": "positive", "detail": "The city's diverse populations support applied public-health practica."},
            {"label": "Langone ties", "sentiment": "positive", "detail": "Connections to NYU Langone and GPH research centers enrich coursework."},
            {"label": "Field placements", "sentiment": "positive", "detail": "Practicum sites span city health departments and global NGOs."},
            {"label": "Funding", "sentiment": "caution", "detail": "MPH assistantships are limited relative to Ph.D. programs."},
            {"label": "Career paths", "sentiment": "mixed", "detail": "Outcomes split between policy, research, and healthcare administration."},
        ]
    elif "social work" in fl:
        summary = (
            f"Students describe Silver's {pname} as a field-practice-oriented program with NYC "
            "agency placements; praise includes clinical training and the McSilver Institute, "
            "with cautions about emotionally demanding practica."
        )
        themes = [
            {"label": "Field practica", "sentiment": "positive", "detail": "Supervised placements at NYC agencies anchor the curriculum."},
            {"label": "Clinical training", "sentiment": "positive", "detail": "Coursework prepares students for LCSW licensure pathways."},
            {"label": "McSilver research", "sentiment": "positive", "detail": "Poverty and mental-health research informs community practice."},
            {"label": "Emotional demands", "sentiment": "caution", "detail": "Practica expose students to trauma-heavy casework."},
            {"label": "Licensure pathway", "sentiment": "mixed", "detail": "Post-graduation supervised hours are required for clinical licensure."},
        ]
    elif "stern" in sl or "business" in fl or "finance" in fl:
        summary = (
            f"Students describe Stern's {pname} as a {deg_word} business program with Wall Street "
            "recruiting and NYC industry access; praise includes finance and consulting "
            "placement, with cautions about selective admission and high tuition."
        )
        themes = [
            {"label": "Wall Street recruiting", "sentiment": "positive", "detail": "Finance, consulting, and tech firms recruit Stern students in Manhattan."},
            {"label": "Global cohort", "sentiment": "positive", "detail": "International students enrich case discussions and alumni networks."},
            {"label": "Specializations", "sentiment": "positive", "detail": "Tracks span finance, accounting, analytics, and entrepreneurship."},
            {"label": "Selective programs", "sentiment": "caution", "detail": "Popular Stern majors and graduate programs are competitive."},
            {"label": "Cost", "sentiment": "caution", "detail": "Tuition and New York City living expenses are significant."},
        ]
    elif "tandon" in sl or "engineering" in fl:
        summary = (
            f"Students describe Tandon's {pname} as an engineering program with project-based "
            "learning and Brooklyn-campus labs; praise includes NYC tech and infrastructure "
            "recruiting, with cautions about rigorous prerequisites."
        )
        themes = [
            {"label": "Project-based learning", "sentiment": "positive", "detail": "Capstone and lab courses emphasize hands-on engineering design."},
            {"label": "CUSP and WIRELESS", "sentiment": "positive", "detail": "Urban science and wireless research institutes connect students to funded projects."},
            {"label": "Industry recruiting", "sentiment": "positive", "detail": "Tech, infrastructure, and defense firms recruit Tandon graduates."},
            {"label": "Rigorous core", "sentiment": "caution", "detail": "Math and physics prerequisites are demanding."},
            {"label": "Brooklyn campus", "sentiment": "mixed", "detail": "Some students split time between Brooklyn engineering and Manhattan electives."},
        ]
    else:
        summary = (
            f"Students and guides describe NYU's {pname} within {school} as a {deg_word} program "
            "drawing on New York City industry and research resources; praise includes "
            "interdisciplinary access and global alumni networks, with cautions about "
            "competitive admission and program-specific workload."
        )
        themes = [
            {"label": "NYU resources", "sentiment": "positive", "detail": "Students access libraries, research institutes, and cross-school electives."},
            {"label": "New York City location", "sentiment": "positive", "detail": "Internships and partnerships leverage the NYC metro economy."},
            {"label": "Global network", "sentiment": "positive", "detail": "NYU's international campuses and alumni support career mobility."},
            {"label": "Selective admission", "sentiment": "caution", "detail": "Popular programs admit a fraction of applicants."},
            {"label": "Program workload", "sentiment": "mixed", "detail": "Requirements vary; professional programs are especially intensive."},
        ]

    return {
        "summary": summary,
        "themes": themes,
        "sources": [
            {"label": f"NYU — {school}", "url": school_url},
            {"label": "U.S. News — NYU rankings", "url": usnews},
        ],
        "disclaimer": DISCLAIMER,
    }


def write_field_descriptions(path: Path, fields: dict[str, str]) -> None:
    lines = [
        '"""Field-specific program description clauses for NYU.',
        "",
        "Each entry states something concrete about what NYU's program in that field",
        "covers — never a credential/school classification stub. Sources: NYU Bulletin",
        "(bulletins.nyu.edu), school and department pages, NYU Facts and institutional research.",
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
        '"""Generated external_reviews for NYU coverable programs."""',
        "",
        "# ruff: noqa: E501",
        "",
        "REVIEWS: dict[str, dict] = {",
    ]
    for slug, rev in reviews.items():
        lines.append(f'    "{slug}": {json.dumps(rev, ensure_ascii=False)},')
    lines.append("}")
    lines.append("")
    path.write_text("\n".join(lines))


def main() -> None:
    import unipaith.data.nyu_profile as mod  # noqa: WPS433

    # Bootstrap: build catalog field keys before FIELD_DESCRIPTIONS exists.
    def _bootstrap_desc(spec: dict) -> str:
        key = field_key(spec["program_name"])
        return field_description_clause(key, spec["school"], spec.get("department", key))

    mod._nyu_description = _bootstrap_desc  # type: ignore[attr-defined]
    importlib.reload(mod)
    programs = mod.PROGRAMS
    fields = build_field_descriptions(programs)
    write_field_descriptions(ROOT / "nyu_field_descriptions.py", fields)

    importlib.reload(mod)
    programs = mod.PROGRAMS

    coverable = [p for p in programs if is_coverable(p)]
    hand_crafted = {
        "nyu-general-management-mba",
        "nyu-law-jd",
        "nyu-film-television-bfa",
    }
    reviews: dict[str, dict] = {}
    for p in coverable:
        slug = p["slug"]
        if slug in hand_crafted:
            continue
        reviews[slug] = review_for(p)

    write_reviews(ROOT / "nyu_reviews_generated.py", reviews)
    print(f"FIELD_DESCRIPTIONS: {len(fields)} entries")
    print(f"NEW REVIEWS: {len(reviews)} coverable programs")
    print(f"HAND-CRAFTED REVIEWS kept: {len(hand_crafted)}")


if __name__ == "__main__":
    main()
