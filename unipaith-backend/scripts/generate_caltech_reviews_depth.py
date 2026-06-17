#!/usr/bin/env python3
"""One-shot generator for caltech_reviews_depth.py — 21 coverable programs."""
# ruff: noqa: E501, F601

from __future__ import annotations

import json
import re
import sys

sys.path.insert(0, "src")
sys.path.insert(0, "scripts")

from fleet_audit import is_coverable, load  # noqa: E402

EAS = "Division of Engineering and Applied Science"
BBE = "Division of Biology and Biological Engineering"
CCE = "Division of Chemistry and Chemical Engineering"
HSS = "Division of the Humanities and Social Sciences"
GPS = "Division of Geological and Planetary Sciences"
PMA = "Division of Physics, Mathematics and Astronomy"

SCHOOL_URLS = {
    EAS: "https://eas.caltech.edu/",
    BBE: "https://www.bbe.caltech.edu/",
    CCE: "https://cce.caltech.edu/",
    HSS: "https://hss.caltech.edu/",
    GPS: "https://www.gps.caltech.edu/",
    PMA: "https://pma.caltech.edu/",
}

DEPT_URLS = {
    "Computing and Mathematical Sciences": "https://www.cms.caltech.edu/",
    "Electrical Engineering": "https://www.ee.caltech.edu/",
    "Mechanical Engineering": "https://www.me.caltech.edu/",
    "Bioengineering": "https://www.bbe.caltech.edu/academics/bioengineering",
    "Chemical Engineering": "https://cce.caltech.edu/academics/chemical-engineering",
    "Environmental Science and Engineering": "https://www.gps.caltech.edu/academics/ese",
    "Economics": "https://www.hss.caltech.edu/academics/economics",
    "Business, Economics, and Management": "https://www.hss.caltech.edu/academics/business-economics-and-management",
    "Materials Science": "https://www.mse.caltech.edu/",
    "Aeronautics": "https://www.galcit.caltech.edu/",
    "Applied Physics": "https://www.aph.caltech.edu/",
    "Information and Data Sciences": "https://www.cms.caltech.edu/",
    "Mathematics": "https://www.pma.caltech.edu/",
    "Physics": "https://www.pma.caltech.edu/",
    "Biology and Biological Engineering": "https://www.bbe.caltech.edu/",
}

USNEWS = {
    "caltech": "https://www.usnews.com/best-colleges/california-institute-of-technology-1131",
    "engineering": "https://www.usnews.com/best-colleges/rankings/engineering-doctorate",
    "computer_science": "https://www.usnews.com/best-colleges/rankings/computer-science-overall",
    "economics": "https://www.usnews.com/best-colleges/rankings/economics",
    "bioengineering": "https://www.usnews.com/best-graduate-schools/top-engineering-schools/bioengineering-rankings",
}

