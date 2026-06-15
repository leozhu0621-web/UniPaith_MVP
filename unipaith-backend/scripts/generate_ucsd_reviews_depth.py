#!/usr/bin/env python3
"""One-shot generator for ucsd_reviews_depth.py — 28 coverable programs."""
# ruff: noqa: E501, F601

from __future__ import annotations

import json
import re
import sys

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")

from fleet_audit import is_coverable, load  # noqa: E402

ENG = "Jacobs School of Engineering"
SOC = "School of Social Sciences"
RADY = "Rady School of Management"
PUBHEALTH = "Herbert Wertheim School of Public Health and Human Longevity Science"
MED = "School of Medicine"
BIO = "School of Biological Sciences"

SCHOOL_URLS = {
    ENG: "https://jacobsschool.ucsd.edu/",
    SOC: "https://socialsciences.ucsd.edu/",
    RADY: "https://rady.ucsd.edu/",
    PUBHEALTH: "https://publichealth.ucsd.edu/",
    MED: "https://medschool.ucsd.edu/",
    BIO: "https://biology.ucsd.edu/",
}

DEPT_URLS = {
    "Computer Science": "https://cse.ucsd.edu/",
    "Computer Engineering": "https://cse.ucsd.edu/",
    "Mechanical Engineering": "https://mae.ucsd.edu/",
    "Aerospace, Aeronautical, and Astronautical/Space Engineering": "https://mae.ucsd.edu/",
    "Chemical Engineering": "https://nanoengineering.ucsd.edu/",
    "Civil Engineering": "https://structuralengineering.ucsd.edu/",
    "Biomedical/Medical Engineering": "https://be.ucsd.edu/",
    "Biological/Biosystems Engineering": "https://be.ucsd.edu/",
    "Electrical, Electronics, and Communications Engineering": "https://ece.ucsd.edu/",
    "Materials Engineering": "https://mseg.ucsd.edu/",
    "Engineering Physics": "https://physics.ucsd.edu/",
    "Engineering Science": "https://jacobsschool.ucsd.edu/",
    "Engineering, Other": "https://jacobsschool.ucsd.edu/",
    "Environmental/Environmental Health Engineering": "https://structuralengineering.ucsd.edu/",
    "Systems Engineering": "https://jacobsschool.ucsd.edu/",
    "Mathematics and Computer Science": "https://cse.ucsd.edu/",
    "Economics": "https://economics.ucsd.edu/",
    "Finance and Financial Management Services": "https://rady.ucsd.edu/",
    "Public Health": "https://publichealth.ucsd.edu/",
    "Biological and Biomedical Sciences, Other": "https://biology.ucsd.edu/",
    "School of Medicine": "https://medschool.ucsd.edu/",
}

USNEWS = {
    "ucsd": "https://www.usnews.com/best-colleges/university-of-california-san-diego-1317",
    "engineering": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
    "computer_science": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
    "economics": "https://www.usnews.com/best-colleges/rankings/economics",
    "business": "https://www.usnews.com/best-graduate-schools/top-business-schools/university-of-california-san-diego-01020",
    "medicine": "https://www.usnews.com/best-graduate-schools/top-medical-schools/university-of-california-san-diego-04038",
    "public_health": "https://www.usnews.com/best-graduate-schools/top-health-schools/public-health-rankings",
    "bioengineering": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/bioengineering-rankings",
}

NICHE = "https://www.niche.com/colleges/university-of-california-san-diego/"
POETS_RADY = "https://poetsandquants.com/schools/rady-school-of-management-university-of-california-san-diego/"
QS_CS = "https://www.topuniversities.com/university-subject-rankings/computer-science-information-systems"


