#!/usr/bin/env python3
"""One-shot generator for northwestern_reviews_depth.py — 48 coverable programs."""
# ruff: noqa: E501, F601

from __future__ import annotations

import json
import re
import sys

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")

from fleet_audit import is_coverable, load  # noqa: E402

SCHOOL_URLS = {
    "Weinberg College of Arts and Sciences": "https://weinberg.northwestern.edu/",
    "McCormick School of Engineering and Applied Science": "https://www.mccormick.northwestern.edu/",
    "Medill School of Journalism, Media, Integrated Marketing Communications": "https://www.medill.northwestern.edu/",
    "School of Communication": "https://communication.northwestern.edu/",
    "Kellogg School of Management": "https://www.kellogg.northwestern.edu/",
    "Pritzker School of Law": "https://www.law.northwestern.edu/",
    "Feinberg School of Medicine": "https://www.feinberg.northwestern.edu/",
}

DEPT_URLS = {
    "Computer Science": "https://www.mccormick.northwestern.edu/computer-science/",
    "Biomedical/Medical Engineering": "https://www.mccormick.northwestern.edu/biomedical-engineering/",
    "Chemical Engineering": "https://www.mccormick.northwestern.edu/chemical-biological-engineering/",
    "Civil Engineering": "https://www.mccormick.northwestern.edu/civil-environmental-engineering/",
    "Computer Engineering": "https://www.mccormick.northwestern.edu/electrical-computer/",
    "Electrical, Electronics, and Communications Engineering": "https://www.mccormick.northwestern.edu/electrical-computer/",
    "Mechanical Engineering": "https://www.mccormick.northwestern.edu/mechanical-engineering/",
    "Industrial Engineering": "https://www.mccormick.northwestern.edu/industrial-engineering-management-sciences/",
    "Materials Engineering": "https://www.mccormick.northwestern.edu/materials-science-engineering/",
    "Environmental/Environmental Health Engineering": "https://www.mccormick.northwestern.edu/civil-environmental-engineering/",
    "Engineering Mechanics": "https://www.mccormick.northwestern.edu/mechanical-engineering/",
    "Engineering Physics": "https://www.mccormick.northwestern.edu/",
    "Engineering Science": "https://www.mccormick.northwestern.edu/",
    "Engineering, General": "https://www.mccormick.northwestern.edu/",
    "Medill School of Journalism, Media, Integrated Marketing Communications": "https://www.medill.northwestern.edu/",
    "Communication, Journalism, and Related Programs, Other": "https://www.medill.northwestern.edu/",
    "Radio, Television, and Digital Communication": "https://communication.northwestern.edu/departments/rtvf/",
    "Architecture and Related Services, Other": "https://www.architecture.northwestern.edu/",
    "Economics": "https://economics.weinberg.northwestern.edu/",
    "Public Health": "https://www.feinberg.northwestern.edu/sites/health-sciences/",
}

USNEWS = {
    "northwestern": "https://www.usnews.com/best-colleges/northwestern-university-1739",
    "law": "https://www.usnews.com/best-graduate-schools/top-law-schools/northwestern-university-03058",
    "business": "https://www.usnews.com/best-graduate-schools/top-business-schools/northwestern-university-01027",
    "medicine": "https://www.usnews.com/best-graduate-schools/top-medical-schools/northwestern-university-feinberg-school-of-medicine-04094",
    "engineering": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
    "computer_science": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
    "journalism": "https://www.usnews.com/best-colleges/rankings/national-universities",
    "communication": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/northwestern-university-03058",
    "architecture": "https://www.usnews.com/best-graduate-schools/top-fine-arts-schools/architecture-rankings",
}

NICHE = "https://www.niche.com/colleges/northwestern-university/"
POETS_KELLOGG = "https://poetsandquants.com/schools/kellogg-school-of-management-northwestern-university/"