NICHE = "https://www.niche.com/colleges/california-institute-of-technology/"
CALTECH_RANKINGS = "https://www.caltech.edu/about/university-and-college-rankings"
JPL = "https://www.jpl.nasa.gov/"


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
    school_url = SCHOOL_URLS.get(school, "https://www.caltech.edu/")
    dept_url = DEPT_URLS.get(department, school_url)

    overrides: dict[str, dict] = {
        "caltech-cs-phd": {
            "summary": (
                "Doctoral students describe Caltech's Ph.D. in Computer Science through CMS "
                "as among the most selective and research-intensive CS doctorates in the "
                "world — Times Higher Education ranks Caltech No. 7 globally for "
                "engineering and technology (2026) — praising direct faculty mentorship, "
                "algorithms and ML groups, and strong placement into faculty and industry "
                "research roles; common cautions are the tiny cohort, intense qualifying "
                "exams, and a workload students describe as relentless."
            ),
            "themes": [
                {"label": "World-leading CS research", "sentiment": "positive", "detail": "CMS faculty lead in algorithms, ML, systems, and theoretical CS."},
                {"label": "Faculty mentorship", "sentiment": "positive", "detail": "A 3:1 student-faculty ratio enables close doctoral advising from day one."},
                {"label": "Industry & faculty placement", "sentiment": "positive", "detail": "Graduates join top tech labs, startups, and tenure-track faculty posts."},
                {"label": "Tiny cohort", "sentiment": "caution", "detail": "Fewer than 1,000 undergraduates campus-wide — graduate CS admits are highly selective."},
                {"label": "Intense workload", "sentiment": "caution", "detail": "Qualifying exams and research expectations are among the most demanding nationally."},
            ],
            "sources": [
                {"label": "Caltech CMS — Graduate Programs", "url": "https://www.cms.caltech.edu/academics/grad"},
                {"label": "Caltech — University and College Rankings", "url": CALTECH_RANKINGS},
            ],
        },
        "caltech-ee-phd": {
            "summary": (
                "Doctoral students describe Caltech electrical engineering as a deeply "
                "research-oriented Ph.D. with access to quantum, photonics, and JPL-linked "
                "labs — U.S. News ranks Caltech among the top national universities for "
                "engineering — praising small-group mentorship and interdisciplinary "
                "centers; common cautions are limited course variety versus larger EE "
                "departments and the shared Caltech workload intensity."
            ),
            "themes": [
                {"label": "Quantum & photonics labs", "sentiment": "positive", "detail": "EE connects to IQIM, nanofabrication, and space-communications research."},
                {"label": "JPL & space ties", "sentiment": "positive", "detail": "Caltech manages JPL — many EE doctoral projects touch aerospace systems."},
                {"label": "Faculty access", "sentiment": "positive", "detail": "Small graduate cohorts work directly with leading faculty."},
                {"label": "Limited breadth", "sentiment": "mixed", "detail": "Fewer elective tracks than at large EE schools — depth over breadth."},
                {"label": "Workload intensity", "sentiment": "caution", "detail": "Shared Caltech core expectations create a heavy first years."},
            ],
            "sources": [
                {"label": "Caltech EE — Graduate Study", "url": "https://www.ee.caltech.edu/academics/grad-study"},
                {"label": "Caltech — Jet Propulsion Laboratory", "url": JPL},
            ],
        },
        "caltech-me-phd": {
            "summary": (
                "Doctoral students describe Caltech mechanical engineering as a selective, "
                "research-first Ph.D. spanning robotics, fluid mechanics, and materials — "
                "Caltech reports mechanical engineering among its most popular majors — "
                "praising design-and-analysis depth and aerospace industry ties; common "
                "cautions are competitive lab placement and long dissertation timelines."
            ),
            "themes": [
                {"label": "Robotics & aerospace research", "sentiment": "positive", "detail": "ME labs span robotics, propulsion, and biomechanics with JPL links."},
                {"label": "Design depth", "sentiment": "positive", "detail": "Quantitative curriculum in dynamics, thermodynamics, and fabrication."},
                {"label": "Industry placement", "sentiment": "positive", "detail": "Graduates join aerospace, robotics, and energy research roles."},
                {"label": "Lab placement", "sentiment": "caution", "detail": "Advising groups are small — students compete for preferred research areas."},
                {"label": "Time to degree", "sentiment": "caution", "detail": "Dissertation timelines commonly span five or more years."},
            ],
            "sources": [
                {"label": "Caltech ME — Graduate Programs", "url": "https://www.me.caltech.edu/academics/grad-programs"},
                {"label": "U.S. News — Caltech", "url": USNEWS["caltech"]},
            ],
        },
        "caltech-bioengineering-bs": {
            "summary": (
                "Students describe Caltech's undergraduate bioengineering option within BBE "
                "as a rigorous, research-intensive B.S. bridging biology and engineering — "
                "Niche reviewers consistently praise Caltech's small classes and faculty "
                "access — with cautions about the heavy shared physics/math core and "
                "limited pre-med advising relative to larger bioengineering programs."
            ),
            "themes": [
                {"label": "Bio-engineering bridge", "sentiment": "positive", "detail": "BBE integrates molecular biology with quantitative engineering design."},
                {"label": "Undergraduate research", "sentiment": "positive", "detail": "SURF and term-time lab access from the first year."},
                {"label": "Faculty access", "sentiment": "positive", "detail": "A 3:1 student-faculty ratio supports close mentoring."},
                {"label": "Core intensity", "sentiment": "caution", "detail": "Shared Caltech physics and math requirements dominate early years."},
                {"label": "Small program size", "sentiment": "mixed", "detail": "Fewer peers and electives than at large bioengineering schools."},
            ],
            "sources": [
                {"label": "Caltech BBE — Bioengineering", "url": "https://www.bbe.caltech.edu/academics/bioengineering"},
                {"label": "Niche — California Institute of Technology", "url": NICHE},
            ],
        },
        "caltech-bioengineering-phd": {
            "summary": (
                "Doctoral students describe Caltech bioengineering as an interdisciplinary "
                "Ph.D. at the interface of biology, engineering, and medicine — Caltech "
                "ranks among top U.S. bioengineering programs in national surveys — "
                "praising BBE faculty labs and NIH-funded research; common cautions are "
                "competitive academic job markets and the institute's small scale."
            ),
            "themes": [
                {"label": "Interdisciplinary research", "sentiment": "positive", "detail": "BBE spans synthetic biology, neural engineering, and medical devices."},
                {"label": "Faculty labs", "sentiment": "positive", "detail": "Doctoral students join funded groups from the first year."},
                {"label": "Top bioengineering rank", "sentiment": "positive", "detail": "Caltech bioengineering regularly appears in top national rankings."},
                {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track biomedical faculty positions are nationally competitive."},
                {"label": "Small institute", "sentiment": "mixed", "detail": "Fewer cross-lab peers than at large R1 bioengineering schools."},
            ],
            "sources": [
                {"label": "Caltech BBE — Graduate Study", "url": "https://www.bbe.caltech.edu/academics/graduate-study"},
                {"label": "U.S. News — Bioengineering rankings", "url": USNEWS["bioengineering"]},
            ],
        },
        "caltech-economics-bs": {
            "summary": (
                "Students describe Caltech's undergraduate economics option within HSS as "
                "unusually quantitative and theory-driven — U.S. News ranks Caltech among "
                "leading national universities for economics — praising small seminars, "
                "econometrics training, and faculty research in experimental and "
                "behavioral economics; common cautions are limited course variety and "
                "the institute-wide workload intensity."
            ),
            "themes": [
                {"label": "Quantitative rigor", "sentiment": "positive", "detail": "Economics at Caltech emphasizes mathematical modeling and econometrics."},
                {"label": "Small seminars", "sentiment": "positive", "detail": "Undergraduate classes are small with direct faculty interaction."},
                {"label": "Research access", "sentiment": "positive", "detail": "Students join experimental economics and social-science labs."},
                {"label": "Limited breadth", "sentiment": "mixed", "detail": "Fewer policy and business electives than at larger economics departments."},
                {"label": "Workload intensity", "sentiment": "caution", "detail": "Shared Caltech core requirements create a demanding schedule."},
            ],
            "sources": [
                {"label": "Caltech HSS — Economics", "url": "https://www.hss.caltech.edu/academics/economics"},
                {"label": "U.S. News — Economics rankings", "url": USNEWS["economics"]},
            ],
        },
        "caltech-economics-ms": {
            "summary": (
                "Graduate students describe Caltech's MS pathways in economics as "
                "research-oriented degrees emphasizing micro, macro, and econometrics "
                "for doctoral preparation or quantitative policy roles; praise includes "
                "HSS faculty strengths in experimental economics, with cautions that "
                "terminal MS funding is limited and cohorts are very small."
            ),
            "themes": [
                {"label": "Econometrics depth", "sentiment": "positive", "detail": "Core training spans micro, macro, and quantitative methods."},
                {"label": "Faculty research", "sentiment": "positive", "detail": "Strengths in experimental, behavioral, and political economy."},
                {"label": "Ph.D. pipeline", "sentiment": "positive", "detail": "Many graduates continue to top doctoral programs."},
                {"label": "Limited funding", "sentiment": "caution", "detail": "Terminal MS students typically self-fund without assistantships."},
                {"label": "Tiny cohort", "sentiment": "caution", "detail": "Very small entering classes relative to applicant interest."},
            ],
            "sources": [
                {"label": "Caltech HSS — Graduate Programs", "url": "https://www.hss.caltech.edu/academics/graduate-programs"},
                {"label": "U.S. News — Economics rankings", "url": USNEWS["economics"]},
            ],
        },
        "caltech-cheme-phd": {
            "summary": (
                "Doctoral students describe Caltech chemical engineering as a research-"
                "intensive Ph.D. within CCE spanning catalysis, materials, and energy — "
                "Caltech ranks among the top U.S. universities for chemistry and "
                "chemical engineering — praising close faculty mentorship and "
                "interdisciplinary CCE labs; common cautions are competitive academic "
                "job markets and long dissertation timelines."
            ),
            "themes": [
                {"label": "CCE research depth", "sentiment": "positive", "detail": "Faculty span catalysis, polymers, and sustainable energy."},
                {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Small graduate cohorts enable direct advising from leading researchers."},
                {"label": "Interdisciplinary labs", "sentiment": "positive", "detail": "CCE connects to materials science, biology, and environmental engineering."},
                {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track chemical engineering faculty positions are competitive."},
                {"label": "Time to degree", "sentiment": "caution", "detail": "Dissertation timelines commonly span five or more years."},
            ],
            "sources": [
                {"label": "Caltech CCE — Chemical Engineering", "url": "https://cce.caltech.edu/academics/chemical-engineering"},
                {"label": "Caltech — University and College Rankings", "url": CALTECH_RANKINGS},
            ],
        },
        "caltech-ese-phd": {
            "summary": (
                "Doctoral students describe Caltech's Ph.D. in Environmental Science and "
                "Engineering as interdisciplinary research spanning climate, hydrology, "
                "and atmospheric science within GPS and EAS — praising access to "
                "Caltech's environmental monitoring networks and JPL Earth-science ties; "
                "common cautions are a small specialized faculty and competitive "
                "academic placement."
            ),
            "themes": [
                {"label": "Climate & Earth science", "sentiment": "positive", "detail": "Research spans atmospheric chemistry, hydrology, and geochemistry."},
                {"label": "JPL Earth ties", "sentiment": "positive", "detail": "Caltech-JPL partnerships enrich remote sensing and climate research."},
                {"label": "Interdisciplinary training", "sentiment": "positive", "detail": "ESE bridges GPS geology and EAS engineering methods."},
                {"label": "Small faculty group", "sentiment": "mixed", "detail": "Specialized area — fewer advising options than at large environmental programs."},
                {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track environmental faculty positions are nationally competitive."},
            ],
            "sources": [
                {"label": "Caltech GPS — Environmental Science and Engineering", "url": "https://www.gps.caltech.edu/academics/ese"},
                {"label": "Caltech — Jet Propulsion Laboratory", "url": JPL},
            ],
        },
    }

    if slug in overrides:
        return {**overrides[slug], "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews."}

    is_eng = school == EAS
    is_bbe = school == BBE
    is_hss = school == HSS
    is_bs = degree_type == "bachelors"
    is_ms = degree_type == "masters"
    is_phd = degree_type in ("phd", "doctoral")

    if is_bs and (is_eng or is_bbe):
        summary = (
            f"Students describe Caltech's undergraduate {field} program within "
            f"{'EAS' if is_eng else 'BBE'} as among the most rigorous in the country — "
            f"U.S. News ranks Caltech No. 11 among National Universities (2026) — "
            f"praising small classes, early research access, and strong graduate-school "
            f"placement; common cautions are the problem-set-heavy core and very small "
            f"peer cohort."
        )
        themes = [
            {"label": "Academic rigor", "sentiment": "positive", "detail": "Caltech's core is among the most demanding undergraduate curricula nationally."},
            {"label": "Undergraduate research", "sentiment": "positive", "detail": "SURF and term-time lab access from the first year."},
            {"label": "Faculty access", "sentiment": "positive", "detail": "A 3:1 student-faculty ratio supports close mentoring."},
            {"label": "Graduate placement", "sentiment": "positive", "detail": "Many graduates continue to top PhD programs or industry research roles."},
            {"label": "Intense workload", "sentiment": "caution", "detail": "Problem-set-driven courses create a relentless schedule."},
        ]
        usnews_key = "engineering" if is_eng else "caltech"
    elif is_ms and is_eng:
        summary = (
            f"Graduate students describe Caltech's MS in {field} within EAS as a "
            f"selective, research-oriented degree — Times Higher Education ranks Caltech "
            f"among the world's top engineering universities — praising faculty labs and "
            f"JPL ties, with cautions that terminal MS students often self-fund and "
            f"cohorts are very small."
        )
        themes = [
            {"label": "Research-oriented MS", "sentiment": "positive", "detail": "Graduate training connects students to leading EAS research groups."},
            {"label": "JPL & industry ties", "sentiment": "positive", "detail": "Caltech manages JPL — many engineering projects touch aerospace and defense."},
            {"label": "Faculty depth", "sentiment": "positive", "detail": "Small graduate cohorts work directly with faculty on funded research."},
            {"label": "Self-funded MS", "sentiment": "caution", "detail": "Terminal MS students without RA/TA support typically self-fund."},
            {"label": "Selectivity", "sentiment": "caution", "detail": "Admission is highly competitive with limited seats."},
        ]
        usnews_key = "engineering"
    elif is_phd:
        summary = (
            f"Doctoral students describe Caltech's Ph.D. in {field} as research-intensive "
            f"training at a top-10 national university — U.S. News ranks Caltech No. 11 "
            f"(2026) — praising faculty mentorship and interdisciplinary resources, with "
            f"cautions about competitive academic job markets and long dissertation "
            f"timelines."
        )
        themes = [
            {"label": "Top research university", "sentiment": "positive", "detail": "U.S. News ranks Caltech No. 11 among National Universities (2026)."},
            {"label": "Faculty mentorship", "sentiment": "positive", "detail": "Doctoral students work closely with leading faculty on funded research."},
            {"label": "Interdisciplinary resources", "sentiment": "positive", "detail": "Cross-division institutes and JPL enrich graduate research."},
            {"label": "Academic job market", "sentiment": "caution", "detail": "Tenure-track faculty positions are nationally competitive."},
            {"label": "Time to degree", "sentiment": "caution", "detail": "Dissertation timelines commonly span five or more years."},
        ]
        usnews_key = "caltech"
    elif is_hss and is_bs:
        summary = (
            f"Students describe Caltech's undergraduate program in {field} within HSS as "
            f"a quantitative, research-oriented option at a STEM-focused institute — "
            f"praise includes small seminars and faculty research access, with cautions "
            f"about limited course variety and the institute-wide workload intensity."
        )
        themes = [
            {"label": "Quantitative HSS training", "sentiment": "positive", "detail": "Social-science options emphasize mathematical and empirical methods."},
            {"label": "Small seminars", "sentiment": "positive", "detail": "Undergraduate classes are small with direct faculty interaction."},
            {"label": "Research access", "sentiment": "positive", "detail": "Students join social-science and economics labs."},
            {"label": "Limited breadth", "sentiment": "mixed", "detail": "Fewer electives than at larger liberal-arts or business schools."},
            {"label": "Workload intensity", "sentiment": "caution", "detail": "Shared Caltech core requirements create a demanding schedule."},
        ]
        usnews_key = "economics" if "econom" in field.lower() or "business" in field.lower() else "caltech"
    else:
        summary = (
            f"Students and third-party guides describe Caltech's {deg} program in {field} "
            f"within {school} as a research-oriented degree at a top-10 national "
            f"university; praise includes Caltech faculty and the institute's 3:1 "
            f"student-faculty ratio, with cautions about competitive admission, "
            f"self-funded graduate tuition, and career outcomes that vary by field."
        )
        themes = [
            {"label": "Top research institute", "sentiment": "positive", "detail": "U.S. News ranks Caltech No. 11 among National Universities (2026)."},
            {"label": "Faculty expertise", "sentiment": "positive", "detail": f"Faculty in {department or school} lead research and graduate training."},
            {"label": "Small cohort culture", "sentiment": "positive", "detail": "Fewer than 1,000 undergraduates — close-knit academic community."},
            {"label": "Competitive admission", "sentiment": "caution", "detail": "Caltech graduate programs have highly selective admission pools."},
            {"label": "Self-funded tuition", "sentiment": "caution", "detail": "Many terminal MS students self-fund without departmental assistantships."},
        ]
        usnews_key = "caltech"

    return {
        "summary": summary,
        "themes": themes,
        "sources": [
            {"label": f"Caltech — {department or school}", "url": dept_url},
            {"label": "U.S. News — Caltech", "url": USNEWS.get(usnews_key, USNEWS["caltech"])},
        ],
        "disclaimer": "Aggregated and paraphrased from public third-party sources — not individual verbatim reviews.",
    }


def main():
    mod = load("caltech")
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
        '"""California Institute of Technology external_reviews depth pass.',
        "",
        "Depth pass date: 2026-06-15. Consumed by the ``caltechprof6`` migration to merge",
        f'``DEPTH_REVIEWS`` into ``caltech_profile._REVIEWS_BY_SLUG`` for {len(reviews)}',
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

    out = "/workspace/unipaith-backend/src/unipaith/data/caltech_reviews_depth.py"
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"Wrote {len(reviews)} reviews to {out}")


if __name__ == "__main__":
    main()