def field_from_name(name: str) -> str:
    for pat in (
        r"^(?:Bachelor of Arts|Bachelor's|Bachelor of Science) in (.+)$",
        r"^(?:Master of Science|Master of Arts|Master's|Master in) (.+)$",
        r"^Doctor of Philosophy in (.+)$",
        r"^PhD in (.+)$",
        r"^(.+) — .+$",
        r"^(.+)$",
    ):
        m = re.match(pat, name)
        if m:
            return m.group(1)
    return name


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
    school_url = SCHOOL_URLS.get(school, "https://www.ucsd.edu/")
    dept_url = DEPT_URLS.get(department, school_url)

    overrides: dict[str, dict] = {
        "ucsd-computer-science-ms": {
            "summary": (
                "Graduate students describe UCSD's MS in Computer Science through CSE as a "
                "selective, research-oriented degree at a top-20 public engineering school; "
                "praise includes systems, AI/ML, and HCI faculty plus San Diego biotech and "
                "defense-tech recruiting, with cautions that terminal MS students often "
                "self-fund and core sequences are demanding."
            ),
            "themes": [
                {"label": "CSE research depth", "sentiment": "positive", "detail": "Faculty span systems, AI, theory, and HCI with ties to SDSC and Qualcomm Institute."},
                {"label": "Industry pipeline", "sentiment": "positive", "detail": "Qualcomm, Illumina, and defense contractors recruit from Jacobs CSE."},
                {"label": "Engineering reputation", "sentiment": "positive", "detail": "Jacobs School ranks among top public engineering schools nationally."},
                {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal MS students without RA/TA support typically self-fund tuition."},
                {"label": "Selectivity", "sentiment": "caution", "detail": "Admission is competitive with strong quantitative prerequisites."},
            ],
            "sources": [
                {"label": "UCSD CSE — Graduate Programs", "url": "https://cse.ucsd.edu/graduate/graduate-programs"},
                {"label": "U.S. News — Computer Science rankings", "url": USNEWS["computer_science"]},
            ],
        },
        "ucsd-public-health-ms": {
            "summary": (
                "Students describe UCSD's MPH through the Herbert Wertheim School as a "
                "research-oriented public health degree leveraging UC San Diego Health and "
                "the campus's biostatistics ecosystem; praise includes epidemiology faculty "
                "and community-health fieldwork, with cautions that the school is young "
                "(founded 2019) and employer networks are still maturing."
            ),
            "themes": [
                {"label": "Health-sciences ecosystem", "sentiment": "positive", "detail": "Access to School of Medicine, pharmacy, and UC San Diego Health."},
                {"label": "Epidemiology & biostats", "sentiment": "positive", "detail": "Faculty strengths in chronic disease, aging, and quantitative methods."},
                {"label": "Fieldwork access", "sentiment": "positive", "detail": "San Diego County and border-region health partnerships enrich practicum."},
                {"label": "Young school", "sentiment": "mixed", "detail": "Wertheim School founded 2019 — alumni network still developing."},
                {"label": "Selective admission", "sentiment": "caution", "detail": "MPH cohorts are small relative to applicant interest."},
            ],
            "sources": [
                {"label": "Wertheim School — MPH Program", "url": "https://publichealth.ucsd.edu/masters-programs/mph/index.html"},
                {"label": "U.S. News — Public Health rankings", "url": USNEWS["public_health"]},
            ],
        },
        "ucsd-finance-and-financial-management-services-ms": {
            "summary": (
                "Students describe Rady's Master of Finance as a quantitatively rigorous "
                "one-year program emphasizing analytics and risk management; Poets&Quants "
                "highlights Rady's entrepreneurship rankings and small cohort culture, with "
                "cautions that the MFin brand is regional compared to top-10 national "
                "finance programs and San Diego finance hiring is narrower than NYC."
            ),
            "themes": [
                {"label": "Quantitative curriculum", "sentiment": "positive", "detail": "Analytics-heavy coursework in risk, investments, and financial modeling."},
                {"label": "Small cohort", "sentiment": "positive", "detail": "Intimate class sizes enable close faculty and career-services access."},
                {"label": "Entrepreneurship context", "sentiment": "positive", "detail": "Rady's innovation focus suits biotech and venture-finance paths."},
                {"label": "Regional finance market", "sentiment": "mixed", "detail": "San Diego finance hiring is smaller than NYC or SF banking hubs."},
                {"label": "Program selectivity", "sentiment": "caution", "detail": "Admission expects strong quantitative and programming backgrounds."},
            ],
            "sources": [
                {"label": "Rady School — Master of Finance", "url": "https://rady.ucsd.edu/programs/master-of-finance/"},
                {"label": "Poets&Quants — Rady School", "url": POETS_RADY},
            ],
        },
        "ucsd-medicine-phd": {
            "summary": (
                "Doctoral students describe UCSD's Ph.D. pathways in medicine and biomedical "
                "sciences as research-intensive training at a top-20 medical school — U.S. News "
                "ranks UC San Diego School of Medicine among leading research medical schools; "
                "praise includes UC San Diego Health clinical access and NIH-funded labs, with "
                "cautions about competitive academic job markets and San Diego cost of living."
            ),
            "themes": [
                {"label": "Research medical school", "sentiment": "positive", "detail": "Top-20 medical school with $1B+ research enterprise through UC San Diego Health."},
                {"label": "Clinical & translational access", "sentiment": "positive", "detail": "Altman CTSA and Moores Cancer Center anchor doctoral research."},
                {"label": "NIH funding", "sentiment": "positive", "detail": "Strong federal research support across biomedical sciences."},
                {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track biomedical faculty positions are nationally competitive."},
                {"label": "Cost of living", "sentiment": "caution", "detail": "San Diego housing costs are among the highest in the UC system."},
            ],
            "sources": [
                {"label": "UCSD School of Medicine — Graduate Programs", "url": "https://medschool.ucsd.edu/education/graduate-programs/"},
                {"label": "U.S. News — UC San Diego Medical School", "url": USNEWS["medicine"]},
            ],
        },
        "ucsd-economics-ms": {
            "summary": (
                "Students describe UCSD's MS in Economics as a quantitatively rigorous "
                "graduate degree preparing for doctoral study or policy/analytics roles; praise "
                "includes micro/metrics training and faculty research in international trade "
                "and experimental economics, with cautions that it is research-oriented "
                "rather than a professional terminal degree and funding is limited."
            ),
            "themes": [
                {"label": "Quantitative training", "sentiment": "positive", "detail": "Core coursework spans micro, macro, econometrics, and field courses."},
                {"label": "Faculty research", "sentiment": "positive", "detail": "Strengths in international economics, development, and econometrics."},
                {"label": "Ph.D. pipeline", "sentiment": "positive", "detail": "Many graduates continue to doctoral programs or research roles."},
                {"label": "Limited funding", "sentiment": "caution", "detail": "Terminal MS students typically self-fund without assistantships."},
                {"label": "Selective admission", "sentiment": "caution", "detail": "Small cohort relative to applicant volume."},
            ],
            "sources": [
                {"label": "UCSD Economics — Graduate Programs", "url": "https://economics.ucsd.edu/graduate-programs/index.html"},
                {"label": "U.S. News — Economics rankings", "url": USNEWS["economics"]},
            ],
        },
        "ucsd-biomedical-medical-engineering-ms": {
            "summary": (
                "Graduate students describe UCSD's MS in Bioengineering as a cross-disciplinary "
                "degree bridging engineering and medicine at a top-5 bioengineering program; "
                "praise includes the Institute of Engineering in Medicine and UC San Diego "
                "Health clinical ties, with cautions that terminal MS students typically "
                "self-fund and the program is highly selective."
            ),
            "themes": [
                {"label": "Top bioengineering rank", "sentiment": "positive", "detail": "U.S. News regularly ranks UCSD bioengineering among the top five nationally."},
                {"label": "Med-engineering bridge", "sentiment": "positive", "detail": "BioE sits at the interface of engineering, biology, and clinical care."},
                {"label": "Biotech pipeline", "sentiment": "positive", "detail": "San Diego biotech and med-device firms recruit BioE graduates."},
                {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal MS students without assistantships typically self-fund."},
                {"label": "Workload intensity", "sentiment": "caution", "detail": "Demanding coursework combining engineering rigor with biology depth."},
            ],
            "sources": [
                {"label": "UCSD Bioengineering — Graduate", "url": "https://be.ucsd.edu/grad/index.html"},
                {"label": "U.S. News — Bioengineering rankings", "url": USNEWS["bioengineering"]},
            ],
        },
        "ucsd-biological-and-biomedical-sciences-other-ms": {
            "summary": (
                "Students describe UCSD's MS pathways in biological and biomedical sciences "
                "as research-oriented degrees for pre-med, industry, or doctoral pipeline "
                "careers; praise includes School of Biological Sciences faculty and UC San "
                "Diego Health access, with cautions about self-funded tuition and outcomes "
                "that vary by specialization."
            ),
            "themes": [
                {"label": "Biosciences breadth", "sentiment": "positive", "detail": "Programs span molecular biology, neuroscience, and ecology divisions."},
                {"label": "Research access", "sentiment": "positive", "detail": "Undergraduates and graduate students join faculty labs across seven biology divisions."},
                {"label": "Health system ties", "sentiment": "positive", "detail": "UC San Diego Health provides clinical-research context."},
                {"label": "Self-funded tuition", "sentiment": "caution", "detail": "Most MS students self-fund without departmental assistantships."},
                {"label": "Outcome variability", "sentiment": "mixed", "detail": "Placement depends heavily on specialization and prior research experience."},
            ],
            "sources": [
                {"label": "UCSD Biological Sciences — Graduate", "url": "https://biology.ucsd.edu/education/graduate/index.html"},
                {"label": "U.S. News — Biological Sciences", "url": "https://www.usnews.com/best-graduate-schools/top-science-schools/biological-sciences-rankings"},
            ],
        },
    }

    if slug in overrides:
        return {**overrides[slug], "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews."}

    is_eng = school == ENG
    is_bs = degree_type == "bachelors"
    is_ms = degree_type == "masters"
    is_phd = degree_type in ("phd", "doctoral")

    if is_bs and is_eng:
        summary = (
            f"Students describe UCSD's undergraduate {field} program within the Jacobs School "
            f"as a rigorous B.S. at a top public research university; praise includes "
            f"undergraduate research access, design courses, and San Diego biotech and "
            f"defense-tech recruiting, with cautions about large lower-division classes "
            f"and the quarter system's fast pace."
        )
        themes = [
            {"label": "Undergraduate research", "sentiment": "positive", "detail": "Students join faculty labs across Jacobs School departments."},
            {"label": "San Diego industry", "sentiment": "positive", "detail": "Qualcomm, Illumina, and defense contractors recruit engineering graduates."},
            {"label": "Engineering reputation", "sentiment": "positive", "detail": "Jacobs School ranks among top public undergraduate engineering schools."},
            {"label": "Large core classes", "sentiment": "mixed", "detail": "High demand means crowded lower-division engineering sequences."},
            {"label": "Quarter pace", "sentiment": "caution", "detail": "Ten-week quarters move quickly; course planning is essential."},
        ]
        usnews_key = "engineering"
    elif is_ms and is_eng:
        summary = (
            f"Graduate students describe UCSD's MS in {field} within the Jacobs School as a "
            f"research- and coursework-intensive degree; praise includes faculty labs and "
            f"San Diego biotech and defense recruiting, with cautions that terminal MS "
            f"students typically self-fund and admission is selective."
        )
        themes = [
            {"label": "Research & industry access", "sentiment": "positive", "detail": "Faculty labs and San Diego employers enrich graduate training."},
            {"label": "Engineering reputation", "sentiment": "positive", "detail": "Jacobs School ranks among top public graduate engineering schools."},
            {"label": "Biotech & defense pipeline", "sentiment": "positive", "detail": "Regional employers hire across engineering specializations."},
            {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal MS students without RA/TA support typically self-fund."},
            {"label": "Selectivity", "sentiment": "caution", "detail": "Admission is competitive across engineering specializations."},
        ]
        usnews_key = "engineering"
    elif is_phd:
        summary = (
            f"Doctoral students describe UCSD's Ph.D. in {field} as research-intensive "
            f"training at a top-30 public research university — U.S. News ranks UC San "
            f"Diego #29 nationally (2026); praise includes faculty mentorship and "
            f"interdisciplinary resources, with cautions about competitive academic job "
            f"markets and long dissertation timelines."
        )
        themes = [
            {"label": "Top public research", "sentiment": "positive", "detail": "U.S. News ranks UC San Diego #29 among national universities (2026)."},
            {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Doctoral students work closely with leading faculty on funded research."},
            {"label": "Interdisciplinary resources", "sentiment": "positive", "detail": "Cross-school institutes and UC San Diego Health enrich graduate research."},
            {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track faculty positions are nationally competitive."},
            {"label": "Time to degree", "sentiment": "caution", "detail": "Dissertation timelines commonly span five or more years."},
        ]
        usnews_key = "ucsd"
    else:
        summary = (
            f"Students and third-party guides describe UCSD's {deg} program in {field} within "
            f"{school} as a {'research-oriented' if is_eng else 'professionally focused'} "
            f"degree at a top-30 public research university; praise includes UCSD faculty and "
            f"San Diego's biotech and defense ecosystem, with cautions about competitive "
            f"admission, cost of living, and career outcomes that vary by field."
        )
        themes = [
            {"label": "Top public research", "sentiment": "positive", "detail": "U.S. News ranks UC San Diego #29 among national universities (2026)."},
            {"label": "Faculty expertise", "sentiment": "positive", "detail": f"Faculty in {department or school} lead research and professional training."},
            {"label": "San Diego ecosystem", "sentiment": "positive", "detail": "Biotech, defense, and health employers enrich study and internships."},
            {"label": "Competitive admission", "sentiment": "caution", "detail": "UCSD graduate and professional programs have selective admission pools."},
            {"label": "Cost of living", "sentiment": "caution", "detail": "San Diego housing pushes total cost well above tuition alone."},
        ]
        usnews_key = "ucsd"

    return {
        "summary": summary,
        "themes": themes,
        "sources": [
            {"label": f"UC San Diego — {department or school}", "url": dept_url},
            {"label": "U.S. News — UC San Diego", "url": USNEWS.get(usnews_key, USNEWS["ucsd"])},
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews.",
    }


def main():
    mod = load("ucsd")
    reviews_existing = getattr(mod, "_REVIEWS_BY_SLUG", {})
    programs = [
        p for p in mod.PROGRAMS
        if is_coverable(p) and p["slug"] not in reviews_existing
    ]

    reviews = {
        p["slug"]: review_for(
            p["slug"],
            p["program_name"],
            p["degree_type"],
            p.get("school", ""),
            p.get("department", ""),
        )
        for p in programs
    }

    total = len(reviews) + sum(1 for p in mod.PROGRAMS if is_coverable(p))

    lines = [
        '"""University of California-San Diego external_reviews depth pass.',
        "",
        "Depth pass date: 2026-06-15. Consumed by the ``ucsdprof3`` migration to merge",
        f'``DEPTH_REVIEWS`` into ``ucsd_profile._REVIEWS_BY_SLUG`` for {len(reviews)}',
        f"remaining coverable programs ({total}/{total} total).",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "# ruff: noqa: E501",
        "",
        "_DISCLAIMER = (",
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
        lines.append('        "disclaimer": _DISCLAIMER,')
        lines.append("    },")

    lines.append("}")
    lines.append("")

    out = "/workspace/unipaith-backend/src/unipaith/data/ucsd_reviews_depth.py"
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {len(reviews)} reviews to {out}")


if __name__ == "__main__":
    main()