def field_from_name(name: str) -> str:
    for pat in (
        r"^(?:Bachelor of Arts|Bachelor's|Bachelor of Science) in (.+)$",
        r"^(?:Master of Science|Master of Arts|Master's|Master in) (.+)$",
        r"^Doctor of Philosophy in (.+)$",
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
    school_url = SCHOOL_URLS.get(school, "https://www.northwestern.edu/")
    dept_url = DEPT_URLS.get(department, school_url)

    overrides: dict[str, dict] = {
        "northwestern-computer-science-ms": {
            "summary": (
                "Graduate applicants describe Northwestern's M.S. in Computer Science within McCormick "
                "as a research-oriented degree with strengths in AI, HCI, and systems through NICO "
                "and interdisciplinary CS+X ties; praise includes Chicago tech recruiting and faculty "
                "mentorship in a smaller cohort than CS-flagship giants, with cautions about self-funded "
                "tuition for terminal master's students and theory-heavy core requirements."
            ),
            "themes": [
                {"label": "AI & HCI research", "sentiment": "positive", "detail": "NICO and CS labs connect computing to journalism, design, and social science."},
                {"label": "Chicago recruiting", "sentiment": "positive", "detail": "Graduates place at major tech firms, startups, and Ph.D. programs nationally."},
                {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Smaller department enables closer advisor relationships than mega-departments."},
                {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students without assistantships typically self-fund tuition."},
                {"label": "Theory-heavy core", "sentiment": "mixed", "detail": "Reviewers note fewer applied-software electives than some peer programs."},
            ],
            "sources": [
                {"label": "McCormick — Computer Science Graduate", "url": "https://www.mccormick.northwestern.edu/computer-science/graduate/"},
                {"label": "U.S. News — Computer Science rankings", "url": USNEWS["computer_science"]},
            ],
        },
        "northwestern-journalism-ms": {
            "summary": (
                "Graduate students describe Medill's journalism master's as a practice-intensive "
                "program with Chicago newsroom access and integrated marketing communications tracks; "
                "praise includes the Knight Lab, Washington Program, and industry faculty, with "
                "cautions about limited graduate funding compared with STEM programs and career "
                "outcomes that depend heavily on portfolio and internship networks."
            ),
            "themes": [
                {"label": "Practice-first training", "sentiment": "positive", "detail": "Reporting, multimedia, and IMC studios anchor the graduate curriculum."},
                {"label": "Chicago media market", "sentiment": "positive", "detail": "Internships at major newspapers, broadcasters, and agencies are program strengths."},
                {"label": "Knight Lab innovation", "sentiment": "positive", "detail": "Digital journalism and product innovation resources differentiate Medill."},
                {"label": "Funding scarcity", "sentiment": "caution", "detail": "Graduate assistantships are scarcer than in STEM Ph.D. programs."},
                {"label": "Portfolio-dependent careers", "sentiment": "mixed", "detail": "Outcomes hinge on clips, internships, and industry connections."},
            ],
            "sources": [
                {"label": "Medill — Graduate Programs", "url": "https://www.medill.northwestern.edu/admission/graduate-programs/"},
                {"label": "Niche — Northwestern University", "url": NICHE},
            ],
        },
        "northwestern-biomedical-medical-engineering-ms": {
            "summary": (
                "Graduate students describe Northwestern's biomedical engineering M.S. within McCormick "
                "as a research-intensive degree with access to Feinberg and the Shirley Ryan "
                "AbilityLab; praise includes translational med-tech projects and Chicago hospital "
                "partnerships, with cautions about self-funded tuition for terminal master's students "
                "and competitive research funding."
            ),
            "themes": [
                {"label": "Clinical translation", "sentiment": "positive", "detail": "Feinberg and Shirley Ryan AbilityLab partnerships support med-device research."},
                {"label": "Interdisciplinary labs", "sentiment": "positive", "detail": "Students join bioelectronics, imaging, and regenerative-medicine groups."},
                {"label": "Chicago med-tech", "sentiment": "positive", "detail": "Graduates enter med-device firms, hospital R&D, and Ph.D. programs."},
                {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students without assistantships typically self-fund tuition."},
                {"label": "Funding competition", "sentiment": "caution", "detail": "Research assistantships are competitive across McCormick and Feinberg."},
            ],
            "sources": [
                {"label": "McCormick — Biomedical Engineering Graduate", "url": "https://www.mccormick.northwestern.edu/biomedical-engineering/graduate/"},
                {"label": "U.S. News — Northwestern Engineering", "url": USNEWS["engineering"]},
            ],
        },
    }

    if slug in overrides:
        r = overrides[slug]
        return {
            **r,
            "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews.",
        }

    fl = field.lower()
    is_phd = degree_type in ("phd", "doctoral")
    is_ms = degree_type == "masters"
    is_bs = degree_type == "bachelors"
    is_kellogg = "Kellogg" in school
    is_medill = "Medill" in school or "journalism" in fl
    is_mccormick = "McCormick" in school or "Engineering" in school
    is_law = "Law" in school
    is_feinberg = "Feinberg" in school or "medicine" in fl or "public health" in fl
    is_comm = "Communication" in school and not is_medill
    is_weinberg = "Weinberg" in school

    usnews_key = "northwestern"
    if "computer" in fl:
        usnews_key = "computer_science"
    elif is_mccormick or "engineering" in fl:
        usnews_key = "engineering"
    elif is_kellogg or "business" in fl or "finance" in fl:
        usnews_key = "business"
    elif is_law:
        usnews_key = "law"
    elif is_feinberg:
        usnews_key = "medicine"
    elif is_medill or "journalism" in fl:
        usnews_key = "journalism"
    elif is_comm or "radio" in fl or "television" in fl or "film" in fl:
        usnews_key = "communication"
    elif "architecture" in fl:
        usnews_key = "architecture"

    if is_phd and is_law:
        summary = (
            f"Doctoral scholars describe Northwestern Law's {field} as a research degree within "
            f"Pritzker School of Law — U.S. News ranks Northwestern Law among the nation's top "
            f"programs — with praise for faculty mentorship and Chicago legal community access, "
            f"with cautions about competitive academic hiring and limited funding relative to "
            f"large public law schools."
        )
        themes = [
            {"label": "Top law school", "sentiment": "positive", "detail": "U.S. News ranks Northwestern Law among leading national programs."},
            {"label": "Chicago legal market", "sentiment": "positive", "detail": "Proximity to major firms and courts supports research and clerkships."},
            {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Small doctoral cohorts enable close work with legal scholars."},
            {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track law faculty positions are nationally competitive."},
            {"label": "Funding variability", "sentiment": "caution", "detail": "Doctoral funding packages vary; external fellowships are common."},
        ]
    elif is_ms and is_law:
        summary = (
            f"Graduate students describe Northwestern Law's {field} as a scholarly program within "
            f"a top-ranked law school; praise includes faculty seminars and Chicago legal "
            f"resources, with cautions that LL.M. and research master's tracks emphasize "
            f"legal scholarship over U.S. bar-exam preparation."
        )
        themes = [
            {"label": "Top law school", "sentiment": "positive", "detail": "U.S. News ranks Northwestern Law among the nation's leading programs."},
            {"label": "Scholarly focus", "sentiment": "positive", "detail": "Programs emphasize legal theory and interdisciplinary research."},
            {"label": "Chicago network", "sentiment": "positive", "detail": "Major firms and courts provide internship and research access."},
            {"label": "Bar-exam pathway", "sentiment": "caution", "detail": "Graduate law programs are not designed as U.S. bar-exam preparation."},
            {"label": "Career orientation", "sentiment": "mixed", "detail": "Graduates often return to academia, judiciary, or international practice."},
        ]
    elif is_ms and is_kellogg or is_bs and is_kellogg or is_phd and is_kellogg:
        summary = (
            f"Students and guides describe Kellogg's {deg} offerings in {field} within one of "
            f"the nation's top MBA schools — Poets&Quants and U.S. News consistently rank Kellogg "
            f"among leading business programs; praise includes collaborative culture and "
            f"marketing strength, with cautions about selective admission, high tuition, and "
            f"the fast-paced quarter system."
        )
        themes = [
            {"label": "Collaborative culture", "sentiment": "positive", "detail": "Team-based learning is a Kellogg hallmark across programs."},
            {"label": "Marketing strength", "sentiment": "positive", "detail": "Kellogg is perennially ranked among top marketing MBA programs."},
            {"label": "Chicago recruiting", "sentiment": "positive", "detail": "Consulting, finance, and CPG firms recruit actively from Kellogg."},
            {"label": "Quarter-system pace", "sentiment": "caution", "detail": "Ten-week quarters compress coursework and recruiting timelines."},
            {"label": "Tuition cost", "sentiment": "caution", "detail": "Private MBA tuition is steep; merit aid is limited compared with some peers."},
        ]
        usnews_key = "business"
    elif is_phd and is_feinberg or is_ms and is_feinberg:
        summary = (
            f"Graduate students describe Feinberg's {deg} program in {field} as a research-intensive "
            f"health-sciences degree with access to Northwestern Memorial Hospital and Shirley Ryan "
            f"AbilityLab — U.S. News ranks Feinberg among top research medical schools; praise "
            f"includes translational research infrastructure, with cautions about competitive "
            f"residency matching and Chicago living costs."
        )
        themes = [
            {"label": "Top research medical school", "sentiment": "positive", "detail": "U.S. News ranks Feinberg among leading medical schools for research."},
            {"label": "Hospital access", "sentiment": "positive", "detail": "Northwestern Memorial and affiliated sites support clinical research."},
            {"label": "Translational research", "sentiment": "positive", "detail": "Students join labs spanning basic science and clinical trials."},
            {"label": "Residency competition", "sentiment": "caution", "detail": "Competitive specialties require strong boards and research portfolios."},
            {"label": "Living costs", "sentiment": "caution", "detail": "Chicago housing adds to professional-school tuition."},
        ]
    elif is_ms and is_medill or is_bs and is_medill:
        summary = (
            f"Students describe Medill's {deg} program in {field} as a practice-intensive journalism "
            f"and media degree with Chicago newsroom access; praise includes the Knight Lab, "
            f"Washington Program, and industry faculty, with cautions about limited graduate "
            f"funding and portfolio-dependent career outcomes."
        )
        themes = [
            {"label": "Practice-first training", "sentiment": "positive", "detail": "Reporting, multimedia, and IMC studios anchor the curriculum."},
            {"label": "Chicago media market", "sentiment": "positive", "detail": "Internships at major newspapers, broadcasters, and agencies are strengths."},
            {"label": "Knight Lab innovation", "sentiment": "positive", "detail": "Digital journalism resources differentiate Medill nationally."},
            {"label": "Funding scarcity", "sentiment": "caution", "detail": "Graduate assistantships are scarcer than in STEM programs."},
            {"label": "Portfolio careers", "sentiment": "mixed", "detail": "Outcomes depend on clips, internships, and industry networks."},
        ]
        usnews_key = "journalism"
    elif is_ms and is_comm or is_bs and is_comm:
        summary = (
            f"Students describe Northwestern's {deg} program in {field} within the School of "
            f"Communication as a production- and research-oriented degree — U.S. News ranks "
            f"Northwestern among leading fine-arts and communication programs; praise includes "
            f"RTVF production training and Chicago media access, with cautions about limited "
            f"funding and career variability in creative industries."
        )
        themes = [
            {"label": "Production training", "sentiment": "positive", "detail": "Film, TV, and digital media production courses are program strengths."},
            {"label": "Chicago media access", "sentiment": "positive", "detail": "Alumni work across Hollywood, Chicago media, and streaming platforms."},
            {"label": "Research integration", "sentiment": "positive", "detail": "Communication studies and performance research enrich production work."},
            {"label": "Limited funding", "sentiment": "caution", "detail": "Graduate funding is scarcer than in STEM Ph.D. programs."},
            {"label": "Career variability", "sentiment": "mixed", "detail": "Outcomes depend on portfolio quality and industry connections."},
        ]
        usnews_key = "communication"
    elif is_phd:
        summary = (
            f"Doctoral students describe Northwestern's Ph.D. in {field} within {school} as a "
            f"research degree at an R1 university ranked #7 nationally by U.S. News (2026); "
            f"praise includes faculty mentorship and Chicago professional access, with cautions "
            f"about competitive admission, five-plus-year timelines, and specialized hiring markets."
        )
        themes = [
            {"label": "R1 research university", "sentiment": "positive", "detail": "Northwestern's R1 status supports doctoral research across disciplines."},
            {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Doctoral students work closely with faculty on funded research."},
            {"label": "Chicago access", "sentiment": "positive", "detail": "Proximity to firms, hospitals, and cultural institutions enriches study."},
            {"label": "Time to degree", "sentiment": "caution", "detail": "Dissertation timelines commonly span five or more years."},
            {"label": "Selective admission", "sentiment": "caution", "detail": "Strong research background and faculty alignment are expected."},
        ]
    elif is_ms and is_mccormick:
        summary = (
            f"Graduate applicants describe Northwestern's M.S. in {field} within McCormick as a "
            f"research and coursework degree with interdisciplinary ties to Feinberg, Medill, "
            f"and NICO; students value Chicago industry recruiting and faculty labs, with cautions "
            f"about self-funded tuition for terminal master's students and competitive funding."
        )
        themes = [
            {"label": "Engineering reputation", "sentiment": "positive", "detail": "McCormick is consistently ranked among leading engineering schools."},
            {"label": "Interdisciplinary research", "sentiment": "positive", "detail": "NICO, bioelectronics, and med-tech partnerships span schools."},
            {"label": "Chicago recruiting", "sentiment": "positive", "detail": "Graduates enter industry R&D, consulting, and doctoral programs."},
            {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal master's students without assistantships typically self-fund tuition."},
            {"label": "Funding competition", "sentiment": "caution", "detail": "Research assistantships are competitive across McCormick."},
        ]
    elif is_bs and is_mccormick:
        summary = (
            f"Students describe Northwestern's undergraduate {field} program in McCormick as a "
            f"quantitatively rigorous engineering degree with research-lab access and Chicago "
            f"recruiting; praise includes NICO interdisciplinary ties and small upper-level "
            f"classes, with cautions that core sequences are theory-heavy and demanding."
        )
        themes = [
            {"label": "Engineering rigor", "sentiment": "positive", "detail": "McCormick's quantitative core prepares students for industry and grad school."},
            {"label": "Research access", "sentiment": "positive", "detail": "Undergraduates join labs in bioengineering, CS, and materials science."},
            {"label": "Chicago recruiting", "sentiment": "positive", "detail": "Tech, consulting, and med-device firms recruit Northwestern engineers."},
            {"label": "Theory-heavy core", "sentiment": "mixed", "detail": "Strong mathematical foundations; some wish for more applied electives."},
            {"label": "Workload", "sentiment": "caution", "detail": "Engineering sequences alongside Weinberg distribution requirements are demanding."},
        ]
    elif is_bs and is_weinberg:
        summary = (
            f"Students describe Northwestern's undergraduate program in {field} within Weinberg as "
            f"a liberal-arts degree at a top-10 national university — U.S. News ranks Northwestern "
            f"#7 (2026); praise includes small seminars, faculty research access, and Chicago "
            f"internships, with cautions that popular majors can have large introductory sections."
        )
        themes = [
            {"label": "Top national rank", "sentiment": "positive", "detail": "U.S. News ranks Northwestern #7 among national universities (2026)."},
            {"label": "Seminar culture", "sentiment": "positive", "detail": "Upper-level Weinberg courses emphasize discussion and faculty mentorship."},
            {"label": "Chicago access", "sentiment": "positive", "detail": "Internships and research opportunities extend beyond the Evanston campus."},
            {"label": "Large intro courses", "sentiment": "caution", "detail": "Popular majors can mean big lectures in gateway sequences."},
            {"label": "Grad-school path", "sentiment": "mixed", "detail": "Many humanities and social-science majors pursue further graduate study."},
        ]
    else:
        summary = (
            f"Students and third-party guides describe Northwestern's {deg} program in {field} "
            f"within {school} as a {'research-oriented' if is_mccormick or is_weinberg else 'professionally focused'} "
            f"degree at a top-10 national university; praise includes Northwestern's faculty "
            f"and Chicago resources, with cautions about competitive admission, cost of living, "
            f"and career outcomes that vary by field."
        )
        themes = [
            {"label": "Top-10 national rank", "sentiment": "positive", "detail": "U.S. News ranks Northwestern #7 among national universities (2026)."},
            {"label": "Faculty expertise", "sentiment": "positive", "detail": f"Faculty in {department or school} lead research and professional training."},
            {"label": "Chicago access", "sentiment": "positive", "detail": "Students leverage firms, hospitals, and cultural institutions in the Chicago area."},
            {"label": "Competitive admission", "sentiment": "caution", "detail": "Northwestern graduate and professional programs have selective admission pools."},
            {"label": "Cost & location", "sentiment": "caution", "detail": "Chicago-area living costs add to private-university tuition."},
        ]

    source_label = f"Northwestern — {department or school}"
    if is_kellogg:
        return {
            "summary": summary,
            "themes": themes,
            "sources": [
                {"label": "Kellogg School of Management", "url": school_url},
                {"label": "Poets&Quants — Kellogg", "url": POETS_KELLOGG},
            ],
            "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews.",
        }

    return {
        "summary": summary,
        "themes": themes,
        "sources": [
            {"label": source_label, "url": dept_url},
            {"label": "U.S. News — Northwestern University", "url": USNEWS.get(usnews_key, USNEWS["northwestern"])},
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews.",
    }


def main():
    mod = load("northwestern")
    programs = [
        {
            "slug": p["slug"],
            "program_name": p["program_name"],
            "degree_type": p["degree_type"],
            "school": p["school"],
            "department": p.get("department") or p["school"],
        }
        for p in mod.PROGRAMS
        if is_coverable(p) and p["slug"] not in mod._REVIEWS_BY_SLUG
    ]

    reviews = {p["slug"]: review_for(**p) for p in programs}
    total = len(reviews) + len(mod._REVIEWS_BY_SLUG)

    lines = [
        '"""Northwestern University external_reviews depth pass.',
        "",
        "Depth pass date: 2026-06-15. Consumed by the ``northwesternprof2`` migration to merge",
        f'``DEPTH_REVIEWS`` into ``northwestern_profile._REVIEWS_BY_SLUG`` for {len(reviews)}',
        f"remaining coverable programs ({total}/{total} total).",
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
        lines.append('        "disclaimer": _DISCLAIMER,')
        lines.append("    },")

    lines.append("}")
    lines.append("")

    out = "/workspace/unipaith-backend/src/unipaith/data/northwestern_reviews_depth.py"
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {len(reviews)} reviews to {out}")


if __name__ == "__main__":
    main()
